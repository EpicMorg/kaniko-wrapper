import logging
from unittest import mock

from kaniko.commands.build.cmd import run
from kaniko.helpers.logger_file import VerbosityLevel


def test_run_dry_run_mode_no_push():
    opts = {
        "--compose-file": "docker-compose.yml",
        "--kaniko-image": "gcr.io/kaniko-project/executor:latest",
        "--dry-run": True,
        "--push": False,
        "--deploy": False,
        "verbosity": VerbosityLevel.NORMAL,
    }

    # Mock logger
    logger = logging.getLogger("KanikoComposeWrapper")
    logger.info = mock.MagicMock()
    logger.warning = mock.MagicMock()
    logger.error = mock.MagicMock()

    # Act
    run(opts)

    # Assert
    logger.info.assert_any_call("🔍 Running in dry-run mode. No images will be pushed.")
    logger.info.assert_any_call("✅ Kaniko build process completed successfully!")
    logger.warning.assert_not_called()
    logger.error.assert_not_called()
