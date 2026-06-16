import sys
from kaniko_wrapper.settings import SCRIPT_VERSION
from kaniko_wrapper.helper._dataclass import ArgParser, KanikoBuildError
from kaniko_wrapper.helper.class_kaniko import KanikoBuilder
from kaniko_wrapper.helper.log_print import logger, show_help


def main():
    """
    Main function to process command-line arguments, build services using Kaniko,
    and handle various tasks like displaying version or help.
    """
    parser = ArgParser()
    args = parser.parse_args()
    if args.log_level:
        logger.setLevel(args.log_level)
    elif args.verbose:
        logger.setLevel("DEBUG")

    if len(sys.argv) == 1 or args.help:
        show_help()
        return

    if args.version:
        logger.info(f"Kaniko Compose Wrapper Version: {SCRIPT_VERSION}")
        return

    try:
        kaniko_builder = KanikoBuilder(args)
        kaniko_builder.validate_compose_file()  # Validate docker-compose file
        kaniko_builder.process_services()  # Process all services
        kaniko_builder.build_services()  # Build services
    except KanikoBuildError as e:
        # One or more builds/pushes returned a non-zero exit code.
        logger.error(f"Build failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid value: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()