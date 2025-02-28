from kaniko_wrapper.helper.log_print import logger
from kaniko_wrapper.helper._dataclass import ComposeFileLoader, BuildKaniko


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
            dockerfile = service_info.get("build", {}).get("dockerfile", "Dockerfile")
            build_context = service_info.get("build", {}).get("context", ".")
            image_name = service_info.get("image", "")
            build_args = service_info.get("build", {}).get("args", {})

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
            )
            self.services.append(service)

    def build_services(self):
        """Build all services using Kaniko."""
        for service in self.services:
            try:
                service.build()
            except Exception as e:
                logger.error(f"Failed to build service {service.service_name}: {e}")
