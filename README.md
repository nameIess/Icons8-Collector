# 🎨 Icons8 Collector

_The ultimate way to bulk download high-quality icons from Icons8!_

---

## 🚀 Overview

**Icons8 Collector** is a production-grade Python tool for bulk downloading icons from your Icons8 collections.  
It automates the entire pipeline: from stealthy scraping and session-cached login to downloading high-res assets and converting them into production-ready **multi-size ICO and ICNS** files.  
Ideal for developers and designers who need perfectly scaled icons for Windows and macOS without the manual hassle.

---

## ✨ Features

- 🔐 **Automated Login** with persistent session caching — login once, collect forever.
- 🕵️ **Stealth Engine**: Advanced Playwright-based scraping to bypass blocks and 403 errors.
- 📦 **Multi-Size Generation**: Automatically builds icons containing all standard OS resolutions (16px to 1024px).
- 🧹 **Clean Workflow**: Automatically fetches 512px sources and cleans up temporary files after conversion.
- 🏃‍♂️ **Headless or Interactive**: Use the beautiful interactive CLI or script it with arguments.

---

## 🛠️ Setup Instructions

Follow these steps to get the tool up and running on your system:

### 1. Prerequisites
Ensure you have **Python 3.10** or higher installed. You can check your version with:
```bash
python --version
```

### 2. Get the Code
Clone the repository:
```bash
git clone https://github.com/nameIess/Icons8-Collector.git
cd Icons8-Collector
```
Or [Download as ZIP](https://github.com/nameIess/Icons8-Collector/archive/refs/heads/master.zip).

### 3. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 4. Install the Package
Install in editable mode to make the `icons8-collector` command available globally in your environment:
```bash
pip install -e .
```

### 5. Install Browser Engine
The tool uses Playwright to mimic a real user. Install the required Chromium browser:
```bash
python -m playwright install chromium
```

---

## 🏗️ Usage

Run the collector with the default interactive guide:
```bash
icons8-collector --interactive
```

Or run in headless/script mode:
```bash
icons8-collector --url "https://icons8.com/icons/collections/..." --format ico
```

### ⚙️ Available Options

| Option | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--url` | `-u` | The full URL to your Icons8 collection | **Required** |
| `--format` | `-f` | Output format: `ico`, `icns`, or `both` | `ico` |
| `--output` | `-o` | Directory where icons will be saved | `icons` |
| `--interactive`| `-i` | Run with step-by-step prompts | `false` |
| `--email` | `-e` | Your Icons8 account email | `Optional` |
| `--password` | `-P` | Your Icons8 account password | `Optional` |
| `--visible` | | Show the browser window (for debugging) | `headless`|
| `--verbose` | `-v` | Enable detailed processing logs | `false` |
| `--debug` | | Enable maximum logging for developers | `false` |

---

## 📚 Example

```bash
icons8-collector --url "YOUR_COLLECTION_URL" --format both --output my_icons
```
This command scrapes the collection, downloads the best source quality, and generates both `.ico` and `.icns` files in the `my_icons` folder.

---

## 📝 License

This project is licensed under the [MIT-LICENSE](LICENSE).

---
