"""
Icons8 Client - Centralized network operations and API management.

This module provides an abstraction layer for all Icons8 API interactions,
isolating network logic from the rest of the application.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlencode

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .exceptions import DownloadError, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# Constants - All URLs and domains are centralized here
# ============================================================================

class Icons8URLs:
    """Centralized URL configuration for Icons8 API."""
    
    BASE_DOMAIN = "icons8.com"
    IMAGE_DOMAIN = "img.icons8.com"
    CDN_DOMAINS = ["maxst.icons8.com"]
    
    # Base URLs
    BASE_URL = f"https://{BASE_DOMAIN}"
    IMAGE_BASE_URL = f"https://{IMAGE_DOMAIN}"
    LOGIN_URL = f"{BASE_URL}/login"
    
    # Allowed domains for downloads
    ALLOWED_DOWNLOAD_DOMAINS = [BASE_DOMAIN, IMAGE_DOMAIN] + CDN_DOMAINS
    ALLOWED_COLLECTION_DOMAINS = [BASE_DOMAIN]
    ALLOWED_SCHEMES = ["https"]
    
    @classmethod
    def build_icon_url(cls, icon_id: str, size: int = 256, fmt: str = "png") -> str:
        """Build a download URL for an icon.
        
        Args:
            icon_id: The unique icon identifier
            size: Icon size in pixels (default: 256)
            fmt: Image format (default: png)
            
        Returns:
            Full download URL for the icon
        """
        params = urlencode({
            "size": size,
            "id": icon_id,
            "format": fmt,
        })
        return f"{cls.IMAGE_BASE_URL}/?{params}"
    
    @classmethod
    def is_valid_domain(cls, url: str, allowed_domains: list[str]) -> bool:
        """Check if a URL belongs to an allowed domain.
        
        Args:
            url: URL to validate
            allowed_domains: List of allowed domain names
            
        Returns:
            True if domain is allowed, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return any(
                domain == allowed or domain.endswith('.' + allowed)
                for allowed in allowed_domains
            )
        except Exception:
            return False


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Icon:
    """Represents an icon from an Icons8 collection."""
    
    id: str
    name: str
    url: str
    
    def __post_init__(self) -> None:
        """Validate icon data after initialization."""
        if not self.id:
            raise ValueError("Icon ID cannot be empty")
        if not self.url:
            raise ValueError("Icon URL cannot be empty")


# ============================================================================
# HTTP Client Configuration
# ============================================================================

# Default headers for HTTP requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/png,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Security limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max file size
MIN_IMAGE_SIZE = 100  # bytes - minimum valid image size
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# PNG file signature for validation
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


# ============================================================================
# Icons8 Client Class
# ============================================================================

