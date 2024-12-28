import logging
from logging.handlers import RotatingFileHandler
import os
from enum import Enum, auto
from sentry_sdk import capture_exception

class ExceptionLevel(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

def init_logger():
    """
    Initialize logger
    :return:
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if not os.path.exists("log"):
        os.makedirs("log")

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s : [%(levelname)s] %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler("log/pricetracker.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    rotating_file_handler = RotatingFileHandler(
        "log/pricetracker.err", maxBytes=5 * 1024 * 1024, backupCount=3
    )
    rotating_file_handler.setLevel(logging.ERROR)
    rotating_file_handler.setFormatter(formatter)
    logger.addHandler(rotating_file_handler)

def log_exception(exception: Exception, level: ExceptionLevel = ExceptionLevel.ERROR, message: str = None, capture: bool = True):
    """
    Log exception
    :param e:
    :param level:
    :param message:
    :param capture:
    :return:
    """
    match (level):
        case ExceptionLevel.INFO:
            logging.info(f"{message}: {exception}")
        case ExceptionLevel.WARNING:
            logging.warning(f"{message}: {exception}")
        case ExceptionLevel.ERROR:
            logging.error(f"{message}: {exception}")
        case ExceptionLevel.CRITICAL:
            logging.critical(f"{message}: {exception}")

    if capture:
        capture_exception(exception)