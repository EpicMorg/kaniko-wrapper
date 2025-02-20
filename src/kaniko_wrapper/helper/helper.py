import logging
import colorlog

from kaniko_wrapper.setting import settings


def setup_logger():
    logger = logging.getLogger("logger_kaniko")
    logger.setLevel(settings.log_level.upper())

    ch = colorlog.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = colorlog.ColoredFormatter(
        fmt=settings.log_format,
        datefmt=settings.datefmt,
        log_colors=settings.log_colors,
    )

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
