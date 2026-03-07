# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
source venv/bin/activate
python3 main.py
```

Use `python3` (not `python`). Dependencies: `pip install -r requirements.txt` (PyQt6).

## Packaging

```bash
pyinstaller publisher.spec
```

Produces `dist/PublisherClone.app` on macOS. PyQt6-QSvg is bundled with PyQt6 (no separate install needed but listed as a hidden import in the spec).

## Architecture

**Desktop publishing app** (Microsoft Publisher clone) built with Python 3 + PyQt6. No tests exist in this project.

### Data/View Separation

Every canvas item has two representations:
- **ItemData** (`app/models/items.py`): Plain dataclass holding serializable state (position, colors, points, etc.). Subclassed per item type (RectItemData, TextItemData, etc.).
- **Publisher*Item** (`app/canvas/canvas_items.py`): QGraphicsItem subclass that renders on the canvas. Uses `PublisherItemMixin` which provides `sync_from_data()` (data -> Qt) and `sync_to_data()` (Qt -> data).

The factory `create_item_from_data(data)` maps an ItemData to the correct QGraphicsItem subclass.

### Page Model

One `PublisherScene` (QGraphicsScene) per page. Page switching calls `view.setScene()`. Pages can be infinite (width/height = 0) or defined size. All coordinates are in **points** (72pt = 1 inch). The `MainWindow.scenes` list parallels `Document.pages`.

### Tool System (Strategy Pattern)

`BaseTool` defines the interface (mouse_press/move/release, key_press, etc.). Concrete tools: SelectTool, ShapeTool, TextTool, FreehandTool, ImageTool. `ToolManager` holds the active tool; `PublisherScene` forwards all input events to `tool_manager.active_tool`.

`CanvasInterface` (defined in main_window.py) is the mediator passed to tools — it provides access to scene, view, command stack, and document without tools depending on MainWindow directly.

### Undo/Redo

`QUndoStack` wrapped by `CommandStack`. All mutations go through `QUndoCommand` subclasses in `app/commands/`. Multi-step operations use `beginMacro()`/`endMacro()`. Commands store old/new state and directly update both the QGraphicsItem and its ItemData.

### Serialization

Documents save as `.pubd` files (JSON). `dataclasses.asdict()` serializes ItemData; `dict_to_item_data()` deserializes back. Points (polygon vertices, freehand paths) are stored as lists of `[x, y]` pairs. Images are base64-embedded. Groups track children by ID (`child_ids`); when copying/pasting/duplicating, an `old_to_new` ID map remaps group references.

### Key Conventions

- New item IDs: `uuid.uuid4().hex[:12]` via `_new_id()` in `app/models/items.py`
- Unit conversions in `app/models/enums.py` (points_to_unit, unit_to_points)
- `scene.get_publisher_items()` filters out non-data items (handles, decorations)
- Properties panel updates come from `selectionChanged` -> `_on_selection_changed` with a reentrance guard (`_in_selection_change`)

## Agent Workflow Rules

These rules apply to every Claude agent working in this repository. They are mandatory and must be followed after completing any task.

### 1. Update `app/version.py`

After finishing a task, add a bullet describing what you did to the `RELEASE_NOTES` entry for the current version (the version string assigned to `VERSION`). Keep the description concise — one line, matching the style of existing entries. Do not bump the version number; only add to the notes list.

### 2. Stage and Commit All Changes

After updating `app/version.py`, stage every changed file and commit with a descriptive message summarizing the task. The user manages pushing; do not push.

```bash
git add -A
git commit -m "Short description of what was done"
```

Do not skip this step. Every completed task must end with a commit.
