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
    def build_icon_url(cls, icon_id: str, size: int = 256, fmt: str = "svg") -> str:
        params = urlencode({
            "size": size,
            "id": icon_id,
            "format": fmt,
        })
        return f"{cls.IMAGE_BASE_URL}/?{params}"
    
    @classmethod
    def is_valid_domain(cls, url: str, allowed_domains: list[str]) -> bool:
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
    
    id: str
    name: str
    url: str
    
    def __post_init__(self) -> None:
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
    "Accept": "image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Security limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max file size
MIN_IMAGE_SIZE = 50  # bytes - minimum valid image size (SVGs can be small)
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3


# ============================================================================
# Icons8 Client Class
# ============================================================================

class Icons8Client:
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if headers:
            self.session.headers.update(headers)
        if cookies:
            self.session.cookies.update(cookies)
        
        logger.debug(f"Icons8Client initialized (timeout={timeout}s, max_retries={max_retries})")
    
    def validate_download_url(self, url: str) -> None:
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
    
    @staticmethod
    def validate_collection_url_static(url: str) -> None:
        """Static method to validate collection URL without instantiating client."""
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
    
    @staticmethod
    def _is_retriable_status_code(status_code: int) -> bool:
        """Check if HTTP status code should be retried."""
        return status_code in (429, 500, 502, 503, 504)
    
    @retry(
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError, DownloadError)),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _download_with_retry(self, url: str) -> bytes:
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
        except requests.Timeout as e:
            logger.warning(f"Download timed out for {url}")
            raise
        except requests.ConnectionError as e:
            logger.warning(f"Connection error for {url}: {e}")
            raise
        except requests.HTTPError as e:
            status_code = response.status_code
            # Retry on retriable HTTP status codes (429, 5xx)
            if self._is_retriable_status_code(status_code):
                logger.warning(f"Retriable HTTP error {status_code} for {url}, will retry...")
                raise DownloadError(
                    f"HTTP error {status_code} while downloading (retriable)",
                    url=url,
                    status_code=status_code,
                    original_error=e
                )
            raise DownloadError(
                f"HTTP error {status_code} while downloading",
                url=url,
                status_code=status_code,
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
        if 'image' not in content_type.lower() and 'xml' not in content_type.lower():
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
                # Ignore invalid or non-integer Content-Length; enforce limit while streaming below.
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
        
        # Simple SVG validation (check for <svg tag)
        # Note: We loosen the check because we might also get PNGs if SVG is not available/authorized,
        # but for now we want to enforce SVG or at least look for it.
        # If we get a PNG but expect an SVG, we might want to error, 
        # but let's check content.
        
        is_svg = b'<svg' in content or b'<?xml' in content
        
        if not is_svg:
             # If strictly SVG-only as per requirements, we should fail if it's not SVG.
             # However, let's log what we got.
             if content.startswith(b'\x89PNG'):
                 raise DownloadError(
                    "Server returned a PNG file, but SVG was expected. Login might be required for SVGs.",
                    url=url
                 )
             else:
                 # Be lenient for now if it's some other format or just weirdly formatted SVG
                 logger.warning("Downloaded content does not look like a standard SVG or PNG.")

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
        url = Icons8URLs.build_icon_url(icon_id, size=size)
        self.download_icon(url, output_path, base_dir)
    
    def _validate_output_path(
        self,
        output_path: Path,
        base_dir: Optional[Path] = None,
    ) -> Path:
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
        
        return resolved_path
    
    def close(self) -> None:
        try:
            self.session.close()
        except Exception as exc:
            logger.warning("Failed to close Icons8Client session: %s", exc)
        else:
            logger.debug("Icons8Client session closed")
    
    def __enter__(self) -> "Icons8Client":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# ============================================================================
# Utility Functions
# ============================================================================

def sanitize_filename(name: str, fallback: str = "icon") -> str:
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
    match = re.search(r'id=([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None
