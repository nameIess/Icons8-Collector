from pathlib import Path
from urllib.parse import urlparse

import requests

from .exceptions import DownloadError, ValidationError


# HTTP headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

# Security constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_DOMAINS = ['icons8.com', 'img.icons8.com', 'maxst.icons8.com']
ALLOWED_SCHEMES = ['https']
MIN_IMAGE_SIZE = 100  # bytes


def validate_url(url: str) -> None:
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
    
    # Check scheme
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValidationError(
            f"Only HTTPS URLs are allowed. Got: {parsed.scheme}",
            field_name="url"
        )
    
    # Check domain
    domain = parsed.netloc.lower()
    if not any(domain == allowed or domain.endswith('.' + allowed) for allowed in ALLOWED_DOMAINS):
        raise ValidationError(
            f"URL domain not allowed: {domain}. Only Icons8 domains are permitted.",
            field_name="url"
        )


def validate_output_path(output_path: Path, base_dir: Path | None = None) -> Path:
    try:
        resolved_path = output_path.resolve()
    except Exception as e:
        raise ValidationError(
            f"Invalid output path: {output_path}",
            field_name="output_path",
            original_error=e
        )
    
    # If base_dir is specified, ensure path doesn't escape it
    if base_dir is not None:
        try:
            resolved_base = base_dir.resolve()
            # Check that the resolved path starts with the base directory
            resolved_path.relative_to(resolved_base)
        except ValueError:
            raise ValidationError(
                "Output path attempts to escape the designated output directory",
                field_name="output_path"
            )
    
    # Check for suspicious patterns
    path_str = str(output_path)
    if '..' in path_str or path_str.startswith('/') or path_str.startswith('\\'):
        # Double-check the resolved path
        if base_dir:
            try:
                resolved_path.relative_to(base_dir.resolve())
            except ValueError:
                raise ValidationError(
                    "Path contains potentially dangerous patterns",
                    field_name="output_path"
                )
    
    return resolved_path


def download_icon(url: str, output_path: str | Path, base_dir: Path | None = None) -> None:
    # Validate URL first
    validate_url(url)
    
    output_path = Path(output_path)
    
    # Validate and resolve output path
    resolved_path = validate_output_path(output_path, base_dir)
    
    try:
        response = requests.get(
            url, 
            headers=HEADERS, 
            stream=True, 
            timeout=30,
            allow_redirects=False  # Don't follow redirects to untrusted domains
        )
        response.raise_for_status()
    except requests.Timeout as e:
        raise DownloadError(
            f"Download timed out for {url}",
            url=url,
            original_error=e
        )
    except requests.ConnectionError as e:
        raise DownloadError(
            f"Connection error while downloading {url}: {e}",
            url=url,
            original_error=e
        )
    except requests.HTTPError as e:
        raise DownloadError(
            f"HTTP error {response.status_code} while downloading {url}",
            url=url,
            status_code=response.status_code,
            original_error=e
        )
    except requests.RequestException as e:
        raise DownloadError(
            f"Failed to download {url}: {e}",
            url=url,
            original_error=e
        )
    
    # Validate response is an image
    content_type = response.headers.get('content-type', '')
    if 'image' not in content_type.lower():
        raise DownloadError(
            f"Response is not an image. Content-Type: {content_type}",
            url=url
        )
    
    # Check content length if available
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
            pass  # Content-Length header was malformed, proceed with download
    
    # Download with size limit
    content = b''
    for chunk in response.iter_content(chunk_size=8192):
        content += chunk
        if len(content) > MAX_FILE_SIZE:
            raise DownloadError(
                f"File exceeds maximum size of {MAX_FILE_SIZE} bytes",
                url=url
            )
    
    if len(content) < MIN_IMAGE_SIZE:
        raise DownloadError(
            f"Response content too small ({len(content)} bytes), likely not a valid image",
            url=url
        )
    
    # Validate image magic bytes (PNG signature)
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
    if not content.startswith(PNG_SIGNATURE):
        raise DownloadError(
            "Downloaded content is not a valid PNG file",
            url=url
        )
    
    # Ensure parent directory exists
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file atomically
    temp_path = resolved_path.with_suffix('.tmp')
    try:
        with open(temp_path, 'wb') as f:
            f.write(content)
        # Use replace() instead of rename() - works on Windows when target exists
        temp_path.replace(resolved_path)
    except OSError as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise DownloadError(
            f"Failed to write file to disk: {e}",
            url=url,
            original_error=e
        )


def sanitize_filename(name: str, fallback: str = "icon") -> str:
    if not name or not isinstance(name, str):
        return fallback
    
    # Remove path separators and null bytes (critical security fix)
    name = name.replace('/', '_').replace('\\', '_').replace('\x00', '')
    
    # Remove or replace other dangerous characters
    name = name.replace('..', '_')  # Prevent path traversal
    
    # Keep only alphanumeric, space, dash, and underscore
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    
    # Limit length to prevent filesystem issues
    max_length = 200
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
    
    # Ensure we don't return empty string or just dots
    if not safe_name or safe_name.strip('.') == '':
        return fallback
    
    return safe_name
