"""
Command-line interface for Icons8 Collector.

Provides both interactive and command-line modes for downloading icons.
"""

import argparse
import getpass
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from . import __version__
from .logging_config import setup_logging, get_logger

logger = get_logger("cli")


# ============================================================================
# Constants
# ============================================================================

DEFAULT_SIZE = 256
DEFAULT_OUTPUT_DIR = "data"
VALID_SIZES = [16, 24, 32, 48, 64, 96, 128, 256, 512]


# ============================================================================
# Data Classes and Enums
# ============================================================================

class OutputFormat(Enum):
    """Supported output formats for icons."""
    PNG = "png"
    ICO = "ico"
    BOTH = "both"


@dataclass
class UserConfig:
    """User configuration for download operation."""
    url: str
    email: Optional[str]
    password: Optional[str]
    output_format: OutputFormat
    size: int
    headless: bool
    output_dir: str


# ============================================================================
# Interactive Mode Functions
# ============================================================================

def _mask_email(email: str) -> str:
    """Mask email for display."""
    if '@' not in email:
        return email[:2] + '***'
    local, domain = email.rsplit('@', 1)
    masked_local = local[:2] + '***' if len(local) > 2 else local[0] + '***'
    return f"{masked_local}@{domain}"


def clear_screen() -> None:
    """Clear the terminal screen."""
    if sys.platform == 'win32':
        subprocess.run(['cmd', '/c', 'cls'], shell=False, capture_output=True)
    else:
        subprocess.run(['clear'], shell=False, capture_output=True)


def print_header() -> None:
    """Print the application header."""
    clear_screen()
    print("\n")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                                                          ║")
    print("  ║             🎨  ICONS8 COLLECTOR  🎨                     ║")
    print("  ║                                                          ║")
    print("  ║        Download icons from your Icons8 collections       ║")
    print("  ║                                                          ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(f"                         v{__version__}")
    print("\n")


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n  ┌─ {title} " + "─" * (50 - len(title)) + "┐")


def print_option(num: int, text: str, default: bool = False) -> None:
    """Print a menu option."""
    default_str = " (default)" if default else ""
    print(f"  │  [{num}] {text}{default_str}")


def print_section_end() -> None:
    """Print section footer."""
    print("  └" + "─" * 54 + "┘")


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Get input from user with optional default."""
    if default:
        result = input(f"  │  {prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"  │  {prompt}: ").strip()


def get_interactive_input() -> Optional[UserConfig]:
    """
    Run interactive mode to get user configuration.
    
    Returns:
        UserConfig if successful, None if cancelled
    """
    print_header()
    
    # Collection URL
    print_section("COLLECTION URL")
    print("  │")
    url = get_input("Enter collection URL")
    if not url:
        print("  │  ⚠ URL is required.")
        return None
    print("  │")
    print_section_end()
    
    # Login credentials
    print_section("LOGIN CREDENTIALS")
    print("  │")
    print("  │  (Leave empty if already logged in via saved session)")
    print("  │")
    email = get_input("Email")
    password = None
    if email:
        password = getpass.getpass("  │  Password: ")
    print("  │")
    print_section_end()
    
    # Output format
    print_section("OUTPUT FORMAT")
    print("  │")
    print_option(1, "PNG only")
    print_option(2, "ICO only (deletes PNG after conversion)", default=True)
    print_option(3, "Both PNG and ICO")
    print("  │")
    while True:
        format_choice = get_input("Select format", "2")
        if format_choice in ['1', '2', '3']:
            break
        print("  │  ⚠ Invalid choice. Please enter 1, 2, or 3.")
    
    format_map = {'1': OutputFormat.PNG, '2': OutputFormat.ICO, '3': OutputFormat.BOTH}
    output_format = format_map[format_choice]
    print("  │")
    print_section_end()
    
    # Icon size
    print_section("ICON SIZE")
    print("  │")
    print_option(1, "64px  - Small")
    print_option(2, "128px - Medium")
    print_option(3, "256px - Large (Best Quality)", default=True)
    print_option(4, "512px - Extra Large")
    print_option(5, "Custom size")
    print("  │")
    size_choice = get_input("Select size", "3")
    size_map = {'1': 64, '2': 128, '3': 256, '4': 512}
    
    if size_choice in size_map:
        size = size_map[size_choice]
    elif size_choice == '5':
        custom = get_input("Enter custom size (px)", "256")
        if custom.isdigit():
            size = int(custom)
            if size < 16 or size > 512:
                print("  │  ⚠ Size must be between 16 and 512. Using 256.")
                size = 256
        else:
            size = 256
    else:
        size = 256
    print("  │")
    print_section_end()
    
    # Output directory
    print_section("OUTPUT DIRECTORY")
    print("  │")
    output_dir = get_input("Output directory", DEFAULT_OUTPUT_DIR)
    print("  │")
    print_section_end()

    # Browser mode
    print_section("BROWSER MODE")
    print("  │")
    print_option(1, "Headless (invisible)", default=True)
    print_option(2, "Visible (show browser window)")
    print("  │")
    browser_choice = get_input("Select mode", "1")
    headless = browser_choice != '2'
    print("  │")
    print_section_end()
    
    # Confirmation
    print("\n")
    print("  ┌─ SUMMARY " + "─" * 43 + "┐")
    print("  │")
    url_display = f"{url[:45]}..." if len(url) > 45 else url
    print(f"  │  Collection: {url_display}")
    email_display = _mask_email(email) if email else '(using saved session)'
    print(f"  │  Email:      {email_display}")
    format_names = {
        OutputFormat.PNG: 'PNG only',
        OutputFormat.ICO: 'ICO only',
        OutputFormat.BOTH: 'Both PNG and ICO'
    }
    print(f"  │  Format:     {format_names[output_format]}")
    print(f"  │  Size:       {size}px")
    print(f"  │  Output:     {output_dir}")
    print(f"  │  Browser:    {'Headless' if headless else 'Visible'}")
    print("  │")
    print("  └" + "─" * 54 + "┘")
    print("\n")
    
    confirm = input("  Press ENTER to start download (or 'q' to quit): ").strip().lower()
    if confirm == 'q':
        print("\n  Cancelled.\n")
        return None
    
    return UserConfig(
        url=url,
        email=email if email else None,
        password=password if password else None,
        output_format=output_format,
        size=size,
        headless=headless,
        output_dir=output_dir
    )


# ============================================================================
# CLI Argument Parser
# ============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="icons8-collector",
        description="Download icons from Icons8.com collections.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  icons8-collector --url "https://icons8.com/collections/..." --email "user@email.com" --password "pass"
  icons8-collector --url "..." --format both --size 512
  icons8-collector --interactive
  icons8-collector --url "..." --verbose

For more information, visit: https://github.com/nameIess/Icons8-Collector
        """
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
        '--password', '-P',
        type=str,
        metavar='PASS',
        help='Icons8 account password'
    )
    
    # Output options
    output_group = parser.add_argument_group('output options')
    output_group.add_argument(
        '--format', '-f',
        type=str,
        choices=['png', 'ico', 'both'],
        default='ico',
        help='Output format (default: ico)'
    )
    output_group.add_argument(
        '--size', '-s',
        type=int,
        default=DEFAULT_SIZE,
        metavar='SIZE',
        help=f'Icon size in pixels (default: {DEFAULT_SIZE})'
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
        help='Run in interactive mode with prompts'
    )
    mode_group.add_argument(
        '--visible',
        action='store_true',
        help='Show browser window (default: headless)'
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
        help='Enable debug output (very verbose)'
    )
    log_group.add_argument(
        '--log-file',
        type=str,
        metavar='FILE',
        help='Write logs to file'
    )
    
    return parser


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = create_argument_parser()
    return parser.parse_args(args)


