# Icons8 Collector

A production-grade CLI tool for downloading icons from your [Icons8](https://icons8.com/) collections. Supports PNG and ICO formats, batch downloads, and robust error handling.

---

## Features

- Download all icons from any Icons8 collection URL
- Supports PNG, ICO, or both formats
- Batch download with progress and error reporting
- Headless or visible browser automation (uses Playwright)
- Secure authentication (no credentials stored)
- Cross-platform (Windows, macOS, Linux)

---

## Quick Start (Recommended Setup)

1. **Clone the repository:**

   ```powershell
   git clone https://github.com/nameIess/Icons8-Collector.git
   cd Icons8-Collector
   ```

   Or [download as ZIP](https://github.com/nameIess/Icons8-Collector/archive/refs/heads/master.zip)

2. **Create and activate a virtual environment:**

   ```powershell
   python -m venv venv
   venv\Scripts\activate.ps1
   ```

3. **Install the project in editable mode:**

   ```powershell
   pip install -e .
   ```

4. **Install Playwright browsers (first time only):**
   ```powershell
   python -m playwright install chromium
   ```

---

## Manual Setup (Dependencies Only)

If you want to install only the dependencies (not as an editable package):

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

---

## Usage Example

Download all icons from a collection as PNG and ICO:

```powershell
icons8-collector --email "your@email.com" --password "yourPassword123" --format "both" --url "https://icons8.com/icons/collections/yourcollectionid"
```

- `--email` and `--password`: Your Icons8 account credentials
- `--format`: `png`, `ico`, or `both` (default: `ico`)
- `--url`: The full URL to your Icons8 collection

### Example Command

```powershell
icons8-collector --email "demo.user@example.com" --password "MySecretPass!" --format "png" --url "https://icons8.com/icons/collections/abcd1234efgh5678"
```

---

## Additional Options

| Option          | Description                          | Default  |
| --------------- | ------------------------------------ | -------- |
| `--size`        | Icon size in pixels                  | `256`    |
| `--output`      | Output directory                     | `data`   |
| `--visible`     | Show browser window                  | headless |
| `--interactive` | Run in interactive mode with prompts | false    |
| `--verbose`     | Enable verbose output                | false    |
| `--debug`       | Enable debug output                  | false    |

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
