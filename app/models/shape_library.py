"""Disk I/O for the custom shape library (~/.publisher_clone/library/)."""

import json
import os
import re
from pathlib import Path


class ShapeLibrary:
    """Manages saved custom shapes on disk."""

    def __init__(self):
        self._base = Path.home() / ".publisher_clone" / "library"

    def base_path(self) -> Path:
        return self._base

    def _sanitize(self, name: str) -> str:
        """Remove characters that are unsafe for filenames."""
        return re.sub(r'[\\/:*?"<>|]', '_', name).strip()

    def save_shape(self, folder: str, name: str, items_dicts: list):
        """Write a shape JSON file. Creates folder if needed."""
        folder = folder.strip()
        safe_name = self._sanitize(name)
        if not safe_name:
            raise ValueError("Shape name is empty")

        if folder:
            dir_path = self._base / self._sanitize(folder)
        else:
            dir_path = self._base
        dir_path.mkdir(parents=True, exist_ok=True)

        data = {"name": name, "version": 1, "items": items_dicts}
        file_path = dir_path / f"{safe_name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_shape(self, folder: str, name: str) -> list:
        """Load a shape and return the list of item dicts."""
        folder = folder.strip()
        safe_name = self._sanitize(name)
        if folder:
            file_path = self._base / self._sanitize(folder) / f"{safe_name}.json"
        else:
            file_path = self._base / f"{safe_name}.json"

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("items", [])

    def get_all_shapes(self) -> dict[str, list[str]]:
        """Return {folder: [shape_names]} for menu building.

        Root-level shapes use '' as the folder key.
        """
        result: dict[str, list[str]] = {}
        if not self._base.exists():
            return result

        # Root-level .json files
        root_shapes = sorted(
            p.stem for p in self._base.glob("*.json") if p.is_file()
        )
        if root_shapes:
            result[''] = root_shapes

        # Subdirectories (one level deep)
        for d in sorted(self._base.iterdir()):
            if d.is_dir():
                shapes = sorted(p.stem for p in d.glob("*.json") if p.is_file())
                if shapes:
                    result[d.name] = shapes

        return result

    def delete_shape(self, folder: str, name: str):
        """Delete a shape file."""
        folder = folder.strip()
        safe_name = self._sanitize(name)
        if folder:
            file_path = self._base / self._sanitize(folder) / f"{safe_name}.json"
        else:
            file_path = self._base / f"{safe_name}.json"
        if file_path.exists():
            file_path.unlink()

    def list_folders(self) -> list[str]:
        """Return sorted list of existing folder names."""
        if not self._base.exists():
            return []
        return sorted(d.name for d in self._base.iterdir() if d.is_dir())

    def shape_exists(self, folder: str, name: str) -> bool:
        """Check if a shape file already exists."""
        folder = folder.strip()
        safe_name = self._sanitize(name)
        if folder:
            file_path = self._base / self._sanitize(folder) / f"{safe_name}.json"
        else:
            file_path = self._base / f"{safe_name}.json"
        return file_path.exists()
