import shutil
import sys
from pathlib import Path

from .cli import (
    parse_args,
    get_interactive_input,
    print_download_complete,
    OutputFormat,
)
from .scraper import get_collection_icons
from .downloader import download_icon, sanitize_filename
from .converter import convert_png_to_ico
from .exceptions import (
    Icons8CollectorError,
    DownloadError,
    ConversionError,
)


def run_download(
    url: str,
    email: str | None,
    password: str | None,
    size: int,
    output_format: OutputFormat,
    output_dir: str,
    headless: bool,
) -> None:
    # Scrape collection
    print(f"\n  📂 Scraping collection from: {url}")
    icons = get_collection_icons(url, size, email, password, headless)
    
    print(f"Found {len(icons)} icons")
    
    # Setup output directories
    png_path: Path | None = None
    ico_path: Path | None = None
    temp_png_path: Path | None = None
    
    if output_format in (OutputFormat.PNG, OutputFormat.BOTH):
        png_path = Path(output_dir) / "Collection_PNG"
        png_path.mkdir(parents=True, exist_ok=True)
    
    if output_format in (OutputFormat.ICO, OutputFormat.BOTH):
        ico_path = Path(output_dir) / "Collection_ICO"
        ico_path.mkdir(parents=True, exist_ok=True)
    
    # Temp directory for ICO-only mode
    if output_format == OutputFormat.ICO:
        temp_png_path = Path(output_dir) / '.temp_png'
        temp_png_path.mkdir(parents=True, exist_ok=True)
    
    # Determine where to save PNGs
    download_dir = png_path if png_path else temp_png_path
    
    print(f"\nDownloading icons...")
    downloaded = 0
    converted = 0
    errors: list[str] = []
    
    for i, icon in enumerate(icons, 1):
        name = icon.name or f'icon_{i}'
        safe_name = sanitize_filename(name, f'icon_{i}')
        
        png_file = download_dir / f"{safe_name}.png"
        
        print(f"[{i}/{len(icons)}] {name}...")
        
        try:
            download_icon(icon.url, png_file, base_dir=download_dir)
            downloaded += 1
            
            if output_format in (OutputFormat.ICO, OutputFormat.BOTH):
                ico_file = ico_path / f"{safe_name}.ico"
                try:
                    convert_png_to_ico(png_file, ico_file)
                    converted += 1
                except ConversionError as e:
                    errors.append(f"Conversion failed for {name}: {e}")
                    print(f"  ⚠ Conversion error: {e}")
                
                # Remove PNG if ICO-only mode
                if output_format == OutputFormat.ICO:
                    png_file.unlink(missing_ok=True)
                    
        except DownloadError as e:
            errors.append(f"Download failed for {name}: {e}")
            print(f"  ⚠ Download error: {e}")
    
    # Clean up temp directory
    if temp_png_path and temp_png_path.exists():
        shutil.rmtree(temp_png_path)
    
    # Print summary
    print_download_complete(
        output_format=output_format,
        downloaded=downloaded,
        converted=converted,
        png_path=str(png_path) if png_path else None,
        ico_path=str(ico_path) if ico_path else None,
    )
    
    # Report errors if any
    if errors:
        print(f"  ⚠ {len(errors)} error(s) occurred during download:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"    - {error}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more")
        print()


def main() -> int:
    args = parse_args()
    
    try:
        # Interactive mode if no URL provided or explicitly requested
        if args.interactive or not args.url:
            user_input = get_interactive_input()
            
            if user_input is None:
                return 0
            
            run_download(
                url=user_input.url,
                email=user_input.email,
                password=user_input.password,
                size=user_input.size,
                output_format=user_input.output_format,
                output_dir=user_input.output_dir,
                headless=user_input.headless,
            )
        else:
            # CLI mode
            format_map = {
                'png': OutputFormat.PNG,
                'ico': OutputFormat.ICO,
                'both': OutputFormat.BOTH,
            }
            
            run_download(
                url=args.url,
                email=args.email,
                password=args.password,
                size=args.size,
                output_format=format_map[args.format],
                output_dir=args.output,
                headless=not args.visible,
            )
        
        return 0
        
    except Icons8CollectorError as e:
        print(f"\n  ❌ Error: {e}\n", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n  Cancelled by user.\n")
        return 130


if __name__ == "__main__":
    sys.exit(main())
