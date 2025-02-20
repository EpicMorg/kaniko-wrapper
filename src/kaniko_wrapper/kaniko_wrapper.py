from kaniko_wrapper.setting import SCRIPT_VERSION
from kaniko_wrapper.helper._dataclass import ArgParser
from kaniko_wrapper.helper.class_kaniko import KanikoBuilder
from kaniko_wrapper.helper.log_print import logger, show_help


def main():
    """
    Main function to process command-line arguments, build services using Kaniko,
    and handle various tasks like displaying version or help.
    """
    args = ArgParser().parse_args()

    # Version flag
    if args.version:
        logger.info(f"Kaniko Compose Wrapper Version: {SCRIPT_VERSION}")
        return

    # Help flag
    if args.help:
        show_help()
        return

    try:
        kaniko_builder = KanikoBuilder(args)
        kaniko_builder.validate_compose_file()  # Validate docker-compose file
        kaniko_builder.process_services()  # Process all services
        kaniko_builder.build_services()  # Build services
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid value: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()
