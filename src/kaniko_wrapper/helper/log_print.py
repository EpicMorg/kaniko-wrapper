from termcolor import colored
from dotenv import load_dotenv
from kaniko_wrapper.helper.helper import setup_logger

logger = setup_logger()
load_dotenv()


def show_help():
    """
    Displays detailed information about available commands and arguments.
    """
    help_text = f"""
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
  {colored('--kaniko-image IMAGE', 'green')} : Name of the Kaniko executor image (default: gcr.io/kaniko-project/executor:latest)
  {colored('--push, --deploy, -d', 'green')} : Deploy the built images to the registry
  {colored('--dry-run, --dry', 'green')}     : Perform a build without pushing and with cleanup

{colored('Note:', 'yellow', attrs=['bold'])}
  This script uses Kaniko to build Docker images in a secure, efficient, and scalable way. Make sure to configure your environment properly.
"""
    logger.info(help_text)
