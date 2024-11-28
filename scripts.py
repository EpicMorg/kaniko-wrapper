"""
Scripts collection for use poetry scripts
"""
import logging
import pathlib
import sys

import black
from isort import main as isort_main

logging.basicConfig(
    level=logging.INFO, format="%(levelname)-7s %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)

testrunner_top_level_dir = pathlib.Path(__file__).parent


def format():
    if len(sys.argv) > 1:
        logger.warning("format not support arguments")
        logger.warning("Ignoring arguments: %s", sys.argv[1:])

    sys.argv = [
        "isort",
        str(testrunner_top_level_dir / "kaniko"),
        str(testrunner_top_level_dir / "tests"),
    ]
    isort_main.main()

    sys.argv = [
        "black",
        str(testrunner_top_level_dir / "kaniko"),
        str(testrunner_top_level_dir / "tests"),
        "--config",
        str(testrunner_top_level_dir / "pyproject.toml"),
    ]
    black.patched_main()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("No arguments provided")

    func_to_run = sys.argv.pop(1)
    if func_to_run not in globals():
        raise ValueError(f"Function {func_to_run} not found")

    globals()[func_to_run]()
