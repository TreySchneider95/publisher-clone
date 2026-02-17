"""JSON save/load for .pubd format."""

import json
from dataclasses import asdict
from typing import Optional

from app.models.document import Document, Page
from app.models.enums import UnitType, ItemType
from app.models.items import (
    ItemData, RectItemData, EllipseItemData, LineItemData, ArrowItemData,
    PolygonItemData, TextItemData, ImageItemData, FreehandItemData,
    GroupItemData
)

FORMAT_VERSION = 1

_TYPE_MAP = {
    ItemType.RECT: RectItemData,
    ItemType.ELLIPSE: EllipseItemData,
    ItemType.LINE: LineItemData,
    ItemType.ARROW: ArrowItemData,
    ItemType.POLYGON: PolygonItemData,
    ItemType.TEXT: TextItemData,
    ItemType.IMAGE: ImageItemData,
    ItemType.FREEHAND: FreehandItemData,
    ItemType.GROUP: GroupItemData,
}


def serialize_document(document: Document, scenes: list) -> dict:
    """Convert document + scenes to a JSON-serializable dict."""
    from app.canvas.canvas_items import PublisherItemMixin

    pages = []
    for i, page in enumerate(document.pages):
        scene = scenes[i] if i < len(scenes) else None
        items_data = []
        if scene:
            for item in scene.get_publisher_items():
                item.sync_to_data()
                d = item_data_to_dict(item.item_data)
                items_data.append(d)

        pages.append({
            "width_pt": page.width_pt,
            "height_pt": page.height_pt,
            "name": page.name,
            "items": items_data,
        })

    return {
        "format_version": FORMAT_VERSION,
        "unit": document.unit.value,
        "pages": pages,
    }


def item_data_to_dict(data: ItemData) -> dict:
    """Convert an ItemData to a plain dict."""
    d = asdict(data)
    # Convert enum to string
    d["item_type"] = data.item_type.name
    return d


def deserialize_document(data: dict) -> tuple[Document, list[list]]:
    """Parse a .pubd JSON dict into a Document and per-page item data lists.

    Returns (document, pages_items) where pages_items[i] is a list of ItemData
    for page i.
    """
    version = data.get("format_version", 1)
    unit_str = data.get("unit", "in")
    unit = UnitType(unit_str)

    doc = Document(pages=[], unit=unit, format_version=version)
    pages_items = []

    for page_data in data.get("pages", []):
        page = Page(
            width_pt=page_data["width_pt"],
            height_pt=page_data["height_pt"],
            name=page_data.get("name", "Page"),
        )
        doc.pages.append(page)

        items = []
        for item_dict in page_data.get("items", []):
            item_data = dict_to_item_data(item_dict)
            if item_data:
                items.append(item_data)
        pages_items.append(items)

    if not doc.pages:
        doc.pages.append(Page())
        pages_items.append([])

    return doc, pages_items


def dict_to_item_data(d: dict) -> Optional[ItemData]:
    """Convert a plain dict back to the appropriate ItemData subclass."""
    type_name = d.get("item_type", "RECT")
    try:
        item_type = ItemType[type_name]
    except KeyError:
        return None

    cls = _TYPE_MAP.get(item_type)
    if not cls:
        return None

    # Remove item_type from dict since we pass it through the class default
    d_copy = dict(d)
    d_copy.pop("item_type", None)

    # Convert points lists of lists back to lists of tuples
    if "points" in d_copy and isinstance(d_copy["points"], list):
        d_copy["points"] = [tuple(p) for p in d_copy["points"]]

    # Filter only valid fields for the dataclass
    import dataclasses
    valid_fields = {f.name for f in dataclasses.fields(cls)}
    filtered = {k: v for k, v in d_copy.items() if k in valid_fields}

    return cls(**filtered)


def save_to_file(file_path: str, document: Document, scenes: list):
    """Save document to a .pubd file."""
    data = serialize_document(document, scenes)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_from_file(file_path: str) -> tuple[Document, list[list]]:
    """Load a document from a .pubd file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return deserialize_document(data)