def validate_size(size: int) -> int:
    """
    Validate and normalize icon size.
    
    Args:
        size: Requested size in pixels
        
    Returns:
        Valid size (closest valid size if not in VALID_SIZES)
    """
    if size in VALID_SIZES:
        return size
    
    # Find closest valid size
    closest = min(VALID_SIZES, key=lambda x: abs(x - size))
    logger.warning(f"Size {size} not in valid sizes, using closest: {closest}")
    return closest


# ============================================================================
# Output Functions
# ============================================================================

def print_download_complete(
    output_format: OutputFormat,
    downloaded: int,
    converted: int,
    png_path: Optional[str],
    ico_path: Optional[str],
    errors: int = 0,
) -> None:
    """Print download completion summary."""
    print("\n")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                                                          ║")
    print("  ║              ✅  DOWNLOAD COMPLETE!  ✅                  ║")
    print("  ║                                                          ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print("\n")
    
    if output_format == OutputFormat.PNG:
        print(f"  📁 Downloaded {downloaded} PNG files")
        print(f"  📂 Location: {png_path}")
    elif output_format == OutputFormat.ICO:
        print(f"  📁 Converted {converted} ICO files")
        print(f"  📂 Location: {ico_path}")
    else:
        print(f"  📁 Downloaded {downloaded} PNG files to: {png_path}")
        print(f"  📁 Converted {converted} ICO files to: {ico_path}")
    
    if errors > 0:
        print(f"\n  ⚠  {errors} error(s) occurred during download")
    
    print("\n")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"\n  ❌ Error: {message}\n", file=sys.stderr)


# ============================================================================
# Main Entry Point
# ============================================================================

