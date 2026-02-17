"""Document and Page data models."""

from dataclasses import dataclass, field
from typing import Optional
from app.models.enums import PageSizePreset, UnitType


@dataclass
class Page:
    """A single page in the document."""
    width_pt: float = 0
    height_pt: float = 0
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = "Page"

    @property
    def is_infinite(self) -> bool:
        return self.width_pt == 0 or self.height_pt == 0


@dataclass
class Document:
    """Top-level document model."""
    pages: list[Page] = field(default_factory=lambda: [Page()])
    unit: UnitType = UnitType.INCHES
    file_path: Optional[str] = None
    dirty: bool = False
    format_version: int = 1

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def add_page(self, index: int = -1,
                 width_pt: float = 0,
                 height_pt: float = 0) -> Page:
        page = Page(width_pt=width_pt, height_pt=height_pt)
        if index < 0:
            self.pages.append(page)
        else:
            self.pages.insert(index, page)
        self.dirty = True
        return page

    def remove_page(self, index: int) -> Optional[Page]:
        if self.page_count <= 1:
            return None
        self.dirty = True
        return self.pages.pop(index)

    def mark_dirty(self):
        self.dirty = True

    def mark_clean(self):
        self.dirty = False
