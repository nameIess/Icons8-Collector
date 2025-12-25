# 🎨 Icons8 Collector

A production-grade Python CLI tool to download icons from your Icons8 collections. Supports PNG and ICO formats with automatic conversion.

## ⚠️ Disclaimer

This tool is intended for **personal use only** to download icons from collections you have legitimate access to. Please ensure you comply with [Icons8's Terms of Service](https://icons8.com/terms) when using this tool. The authors are not responsible for any misuse.

## ✨ Features

- 🔐 **Secure Authentication** - Login with session caching (no repeated logins)
- 💾 **Session Persistence** - Faster subsequent runs with saved sessions
- 🖼️ **Multiple Formats** - Export as PNG, ICO, or both
- 📐 **Flexible Sizes** - Support for 16px to 512px icons
- 🤖 **Headless Mode** - Run without visible browser window
- 🎛️ **Dual Interface** - Interactive terminal UI or command-line mode
- 🔄 **Automatic Retry** - Built-in retry with exponential backoff for reliability
- 📦 **Bulk Download** - Download entire collections at once
- 🐍 **Installable Package** - Install via pip for easy access

## 📋 Requirements

- Python 3.10 or higher
- Windows, macOS, or Linux
- Icons8 account with access to collections

## 📥 Installation

### Option 1: Install from Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/nameIess/Icons8-Collector.git
cd Icons8-Collector

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Install in development mode
pip install -e .

# Install Playwright browser
python -m playwright install chromium
```

### Option 2: Install Dependencies Only

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## 🚀 Usage

### Command Line Mode

After installation, the `icons8-collector` (or `icons8`) command is available:

```bash
# Basic usage with authentication
icons8-collector --url "https://icons8.com/icons/collections/YOUR_ID" \
    --email "your@email.com" \
    --password "yourpassword"

# Download as PNG with custom size
icons8-collector --url "https://icons8.com/icons/collections/YOUR_ID" \
    --format png --size 512 --output ./my-icons

# Download both PNG and ICO
icons8-collector --url "..." --format both

# Enable verbose output for debugging
icons8-collector --url "..." --verbose

# Show browser window (useful for debugging)
icons8-collector --url "..." --visible
```

### Interactive Mode

Run without a URL or with `--interactive` for a guided experience:

```bash
icons8-collector --interactive
# or simply
icons8-collector
```

The interactive mode will guide you through:

- Collection URL input
- Authentication
- Output format selection (PNG, ICO, or both)
- Icon size selection
- Browser display mode

### Command Line Options

| Option          | Short | Description                                      | Default |
| --------------- | ----- | ------------------------------------------------ | ------- |
| `--url`         | `-u`  | Icons8 collection URL                            | —       |
| `--email`       | `-e`  | Icons8 account email                             | —       |
| `--password`    | `-P`  | Icons8 account password                          | —       |
| `--format`      | `-f`  | Output format: `png`, `ico`, `both`              | `ico`   |
| `--size`        | `-s`  | Icon size: 16, 24, 32, 48, 64, 96, 128, 256, 512 | `256`   |
| `--output`      | `-o`  | Output directory                                 | `data`  |
| `--interactive` | `-i`  | Run in interactive mode                          | `False` |
| `--visible`     |       | Show browser window                              | `False` |
| `--verbose`     | `-v`  | Enable verbose output                            | `False` |
| `--debug`       |       | Enable debug output                              | `False` |
| `--log-file`    |       | Write logs to file                               | —       |
| `--version`     | `-V`  | Show version and exit                            | —       |
| `--help`        | `-h`  | Show help and exit                               | —       |

### Examples

```bash
# Download collection as ICO files (default)
icons8-collector -u "https://icons8.com/icons/collections/abc123" \
    -e "user@example.com" -P "password"

# Download as 512px PNG files to custom directory
icons8-collector -u "https://icons8.com/icons/collections/abc123" \
    -e "user@example.com" -P "password" \
    -f png -s 512 -o ./icons

# Use with verbose logging
icons8-collector -u "..." -e "..." -P "..." -v

# Debug mode with log file
icons8-collector -u "..." -e "..." -P "..." --debug --log-file debug.log
```

## 📁 Output Structure

Downloaded icons are saved to the specified output directory (default: `./data`):

```
data/
├── Collection_PNG/    # PNG icons (if format is png or both)
│   ├── icon_name_1.png
│   ├── icon_name_2.png
│   └── ...
└── Collection_ICO/    # ICO icons (if format is ico or both)
    ├── icon_name_1.ico
    ├── icon_name_2.ico
    └── ...
```

## 🧪 Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=icons8_collector
```

### Project Structure

```
Icons8-Collector/
├── icons8_collector/
│   ├── __init__.py      # Package initialization
│   ├── cli.py           # Command-line interface
│   ├── client.py        # Icons8Client for network operations
│   ├── scraper.py       # Browser automation for collection scraping
│   ├── converter.py     # PNG to ICO conversion
│   ├── downloader.py    # Legacy download functions
│   ├── auth.py          # Authentication handling
│   ├── exceptions.py    # Custom exceptions
│   ├── logging_config.py # Logging configuration
│   └── main.py          # Legacy entry point
├── tests/
│   ├── test_client.py   # Client tests
│   ├── test_cli.py      # CLI tests
│   └── test_converter.py # Converter tests
├── pyproject.toml       # Package configuration
├── requirements.txt     # Dependencies
└── README.md
```

## ⚙️ How It Works

1. **Authentication**: Uses Playwright to automate browser login to Icons8
2. **Session Caching**: Saves browser session to avoid repeated logins
3. **Collection Scraping**: Scrolls through the collection page to load all icons
4. **Icon Extraction**: Extracts icon IDs and metadata from the page
5. **Download**: Downloads each icon as PNG using the Icons8 image API
6. **Conversion**: Optionally converts PNG files to ICO format

## 🛡️ Security Features

- URL validation to prevent SSRF attacks
- Path traversal prevention for output files
- Credential sanitization in error messages
- HTTPS-only connections
- Domain allowlisting for downloads

## ⚠️ Limitations

- **Requires Icons8 Account**: You need valid Icons8 credentials with access to the collections you want to download
- **Rate Limiting**: Icons8 may rate-limit excessive requests
- **Page Structure Changes**: The scraper may break if Icons8 changes their website structure
- **Not for Bulk Scraping**: This tool is designed for downloading your own collections, not for bulk scraping the Icons8 catalog
- **Session Expiry**: Saved sessions may expire and require re-authentication

## 🐛 Troubleshooting

### Browser Launch Fails

```bash
# Reinstall Playwright browsers
python -m playwright install chromium
```

### Login Issues

- Verify your credentials are correct
- Try running with `--visible` to see the browser
- Check if Icons8 is showing a CAPTCHA
- Clear browser data: delete the `.browser_data` directory

### No Icons Found

- Ensure the collection URL is correct
- Verify you have access to the collection
- Try running with `--visible` to debug
- Check verbose output with `--verbose`

### Timeout Errors

- Check your internet connection
- Try with `--visible` to see if the page is loading
- Increase default timeout in the code if needed

## 📄 License

MIT License - see [LICENSE](License) for details.

## 🙏 Acknowledgments

- [Icons8](https://icons8.com) for their excellent icon library
- [Playwright](https://playwright.dev) for browser automation
- [Pillow](https://pillow.readthedocs.io) for image processing

---

**Note**: This is an unofficial tool and is not affiliated with, authorized by, or endorsed by Icons8.
