import subprocess

from kaniko_wrapper.helper.log_print import logger
from kaniko_wrapper.helper._dataclass import (
    ComposeFileLoader,
    BuildKaniko,
    KanikoBuildError,
)


class KanikoBuilder:
    """Class responsible for orchestrating the build process."""

    def __init__(self, args):
        self.args = args
        self.compose_file = args.compose_file
        self.kaniko_image = args.kaniko_image
        self.deploy = args.push
        self.dry_run = args.dry_run
        self.no_push = args.no_push
        self.docker_dir = args.docker_dir
        self.engine = args.engine
        self.network = args.network or ("host" if self.engine == "podman" else None)
        self.services = []

    def validate_compose_file(self):
        """Validate and load the docker-compose file."""
        loader = ComposeFileLoader(self.compose_file)
        try:
            self.compose_data = loader.load()
            logger.info(f"Successfully loaded compose file: {self.compose_file}")
        except Exception as e:
            logger.error(f"Error loading compose file: {e}")
            raise e

    def process_services(self):
        """Process services from the docker-compose file."""
        if "services" not in self.compose_data:
            logger.error("No services found in docker-compose file.")
            raise ValueError("No services found in docker-compose file.")

        for service_name, service_info in self.compose_data["services"].items():
            if not service_info:
                logger.warning(f"Skipping empty service definition: {service_name}")
                continue

            if "build" not in service_info:
                # Pull-only service (external image, no build section): nothing
                # for kaniko to build.
                logger.info(f"Skipping service without build section: {service_name}")
                continue

            build = service_info["build"]
            if not isinstance(build, dict):
                # Short-form `build: ./path` is not handled by the command
                # builder; fail loudly instead of crashing on .get().
                raise ValueError(
                    f"{service_name}: short-form 'build: <path>' is not supported; "
                    f"use the long form with context/dockerfile."
                )

            dockerfile = build.get("dockerfile", "Dockerfile")
            build_context = build.get("context", ".")
            build_args = build.get("args", {})
            image_name = service_info.get("image", "")

            mirrors = service_info.get("x-mirrors", []) or []
            if not isinstance(mirrors, list):
                raise ValueError(
                    f"{service_name}: x-mirrors must be a list of image "
                    f"references, got {type(mirrors).__name__}"
                )

            service = BuildKaniko(
                service_name=service_name,
                build_context=build_context,
                dockerfile=dockerfile,
                image_name=image_name,
                build_args=build_args,
                kaniko_image=self.kaniko_image,
                deploy=self.deploy,
                dry=self.dry_run,
                no_push=self.no_push,
                engine=self.engine,
                mirrors=mirrors,
                network=self.network,
            )
            self.services.append(service)

    def ensure_executor(self):
        """Ensure the kaniko executor image is present locally before building.

        Pulling once, up front, keeps the engine's pull progress (which is
        written to stderr) out of the per-build logs, and fails fast if the
        image is unreachable instead of failing mid-run on the first service.
        """
        inspect = subprocess.run(
            [self.engine, "image", "inspect", self.kaniko_image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if inspect.returncode == 0:
            logger.info(f"Kaniko executor present: {self.kaniko_image}")
            return

        logger.info(f"Pulling kaniko executor: {self.kaniko_image}")
        pull = subprocess.run([self.engine, "pull", self.kaniko_image])
        if pull.returncode != 0:
            raise RuntimeError(
                f"Failed to pull kaniko executor {self.kaniko_image} "
                f"(engine={self.engine}, rc={pull.returncode})"
            )

    def build_services(self):
        """Build all services using Kaniko."""
        if not self.services:
            logger.warning("No services to build.")
            return

        self.ensure_executor()

        failed = []
        for service in self.services:
            try:
                service.build()
            except Exception as e:
                logger.error(f"Failed to build service {service.service_name}: {e}")
                failed.append(service.service_name)

        if failed:
            raise KanikoBuildError(
                f"{len(failed)} service(s) failed: {', '.join(failed)}"
            )