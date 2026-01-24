# 🎨 Icons8 Collector

_A production-grade CLI tool to download and convert icons from Icons8 collections_

---

## 🚀 Overview

**Icons8 Collector** is a powerful Python CLI tool that automates the process of downloading high-quality icons from your Icons8 collections. It features stealthy web scraping, session-cached authentication, and automatic conversion to production-ready multi-size ICO and ICNS files for Windows and macOS applications.

Perfect for developers and designers who need perfectly scaled icons without manual downloading and resizing.

---

## ✨ Key Features

- 🔐 **Smart Authentication**: Persistent session caching - login once, collect forever
- 🕵️ **Stealth Scraping**: Advanced Playwright-based browser automation to bypass restrictions
- 📦 **Multi-Format Output**: Generate ICO, ICNS, or both formats with all standard OS resolutions (16px to 1024px)
- 🎨 **Colorful TUI**: Beautiful colored terminal interface with real-time progress feedback
- 🧹 **Clean Workflow**: Automatic cleanup of temporary files after conversion
- 🏃‍♂️ **Flexible Modes**: Interactive CLI or headless/scripted operation
- ⚡ **High Performance**: Concurrent downloading and efficient conversion pipeline

---

## 🛠️ Quick Start

### Prerequisites

- Python 3.10 or higher
- Git (optional, for cloning)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/nameIess/Icons8-Collector.git
   cd Icons8-Collector
   ```

   Or [Download as ZIP](https://github.com/nameIess/Icons8-Collector/archive/refs/heads/master.zip) and extract.

2. **Create virtual environment:**

   ```bash
   python -m venv icon-venv
   # Windows:
   .\icon-venv\Scripts\activate
   # macOS/Linux:
   source icon-venv/bin/activate
   ```

3. **Install the package:**

   ```bash
   pip install -e .
   ```

4. **Install browser engine:**
   ```bash
   python -m playwright install chromium
   ```

---

## 📖 Usage

### Interactive Mode (Recommended)

```bash
icons8-collector --interactive
```

### Command Line Mode

```bash
icons8-collector --url "https://icons8.com/icons/collections/YOUR_COLLECTION_ID" --format ico
```

### Examples

**Download as ICO files:**

```bash
icons8-collector -u "https://icons8.com/icons/collections/abc123" -f ico -o my-icons
```

**Download both ICO and ICNS:**

```bash
icons8-collector --url "https://icons8.com/icons/collections/abc123" --format both
```

**Debug mode with visible browser:**

```bash
icons8-collector -u "https://icons8.com/icons/collections/abc123" --visible --verbose
```

---

## ⚙️ Command Line Options

| Option          | Short | Description                          | Default      |
| --------------- | ----- | ------------------------------------ | ------------ |
| `--url`         | `-u`  | Icons8 collection URL                | **Required** |
| `--email`       | `-e`  | Icons8 account email                 | Optional     |
| `--password`    | `-p`  | Icons8 account password              | Optional     |
| `--format`      | `-f`  | Output format: `ico`, `icns`, `both` | `ico`        |
| `--output`      | `-o`  | Output directory                     | `icons`      |
| `--interactive` | `-i`  | Run in interactive mode              | `false`      |
| `--visible`     |       | Show browser window                  | `headless`   |
| `--verbose`     | `-v`  | Enable verbose logging               | `false`      |
| `--debug`       |       | Enable debug logging                 | `false`      |
| `--version`     | `-V`  | Show version                         |              |
| `--help`        | `-h`  | Show help                            |              |

---

## 🏗️ Project Structure

```
Icons8-Collector/
├── src/icons8_collector/
│   ├── __init__.py
│   ├── cli.py           # Main CLI interface
│   ├── scraper.py       # Web scraping logic
│   ├── converter.py     # Icon conversion utilities
│   ├── auth.py          # Authentication handling
│   ├── client.py        # Icons8 API client
│   ├── exceptions.py    # Custom exceptions
│   └── logging_config.py # Logging configuration
├── pyproject.toml       # Project configuration
├── requirements.txt     # Dependencies
├── README.md           # This file
└── LICENSE             # MIT License
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](License) file for details.

---

## ⚠️ Disclaimer

This tool is for personal use with Icons8 collections you have access to. Please respect Icons8's terms of service and copyright. The authors are not responsible for misuse.

---
