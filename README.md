# 🎨 Icons8 Collector

A Python tool to download icons from your Icons8 collections. Supports PNG and ICO formats with automatic conversion.

## ✨ Features

- 🔐 Automatic login with session reuse (no repeated logins)
- 💾 Session caching for faster subsequent runs
- 🖼️ Multiple output formats: PNG, ICO, or both
- 📐 Flexible icon sizes: 64–512px (or custom)
- 🤖 Headless browser mode (default)
- 🎛️ Interactive terminal UI or command-line interface
- 🛡️ Fail-fast error handling with clear error messages
- 📦 Bulk download entire collections

## 📋 Requirements

- Python 3.10 or higher
- Windows, macOS, or Linux

## 📥 Installation

1. **Clone or download the repository:**

   ```bash
   git clone https://github.com/nameIess/Icons8-Collector.git
   cd Icons8-Collector
   ```

   Or [download as ZIP](https://github.com/nameIess/Icons8-Collector/archive/refs/heads/master.zip)

2. **Create and activate a virtual environment (recommended):**

   ```bash
   python -m venv venv
   ```

   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browser:**

   ```bash
   python -m playwright install chromium
   ```

## 🚀 Usage

### Interactive Mode

Run without arguments for an interactive menu:

```bash
python run.py
```

The interactive interface will guide you through:

- Collection URL input
- Authentication (optional)
- Output format selection (PNG, ICO, or both)
- Icon size selection
- Browser display mode

### Command Line Mode

```bash
python run.py --url "https://icons8.com/icons/collections/YOUR_COLLECTION_ID" [options]
```

#### Command Line Options

| Option (Long)   | Shortcut | Description                                       | Default |
| --------------- | -------- | ------------------------------------------------- | ------- |
| `--url`         | `-u`     | Icons8 collection URL (required)                  | —       |
| `--email`       | `-e`     | Icons8 account email (required for first time)    | —       |
| `--password`    | `-P`     | Icons8 account password (required for first time) | —       |
| `--format`      | `-f`     | Output format: `png`, `ico`, or `both`            | `ico`   |
| `--size`        | `-z`     | Icon size in pixels (64–512)                      | `256`   |
| `--output`      | `-o`     | Output directory path                             | `data`  |
| `--visible`     | `-v`     | Show browser window (headless by default)         | `False` |
| `--interactive` | `-i`     | Run in interactive mode (prompts for input)       | `False` |
| `--help`        | `-h`     | Show help message and exit                        | —       |

#### Examples

**Download both PNG and ICO with authentication:**

```bash
python run.py --url "https://icons8.com/icons/collections/12345" \
              --email your@email.com \
              --password yourpassword \
              --format both \
              --size 128
```

> ⚠️ **Security Note:** Passing passwords via command-line arguments may expose them in shell history or process lists. For better security, use interactive mode (`python run.py`) or set environment variables.

**Download ICO only at 512px with visible browser:**

```bash
python run.py --url "https://icons8.com/icons/collections/12345" \
              --format ico \
              --size 512 \
              --visible
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

## 🔧 Project Structure

```
Icons8-Collector/
├── icons8_collector/        # Main package
│   ├── __init__.py
│   ├── auth.py             # Authentication handling
│   ├── cli.py              # Command-line interface
│   ├── converter.py        # PNG to ICO conversion
│   ├── downloader.py       # Icon downloading logic
│   ├── exceptions.py       # Custom exceptions
│   ├── main.py             # Main orchestration
│   └── scraper.py          # Web scraping logic
├── data/                    # Default output directory
├── run.py                   # Entry point script
├── requirements.txt         # Python dependencies
├── License                  # MIT License
└── README.md               # This file
```

## 🛠️ Dependencies

- **requests** (≥2.28.0) - HTTP requests for icon downloads
- **Pillow** (≥9.0.0) - Image processing and PNG to ICO conversion
- **Playwright** (≥1.40.0) - Browser automation for scraping

## ⚠️ Troubleshooting

### Authentication Issues

- Ensure your Icons8 email and password are correct
- Sessions are cached; delete `.auth_session` file to force re-login

### Browser Installation

If Playwright fails to launch, reinstall the browser:

```bash
python -m playwright install chromium --force
```

### Size Limitations

Icons8 may not have all sizes available. If a download fails, try a different size (64, 128, 256, or 512).

## 📝 License

This project is licensed under the MIT License - see the [License](License) file for details.

## ⚠️ Disclaimer

This tool is for personal use only. Respect Icons8's terms of service and only download icons you have the right to use. The authors are not responsible for any misuse of this tool.

**Made with ❤️ by NameIess**
