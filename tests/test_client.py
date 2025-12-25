"""
Tests for the Icons8 client module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import responses

from icons8_collector.client import (
    Icons8Client,
    Icons8URLs,
    Icon,
    sanitize_filename,
    extract_icon_id_from_url,
)
from icons8_collector.exceptions import ValidationError, DownloadError


class TestSanitizeFilename:
    """Tests for filename sanitization."""
    
    def test_simple_name(self):
        """Test simple valid name."""
        assert sanitize_filename("icon") == "icon"
    
    def test_name_with_spaces(self):
        """Test name with spaces converted to underscores."""
        assert sanitize_filename("my icon") == "my_icon"
    
    def test_name_with_special_chars(self):
        """Test removal of special characters."""
        assert sanitize_filename("icon@#$%") == "icon"
    
    def test_path_traversal_attack(self):
        """Test prevention of path traversal."""
        assert sanitize_filename("../../../etc/passwd") == "______etc_passwd"
        assert ".." not in sanitize_filename("../icon")
    
    def test_null_byte_injection(self):
        """Test removal of null bytes."""
        # Null byte is simply removed, not replaced with underscore
        assert sanitize_filename("icon\x00.png") == "iconpng"
    
    def test_windows_path_separators(self):
        """Test handling of Windows path separators."""
        assert sanitize_filename("folder\\icon") == "folder_icon"
    
    def test_unix_path_separators(self):
        """Test handling of Unix path separators."""
        assert sanitize_filename("folder/icon") == "folder_icon"
    
    def test_empty_string(self):
        """Test fallback for empty string."""
        assert sanitize_filename("") == "icon"
    
    def test_none_value(self):
        """Test fallback for None."""
        assert sanitize_filename(None) == "icon"
    
    def test_custom_fallback(self):
        """Test custom fallback value."""
        assert sanitize_filename("", fallback="default") == "default"
    
    def test_only_special_chars(self):
        """Test name with only special characters."""
        assert sanitize_filename("@#$%^") == "icon"
    
    def test_very_long_name(self):
        """Test truncation of very long names."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 200
    
    def test_name_with_dashes_and_underscores(self):
        """Test preservation of dashes and underscores."""
        assert sanitize_filename("my-icon_name") == "my-icon_name"
    
    def test_mixed_case_preserved(self):
        """Test that case is preserved."""
        assert sanitize_filename("MyIcon") == "MyIcon"


class TestExtractIconIdFromUrl:
    """Tests for icon ID extraction from URLs."""
    
    def test_standard_url(self):
        """Test extraction from standard Icons8 URL."""
        url = "https://img.icons8.com/?size=256&id=abc123&format=png"
        assert extract_icon_id_from_url(url) == "abc123"
    
    def test_url_with_alphanumeric_id(self):
        """Test extraction with alphanumeric ID."""
        url = "https://img.icons8.com/?id=XYZ789_test&size=128"
        assert extract_icon_id_from_url(url) == "XYZ789_test"
    
    def test_url_without_id(self):
        """Test URL without ID parameter."""
        url = "https://img.icons8.com/?size=256&format=png"
        assert extract_icon_id_from_url(url) is None
    
    def test_malformed_url(self):
        """Test malformed URL."""
        url = "not-a-valid-url"
        assert extract_icon_id_from_url(url) is None


class TestIcons8URLs:
    """Tests for URL building and validation."""
    
    def test_build_icon_url_default(self):
        """Test default icon URL building."""
        url = Icons8URLs.build_icon_url("abc123")
        assert "id=abc123" in url
        assert "size=256" in url
        assert "format=png" in url
        assert url.startswith("https://img.icons8.com/")
    
    def test_build_icon_url_custom_size(self):
        """Test URL building with custom size."""
        url = Icons8URLs.build_icon_url("abc123", size=512)
        assert "size=512" in url
    
    def test_build_icon_url_custom_format(self):
        """Test URL building with custom format."""
        url = Icons8URLs.build_icon_url("abc123", fmt="svg")
        assert "format=svg" in url
    
    def test_is_valid_domain_icons8(self):
        """Test valid Icons8 domain."""
        assert Icons8URLs.is_valid_domain(
            "https://icons8.com/icons",
            Icons8URLs.ALLOWED_DOWNLOAD_DOMAINS
        )
    
    def test_is_valid_domain_img_icons8(self):
        """Test valid img.icons8.com domain."""
        assert Icons8URLs.is_valid_domain(
            "https://img.icons8.com/?id=123",
            Icons8URLs.ALLOWED_DOWNLOAD_DOMAINS
        )
    
    def test_is_valid_domain_invalid(self):
        """Test invalid domain."""
        assert not Icons8URLs.is_valid_domain(
            "https://evil.com/icons",
            Icons8URLs.ALLOWED_DOWNLOAD_DOMAINS
        )
    
    def test_is_valid_domain_subdomain(self):
        """Test subdomain validation."""
        assert Icons8URLs.is_valid_domain(
            "https://cdn.icons8.com/images",
            Icons8URLs.ALLOWED_DOWNLOAD_DOMAINS
        )


class TestIcon:
    """Tests for Icon dataclass."""
    
    def test_icon_creation(self):
        """Test basic icon creation."""
        icon = Icon(id="123", name="test", url="https://img.icons8.com/?id=123")
        assert icon.id == "123"
        assert icon.name == "test"
        assert icon.url == "https://img.icons8.com/?id=123"
    
    def test_icon_empty_id_raises(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError):
            Icon(id="", name="test", url="https://example.com")
    
    def test_icon_empty_url_raises(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError):
            Icon(id="123", name="test", url="")


