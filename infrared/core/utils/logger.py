import logging
import sys
import traceback

import colorlog

from infrared.core.utils import exceptions

logger_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(message)s",
    log_colors=dict(
        DEBUG='blue',
        INFO='green',
        WARNING='yellow',
        ERROR='red',
        CRITICAL='bold_red,bg_white',
    )
)

LOGGER_NAME = "IRLogger"
DEFAULT_LOG_LEVEL = logging.WARNING

LOG = logging.getLogger(LOGGER_NAME)
LOG.setLevel(DEFAULT_LOG_LEVEL)

# Create stream handler with debug level
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)

# Add the logger_formatter to sh
sh.setFormatter(logger_formatter)

# Create logger and add handler to it
LOG.addHandler(sh)


def ir_excepthook(exc_type, exc_value, exc_traceback):
    """
    exception hook that sends IRException to log and other exceptions to
    stderr (default excepthook)
    """

    # sends full exception with trace to log
    if not isinstance(exc_value, exceptions.IRException):
        return sys.__excepthook__(exc_type, exc_value, exc_traceback)

    if LOG.getEffectiveLevel() <= logging.DEBUG:
        formated_exception = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback))
        LOG.error(formated_exception + exc_value.message)
    else:
        LOG.error(exc_value.message)


sys.excepthook = ir_excepthook
