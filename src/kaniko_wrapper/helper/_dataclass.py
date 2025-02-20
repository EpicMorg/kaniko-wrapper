import os
import yaml
import argparse
import subprocess
from typing import Dict, List

from dataclasses import dataclass
from kaniko_wrapper.helper.log_print import logger


@dataclass
class BuildKaniko:
    service_name: str
    build_context: str
    dockerfile: str
    image_name: str
    build_args: dict
    kaniko_image: str
    deploy: bool
    dry: bool
    no_push: bool


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

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Kaniko-Compose Wrapper", add_help=False
    )

    def __post_init__(self):
        self._add_arguments()

    def _add_arguments(self):
        self.parser.add_argument(
            "--compose-file",
            default=os.getenv("COMPOSE_FILE", "docker-compose.yml"),
            help="Path to docker-compose.yml file",
        )
        self.parser.add_argument(
            "--kaniko-image",
            default=os.getenv("KANIKO_IMAGE", "gcr.io/kaniko-project/executor:latest"),
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

    def build(self):
        kaniko_command = self._generate_kaniko_command()
        logger.info(
            f"Building {self.service_name} with Kaniko: {' '.join(kaniko_command)}"
        )

        with subprocess.Popen(
            kaniko_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        ) as process:
            self._log_process_output(process)

            if process.returncode != 0:
                raise Exception(f"Failed to build {self.service_name}")

    def _generate_kaniko_command(self) -> List[str]:
        """Generate the Kaniko command based on the provided parameters."""
        kaniko_command = [
            "docker",
            "run",
            "--rm",
            "-t",
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

        if self.deploy:
            kaniko_command.extend(["--destination", self.image_name])
        elif self.dry:
            kaniko_command.extend(["--no-push"])

        if self.no_push:
            kaniko_command.append("--no-push")

        for arg_name, arg_value in self.build_args.items():
            kaniko_command.append(f"--build-arg {arg_name}={arg_value}")

        return kaniko_command

    @staticmethod
    def _log_process_output(process):
        """Helper function to log the output and errors from the build process."""
        for line in process.stdout:
            logger.info(line.strip())
        for line in process.stderr:
            logger.error(line.strip())
