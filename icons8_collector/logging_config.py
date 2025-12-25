"""
Logging configuration for Icons8 Collector.

Provides structured logging with configurable verbosity levels.
"""

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
    """
    Configure logging for the application.
    
    Args:
        verbose: Enable verbose output (INFO level with timestamps)
        debug: Enable debug output (DEBUG level with full details)
        log_file: Optional path to log file
        
    Returns:
        Configured root logger for the application
    """
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
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"icons8_collector.{name}")


class ProgressLogger:
    """
    Helper class for logging progress during batch operations.
    
    Provides a consistent interface for progress reporting that
    works with both logging and direct console output.
    """
    
    def __init__(
        self,
        total: int,
        logger: Optional[logging.Logger] = None,
        prefix: str = "",
    ) -> None:
        """
        Initialize progress logger.
        
        Args:
            total: Total number of items
            logger: Logger instance (uses print if None)
            prefix: Prefix for progress messages
        """
        self.total = total
        self.current = 0
        self.logger = logger
        self.prefix = prefix
    
    def update(self, message: str = "", success: bool = True) -> None:
        """
        Update progress with a message.
        
        Args:
            message: Progress message
            success: Whether the current item succeeded
        """
        self.current += 1
        status = "✓" if success else "✗"
        progress_msg = f"[{self.current}/{self.total}] {status} {self.prefix}{message}"
        
        if self.logger:
            if success:
                self.logger.info(progress_msg)
            else:
                self.logger.warning(progress_msg)
        else:
            print(progress_msg)
    
    def finish(self, message: str = "Complete") -> None:
        """
        Log completion message.
        
        Args:
            message: Completion message
        """
        if self.logger:
            self.logger.info(f"{self.prefix}{message}")
        else:
            print(f"{self.prefix}{message}")