def run_download(
    url: str,
    email: Optional[str],
    password: Optional[str],
    size: int,
    output_format: OutputFormat,
    output_dir: str,
    headless: bool,
) -> int:
    """
    Execute the download operation.
    
    Args:
        url: Collection URL
        email: Account email (optional)
        password: Account password (optional)
        size: Icon size in pixels
        output_format: Desired output format
        output_dir: Output directory path
        headless: Whether to run browser in headless mode
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from .scraper import get_collection_icons
    from .client import Icons8Client, sanitize_filename
    from .converter import convert_png_to_ico
    from .exceptions import Icons8CollectorError, DownloadError, ConversionError
    
    # Scrape collection
    logger.info(f"Scraping collection from: {url}")
    print(f"\n  📂 Scraping collection from: {url}")
    
    try:
        icons = get_collection_icons(url, size, email, password, headless)
    except Icons8CollectorError as e:
        print_error(str(e))
        return 1
    
    print(f"  ✓ Found {len(icons)} icons")
    logger.info(f"Found {len(icons)} icons in collection")
    
    if not icons:
        print_error("No icons found in the collection")
        return 1
    
    # Setup output directories
    png_path: Optional[Path] = None
    ico_path: Optional[Path] = None
    temp_png_path: Optional[Path] = None
    
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
    
    print(f"\n  📥 Downloading icons...")
    logger.info(f"Starting download of {len(icons)} icons")
    
    downloaded = 0
    converted = 0
    errors: list[str] = []
    
    # Create client with retry support
    client = Icons8Client()
    
    try:
        for i, icon in enumerate(icons, 1):
            name = icon.name or f'icon_{i}'
            safe_name = sanitize_filename(name, f'icon_{i}')
            
            png_file = download_dir / f"{safe_name}.png"
            
            print(f"  [{i}/{len(icons)}] {name}...", end=" ", flush=True)
            logger.debug(f"Downloading icon {i}/{len(icons)}: {name}")
            
            try:
                client.download_icon(icon.url, png_file, base_dir=download_dir)
                downloaded += 1
                print("✓")
                
                if output_format in (OutputFormat.ICO, OutputFormat.BOTH):
                    ico_file = ico_path / f"{safe_name}.ico"
                    try:
                        convert_png_to_ico(png_file, ico_file)
                        converted += 1
                        logger.debug(f"Converted {name} to ICO")
                    except ConversionError as e:
                        errors.append(f"Conversion failed for {name}: {e}")
                        logger.warning(f"Conversion error for {name}: {e}")
                    
                    # Remove PNG if ICO-only mode
                    if output_format == OutputFormat.ICO:
                        png_file.unlink(missing_ok=True)
                        
            except DownloadError as e:
                print("✗")
                errors.append(f"Download failed for {name}: {e}")
                logger.warning(f"Download error for {name}: {e}")
    
    finally:
        client.close()
    
    # Clean up temp directory
    if temp_png_path and temp_png_path.exists():
        shutil.rmtree(temp_png_path, ignore_errors=True)
    
    # Print summary
    print_download_complete(
        output_format=output_format,
        downloaded=downloaded,
        converted=converted,
        png_path=str(png_path) if png_path else None,
        ico_path=str(ico_path) if ico_path else None,
        errors=len(errors),
    )
    
    # Report errors if any
    if errors:
        logger.warning(f"{len(errors)} error(s) occurred during download")
        for error in errors[:5]:
            print(f"    - {error}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more")
        print()
    
    return 0 if downloaded > 0 else 1


def main(args: Optional[list[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command-line arguments (uses sys.argv if None)
        
    Returns:
        Exit code
    """
    from .exceptions import Icons8CollectorError
    
    parsed_args = parse_args(args)
    
    # Setup logging
    setup_logging(
        verbose=parsed_args.verbose,
        debug=parsed_args.debug,
        log_file=parsed_args.log_file,
    )
    
    logger.debug(f"Icons8 Collector v{__version__} starting")
    logger.debug(f"Arguments: {parsed_args}")
    
    try:
        # Interactive mode if no URL provided or explicitly requested
        if parsed_args.interactive or not parsed_args.url:
            user_input = get_interactive_input()
            
            if user_input is None:
                return 0
            
            return run_download(
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
            
            # Validate size
            size = validate_size(parsed_args.size)
            
            return run_download(
                url=parsed_args.url,
                email=parsed_args.email,
                password=parsed_args.password,
                size=size,
                output_format=format_map[parsed_args.format],
                output_dir=parsed_args.output,
                headless=not parsed_args.visible,
            )
    
    except Icons8CollectorError as e:
        print_error(str(e))
        logger.error(f"Operation failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n  Cancelled by user.\n")
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.exception("Unexpected error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())
