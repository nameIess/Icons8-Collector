# IconFlow

A production-grade, browser-only icon export workspace.

## Rebuild

`web-app-production` is a clean web rebuild. The previous Python CLI and Playwright implementation is no longer part of the application.

The app intentionally does **not** automate or scrape Icons8. Icons8's current Site Terms prohibit data-mining, robots, and similar extraction methods. Instead, use Icons8's supported **Export** action to export a collection, then import the resulting archive here. This keeps account credentials and sessions out of the application.

Icons8's official icon documentation describes collection export as an archive workflow and documents PNG/SVG collection exports. Free accounts have asset limitations and attribution requirements; users remain responsible for following the current license.

## Features

- macOS/iOS-inspired glass interface
- Responsive desktop and mobile workspace
- Drag-and-drop ZIP collection import
- PNG, SVG, JPEG and WebP import
- Local-only processing: no backend and no uploaded asset data
- PNG generation at 16, 24, 32, 48, 64, 96, 128, 256, 512 and 1024 px
- Multi-resolution Windows ICO generation
- Multi-resolution macOS ICNS generation
- Original SVG preservation when supplied
- Batch ZIP export
- Selection, filtering and removal
- No Icons8 password handling
- No API secret required

## Run

Node.js 20+ is recommended.

```bash
npm install
npm run dev
```

Production build:

```bash
npm run build
npm run preview
```

## Workflow

1. Open your collection in Icons8.
2. Use Icons8's own **Export** action.
3. Drop the resulting ZIP into IconFlow.
4. Select the assets you need.
5. Choose PNG resolutions and/or SVG, ICO, ICNS.
6. Build the export ZIP.

For discovery/search, use the official Icons8 search page and download/export assets you are licensed to use, then import those files into IconFlow.

## Output

- PNG: configurable 16–1024 px
- ICO: 16–256 px multi-image container
- ICNS: 16–1024 px PNG-backed container
- SVG: original source preserved when available

Raster sources are resized with high-quality browser canvas interpolation. SVG sources are rasterized only for generated PNG/ICO/ICNS output.

## Deployment

The build is static:

```bash
npm run build
```

Deploy `dist/` to a static host such as Cloudflare Pages, Netlify, GitHub Pages, or another static hosting provider.

No server-side environment variables are required.

## Quality gates

Before deployment:
- `npm run build`
- ZIP containing mixed SVG and PNG assets
- Duplicate filenames
- Empty selection
- Every PNG resolution
- ICO and ICNS opening on target operating systems
- Large collection import
- Mobile viewport
- Chromium, Firefox and Safari