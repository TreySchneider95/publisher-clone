"""Registry for loading and caching bundled texture images."""

import os
import sys

from PyQt6.QtGui import QPixmap

_texture_cache: dict[str, QPixmap] = {}


def get_texture_dir() -> str:
    """Return path to the bundled textures directory."""
    if getattr(sys, "frozen", False):
        # PyInstaller bundle
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "resources", "textures")


def _name_from_filename(filename: str) -> str:
    """Derive a display name from a texture filename.

    Example: 'Wood049.jpg' -> 'Wood 049', 'Concrete034.jpg' -> 'Concrete 034'
    """
    stem = os.path.splitext(filename)[0]
    # Insert space before digit runs
    parts = []
    i = 0
    while i < len(stem):
        if stem[i].isdigit():
            # Collect all digits
            j = i
            while j < len(stem) and stem[j].isdigit():
                j += 1
            parts.append(stem[i:j])
            i = j
        else:
            j = i
            while j < len(stem) and not stem[j].isdigit():
                j += 1
            parts.append(stem[i:j])
            i = j
    return " ".join(parts)


def list_textures() -> list[dict]:
    """Scan the textures directory and return metadata for each texture.

    Returns a list of dicts: [{"id": "Wood049", "name": "Wood 049", "path": "/..."}, ...]
    """
    texture_dir = get_texture_dir()
    if not os.path.isdir(texture_dir):
        return []
    textures = []
    for filename in sorted(os.listdir(texture_dir)):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            texture_id = os.path.splitext(filename)[0]
            textures.append({
                "id": texture_id,
                "name": _name_from_filename(filename),
                "path": os.path.join(texture_dir, filename),
            })
    return textures


def load_texture(texture_id: str) -> QPixmap | None:
    """Load and cache a texture pixmap by its ID. Returns None if not found."""
    if texture_id in _texture_cache:
        return _texture_cache[texture_id]

    texture_dir = get_texture_dir()
    # Try common extensions
    for ext in (".jpg", ".jpeg", ".png"):
        path = os.path.join(texture_dir, texture_id + ext)
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                _texture_cache[texture_id] = pixmap
                return pixmap
    return None
