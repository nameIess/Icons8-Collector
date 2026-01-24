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
]
