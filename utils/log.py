import logging
from logging.handlers import RotatingFileHandler
import os, sys

from config import Config
config = Config()

def setup_logging():
    """Set up logging for the application.

    Creates a logger with file and console handlers.
    If the logger already has handlers, it reuses the existing setup.
    """
    os.makedirs(config.app_log_dir, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(module)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        os.path.join(config.app_log_dir, config.app_log_file),
        maxBytes=int(config.max_log_size),
        backupCount=int(config.backup_count),
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger