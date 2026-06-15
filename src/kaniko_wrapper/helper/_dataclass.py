import os
import yaml
import argparse
import subprocess
import threading
from collections import deque
from typing import Dict, List, Optional

from dataclasses import dataclass, field
from kaniko_wrapper.helper.log_print import logger


class KanikoBuildError(RuntimeError):
    """Raised when a kaniko build/push returns a non-zero exit code."""


@dataclass
class ComposeFileLoader:
    """Class responsible for loading the docker-compose.yml file."""

    compose_file: str

    def load(self) -> Dict:
        """Load and parse the YAML docker-compose file."""
        if not os.path.exists(self.compose_file):
            raise FileNotFoundError(f"The file {self.compose_file} does not exist.")
        try:
            with open(self.compose_file, "r") as file:
                return yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise Exception(f"Error loading YAML file: {e}")


@dataclass
class ArgParser:
    """Class responsible for parsing command line arguments."""

    parser: argparse.ArgumentParser = None

    def __post_init__(self):
        if self.parser is None:
            self.parser = argparse.ArgumentParser(
                description="Kaniko-Compose Wrapper", add_help=False
            )
            self._add_arguments()

    def _add_arguments(self):
        self.parser.add_argument(
            "--compose-file",
            default=os.getenv("COMPOSE_FILE", "docker-compose.yml"),
            help="Path to docker-compose.yml file",
        )
        self.parser.add_argument(
            "--kaniko-image",
            default=os.getenv(
                "KANIKO_IMAGE", "ghcr.io/osscontainertools/kaniko:latest"
            ),
            help="Kaniko executor image",
        )
        self.parser.add_argument(
            "--push",
            "--deploy",
            "-d",
            "-p",
            action="store_true",
            help="Deploy the built images to the registry",
        )
        self.parser.add_argument(
            "--dry-run",
            "--dry",
            action="store_true",
            help="Dry run: build images without pushing and with cleanup",
        )
        self.parser.add_argument(
            "--no-push",
            action="store_true",
            help="Do not push the image to the registry",
        )
        self.parser.add_argument(
            "--version", "-v", action="store_true", help="Show script version"
        )
        self.parser.add_argument(
            "--help", "-h", action="store_true", help="Show this help message and exit"
        )
        self.parser.add_argument(
            "--docker-dir",
            type=str,
            help="Path to the directory with Dockerfiles",
        )

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args()


@dataclass
class BuildKaniko:
    """Class responsible for building Docker images using Kaniko."""

    service_name: str
    build_context: str
    dockerfile: str
    image_name: str
    build_args: Dict[str, str]
    kaniko_image: str
    deploy: bool
    dry: bool
    no_push: bool
    # Container engine used to run the kaniko executor. Hardcoded to "docker"
    # for now; exposed as a field so 2.0.2.6 can wire it to --engine without
    # touching the command body.
    engine: str = "docker"
    # Extra push destinations (variant A: kaniko multi --destination).
    # Populated from the compose `x-mirrors` key in KanikoBuilder.
    mirrors: List[str] = field(default_factory=list)

    def build(self) -> None:
        """Build the Docker image using Kaniko."""
        if not os.path.exists(self.build_context):
            raise FileNotFoundError(f"Build context not found: {self.build_context}")
        if not os.path.exists(os.path.join(self.build_context, self.dockerfile)):
            raise FileNotFoundError(f"Dockerfile not found: {self.dockerfile}")

        kaniko_command = self._generate_kaniko_command()
        logger.info(
            f"Building {self.service_name} with Kaniko: {' '.join(kaniko_command)}"
        )

        # Tail of stderr, kept so we can resurface the failure cause at ERROR
        # level when the build fails (stderr itself is logged at DEBUG).
        stderr_tail: deque = deque(maxlen=50)

        process = subprocess.Popen(
            kaniko_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Drain both pipes concurrently. Reading them sequentially deadlocks
        # on heavy images once the unread pipe fills its 64K kernel buffer.
        t_out = threading.Thread(
            target=self._drain, args=(process.stdout, logger.info), daemon=True
        )
        t_err = threading.Thread(
            target=self._drain,
            args=(process.stderr, logger.debug, stderr_tail),
            daemon=True,
        )
        t_out.start()
        t_err.start()
        t_out.join()
        t_err.join()

        returncode = process.wait()

        # Failure is decided by the exit code ONLY. stderr is not an error
        # channel: docker/podman pull progress and kaniko's own logs land
        # there even on a fully successful build.
        if returncode != 0:
            for line in stderr_tail:
                logger.error(f"[{self.service_name}] {line}")
            raise KanikoBuildError(
                f"{self.service_name}: kaniko exited with code {returncode}"
            )

        logger.info(f"{self.service_name} built successfully.")

    def _generate_kaniko_command(self) -> List[str]:
        """Generate the Kaniko command based on the provided parameters."""
        kaniko_command = [
            self.engine,
            "run",
            "--rm",
            "-v",
            f"{os.path.abspath(self.build_context)}:/workspace",
            "-v",
            f'{os.path.expanduser("~")}/.docker:/kaniko/.docker:ro',
            self.kaniko_image,
            "--context",
            "/workspace",
            "--dockerfile",
            f"/workspace/{self.dockerfile}",
            "--use-new-run",
            "--push-retry=7",
            "--image-fs-extract-retry=7",
            "--image-download-retry=7",
            "--snapshot-mode=full",
            "--log-timestamp=false",
            "--cache=false",
            "--single-snapshot",
            "--cleanup",
        ]

        if self.deploy and not self.no_push:
            for dest in self._destinations():
                kaniko_command.extend(["--destination", dest])
        elif self.dry or self.no_push:
            kaniko_command.append("--no-push")

        for arg_name, arg_value in self.build_args.items():
            kaniko_command.extend(["--build-arg", f"{arg_name}={arg_value}"])

        return kaniko_command

    def _destinations(self) -> List[str]:
        """Primary image plus mirrors, de-duplicated, empties dropped.

        Variant A: a single kaniko run pushes the built image to every
        destination via repeated --destination flags. A failed push to any
        destination makes kaniko exit non-zero (after --push-retry), so the
        mirror failure is fatal for free, with no skopeo round-trip.
        """
        seen = set()
        result: List[str] = []
        for dest in [self.image_name, *self.mirrors]:
            dest = (dest or "").strip()
            if dest and dest not in seen:
                seen.add(dest)
                result.append(dest)
        return result

    @staticmethod
    def _drain(stream, log_fn, sink: Optional[deque] = None) -> None:
        """Read a child stream line by line, log each line, optionally buffer.

        Does not reinterpret severity from the stream identity: the caller
        decides the log level (stdout -> info, stderr -> debug). Failure is
        determined later from the process return code.
        """
        try:
            for raw in iter(stream.readline, ""):
                line = raw.rstrip("\n")
                if not line:
                    continue
                log_fn(line)
                if sink is not None:
                    sink.append(line)
        finally:
            stream.close()