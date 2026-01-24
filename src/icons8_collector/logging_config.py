import logging
import sys
from typing import Optional


# Custom log format
VERBOSE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_FORMAT = "%(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    verbose: bool = False,
    debug: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    # Determine log level
    if debug:
        level = logging.DEBUG
        fmt = VERBOSE_FORMAT
    elif verbose:
        level = logging.INFO
        fmt = VERBOSE_FORMAT
    else:
        level = logging.WARNING
        fmt = DEFAULT_FORMAT
    
    # Get the package logger
    logger = logging.getLogger("icons8_collector")
    logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(fmt, datefmt=DATE_FORMAT))
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(VERBOSE_FORMAT, datefmt=DATE_FORMAT)
        )
        logger.addHandler(file_handler)
    
    # Suppress verbose logging from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"icons8_collector.{name}")
