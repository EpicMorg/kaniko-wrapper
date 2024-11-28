"""
EpicMorg: Kaniko-Compose Wrapper

Usage:
    kaniko [--compose-file=<file>] build [--kaniko-image=<image>] [--push | --deploy | --dry-run] [--version] [--help]

Options:
  --compose-file=<file>           Path to the docker-compose.yml file. [default: docker-compose.yml]
  --kaniko-image=<image>          Kaniko executor image for building. [default: gcr.io/kaniko-project/executor:latest]
  --push, -p                      Push the built images to a registry.
  --deploy, -d                    Deploy images to the registry after building.
  --dry-run, --dry                Run in test mode: build images without pushing, with cleanup.
  --version, -v                   Show script version.
  -h --help                       Show this help message and exit.
"""

import logging
import typing as t

from kaniko import helpers
from kaniko.helpers.logger_file import VerbosityLevel
from kaniko.settings import SCRIPT_VERSION


def configure_logging() -> logging.Logger:
    """Configure and return a logger instance."""
    helpers.logger_file.configure_logging(verbosity=VerbosityLevel.NORMAL)
    return logging.getLogger("KanikoComposeWrapper")


def parse_options(opts: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Parse and validate options from the command line."""
    return {
        "compose_file": opts.get("--compose-file", "docker-compose.yml"),
        "kaniko_image": opts.get(
            "--kaniko-image", "gcr.io/kaniko-project/executor:latest"
        ),
        "push": opts.get("--push", False),
        "deploy": opts.get("--deploy", False),
        "dry_run": opts.get("--dry-run", False),
        "version": opts.get("--version", False),
    }


def validate_options(opts: t.Dict[str, t.Any], logger: logging.Logger) -> bool:
    """Validate required options and log errors if needed."""
    if not opts["compose_file"]:
        logger.error(
            "❌ Docker Compose file path is missing. "
            "Please provide a valid file with the --compose-file option."
        )
        return False

    if not opts["kaniko_image"]:
        logger.error(
            "❌ Kaniko executor image is missing. "
            "Please provide a valid image with the --kaniko-image option."
        )
        return False

    return True


def log_build_details(opts: t.Dict[str, t.Any], logger: logging.Logger) -> None:
    """Log detailed build settings."""
    logger.info(f"📁 Using docker-compose file: {opts['compose_file']}")
    logger.info(f"🛠️ Kaniko executor image: {opts['kaniko_image']}")
    if opts["push"]:
        logger.info("📤 Images will be pushed to the registry after build.")
    elif opts["deploy"]:
        logger.info("🌐 Images will be deployed to the registry after build.")
    elif opts["dry_run"]:
        logger.info("🔍 Running in dry-run mode. No images will be pushed.")
    else:
        logger.warning(
            "⚠️ No deployment action specified: images will neither be pushed nor deployed."
        )


def run_build(opts: t.Dict[str, t.Any], logger: logging.Logger) -> None:
    """Simulate the Kaniko build process."""
    logger.debug(
        "\n⚙️ Preparing Kaniko build with options...\n"
        f"compose_file: {opts['compose_file']}, \n"
        f"kaniko_image: {opts['kaniko_image']}, \n"
        f"push: {opts['push']}, \n"
        f"deploy: {opts['deploy']}, \n"
        f"dry_run: {opts['dry_run']}.\n"
    )
    logger.info("⚙️ Kaniko build process is now running... (details not implemented).")
    logger.info("✅ Kaniko build process completed successfully!")


def run(opts: t.Dict[str, t.Any]) -> None:
    """Main entry point for the script."""
    logger = configure_logging()
    options = parse_options(opts)

    if options["version"]:
        logger.info(f"📄 Kaniko Builder Version: {SCRIPT_VERSION}")
        return

    logger.info("🚀 Starting Kaniko build process...")

    if not validate_options(options, logger):
        return

    log_build_details(options, logger)
    run_build(options, logger)
