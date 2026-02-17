# Publisher Clone

A desktop publishing application built with Python and PyQt6, inspired by Microsoft Publisher. Create multi-page documents with shapes, text, images, and freehand drawings, then export to PDF, PNG, or SVG.

## Features

- **Shape tools** — rectangles, ellipses, lines, arrows, polygons
- **Text boxes** — with font, size, bold/italic/underline, alignment controls
- **Image insertion** — drag-to-place with automatic scaling
- **Freehand drawing** — with path smoothing
- **Multi-page documents** — add, delete, duplicate, reorder pages with thumbnail previews
- **Properties panel** — edit position, size, rotation, fill/stroke colors, opacity
- **Layers panel** — z-order management, visibility and lock toggles
- **Rulers** — horizontal and vertical, synced to canvas, switchable units (in/cm/px)
- **Grid and snap** — toggleable grid overlay with snap-to-grid
- **Alignment** — align multiple selected items (left/right/top/bottom/center)
- **Undo/redo** — full undo history for all operations
- **Cut/copy/paste** — duplicate items within and across pages
- **Save/load** — JSON-based `.pubd` format with embedded images
- **Export** — multi-page PDF, per-page PNG/JPEG (configurable DPI), per-page SVG
- **Zoom and pan** — Ctrl+scroll to zoom, middle-click to pan

## Requirements

- Python 3.10 or later
- PyQt6

## Getting Started

### 1. Clone or download the project

```bash
cd ~/Desktop/publisher_clone
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python3 main.py
```

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New | Ctrl+N |
| Open | Ctrl+O |
| Save | Ctrl+S |
| Undo | Ctrl+Z |
| Redo | Ctrl+Shift+Z |
| Cut | Ctrl+X |
| Copy | Ctrl+C |
| Paste | Ctrl+V |
| Delete | Delete / Backspace |
| Select All | Ctrl+A |
| Zoom In | Ctrl++ or Ctrl+Scroll Up |
| Zoom Out | Ctrl+- or Ctrl+Scroll Down |
| Zoom to Fit | Ctrl+0 |
| Pan | Middle-click drag |

## Tool Shortcuts

Select a tool by clicking it in the toolbar, or use the Insert menu.

| Tool | Description |
|---|---|
| Select | Click to select, drag to move, handles to resize/rotate |
| Text | Click or drag to create a text box, double-click to edit |
| Rectangle | Click and drag to draw |
| Ellipse | Click and drag to draw |
| Line | Click and drag to draw |
| Arrow | Click and drag to draw |
| Polygon | Click to add vertices, double-click to close |
| Freehand | Click and drag to draw freehand paths |
| Image | Click to open file picker and place an image |

## File Format

Documents are saved as `.pubd` files — plain JSON with all images base64-embedded, so the file is fully self-contained and portable.

## Packaging for Distribution

You can package Publisher Clone into a standalone desktop app that others can run without installing Python.

### Install PyInstaller

```bash
pip install pyinstaller
```

### Build on macOS

```bash
pyinstaller publisher.spec
```

This creates `dist/PublisherClone.app` — a double-clickable macOS application. Zip it up to share:

```bash
cd dist
zip -r PublisherClone-mac.zip PublisherClone.app
```

### Build on Windows

```bash
pyinstaller publisher.spec
```

This creates `dist/PublisherClone/PublisherClone.exe`. Zip the folder to share:

```
dist\PublisherClone\  →  PublisherClone-win.zip
```

### Build a single-file executable (alternative)

If you prefer one file instead of a folder:

```bash
pyinstaller --onefile --windowed --name PublisherClone main.py
```

This produces a single `dist/PublisherClone` executable (or `PublisherClone.exe` on Windows).

### Notes

- The packaged app includes Python and PyQt6 — recipients do not need anything installed.
- macOS builds only run on macOS, Windows builds only run on Windows. Build on each platform you want to support.
- The resulting app/zip is typically 50-80 MB due to the bundled Qt libraries.

## Project Structure

```
publisher_clone/
├── main.py                      # Entry point
├── requirements.txt             # PyQt6
├── publisher.spec               # PyInstaller build config
├── resources/icons/             # (placeholder for custom icons)
└── app/
    ├── models/
    │   ├── enums.py             # ToolType, UnitType, PageSizePreset
    │   ├── document.py          # Document, Page classes
    │   ├── items.py             # ItemData dataclasses
    │   └── serialization.py     # JSON save/load (.pubd format)
    ├── canvas/
    │   ├── canvas_scene.py      # QGraphicsScene subclass (one per page)
    │   ├── canvas_view.py       # QGraphicsView with zoom/pan
    │   ├── canvas_items.py      # QGraphicsItem subclasses
    │   └── selection_handles.py # Resize/rotate handles
    ├── tools/
    │   ├── base_tool.py         # Abstract tool interface
    │   ├── tool_manager.py      # Active tool routing
    │   ├── select_tool.py       # Select/move/resize/rotate
    │   ├── text_tool.py         # Text box creation/editing
    │   ├── shape_tool.py        # Rect/ellipse/line/arrow/polygon
    │   ├── freehand_tool.py     # Freehand drawing
    │   └── image_tool.py        # Image placement
    ├── ui/
    │   ├── main_window.py       # QMainWindow orchestrator
    │   ├── toolbar.py           # Tool selection toolbar
    │   ├── menu_bar.py          # File/Edit/View/Insert/Format/Help
    │   ├── properties_panel.py  # Transform, color, font controls
    │   ├── layers_panel.py      # Z-order, visibility, lock
    │   ├── pages_panel.py       # Page thumbnails
    │   ├── rulers.py            # Horizontal/vertical rulers
    │   ├── color_button.py      # Color picker button
    │   └── status_bar.py        # Cursor pos, zoom %, page info
    ├── export/
    │   ├── pdf_exporter.py      # Multi-page PDF via QPdfWriter
    │   ├── image_exporter.py    # PNG/JPEG at configurable DPI
    │   └── svg_exporter.py      # SVG via QSvgGenerator
    └── commands/
        ├── command_stack.py     # QUndoStack wrapper
        ├── item_commands.py     # Add/Remove/Move/Resize/Rotate
        ├── property_commands.py # Color, font, z-order changes
        └── page_commands.py     # Add/Remove pages
```
