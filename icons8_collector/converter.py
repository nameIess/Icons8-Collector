from pathlib import Path

from PIL import Image

from .exceptions import ConversionError, ValidationError


# Security constants
MAX_IMAGE_DIMENSION = 4096  # Max pixels in any dimension
MAX_IMAGE_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_IMAGE_FORMATS = {'PNG', 'RGBA'}


def validate_image_file(path: Path) -> None:
    if not path.exists():
        raise ValidationError(
            f"Image file does not exist: {path.name}",
            field_name="source_path"
        )
    
    file_size = path.stat().st_size
    if file_size > MAX_IMAGE_FILE_SIZE:
        raise ValidationError(
            f"Image file too large: {file_size} bytes (max: {MAX_IMAGE_FILE_SIZE} bytes)",
            field_name="source_path"
        )
    
    if file_size == 0:
        raise ValidationError(
            "Image file is empty",
            field_name="source_path"
        )


def validate_image_dimensions(img: Image.Image, source_path: Path) -> None:
    if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
        raise ConversionError(
            f"Image dimensions too large: {img.width}x{img.height} "
            f"(max: {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION})",
            source_path=str(source_path)
        )
    
    if img.width <= 0 or img.height <= 0:
        raise ConversionError(
            f"Invalid image dimensions: {img.width}x{img.height}",
            source_path=str(source_path)
        )


def convert_png_to_ico(
    png_path: str | Path, 
    ico_path: str | Path,
    verify_output: bool = True,
    generate_layers: bool = True
) -> None:
    png_path = Path(png_path)
    ico_path = Path(ico_path)
    
    # Validate input file
    validate_image_file(png_path)
    
    # Open and validate image
    try:
        img = Image.open(png_path)
    except Image.DecompressionBombError as e:
        raise ConversionError(
            f"Image appears to be a decompression bomb (potential attack): {png_path.name}",
            source_path=str(png_path),
            original_error=e
        )
    except Image.UnidentifiedImageError as e:
        raise ConversionError(
            f"Cannot identify image file (may be corrupted): {png_path.name}",
            source_path=str(png_path),
            original_error=e
        )
    except Exception as e:
        raise ConversionError(
            f"Failed to open PNG file {png_path.name}: {e}",
            source_path=str(png_path),
            original_error=e
        )
    
    try:
        # Validate dimensions
        validate_image_dimensions(img, png_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            try:
                img = img.convert('RGBA')
            except Exception as e:
                raise ConversionError(
                    f"Failed to convert image to RGBA mode: {e}",
                    source_path=str(png_path),
                    original_error=e
                )
        
        # Ensure parent directory exists
        ico_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as ICO with atomic write
        temp_path = ico_path.with_suffix('.ico.tmp')
        success = False
        try:
            if generate_layers:
                # Standard Windows ICO sizes
                ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
                
                # Filter sizes larger than the original image to avoid upscaling artifacts
                valid_sizes = [s for s in ico_sizes if s[0] <= img.width and s[1] <= img.height]
                if not valid_sizes:
                    valid_sizes = [(img.width, img.height)]
            else:
                # Use only the original image size
                valid_sizes = [(img.width, img.height)]

            img.save(temp_path, format='ICO', sizes=valid_sizes)
            
            # Verify the temp file was created and has content
            if verify_output:
                if not temp_path.exists():
                    raise ConversionError(
                        "ICO file was not created",
                        source_path=str(png_path),
                        target_path=str(ico_path)
                    )
                if temp_path.stat().st_size == 0:
                    raise ConversionError(
                        "ICO file is empty after conversion",
                        source_path=str(png_path),
                        target_path=str(ico_path)
                    )
            
            # Atomic replace (works on Windows even if target exists)
            temp_path.replace(ico_path)
            success = True
            
        except ConversionError:
            # Re-raise our own errors
            raise
        except Exception as e:
            raise ConversionError(
                f"Failed to save ICO file {ico_path.name}: {e}",
                source_path=str(png_path),
                target_path=str(ico_path),
                original_error=e
            )
        finally:
            # Clean up temp file only on error (not after successful rename)
            if not success and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass  # Best effort cleanup
    finally:
        img.close()
