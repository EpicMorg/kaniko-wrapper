from termcolor import colored
from dotenv import load_dotenv
from kaniko_wrapper.helper.helper import setup_logger

logger = setup_logger()
load_dotenv()


def show_help():
    """
    Displays detailed information about available commands and arguments.
    """
    help_text = rf"""
{colored('Kaniko Compose Wrapper', 'cyan', attrs=['bold'])}
    
    +=================================================+
    | ____|        _)         \  |                    |
    | __|    __ \   |   __|  |\/ |   _ \    __|  _` | |
    | |      |   |  |  (     |   |  (   |  |    (   | |
    |_____|  .__/  _| \___| _|  _| \___/  _|   \__, | |
    | |  /  _|           _)  |                 |___/  |
    | ' /    _` |  __ \   |  |  /   _ \               |
    | . \   (   |  |   |  |    <   (   |              |
    |_|\_\ \__,_| _|  _| _| _|\_\ \___/               |
    |\ \        /                                     |
    | \ \  \   /   __|  _` |  __ \   __ \    _ \   __||
    |  \ \  \ /   |    (   |  |   |  |   |   __/  |   |
    |   \_/\_/   _|   \__,_|  .__/   .__/  \___| _|   |
    |                        _|     _|                |
    +=================================================+

This script allows you to build Docker images using Kaniko.

{colored('Commands:', 'yellow', attrs=['bold'])}
  {colored('--version, -v', 'green')}       : Show the version of the script
  {colored('--help, -h', 'green')}          : Display this help message

{colored('Options:', 'yellow', attrs=['bold'])}
  {colored('--compose-file FILE', 'green')}  : Path to the docker-compose.yml file (default: docker-compose.yml)
  {colored('--kaniko-image IMAGE', 'green')} : Kaniko executor image (default: ghcr.io/osscontainertools/kaniko:latest)
  {colored('--push, --deploy, -d', 'green')} : Build and push to the registry and all x-mirrors
  {colored('--dry-run, --dry', 'green')}     : Build without pushing
  {colored('--no-push', 'green')}            : Build without pushing to the registry
  {colored('--verbose, -V', 'green')}        : Verbose output (shortcut for --log-level DEBUG)
  {colored('--log-level LEVEL', 'green')}    : Override log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  {colored('--engine ENGINE', 'green')}     : Container engine: docker (default) or podman

{colored('Mirrors:', 'yellow', attrs=['bold'])}
  Add an {colored('x-mirrors', 'green')} list to a compose service to push the built image to
  additional registries within the same build. A failed push to any mirror
  fails the build.

  services:
    app:
      image: docker.io/epicmorg/app:latest
      x-mirrors:
        - quay.io/epicmorg/app:latest

{colored('Note:', 'yellow', attrs=['bold'])}
  This script uses Kaniko to build Docker images in a secure, efficient, and scalable way. Make sure to configure your environment properly.
"""
    print(help_text)
