"""
Tests for the CLI module.
"""

import pytest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from icons8_collector.cli import (
    parse_args,
    validate_size,
    OutputFormat,
    UserConfig,
    DEFAULT_SIZE,
    VALID_SIZES,
)


class TestParseArgs:
    """Tests for argument parsing."""
    
    def test_url_argument(self):
        """Test URL argument parsing."""
        args = parse_args(["--url", "https://icons8.com/collection/test"])
        assert args.url == "https://icons8.com/collection/test"
    
    def test_url_short_argument(self):
        """Test URL short argument."""
        args = parse_args(["-u", "https://icons8.com/collection/test"])
        assert args.url == "https://icons8.com/collection/test"
    
    def test_email_argument(self):
        """Test email argument."""
        args = parse_args(["--email", "test@example.com"])
        assert args.email == "test@example.com"
    
    def test_password_argument(self):
        """Test password argument."""
        args = parse_args(["--password", "secret123"])
        assert args.password == "secret123"
    
    def test_format_png(self):
        """Test PNG format argument."""
        args = parse_args(["--format", "png"])
        assert args.format == "png"
    
    def test_format_ico(self):
        """Test ICO format argument."""
        args = parse_args(["--format", "ico"])
        assert args.format == "ico"
    
    def test_format_both(self):
        """Test both format argument."""
        args = parse_args(["--format", "both"])
        assert args.format == "both"
    
    def test_format_default(self):
        """Test default format is ico."""
        args = parse_args([])
        assert args.format == "ico"
    
    def test_size_argument(self):
        """Test size argument."""
        args = parse_args(["--size", "512"])
        assert args.size == 512
    
    def test_size_default(self):
        """Test default size."""
        args = parse_args([])
        assert args.size == DEFAULT_SIZE
    
    def test_output_argument(self):
        """Test output directory argument."""
        args = parse_args(["--output", "/tmp/icons"])
        assert args.output == "/tmp/icons"
    
    def test_output_default(self):
        """Test default output directory."""
        args = parse_args([])
        assert args.output == "data"
    
    def test_verbose_flag(self):
        """Test verbose flag."""
        args = parse_args(["--verbose"])
        assert args.verbose is True
    
    def test_verbose_short_flag(self):
        """Test verbose short flag."""
        args = parse_args(["-v"])
        assert args.verbose is True
    
    def test_debug_flag(self):
        """Test debug flag."""
        args = parse_args(["--debug"])
        assert args.debug is True
    
    def test_interactive_flag(self):
        """Test interactive flag."""
        args = parse_args(["--interactive"])
        assert args.interactive is True
    
    def test_visible_flag(self):
        """Test visible flag."""
        args = parse_args(["--visible"])
        assert args.visible is True
    
    def test_log_file_argument(self):
        """Test log file argument."""
        args = parse_args(["--log-file", "output.log"])
        assert args.log_file == "output.log"
    
    def test_combined_arguments(self):
        """Test multiple arguments together."""
        args = parse_args([
            "--url", "https://icons8.com/collection/test",
            "--email", "test@example.com",
            "--password", "secret",
            "--format", "both",
            "--size", "256",
            "--output", "icons",
            "--verbose"
        ])
        
        assert args.url == "https://icons8.com/collection/test"
        assert args.email == "test@example.com"
        assert args.password == "secret"
        assert args.format == "both"
        assert args.size == 256
        assert args.output == "icons"
        assert args.verbose is True
    
    def test_invalid_format_rejected(self):
        """Test that invalid format is rejected."""
        with pytest.raises(SystemExit):
            parse_args(["--format", "jpg"])


class TestValidateSize:
    """Tests for size validation."""
    
    def test_valid_sizes(self):
        """Test all valid sizes pass through."""
        for size in VALID_SIZES:
            assert validate_size(size) == size
    
    def test_invalid_size_rounds_down(self):
        """Test invalid size rounds to nearest valid."""
        # 100 should round to 96
        result = validate_size(100)
        assert result in VALID_SIZES
    
    def test_invalid_size_rounds_up(self):
        """Test invalid size rounds to nearest valid."""
        # 300 should round to 256
        result = validate_size(300)
        assert result in VALID_SIZES
    
    def test_very_small_size(self):
        """Test very small size rounds to minimum."""
        result = validate_size(1)
        assert result == 16  # minimum valid size


class TestOutputFormat:
    """Tests for OutputFormat enum."""
    
    def test_png_value(self):
        """Test PNG enum value."""
        assert OutputFormat.PNG.value == "png"
    
    def test_ico_value(self):
        """Test ICO enum value."""
        assert OutputFormat.ICO.value == "ico"
    
    def test_both_value(self):
        """Test BOTH enum value."""
        assert OutputFormat.BOTH.value == "both"


class TestUserConfig:
    """Tests for UserConfig dataclass."""
    
    def test_user_config_creation(self):
        """Test UserConfig creation."""
        config = UserConfig(
            url="https://icons8.com/collection/test",
            email="test@example.com",
            password="secret",
            output_format=OutputFormat.PNG,
            size=256,
            headless=True,
            output_dir="data"
        )
        
        assert config.url == "https://icons8.com/collection/test"
        assert config.email == "test@example.com"
        assert config.password == "secret"
        assert config.output_format == OutputFormat.PNG
        assert config.size == 256
        assert config.headless is True
        assert config.output_dir == "data"
    
    def test_user_config_optional_credentials(self):
        """Test UserConfig with optional credentials."""
        config = UserConfig(
            url="https://icons8.com/collection/test",
            email=None,
            password=None,
            output_format=OutputFormat.ICO,
            size=128,
            headless=False,
            output_dir="output"
        )
        
        assert config.email is None
        assert config.password is None


class TestHelpOutput:
    """Tests for help output."""
    
    def test_help_shows_version(self):
        """Test that --version works."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--version"])
        assert exc_info.value.code == 0
    
    def test_help_shows_help(self):
        """Test that --help works."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--help"])
        assert exc_info.value.code == 0
