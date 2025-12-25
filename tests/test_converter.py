"""
Tests for the converter module.
"""

import pytest
from pathlib import Path
from PIL import Image

from icons8_collector.converter import convert_png_to_ico
from icons8_collector.exceptions import ConversionError, ValidationError


class TestConvertPngToIco:
    """Tests for PNG to ICO conversion."""
    
    def test_convert_valid_png(self, tmp_path):
        """Test successful conversion of valid PNG."""
        # Create a test PNG
        png_path = tmp_path / "test.png"
        ico_path = tmp_path / "test.ico"
        
        img = Image.new('RGBA', (64, 64), color=(255, 0, 0, 255))
        img.save(png_path, 'PNG')
        
        convert_png_to_ico(png_path, ico_path)
        
        assert ico_path.exists()
        assert ico_path.stat().st_size > 0
    
    def test_convert_creates_parent_dirs(self, tmp_path):
        """Test that conversion creates parent directories."""
        png_path = tmp_path / "test.png"
        ico_path = tmp_path / "subdir" / "nested" / "test.ico"
        
        img = Image.new('RGBA', (32, 32), color=(0, 255, 0, 255))
        img.save(png_path, 'PNG')
        
        convert_png_to_ico(png_path, ico_path)
        
        assert ico_path.exists()
    
    def test_convert_nonexistent_png(self, tmp_path):
        """Test error on nonexistent PNG file."""
        png_path = tmp_path / "nonexistent.png"
        ico_path = tmp_path / "test.ico"
        
        with pytest.raises(ValidationError):
            convert_png_to_ico(png_path, ico_path)
    
    def test_convert_rgb_to_rgba(self, tmp_path):
        """Test conversion of RGB image (should convert to RGBA)."""
        png_path = tmp_path / "test_rgb.png"
        ico_path = tmp_path / "test.ico"
        
        # Create RGB image (no alpha)
        img = Image.new('RGB', (48, 48), color=(0, 0, 255))
        img.save(png_path, 'PNG')
        
        convert_png_to_ico(png_path, ico_path)
        
        assert ico_path.exists()
    
    def test_convert_preserves_transparency(self, tmp_path):
        """Test that transparency is preserved."""
        png_path = tmp_path / "test_alpha.png"
        ico_path = tmp_path / "test.ico"
        
        # Create image with transparency
        img = Image.new('RGBA', (64, 64), color=(255, 255, 255, 0))
        img.save(png_path, 'PNG')
        
        convert_png_to_ico(png_path, ico_path)
        
        assert ico_path.exists()
    
    def test_convert_various_sizes(self, tmp_path):
        """Test conversion of various icon sizes."""
        sizes = [16, 32, 48, 64, 128, 256]
        
        for size in sizes:
            png_path = tmp_path / f"test_{size}.png"
            ico_path = tmp_path / f"test_{size}.ico"
            
            img = Image.new('RGBA', (size, size), color=(128, 128, 128, 255))
            img.save(png_path, 'PNG')
            
            convert_png_to_ico(png_path, ico_path)
            
            assert ico_path.exists(), f"Failed for size {size}"
    
    def test_convert_empty_file(self, tmp_path):
        """Test error on empty PNG file."""
        png_path = tmp_path / "empty.png"
        ico_path = tmp_path / "test.ico"
        
        # Create empty file
        png_path.touch()
        
        with pytest.raises(ValidationError):
            convert_png_to_ico(png_path, ico_path)
    
    def test_convert_corrupted_file(self, tmp_path):
        """Test error on corrupted PNG file."""
        png_path = tmp_path / "corrupted.png"
        ico_path = tmp_path / "test.ico"
        
        # Create file with invalid content
        png_path.write_bytes(b"not a valid png file content")
        
        with pytest.raises(ConversionError):
            convert_png_to_ico(png_path, ico_path)
    
    def test_convert_overwrites_existing(self, tmp_path):
        """Test that conversion overwrites existing ICO file."""
        png_path = tmp_path / "test.png"
        ico_path = tmp_path / "test.ico"
        
        # Create test PNG
        img = Image.new('RGBA', (64, 64), color=(255, 0, 0, 255))
        img.save(png_path, 'PNG')
        
        # Create existing ICO with different content
        ico_path.write_bytes(b"old content")
        old_size = ico_path.stat().st_size
        
        convert_png_to_ico(png_path, ico_path)
        
        # File should be different
        assert ico_path.stat().st_size != old_size
