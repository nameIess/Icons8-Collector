__version__ = "1.0.0"
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

__all__ = [
    "Icons8CollectorError",
    "AuthenticationError",
    "ScrapingError",
    "DownloadError",
    "ConversionError",
    "ConfigurationError",
    "BrowserError",
    "ValidationError",
]
