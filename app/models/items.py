"""Data classes for all item types. These hold serializable state separate from Qt items."""

from dataclasses import dataclass, field
from typing import Optional
import uuid

from app.models.enums import ItemType


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class ItemData:
    """Base data for all items."""
    id: str = field(default_factory=_new_id)
    item_type: ItemType = ItemType.RECT
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0
    rotation: float = 0.0
    z_value: float = 0.0
    locked: bool = False
    visible: bool = True
    name: str = ""
    flip_h: bool = False
    flip_v: bool = False

    # Fill and stroke
    fill_color: str = "#4A90D9"
    fill_opacity: float = 1.0
    fill_texture: str = ""  # texture ID, empty = solid color fill
    stroke_color: str = "#000000"
    stroke_width: float = 1.0
    stroke_opacity: float = 1.0


@dataclass
class RectItemData(ItemData):
    item_type: ItemType = ItemType.RECT
    corner_radius: float = 0.0


@dataclass
class EllipseItemData(ItemData):
    item_type: ItemType = ItemType.ELLIPSE


@dataclass
class LineItemData(ItemData):
    item_type: ItemType = ItemType.LINE
    x2: float = 100.0
    y2: float = 100.0
    fill_color: str = "transparent"


@dataclass
class ArrowItemData(ItemData):
    item_type: ItemType = ItemType.ARROW
    x2: float = 100.0
    y2: float = 100.0
    arrow_size: float = 12.0
    fill_color: str = "transparent"


@dataclass
class PolygonItemData(ItemData):
    item_type: ItemType = ItemType.POLYGON
    points: list[tuple[float, float]] = field(default_factory=list)


@dataclass
class TextItemData(ItemData):
    item_type: ItemType = ItemType.TEXT
    text: str = "Text"
    font_family: str = "Arial"
    font_size: float = 12.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    text_color: str = "#000000"
    alignment: str = "left"
    fill_color: str = "transparent"
    stroke_width: float = 0.0


@dataclass
class ImageItemData(ItemData):
    item_type: ItemType = ItemType.IMAGE
    image_data_b64: str = ""
    source_path: str = ""
    maintain_aspect: bool = True
    fill_color: str = "transparent"
    stroke_width: float = 0.0


@dataclass
class FreehandItemData(ItemData):
    item_type: ItemType = ItemType.FREEHAND
    points: list[tuple[float, float]] = field(default_factory=list)
    fill_color: str = "transparent"
    stroke_width: float = 2.0


@dataclass
class GroupItemData(ItemData):
    item_type: ItemType = ItemType.GROUP
    child_ids: list[str] = field(default_factory=list)
    fill_color: str = "transparent"
    fill_opacity: float = 0.0
    stroke_color: str = "transparent"
    stroke_width: float = 0.0
