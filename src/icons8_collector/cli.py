import argparse
import asyncio
import getpass
import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import __version__
from .logging_config import setup_logging, get_logger
from .auth import _mask_email
from .scraper import scrape_collection, download_files_via_browser
from .converter import IconConverter, ConversionError
from .exceptions import Icons8CollectorError

logger = get_logger("cli")


# ============================================================================ 
# Constants
# ============================================================================ 

DEFAULT_OUTPUT_DIR = "icons"


# ============================================================================ 
# Data Classes
# ============================================================================ 

@dataclass
class UserConfig:
    url: str
    email: Optional[str]
    password: Optional[str]
    headless: bool
    output_dir: str
    output_format: str


# ============================================================================ 
# Interactive Mode Functions
# ============================================================================ 

def get_input(prompt: str, default: Optional[str] = None) -> str:
    if default:
        result = input(f"  │  {prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"  │  {prompt}: ").strip()


def get_interactive_input() -> Optional[UserConfig]:
    print("\n")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                                                          ║")
    print("  ║             🎨  ICONS8 COLLECTOR  🎨                     ║")
    print("  ║                                                          ║")
    print("  ║        Download icons from your Icons8 collections       ║")
    print("  ║            (Generates multi-size ICO/ICNS)               ║")
    print("  ║                                                          ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(f"                         v{__version__}")
    print("\n")
    
    # Collection URL
    print("  ┌─ COLLECTION URL ────────────────────────────────────────┐")
    print("  │")
    url = get_input("Enter collection URL")
    if not url:
        print("  │  ⚠ URL is required.")
        return None
    print("  │")
    print("  └─────────────────────────────────────────────────────────┘")
    
    # Login credentials
    print("\n  ┌─ LOGIN CREDENTIALS ─────────────────────────────────────┐")
    print("  │")
    print("  │  (Leave empty if already logged in via saved session)")
    print("  │")
    email = get_input("Email")
    password = None
    if email:
        password = getpass.getpass("  │  Password: ")
    print("  │")
    print("  └─────────────────────────────────────────────────────────┘")
    
    # Output Format
    print("\n  ┌─ OUTPUT FORMAT ─────────────────────────────────────────┐")
    print("  │")
    print("  │  [1] Windows (.ico) (default)")
    print("  │  [2] Mac (.icns)")
    print("  │  [3] Both")
    print("  │")
    format_choice = get_input("Select format", "1")
    format_map = {'1': 'ico', '2': 'icns', '3': 'both'}
    output_format = format_map.get(format_choice, 'ico')
    print("  │")
    print("  └─────────────────────────────────────────────────────────┘")

    # Output directory
    print("\n  ┌─ OUTPUT DIRECTORY ──────────────────────────────────────┐")
    print("  │")
    output_dir = get_input("Output directory", DEFAULT_OUTPUT_DIR)
    print("  │")
    print("  └─────────────────────────────────────────────────────────┘")
    
    # Confirmation
    print("\n")
    print("  ┌─ SUMMARY ───────────────────────────────────────────────┐")
    print("  │")
    url_display = f"{url[:45]}..." if len(url) > 45 else url
    print(f"  │  Collection: {url_display}")
    email_display = _mask_email(email) if email else '(using saved session)'
    print(f"  │  Email:      {email_display}")
    print(f"  │  Format:     {output_format.upper()}")
    print(f"  │  Output:     {output_dir}")
    print("  │")
    print("  └─────────────────────────────────────────────────────────┘")
    print("\n")
    
    confirm = input("  Press ENTER to start download (or 'q' to quit): ").strip().lower()
    if confirm == 'q':
        print("\n  Cancelled.\n")
        return None
    
    return UserConfig(
        url=url,
        email=email if email else None,
        password=password if password else None,
        headless=True,
        output_dir=output_dir,
        output_format=output_format
    )


# ============================================================================ 
# CLI Argument Parser
# ============================================================================ 

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="icons8-collector",
        description="Download icons from Icons8 and convert to multi-size ICO/ICNS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Version
    parser.add_argument(
        '--version', '-V',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    # Required arguments
    parser.add_argument(
        '--url', '-u',
        type=str,
        metavar='URL',
        help='Icons8 collection URL to download from'
    )
    
    # Authentication
    auth_group = parser.add_argument_group('authentication')
    auth_group.add_argument(
        '--email', '-e',
        type=str,
        metavar='EMAIL',
        help='Icons8 account email'
    )
    auth_group.add_argument(
        '--password', '-p',
        type=str,
        metavar='PASS',
        help='Icons8 account password'
    )
    
    # Output options
    output_group = parser.add_argument_group('output options')
    output_group.add_argument(
        '--format', '-f',
        type=str,
        choices=['ico', 'icns', 'both'],
        default='ico',
        help='Output format (default: ico)'
    )
    output_group.add_argument(
        '--output', '-o',
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        metavar='DIR',
        help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})'
    )
    
    # Mode options
    mode_group = parser.add_argument_group('mode options')
    mode_group.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    mode_group.add_argument(
        '--visible',
        action='store_true',
        help='Show browser window during scraping/conversion'
    )
    
    # Logging options
    log_group = parser.add_argument_group('logging options')
    log_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    log_group.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    log_group.add_argument(
        '--log-file',
        type=str,
        metavar='FILE',
        help='Write logs to file'
    )
    
    return parser


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = create_argument_parser()
    return parser.parse_args(args)


# ============================================================================ 
# Main Logic
# ============================================================================ 

async def async_run_download(
    url: str,
    email: Optional[str],
    password: Optional[str],
    output_dir: str,
    output_format: str,
    headless: bool
) -> int:
    # 1. Scrape Collection
    logger.info(f"Scraping collection: {url}")
    print(f"\n  🔍 Scraping collection...")
    
    try:
        # We don't pass size anymore, letting scraper default or use what's needed for SVG
        # We also ignore the cookies/ua return since download_files_via_browser handles it internally
        icons, _, _ = await scrape_collection(url, email=email, password=password, headless=headless)
    except Icons8CollectorError as e:
        print(f"\n  ❌ Error: {e}")
        return 1

    print(f"  ✓ Found {len(icons)} icons")
    logger.info(f"Found {len(icons)} icons")

    if not icons:
        print("\n  ⚠ No icons found.")
        return 1

    # Prepare directories
    base_path = Path(output_dir)
    png_dir = base_path / "png"
    png_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Download PNGs using Browser (Stealth)
    # We use the scraper module's download function to share the session and bypass 403
    downloaded_paths = await download_files_via_browser(icons, png_dir, headless)
    
    downloaded_files = [Path(p) for p in downloaded_paths]

    if not downloaded_files:
        print("\n  ❌ No files downloaded successfully.")
        return 1

    # 3. Convert to ICO/ICNS
    print(f"\n  🎨 Converting to {output_format.upper()}...")
    converted_count = 0
    
    # Determine requested formats
    requested_formats = ["ico", "icns"] if output_format == "both" else [output_format]
    
    # Initialize Icon Converter (Pillow based)
    converter = IconConverter()
    total = len(downloaded_files)
    for i, img_path in enumerate(downloaded_files, 1):
        print(f"  [{i}/{total}] Converting {img_path.stem}...", end=" ", flush=True)
        try:
            # Output to the parent directory (root of output_dir), not png_dir
            converter.convert_image_to_formats(
                img_path, 
                output_dir=base_path,
                formats=requested_formats
            )
            converted_count += 1
            print("✓")
            
            # Cleanup: Delete the source PNG after conversion
            try:
                img_path.unlink()
            except Exception:
                pass
                
        except ConversionError as e:
            print("✗")
            logger.error(f"Conversion failed for {img_path.name}: {e}")

    # Cleanup: Remove the temporary PNG directory
    try:
        shutil.rmtree(png_dir)
    except Exception:
        pass

    # Summary
    print("\n")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                                                          ║")
    print("  ║              ✅  PROCESS COMPLETE!  ✅                   ║")
    print("  ║                                                          ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print("\n")
    print(f"  📁 PNGs Downloaded: {len(downloaded_files)}")
    print(f"  🎨 Icons Converted: {converted_count}")
    print(f"  📂 Output Location: {base_path.absolute()}")
            
    return 0


def main(args: Optional[list[str]] = None) -> int:
    parsed_args = parse_args(args)
    
    setup_logging(
        verbose=parsed_args.verbose,
        debug=parsed_args.debug,
        log_file=parsed_args.log_file,
    )
    
    logger.debug("Starting CLI...")
    
    try:
        if parsed_args.interactive or not parsed_args.url:
            user_config = get_interactive_input()
            if not user_config:
                return 0
            
            return asyncio.run(async_run_download(
                url=user_config.url,
                email=user_config.email,
                password=user_config.password,
                output_dir=user_config.output_dir,
                output_format=user_config.output_format,
                headless=user_config.headless
            ))
        else:
            return asyncio.run(async_run_download(
                url=parsed_args.url,
                email=parsed_args.email,
                password=parsed_args.password,
                output_dir=parsed_args.output,
                output_format=parsed_args.format,
                headless=not parsed_args.visible
            ))
            
    except KeyboardInterrupt:
        print("\n  Cancelled by user.")
        return 130
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n  ❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())