class Icons8Client:
    """
    Client for interacting with Icons8 services.
    
    Handles all network operations including icon downloads with proper
    error handling, retries, and validation.
    
    Example:
        >>> client = Icons8Client()
        >>> client.download_icon("abc123", Path("output/icon.png"), size=256)
    """
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        headers: Optional[dict] = None,
    ) -> None:
        """
        Initialize the Icons8 client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            headers: Additional headers to include in requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if headers:
            self.session.headers.update(headers)
        
        logger.debug(f"Icons8Client initialized (timeout={timeout}s, max_retries={max_retries})")
    
    def validate_download_url(self, url: str) -> None:
        """
        Validate that a URL is safe to download from.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If URL is invalid or from untrusted domain
        """
        if not url or not isinstance(url, str):
            raise ValidationError(
                "URL must be a non-empty string",
                field_name="url"
            )
        
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValidationError(
                "Invalid URL format",
                field_name="url",
                original_error=e
            )
        
        if parsed.scheme not in Icons8URLs.ALLOWED_SCHEMES:
            raise ValidationError(
                f"Only HTTPS URLs are allowed. Got: {parsed.scheme}",
                field_name="url"
            )
        
        if not Icons8URLs.is_valid_domain(url, Icons8URLs.ALLOWED_DOWNLOAD_DOMAINS):
            raise ValidationError(
                f"URL domain not allowed: {parsed.netloc}. Only Icons8 domains are permitted.",
                field_name="url"
            )
    
    def validate_collection_url(self, url: str) -> None:
        """
        Validate that a URL is a valid Icons8 collection URL.
        
        Args:
            url: Collection URL to validate
            
        Raises:
            ValidationError: If URL is not a valid collection URL
        """
        if not url or not isinstance(url, str):
            raise ValidationError(
                "Collection URL must be a non-empty string",
                field_name="url"
            )
        
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValidationError(
                f"Invalid URL format",
                field_name="url",
                original_error=e
            )
        
        if parsed.scheme not in Icons8URLs.ALLOWED_SCHEMES:
            raise ValidationError(
                f"Only HTTPS URLs are allowed. Got: {parsed.scheme}",
                field_name="url"
            )
        
        if not Icons8URLs.is_valid_domain(url, Icons8URLs.ALLOWED_COLLECTION_DOMAINS):
            raise ValidationError(
                f"URL domain not allowed: {parsed.netloc}. Only Icons8 domains are permitted.",
                field_name="url"
            )
        
        if '/collection/' not in parsed.path and '/collections/' not in parsed.path:
            raise ValidationError(
                "URL does not appear to be a valid Icons8 collection URL. "
                "Expected path to contain '/collection/' or '/collections/'",
                field_name="url"
            )
    
    @retry(
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _download_with_retry(self, url: str) -> bytes:
        """
        Download content from URL with retry logic.
        
        Args:
            url: URL to download from
            
        Returns:
            Downloaded content as bytes
            
        Raises:
            DownloadError: If download fails after all retries
        """
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
                allow_redirects=False,
            )
            response.raise_for_status()
        except requests.Timeout as e:
            logger.warning(f"Download timed out for {url}")
            raise
        except requests.ConnectionError as e:
            logger.warning(f"Connection error for {url}: {e}")
            raise
        except requests.HTTPError as e:
            raise DownloadError(
                f"HTTP error {response.status_code} while downloading",
                url=url,
                status_code=response.status_code,
                original_error=e
            )
        except requests.RequestException as e:
            raise DownloadError(
                f"Failed to download: {e}",
                url=url,
                original_error=e
            )
        
        # Validate content type
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type.lower():
            raise DownloadError(
                f"Response is not an image. Content-Type: {content_type}",
                url=url
            )
        
        # Check content length
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_FILE_SIZE:
                    raise DownloadError(
                        f"File too large: {size} bytes (max: {MAX_FILE_SIZE} bytes)",
                        url=url
                    )
            except ValueError:
                pass
        
        # Download with size limit
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > MAX_FILE_SIZE:
                raise DownloadError(
                    f"File exceeds maximum size of {MAX_FILE_SIZE} bytes",
                    url=url
                )
        
        return content
    
    def download_icon(
        self,
        url: str,
        output_path: Path,
        base_dir: Optional[Path] = None,
    ) -> None:
        """
        Download an icon from the given URL.
        
        Args:
            url: Icon URL to download
            output_path: Path to save the icon
            base_dir: Base directory for path validation (optional)
            
        Raises:
            ValidationError: If URL or path is invalid
            DownloadError: If download fails
        """
        self.validate_download_url(url)
        output_path = Path(output_path)
        
        # Validate output path
        resolved_path = self._validate_output_path(output_path, base_dir)
        
        logger.debug(f"Downloading icon from {url}")
        
        try:
            content = self._download_with_retry(url)
        except (requests.Timeout, requests.ConnectionError) as e:
            raise DownloadError(
                f"Network error after {self.max_retries} retries",
                url=url,
                original_error=e
            )
        
        # Validate image content
        if len(content) < MIN_IMAGE_SIZE:
            raise DownloadError(
                f"Response content too small ({len(content)} bytes), likely not a valid image",
                url=url
            )
        
        if not content.startswith(PNG_SIGNATURE):
            raise DownloadError(
                "Downloaded content is not a valid PNG file",
                url=url
            )
        
        # Write file atomically
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = resolved_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'wb') as f:
                f.write(content)
            temp_path.replace(resolved_path)
            logger.debug(f"Saved icon to {resolved_path}")
        except OSError as e:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise DownloadError(
                f"Failed to write file to disk: {e}",
                url=url,
                original_error=e
            )
    
    def download_icon_by_id(
        self,
        icon_id: str,
        output_path: Path,
        size: int = 256,
        base_dir: Optional[Path] = None,
    ) -> None:
        """
        Download an icon by its ID.
        
        Args:
            icon_id: Unique icon identifier
            output_path: Path to save the icon
            size: Icon size in pixels
            base_dir: Base directory for path validation
        """
        url = Icons8URLs.build_icon_url(icon_id, size=size)
        self.download_icon(url, output_path, base_dir)
    
    def _validate_output_path(
        self,
        output_path: Path,
        base_dir: Optional[Path] = None,
    ) -> Path:
        """
        Validate and resolve an output path.
        
        Args:
            output_path: Path to validate
            base_dir: Base directory constraint
            
        Returns:
            Resolved absolute path
            
        Raises:
            ValidationError: If path is invalid or escapes base_dir
        """
        try:
            resolved_path = output_path.resolve()
        except Exception as e:
            raise ValidationError(
                f"Invalid output path: {output_path}",
                field_name="output_path",
                original_error=e
            )
        
        if base_dir is not None:
            try:
                resolved_base = base_dir.resolve()
                resolved_path.relative_to(resolved_base)
            except ValueError:
                raise ValidationError(
                    "Output path attempts to escape the designated output directory",
                    field_name="output_path"
                )
        
        path_str = str(output_path)
        if '..' in path_str or path_str.startswith('/') or path_str.startswith('\\'):
            if base_dir:
                try:
                    resolved_path.relative_to(base_dir.resolve())
                except ValueError:
                    raise ValidationError(
                        "Path contains potentially dangerous patterns",
                        field_name="output_path"
                    )
        
        return resolved_path
    
    def close(self) -> None:
        """Close the client session."""
        self.session.close()
        logger.debug("Icons8Client session closed")
    
    def __enter__(self) -> "Icons8Client":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# ============================================================================
# Utility Functions
# ============================================================================

def sanitize_filename(name: str, fallback: str = "icon") -> str:
    """
    Sanitize a filename to be safe for filesystem operations.
    
    Args:
        name: Original filename
        fallback: Fallback name if sanitization produces empty result
        
    Returns:
        Safe filename string
    """
    if not name or not isinstance(name, str):
        return fallback
    
    # Remove path separators and null bytes
    name = name.replace('/', '_').replace('\\', '_').replace('\x00', '')
    
    # Prevent path traversal
    name = name.replace('..', '_')
    
    # Keep only safe characters
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    
    # Limit length
    max_length = 200
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
    
    # Ensure non-empty result
    if not safe_name or safe_name.strip('.') == '':
        return fallback
    
    return safe_name


def extract_icon_id_from_url(url: str) -> Optional[str]:
    """
    Extract icon ID from an Icons8 image URL.
    
    Args:
        url: Image URL containing icon ID
        
    Returns:
        Icon ID if found, None otherwise
    """
    match = re.search(r'id=([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None