class TestIcons8ClientValidation:
    """Tests for Icons8Client URL validation."""
    
    def test_validate_download_url_valid(self):
        """Test validation of valid download URL."""
        client = Icons8Client()
        # Should not raise
        client.validate_download_url("https://img.icons8.com/?id=123&size=256")
        client.close()
    
    def test_validate_download_url_invalid_scheme(self):
        """Test rejection of HTTP URL."""
        client = Icons8Client()
        with pytest.raises(ValidationError) as exc_info:
            client.validate_download_url("http://img.icons8.com/?id=123")
        assert "HTTPS" in str(exc_info.value)
        client.close()
    
    def test_validate_download_url_invalid_domain(self):
        """Test rejection of non-Icons8 domain."""
        client = Icons8Client()
        with pytest.raises(ValidationError) as exc_info:
            client.validate_download_url("https://evil.com/icon.png")
        assert "not allowed" in str(exc_info.value)
        client.close()
    
    def test_validate_download_url_empty(self):
        """Test rejection of empty URL."""
        client = Icons8Client()
        with pytest.raises(ValidationError):
            client.validate_download_url("")
        client.close()
    
    def test_validate_collection_url_valid(self):
        """Test validation of valid collection URL."""
        client = Icons8Client()
        # Should not raise
        client.validate_collection_url("https://icons8.com/icons/collection/abc123")
        client.close()
    
    def test_validate_collection_url_no_collection_path(self):
        """Test rejection of URL without collection path."""
        client = Icons8Client()
        with pytest.raises(ValidationError) as exc_info:
            client.validate_collection_url("https://icons8.com/icons/set/home")
        assert "collection" in str(exc_info.value).lower()
        client.close()


class TestIcons8ClientDownload:
    """Tests for Icons8Client download functionality."""
    
    @responses.activate
    def test_download_icon_success(self, tmp_path):
        """Test successful icon download."""
        # PNG signature + minimal data
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        
        responses.add(
            responses.GET,
            "https://img.icons8.com/?id=test123&size=256&format=png",
            body=png_data,
            status=200,
            headers={"content-type": "image/png"}
        )
        
        client = Icons8Client()
        output_path = tmp_path / "icon.png"
        
        client.download_icon(
            "https://img.icons8.com/?id=test123&size=256&format=png",
            output_path
        )
        
        assert output_path.exists()
        assert output_path.read_bytes().startswith(b'\x89PNG')
        client.close()
    
    @responses.activate
    def test_download_icon_http_error(self, tmp_path):
        """Test handling of HTTP errors."""
        responses.add(
            responses.GET,
            "https://img.icons8.com/?id=notfound&size=256&format=png",
            status=404
        )
        
        client = Icons8Client()
        output_path = tmp_path / "icon.png"
        
        with pytest.raises(DownloadError) as exc_info:
            client.download_icon(
                "https://img.icons8.com/?id=notfound&size=256&format=png",
                output_path
            )
        
        assert "404" in str(exc_info.value) or "HTTP" in str(exc_info.value)
        client.close()
    
    @responses.activate
    def test_download_icon_not_image(self, tmp_path):
        """Test rejection of non-image content."""
        responses.add(
            responses.GET,
            "https://img.icons8.com/?id=test&size=256&format=png",
            body=b"<html>Not an image</html>",
            status=200,
            headers={"content-type": "text/html"}
        )
        
        client = Icons8Client()
        output_path = tmp_path / "icon.png"
        
        with pytest.raises(DownloadError) as exc_info:
            client.download_icon(
                "https://img.icons8.com/?id=test&size=256&format=png",
                output_path
            )
        
        assert "not an image" in str(exc_info.value).lower()
        client.close()
    
    @responses.activate
    def test_download_icon_invalid_png(self, tmp_path):
        """Test rejection of invalid PNG content."""
        responses.add(
            responses.GET,
            "https://img.icons8.com/?id=test&size=256&format=png",
            body=b"not png data" + b"\x00" * 100,
            status=200,
            headers={"content-type": "image/png"}
        )
        
        client = Icons8Client()
        output_path = tmp_path / "icon.png"
        
        with pytest.raises(DownloadError) as exc_info:
            client.download_icon(
                "https://img.icons8.com/?id=test&size=256&format=png",
                output_path
            )
        
        assert "PNG" in str(exc_info.value)
        client.close()
    
    def test_context_manager(self):
        """Test client as context manager."""
        with Icons8Client() as client:
            assert client is not None
        # Should not raise


class TestIcons8ClientPathValidation:
    """Tests for output path validation."""
    
    def test_validate_output_path_traversal(self, tmp_path):
        """Test rejection of path traversal attempts."""
        client = Icons8Client()
        
        with pytest.raises(ValidationError):
            client._validate_output_path(
                Path("../../../etc/passwd"),
                base_dir=tmp_path
            )
        
        client.close()
    
    def test_validate_output_path_within_base(self, tmp_path):
        """Test acceptance of path within base directory."""
        client = Icons8Client()
        
        output_path = tmp_path / "subdir" / "icon.png"
        result = client._validate_output_path(output_path, base_dir=tmp_path)
        
        assert result.is_absolute()
        client.close()
