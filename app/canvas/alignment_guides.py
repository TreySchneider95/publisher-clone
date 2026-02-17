"""Alignment guide engine for snap-to-object during drag."""

from dataclasses import dataclass
from PyQt6.QtWidgets import QGraphicsLineItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QColor

from app.models.settings import get_settings


@dataclass
class GuideLine:
    """A single alignment guide (horizontal or vertical)."""
    is_horizontal: bool  # True = horizontal line (constant y), False = vertical (constant x)
    value: float         # the y (horizontal) or x (vertical) coordinate
    source_rect: QRectF  # bounding rect of the item that generated this guide


class AlignmentGuideEngine:
    """Computes snap offsets and renders temporary guide lines."""

    def __init__(self):
        self._scene = None
        self._guides: list[GuideLine] = []
        self._visual_items: list[QGraphicsLineItem] = []
        self._dragged_ids: set[str] = set()

    def begin_drag(self, scene, dragged_items: list):
        """Pre-compute guide lines from all non-dragged items."""
        self._scene = scene
        self._guides.clear()
        self._clear_visuals()

        cfg = get_settings().snap
        if cfg.snap_distance <= 0:
            return

        # Collect IDs of dragged items (including group children)
        self._dragged_ids = set()
        for item in dragged_items:
            if hasattr(item, 'item_data'):
                self._dragged_ids.add(item.item_data.id)

        # Generate guides from all non-dragged publisher items
        for item in scene.get_publisher_items():
            if not hasattr(item, 'item_data'):
                continue
            if item.item_data.id in self._dragged_ids:
                continue
            rect = item.sceneBoundingRect()
            self._add_guides_for_rect(rect, cfg.guides)

    def _add_guides_for_rect(self, rect: QRectF, cfg):
        """Generate guide lines from one item's bounding rect."""
        left = rect.left()
        right = rect.right()
        top = rect.top()
        bottom = rect.bottom()
        cx = rect.center().x()
        cy = rect.center().y()
        w = rect.width()
        h = rect.height()

        if cfg.edges:
            # Vertical guides at left/right edges
            self._guides.append(GuideLine(False, left, rect))
            self._guides.append(GuideLine(False, right, rect))
            # Horizontal guides at top/bottom edges
            self._guides.append(GuideLine(True, top, rect))
            self._guides.append(GuideLine(True, bottom, rect))

        if cfg.center:
            self._guides.append(GuideLine(False, cx, rect))
            self._guides.append(GuideLine(True, cy, rect))

        if cfg.thirds:
            self._guides.append(GuideLine(False, left + w / 3, rect))
            self._guides.append(GuideLine(False, left + 2 * w / 3, rect))
            self._guides.append(GuideLine(True, top + h / 3, rect))
            self._guides.append(GuideLine(True, top + 2 * h / 3, rect))

        if cfg.quarters:
            self._guides.append(GuideLine(False, left + w / 4, rect))
            self._guides.append(GuideLine(False, left + 3 * w / 4, rect))
            self._guides.append(GuideLine(True, top + h / 4, rect))
            self._guides.append(GuideLine(True, top + 3 * h / 4, rect))

    def compute_snap(self, dragged_rect: QRectF, snap_distance: float):
        """Find best snap offset and active guides.

        Returns (dx, dy, active_guides) where dx/dy are the snap correction
        to apply, and active_guides is the list of guides that matched.
        """
        if not self._guides or snap_distance <= 0:
            return 0.0, 0.0, []

        cfg = get_settings().snap.guides

        # Points on the dragged rect to check
        d_left = dragged_rect.left()
        d_right = dragged_rect.right()
        d_top = dragged_rect.top()
        d_bottom = dragged_rect.bottom()
        d_cx = dragged_rect.center().x()
        d_cy = dragged_rect.center().y()
        d_w = dragged_rect.width()
        d_h = dragged_rect.height()

        # Build list of dragged-rect reference values per axis
        x_refs = []
        y_refs = []
        if cfg.edges:
            x_refs.extend([d_left, d_right])
            y_refs.extend([d_top, d_bottom])
        if cfg.center:
            x_refs.append(d_cx)
            y_refs.append(d_cy)
        if cfg.thirds:
            x_refs.extend([d_left + d_w / 3, d_left + 2 * d_w / 3])
            y_refs.extend([d_top + d_h / 3, d_top + 2 * d_h / 3])
        if cfg.quarters:
            x_refs.extend([d_left + d_w / 4, d_left + 3 * d_w / 4])
            y_refs.extend([d_top + d_h / 4, d_top + 3 * d_h / 4])

        # If nothing enabled, fall back to edges + center
        if not x_refs:
            x_refs = [d_left, d_right, d_cx]
            y_refs = [d_top, d_bottom, d_cy]

        best_dx = None
        best_dist_x = snap_distance + 1
        best_dy = None
        best_dist_y = snap_distance + 1

        active_x_guides = []
        active_y_guides = []

        for guide in self._guides:
            if guide.is_horizontal:
                # Compare guide.value against each y reference
                for ref in y_refs:
                    dist = abs(ref - guide.value)
                    if dist <= snap_distance:
                        if dist < best_dist_y:
                            best_dist_y = dist
                            best_dy = guide.value - ref
                            active_y_guides = [guide]
                        elif dist == best_dist_y:
                            active_y_guides.append(guide)
            else:
                # Compare guide.value against each x reference
                for ref in x_refs:
                    dist = abs(ref - guide.value)
                    if dist <= snap_distance:
                        if dist < best_dist_x:
                            best_dist_x = dist
                            best_dx = guide.value - ref
                            active_x_guides = [guide]
                        elif dist == best_dist_x:
                            active_x_guides.append(guide)

        dx = best_dx if best_dx is not None else 0.0
        dy = best_dy if best_dy is not None else 0.0
        active = active_x_guides + active_y_guides
        return dx, dy, active

    def update_visuals(self, active_guides: list[GuideLine]):
        """Add/remove temporary guide line visuals on the scene."""
        self._clear_visuals()
        if not self._scene or not active_guides:
            return

        pen = QPen(QColor(255, 50, 50, 180), 1, Qt.PenStyle.DashDotLine)
        pen.setCosmetic(True)

        scene_rect = self._scene.sceneRect()
        # Extend guides well beyond visible area
        extent = max(scene_rect.width(), scene_rect.height()) * 2

        for guide in active_guides:
            if guide.is_horizontal:
                line = QGraphicsLineItem(
                    scene_rect.left() - extent, guide.value,
                    scene_rect.right() + extent, guide.value
                )
            else:
                line = QGraphicsLineItem(
                    guide.value, scene_rect.top() - extent,
                    guide.value, scene_rect.bottom() + extent
                )
            line.setPen(pen)
            line.setZValue(9999)
            self._scene.addItem(line)
            self._visual_items.append(line)

    def end_drag(self):
        """Remove all guide visuals and clear state."""
        self._clear_visuals()
        self._guides.clear()
        self._dragged_ids.clear()
        self._scene = None

    def _clear_visuals(self):
        for item in self._visual_items:
            if item.scene():
                item.scene().removeItem(item)
        self._visual_items.clear()
