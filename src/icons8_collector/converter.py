import logging
import io
from pathlib import Path
from typing import Optional, Dict, List

from PIL import Image

from .exceptions import ConversionError, ValidationError

logger = logging.getLogger(__name__)

# Standard Icon Sizes
WIN_SIZES = [16, 32, 48, 64, 128, 256]
MAC_SIZES = [16, 32, 64, 128, 256, 512, 1024]

class IconConverter:
    """
    Handles conversion of source PNG files to multi-resolution ICO and ICNS files
    using Pillow for high-quality resizing.
    """
    
    def __init__(self):
        pass

    def resize_image(self, source_img: Image.Image, sizes: List[int]) -> Dict[int, Image.Image]:
        """
        Resizes a single Image into multiple sizes.
        Returns a dictionary mapping size (int) -> PIL.Image.
        """
        results = {}
        # Ensure image is in RGBA for transparency support
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')

        for size in sizes:
            # Use LANCZOS for high-quality downscaling
            resized = source_img.resize((size, size), Image.Resampling.LANCZOS)
            results[size] = resized
            
        return results

    def create_ico(self, images: Dict[int, Image.Image], output_path: Path):
        """
        Saves a dictionary of {size: Image} as a multi-size .ico file.
        Uses a custom packer to avoid Pillow's internal resampling.
        """
        if not images:
            raise ConversionError("No images provided for ICO creation")
        
        self._write_custom_ico(images, output_path)

    def _write_custom_ico(self, images: Dict[int, Image.Image], output_path: Path):
        """
        Packs distinct PIL images into an ICO file without resampling.
        """
        sorted_sizes = sorted(images.keys(), reverse=True) 
        
        png_blobs = []
        for size in sorted_sizes:
            img = images[size]
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            png_blobs.append({
                'size': size,
                'data': bio.getvalue(),
                'width': size if size < 256 else 0,
                'height': size if size < 256 else 0
            })
            
        with open(output_path, 'wb') as f:
            f.write(b'\x00\x00') # Reserved
            f.write(b'\x01\x00') # Type 1 (ICO)
            f.write(len(png_blobs).to_bytes(2, 'little'))
            
            offset = 6 + (16 * len(png_blobs))
            
            for blob in png_blobs:
                f.write(blob['width'].to_bytes(1, 'little'))
                f.write(blob['height'].to_bytes(1, 'little'))
                f.write(b'\x00') # Colors
                f.write(b'\x00') # Reserved
                f.write(b'\x01\x00') # Planes
                f.write(b'\x20\x00') # Bit count
                f.write(len(blob['data']).to_bytes(4, 'little'))
                f.write(offset.to_bytes(4, 'little'))
                offset += len(blob['data'])
                
            for blob in png_blobs:
                f.write(blob['data'])
                
        logger.debug(f"Saved multi-size ICO to {output_path}")

    def create_icns(self, images: Dict[int, Image.Image], output_path: Path):
        """
        Saves a dictionary of {size: Image} as a multi-size .icns file.
        """
        if not images:
            raise ConversionError("No images provided for ICNS creation")
            
        # Pillow ICNS support
        sorted_imgs = [images[s] for s in sorted(images.keys())]
        base_img = sorted_imgs[0]
        other_imgs = sorted_imgs[1:]
        
        try:
            base_img.save(output_path, format='ICNS', append_images=other_imgs)
            logger.debug(f"Saved ICNS to {output_path}")
        except Exception as e:
            raise ConversionError(f"Failed to save ICNS file: {e}", original_error=e)

    def convert_image_to_formats(self, image_path: Path, output_dir: Optional[Path] = None, formats: List[str] = ["ico", "icns"]):
        """
        Full workflow: Resize -> Save ICO / Save ICNS based on requested formats.
        """
        if output_dir is None:
            output_dir = image_path.parent
            
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = image_path.stem
        
        # Determine unique sizes needed
        needed_sizes = set()
        if "ico" in formats:
            needed_sizes.update(WIN_SIZES)
        if "icns" in formats:
            needed_sizes.update(MAC_SIZES)
            
        if not needed_sizes:
            return

        all_sizes = sorted(list(needed_sizes))
        
        try:
            with Image.open(image_path) as source_img:
                logger.info(f"Resizing {image_path.name} to {len(all_sizes)} sizes...")
                images_map = self.resize_image(source_img, all_sizes)
                
                generated = []

                if "ico" in formats:
                    ico_images = {s: images_map[s] for s in WIN_SIZES if s in images_map}
                    ico_path = output_dir / f"{base_name}.ico"
                    self.create_ico(ico_images, ico_path)
                    generated.append(".ico")
                
                if "icns" in formats:
                    icns_images = {s: images_map[s] for s in MAC_SIZES if s in images_map}
                    icns_path = output_dir / f"{base_name}.icns"
                    self.create_icns(icns_images, icns_path)
                    generated.append(".icns")
                
                logger.info(f"Converted {image_path.name} -> {', '.join(generated)}")
        except Exception as e:
            raise ConversionError(f"Failed to convert {image_path.name}: {e}")
