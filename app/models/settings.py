"""Application settings with persistence to ~/.publisher_clone/settings.json."""

import json
from dataclasses import dataclass, field, fields, asdict
from pathlib import Path


def _filter_fields(cls, data: dict) -> dict:
    """Keep only keys that match dataclass field names."""
    valid = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in valid}


@dataclass
class GuideSettings:
    """Which alignment guides to show."""
    center: bool = True
    edges: bool = True
    thirds: bool = False
    quarters: bool = False


@dataclass
class SnapSettings:
    """Snap behavior during drag."""
    snap_distance: int = 8  # pixels; 0 = off
    guides: GuideSettings = field(default_factory=GuideSettings)


@dataclass
class DefaultColorSettings:
    """Default colors for new shapes."""
    fill_color: str = "#4A90D9"
    stroke_color: str = "#000000"
    stroke_width: float = 1.0


@dataclass
class AppSettings:
    """Top-level application settings."""
    snap: SnapSettings = field(default_factory=SnapSettings)
    defaults: DefaultColorSettings = field(default_factory=DefaultColorSettings)

    _path: Path = field(default_factory=lambda: Path.home() / ".publisher_clone" / "settings.json",
                        repr=False, compare=False)

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        data.pop('_path', None)
        self._path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls) -> 'AppSettings':
        path = Path.home() / ".publisher_clone" / "settings.json"
        try:
            raw = json.loads(path.read_text())
            guides = GuideSettings(**_filter_fields(GuideSettings, raw.get('snap', {}).get('guides', {})))
            snap_raw = raw.get('snap', {})
            snap = SnapSettings(
                snap_distance=snap_raw.get('snap_distance', 8),
                guides=guides,
            )
            defaults = DefaultColorSettings(**_filter_fields(DefaultColorSettings, raw.get('defaults', {})))
            return cls(snap=snap, defaults=defaults)
        except Exception:
            return cls()


_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Module-level singleton accessor."""
    global _settings
    if _settings is None:
        _settings = AppSettings.load()
    return _settings
