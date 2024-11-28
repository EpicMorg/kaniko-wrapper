"""
EpicMorg: Kaniko-Compose Wrapper

Description:
    This script is designed to automate Docker image building using Kaniko and docker-compose.
    It supports testing, deployment, and publishing images to a registry.

Usage:
    kaniko [options...] <command> [<args>...]
    kaniko (-h | --help | --version)


Global Options:
    -e, --allow-dotenv <path>       Load environment variables from the specified file. [default: .env]
    -h, --help                      Show usage help.
    --version                       Show script version.

Commands:
    build                       Run image building with Kaniko.

Examples:
    1. Build and push images with default settings:
       kaniko build --push

    2. Build using a custom docker-compose file and Kaniko image:
       kaniko build --compose-file=custom-compose.yml --kaniko-image=my-kaniko-image

    3. Test build without pushing to registry:
       kaniko build --dry-run
"""

import json
import logging
import types
import typing as t

import docopt
import dotenv

from kaniko.helpers.logger_file import configure_logging, VerbosityLevel
from kaniko import settings, helpers, commands

logger = logging.getLogger(__name__)

settings.PACKAGE_VERSION = PACKAGE_VERSION = helpers


def run_command(opts: t.Dict[str, t.Any]):
    command_name = opts["<command>"]
    match command_name:
        case "build":
            cmd_module: types.ModuleType = commands.build
        case _:
            raise ValueError(f"Unknown command: {command_name}")

    if cmd_module.__doc__ is None:
        raise RuntimeError(f"Command <{command_name}> has no docstring")

    cmd_options = docopt.docopt(
        cmd_module.__doc__, argv=[command_name] + opts["<args>"]
    )
    logger.debug(
        "Run command <%s> with options: %s", command_name, json.dumps(cmd_options)
    )

    return cmd_module.run(cmd_options)


def main(opts: t.Dict[str, t.Any]):
    helpers.logger_file.configure_logging(verbosity=VerbosityLevel.NORMAL)

    logger.debug("Run app with options: %s", json.dumps(opts))

    for path in opts["--allow-dotenv"]:
        logger.info(f"Loading environment variables from {path}")
        dotenv.load_dotenv(path)

    try:
        run_command(opts)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main(
        docopt.docopt(
            __doc__,
            options_first=True,
            version=PACKAGE_VERSION,
        )
    )
