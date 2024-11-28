import logging
import enum
from typing import List, Literal


DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
CORE_LOGGERS = ["core_logger"]
IMPORTANT_LOGGERS = ["important_logger"]


class VerbosityLevel(enum.IntEnum):
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    VERY_VERBOSE = 3


class LogSeverity(enum.IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def from_verbosity(
        cls,
        verbosity: VerbosityLevel,
        category: Literal["core", "important", "general"],
    ) -> "LogSeverity":
        if verbosity == VerbosityLevel.QUIET:
            return cls.CRITICAL
        if verbosity == VerbosityLevel.NORMAL:
            return cls.INFO if category == "core" else cls.WARNING
        if verbosity == VerbosityLevel.VERBOSE:
            return cls.DEBUG if category == "core" else cls.INFO
        if verbosity == VerbosityLevel.VERY_VERBOSE:
            return cls.DEBUG if category in ["core", "important"] else cls.INFO
        return cls.DEBUG


def configure_logging(verbosity: VerbosityLevel) -> None:
    def add_handlers_to_loggers(
        logger_names: List[str], severity: int
    ) -> List[logging.Logger]:
        loggers = [
            logging.getLogger(name)
            for name in logging.root.manager.loggerDict.keys()
            if name in logger_names
        ]
        for logger in loggers:
            if not any(
                isinstance(handler, logging.StreamHandler)
                for handler in logger.handlers
            ):
                logger.addHandler(console_handler)
            logger.setLevel(severity)
        return loggers

    if verbosity == VerbosityLevel.QUIET:
        logging.disable(logging.CRITICAL)
        return

    # Configure console handler
    console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(
        logging.DEBUG if verbosity >= VerbosityLevel.VERBOSE else logging.INFO
    )

    # Apply logging configurations
    add_handlers_to_loggers(CORE_LOGGERS, LogSeverity.from_verbosity(verbosity, "core"))
    add_handlers_to_loggers(
        IMPORTANT_LOGGERS, LogSeverity.from_verbosity(verbosity, "important")
    )

    # Configure other loggers
    other_logger_names = [
        name
        for name in logging.root.manager.loggerDict.keys()
        if name.split(".")[0] not in CORE_LOGGERS + IMPORTANT_LOGGERS
    ]
    add_handlers_to_loggers(
        other_logger_names, LogSeverity.from_verbosity(verbosity, "general")
    )
