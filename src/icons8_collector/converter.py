import asyncio
import logging
import io
from pathlib import Path
from typing import Optional, Dict, List

from PIL import Image
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .exceptions import ConversionError, ValidationError

logger = logging.getLogger(__name__)

# Standard Icon Sizes
WIN_SIZES = [16, 32, 48, 64, 128, 256]
MAC_SIZES = [16, 32, 64, 128, 256, 512, 1024]

class SVGConverter:
    """
    Handles conversion of SVG files to multi-resolution ICO and ICNS files
    using Playwright for accurate rasterization.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Initializes the browser for rasterization."""
        if self.browser:
            return

        logger.debug("Starting SVGConverter browser...")
        self.playwright = await async_playwright().start()
        try:
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
        except Exception as e:
            logger.warning(f"Chromium launch failed: {e}. Trying to install browsers or fallback.")
            raise ConversionError(f"Failed to launch browser for SVG conversion: {e}")
        
        self.context = await self.browser.new_context()
        self._page = await self.context.new_page()

    async def stop(self):
        """Closes the browser."""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        logger.debug("SVGConverter browser stopped.")

    async def _get_page(self) -> Page:
        if not self._page or self._page.is_closed():
            if not self.context:
                await self.start()
            self._page = await self.context.new_page()
        return self._page

    async def rasterize_svg(self, svg_path: Path, sizes: List[int]) -> Dict[int, Image.Image]:
        """
        Rasterizes a single SVG file into multiple sizes.
        Returns a dictionary mapping size (int) -> PIL.Image.
        """
        if not svg_path.exists():
            raise ValidationError(f"SVG file not found: {svg_path}")

        page = await self._get_page()
        
        # Read SVG content
        try:
            svg_content = svg_path.read_text(encoding='utf-8')
        except Exception as e:
            raise ConversionError(f"Failed to read SVG file: {svg_path}", original_error=e)

        # We load the SVG directly into the page
        # Using a data URI or just setting content. Setting content is safer for local files.
        # We wrap it in a simple HTML to ensure no margin/padding issues
        html_content = f"""
        <html>
        <body style="margin: 0; padding: 0; overflow: hidden; background: transparent;">
            <div id="container" style="display: inline-block;">
                {svg_content}
            </div>
        </body>
        </html>
        """
        
        try:
            await page.set_content(html_content)
            
            # Locate the SVG element or the container
            # We assume the SVG is valid.
            element = page.locator("#container")
            
            results = {}
            for size in sizes:
                # Resize the container/SVG via JS to ensure crisp rendering at target size
                # We force the SVG to fill the requested size
                await page.evaluate(f'''() => {{
                    const svg = document.querySelector('svg');
                    if (svg) {{
                        svg.setAttribute('width', '{size}px');
                        svg.setAttribute('height', '{size}px');
                        svg.style.width = '{size}px';
                        svg.style.height = '{size}px';
                    }}
                }}''')
                
                # Take screenshot of the element
                # omit_background=True gives us transparency (requires PNG format)
                png_bytes = await element.screenshot(type='png', omit_background=True)
                
                # Convert to PIL Image
                img = Image.open(io.BytesIO(png_bytes))
                results[size] = img.copy() # Copy to keep it in memory after BytesIO closes (though BytesIO is memory)
                img.close()
                
            return results

        except Exception as e:
            raise ConversionError(f"Failed to rasterize SVG {svg_path.name}: {e}", original_error=e)

    def create_ico(self, images: Dict[int, Image.Image], output_path: Path):
        """
        Saves a dictionary of {size: Image} as a multi-size .ico file.
        """
        if not images:
            raise ConversionError("No images provided for ICO creation")

        # Sort images by size (large to small is often preferred, or Pillow handles it)
        # Pillow's ICO plugin expects a list of images.
        # The first image is the 'primary' one, but 'sizes' param in save() can take all.
        # Actually, if we pass a sequence to save(..., append_images=...), it works for some formats (GIF/TIFF/PDF).
        # For ICO, Pillow uses the `sizes` argument which implies it resamples, OR we can pass a list containing all sizes.
        
        # Correct approach for modern Pillow:
        # img.save(fp, format='ICO', sizes=[(w, h), ...]) RE-SAMPLES.
        # To avoid resampling and use our exact rasters, we need to construct the ICO carefully.
        # Pillow supports saving multiple sizes if we pass them? 
        # Actually Pillow's ICO support is a bit basic. It often resamples from the *saving* image.
        
        # Strategy: The standard Pillow `save(format='ICO')` takes `sizes=[(w,h)...]` and resamples the source image.
        # We DON'T want that. We want to pack our pre-rendered images.
        # Pillow 9.2+ supports `append_images` for ICO? No.
        
        # Workaround: Use the largest image as the base, and pass the others.
        # BUT Pillow will re-scale the base image to the other sizes defined in `sizes=...`.
        # This defeats our "crisp rasterization" goal.
        
        # WE NEED to use a library that packs existing PNGs/Images into ICO without resampling,
        # OR verify if Pillow has a way to "append" images for ICO.
        # Checking Pillow docs: "The sizes parameter... is a list of sizes... the image will be resized..."
        
        # ALTERNATIVE: Use `magick` cli if available? No, must be python.
        # Custom ICO writer? Or strict Pillow usage.
        
        # Let's check `PIL.IcoImagePlugin`.
        # It seems Pillow *always* resizes. This is annoying.
        
        # WAIT! If we look at `save` method for ICO:
        # "You can specify the sizes... The image will be resized..."
        
        # We might need to implement a simple ICO packer or use a workaround.
        # However, for the sake of progress and standard library usage:
        # If we use the largest image (256x256) and let Pillow downscale, it might be "okay" but not "perfect".
        # BUT the prompt asked for "Ensure conversion rasterizes the SVG at those resolutions... Icons must look sharp".
        
        # If Pillow doesn't support packing distinct images, we can write a simple ICO header.
        # ICO format is simple: Header + Directory + PNG data.
        # Since we have PNG bytes (from Playwright) or PIL Images (which can save as PNG).
        # Let's implement a simple ICO packer. It's safer.
        
        self._write_custom_ico(images, output_path)

    def _write_custom_ico(self, images: Dict[int, Image.Image], output_path: Path):
        """
        Packs distinct PIL images into an ICO file without resampling.
        Only supports PNG-compressed icons (Vista+), which is standard now.
        """
        # Header: Reserved (2 bytes), Type (2 bytes, 1=ICO), Count (2 bytes)
        # Directory: 16 bytes per image
        # Image Data: PNG blobs
        
        sorted_sizes = sorted(images.keys(), reverse=True) # Order doesn't strictly matter but nice
        
        # Prepare PNG data for each size
        png_blobs = []
        for size in sorted_sizes:
            img = images[size]
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            png_blobs.append({
                'size': size,
                'data': bio.getvalue(),
                'width': size if size < 256 else 0, # 0 means 256
                'height': size if size < 256 else 0
            })
            
        with open(output_path, 'wb') as f:
            # Header
            f.write(b'\x00\x00') # Reserved
            f.write(b'\x01\x00') # Type 1 (ICO)
            f.write(len(png_blobs).to_bytes(2, 'little'))
            
            offset = 6 + (16 * len(png_blobs))
            
            # Directory
            for blob in png_blobs:
                f.write(blob['width'].to_bytes(1, 'little'))
                f.write(blob['height'].to_bytes(1, 'little'))
                f.write(b'\x00') # Colors (0 = no palette/truecolor)
                f.write(b'\x00') # Reserved
                f.write(b'\x01\x00') # Planes
                f.write(b'\x20\x00') # Bit count (32)
                f.write(len(blob['data']).to_bytes(4, 'little')) # Size of data
                f.write(offset.to_bytes(4, 'little')) # Offset
                
                offset += len(blob['data'])
                
            # Image Data
            for blob in png_blobs:
                f.write(blob['data'])
                
        logger.debug(f"Saved custom ICO to {output_path} with sizes: {sorted_sizes}")

    def create_icns(self, images: Dict[int, Image.Image], output_path: Path):
        """
        Saves a dictionary of {size: Image} as a multi-size .icns file.
        Uses Pillow's ICNS support which is decent, or we handle it if needed.
        Pillow's `save(format='ICNS')` supports `append_images`.
        """
        if not images:
            raise ConversionError("No images provided for ICNS creation")
            
        # Pillow ICNS support:
        # img.save(fp, format='ICNS', append_images=[list of other images])
        # This *does* pack them correctly without resizing if they match standard sizes.
        
        # Sort by size
        sorted_imgs = [images[s] for s in sorted(images.keys())]
        base_img = sorted_imgs[0]
        other_imgs = sorted_imgs[1:]
        
        try:
            base_img.save(output_path, format='ICNS', append_images=other_imgs)
            logger.debug(f"Saved ICNS to {output_path}")
        except Exception as e:
            raise ConversionError(f"Failed to save ICNS file: {e}", original_error=e)

    async def convert_svg_to_formats(self, svg_path: Path, output_dir: Optional[Path] = None, formats: List[str] = ["ico", "icns"]):
        """
        Full workflow: Rasterize -> Save ICO / Save ICNS based on requested formats.
        """
        if output_dir is None:
            output_dir = svg_path.parent
            
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = svg_path.stem
        
        # Determine unique sizes needed based on requested formats
        needed_sizes = set()
        if "ico" in formats:
            needed_sizes.update(WIN_SIZES)
        if "icns" in formats:
            needed_sizes.update(MAC_SIZES)
            
        if not needed_sizes:
            logger.warning("No formats requested for conversion.")
            return

        all_sizes = sorted(list(needed_sizes))
        
        logger.info(f"Rasterizing {svg_path.name} to {len(all_sizes)} sizes...")
        images_map = await self.rasterize_svg(svg_path, all_sizes)
        
        generated = []

        # Generate ICO (Windows sizes)
        if "ico" in formats:
            ico_images = {s: images_map[s] for s in WIN_SIZES if s in images_map}
            ico_path = output_dir / f"{base_name}.ico"
            self.create_ico(ico_images, ico_path)
            generated.append(".ico")
        
        # Generate ICNS (Mac sizes)
        if "icns" in formats:
            icns_images = {s: images_map[s] for s in MAC_SIZES if s in images_map}
            icns_path = output_dir / f"{base_name}.icns"
            self.create_icns(icns_images, icns_path)
            generated.append(".icns")
        
        logger.info(f"Converted {svg_path.name} -> {', '.join(generated)}")
