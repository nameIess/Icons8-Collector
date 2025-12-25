"""
Icons8 Collector - Download icons from Icons8 collections.

A production-grade CLI tool for downloading icons from Icons8.com collections
with support for PNG and ICO formats.
"""

__version__ = "2.0.0"
__author__ = "nameIess"

from .exceptions import (
    Icons8CollectorError,
    AuthenticationError,
    ScrapingError,
    DownloadError,
    ConversionError,
    ConfigurationError,
    BrowserError,
    ValidationError,
)

from .client import (
    Icons8Client,
    Icons8URLs,
    Icon,
    sanitize_filename,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Exceptions
    "Icons8CollectorError",
    "AuthenticationError",
    "ScrapingError",
    "DownloadError",
    "ConversionError",
    "ConfigurationError",
    "BrowserError",
    "ValidationError",
    # Client
    "Icons8Client",
    "Icons8URLs",
    "Icon",
    "sanitize_filename",
]
