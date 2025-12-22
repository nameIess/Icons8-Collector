import argparse
import getpass
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .scraper import DEFAULT_SIZE


class OutputFormat(Enum):
    PNG = "png"
    ICO = "ico"
    BOTH = "both"


@dataclass
class UserConfig:
    url: str
    email: Optional[str]
    password: Optional[str]
    output_format: OutputFormat
    size: int
    headless: bool
    output_dir: str


def _mask_email(email: str) -> str:
    if '@' not in email:
        return email[:2] + '***'
    local, domain = email.rsplit('@', 1)
    masked_local = local[:2] + '***' if len(local) > 2 else local[0] + '***'
    return f"{masked_local}@{domain}"


def clear_screen() -> None:
    if sys.platform == 'win32':
        subprocess.run(['cmd', '/c', 'cls'], shell=False)
    else:
        subprocess.run(['clear'], shell=False)


def print_header() -> None:
    clear_screen()
    print("\n")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                                                          ║")
    print("  ║             🎨  ICONS8 DOWNLOADER  🎨                    ║")
    print("  ║                                                          ║")
    print("  ║        Download icons from your Icons8 collections       ║")
    print("  ║                                                          ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print("\n")


def print_section(title: str) -> None:
    print(f"\n  ┌─ {title} " + "─" * (50 - len(title)) + "┐")


def print_option(num: int, text: str, default: bool = False) -> None:
    default_str = " (default)" if default else ""
    print(f"  │  [{num}] {text}{default_str}")


def print_section_end() -> None:
    print("  └" + "─" * 54 + "┘")


def get_input(prompt: str, default: Optional[str] = None) -> str:
    if default:
        result = input(f"  │  {prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"  │  {prompt}: ").strip()


def get_interactive_input() -> Optional[UserConfig]:
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
    email_display = _mask_email(email) if email else '(using env vars or saved session)'
    print(f"  │  Email:      {email_display}")
    format_names = {
        OutputFormat.PNG: 'PNG only',
        OutputFormat.ICO: 'ICO only',
        OutputFormat.BOTH: 'Both PNG and ICO'
    }
    print(f"  │  Format:     {format_names[output_format]}")
    print(f"  │  Size:       {size}px")
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
        output_dir="data"
    )


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Download icons from Icons8.com collections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
        """
Examples:
  %(prog)s --url "https://icons8.com/collections/..." --email "you@email.com" --password "yourpass"
  %(prog)s --url "..." --format both --size 512
  %(prog)s --interactive
        """
    )
    
    parser.add_argument(
        '--url', '-u',
        type=str,
        help='Collection URL to scrape icons from'
    )
    parser.add_argument(
        '--email', '-e',
        type=str,
        help='Icons8 account email'
    )
    parser.add_argument(
        '--password', '-P',
        type=str,
        help='Icons8 account password'
    )
    parser.add_argument(
        '--size', '-z',
        type=int,
        default=DEFAULT_SIZE,
        help=f'Icon size in pixels (default: {DEFAULT_SIZE})'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data',
        help='Output directory (default: data)'
    )
    parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['png', 'ico', 'both'],
        default='ico',
        help='Output format: png, ico, or both (default: ico)'
    )
    parser.add_argument(
        '--visible', '-v',
        action='store_true',
        help='Show browser window (default: headless)'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode (prompts for input)'
    )
    
    return parser


def parse_args() -> argparse.Namespace:
    parser = create_argument_parser()
    return parser.parse_args()


def print_download_complete(
    output_format: OutputFormat,
    downloaded: int,
    converted: int,
    png_path: Optional[str],
    ico_path: Optional[str]
) -> None:
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
    print("\n")
