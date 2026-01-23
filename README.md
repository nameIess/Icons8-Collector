# Icons8 Collector

A production-grade CLI tool for downloading icons from your [Icons8](https://icons8.com/) collections. It automatically fetches high-quality SVGs and generates production-ready, multi-size **ICO** (Windows) and **ICNS** (macOS) files.

---

## Features

- **SVG-First Workflow**: Downloads vector sources for perfect sharpness at any resolution.
- **Multi-Size Generation**:
  - **.ico**: Includes 16, 32, 48, 64, 128, 256 px layers.
  - **.icns**: Includes 16, 32, 64, 128, 256, 512, 1024 px layers.
- **Crisp Rasterization**: Uses browser-engine rendering to ensure icons look exactly as designed.
- **Batch Processing**: Handles entire collections seamlessly.
- **Secure**: Authentication credentials are handled securely and never stored in plain text.

---

## Quick Start (Recommended Setup)

1. **Clone the repository:**

   ```powershell
   git clone https://github.com/nameIess/Icons8-Collector.git
   cd Icons8-Collector
   ```

2. **Create and activate a virtual environment:**

   **Windows (PowerShell):**

   ```powershell
   python -m venv venv
   venv\Scripts\activate.ps1
   ```

   **macOS/Linux (bash/zsh):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the project in editable mode:**

   ```powershell
   pip install -e .
   ```

   After installation, the `icons8-collector` command will be available globally in your terminal.

4. **Install Playwright browsers (first time only):**
   ```powershell
   python -m playwright install chromium
   ```

---

## Usage Example

Download all icons from a collection and generate ICO/ICNS files:

```powershell
icons8-collector --email "your@email.com" --password "yourPassword123" --url "https://icons8.com/icons/collections/yourcollectionid"
```

- `--email` and `--password`: Your Icons8 account credentials
- `--url`: The full URL to your Icons8 collection
- `--output`: Directory to save icons (default: `icons/`)

> ⚠️ **Security Note:** Passing passwords via command-line arguments may expose them in shell history. For better security, use interactive mode:

```powershell
icons8-collector --interactive
```

---

## Additional Options

| Option          | Description                          | Default    |
| --------------- | ------------------------------------ | ---------- |
| `--output`      | Output directory                     | `icons`    |
| `--visible`     | Show browser window                  | headless   |
| `--interactive` | Run in interactive mode with prompts | false      |
| `--verbose`     | Enable verbose output                | false      |
| `--debug`       | Enable debug output                  | false      |

See all options:

```powershell
icons8-collector --help
```

---

## Troubleshooting

- If you see browser errors, ensure Playwright and Chromium are installed: `python -m playwright install chromium`
- For login issues, check your credentials and try running with `--visible` to debug login steps.

---

## License

[MIT](License)

---

## Credits

Developed by [nameIess](https://github.com/nameIess). Not affiliated with [icons8](https://icons8.com/icons).
