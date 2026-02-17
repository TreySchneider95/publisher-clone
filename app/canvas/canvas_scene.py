from PyQt6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PyQt6.QtCore import QRectF, Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QKeyEvent


# Default extent for the infinite canvas (points). ~70 inches in each direction.
_CANVAS_EXTENT = 5000


class PublisherScene(QGraphicsScene):
    """A scene representing a single page/canvas. Dimensions are in points."""

    # Emitted when items change so panels can update
    item_selection_changed = pyqtSignal()

    def __init__(self, width_pt: float = 0, height_pt: float = 0, parent=None):
        super().__init__(parent)
        self.page_width = width_pt
        self.page_height = height_pt
        self._tool_manager = None
        self._show_grid = False
        self._grid_spacing = 18  # 0.25 inch in points

        self._update_scene_rect()

        self.selectionChanged.connect(self._on_selection_changed)

    def _update_scene_rect(self):
        """Set scene rect based on page size — bounded for defined pages, large for infinite."""
        if self._is_defined_size():
            margin = 36  # half-inch margin around page
            self.setSceneRect(-margin, -margin,
                              self.page_width + margin * 2,
                              self.page_height + margin * 2)
        else:
            self.setSceneRect(-_CANVAS_EXTENT, -_CANVAS_EXTENT,
                              _CANVAS_EXTENT * 2, _CANVAS_EXTENT * 2)

    def set_tool_manager(self, tm):
        self._tool_manager = tm

    def _on_selection_changed(self):
        self.item_selection_changed.emit()

    def _is_defined_size(self) -> bool:
        return self.page_width > 0 and self.page_height > 0

    def drawBackground(self, painter, rect):
        """Draw canvas background: page boundary for defined sizes, infinite otherwise."""
        super().drawBackground(painter, rect)

        if self._is_defined_size():
            self._draw_defined_background(painter, rect)
        else:
            self._draw_infinite_background(painter, rect)

    def _draw_defined_background(self, painter, rect):
        """Draw gray workspace with white page rectangle and drop shadow."""
        page_rect = QRectF(0, 0, self.page_width, self.page_height)

        # Gray workspace
        painter.fillRect(rect, QColor(224, 224, 224))

        # Drop shadow behind page
        shadow_offset = 4
        shadow_rect = page_rect.translated(shadow_offset, shadow_offset)
        painter.fillRect(shadow_rect, QColor(160, 160, 160))

        # White page
        painter.fillRect(page_rect, QColor(255, 255, 255))

        # Page border
        painter.setPen(QPen(QColor(180, 180, 180), 0.5))
        painter.drawRect(page_rect)

        # Grid overlay clipped to page
        if self._show_grid:
            painter.save()
            painter.setClipRect(page_rect)
            self._draw_grid(painter, page_rect)
            painter.restore()

    def _draw_infinite_background(self, painter, rect):
        """Draw white infinite canvas with origin crosshair."""
        painter.fillRect(rect, QColor(255, 255, 255))

        # Grid overlay
        if self._show_grid:
            self._draw_grid(painter, rect)

        # Origin crosshair
        painter.setPen(QPen(QColor(200, 200, 200), 0.5, Qt.PenStyle.DotLine))
        if rect.left() <= 0 <= rect.right():
            painter.drawLine(0, int(rect.top()), 0, int(rect.bottom()))
        if rect.top() <= 0 <= rect.bottom():
            painter.drawLine(int(rect.left()), 0, int(rect.right()), 0)

    def _draw_grid(self, painter, rect):
        """Draw grid lines within the given rect."""
        painter.setPen(QPen(QColor(220, 220, 220), 0.5))
        spacing = self._grid_spacing

        left = int(rect.left() / spacing) * spacing
        top = int(rect.top() / spacing) * spacing

        x = left
        while x <= rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += spacing
        y = top
        while y <= rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += spacing

    def set_grid_visible(self, visible: bool):
        self._show_grid = visible
        self.update()

    def set_grid_spacing(self, spacing: float):
        self._grid_spacing = spacing
        self.update()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self._tool_manager and self._tool_manager.active_tool:
            self._tool_manager.active_tool.mouse_press(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self._tool_manager and self._tool_manager.active_tool:
            self._tool_manager.active_tool.mouse_move(event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._tool_manager and self._tool_manager.active_tool:
            self._tool_manager.active_tool.mouse_release(event)
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        if self._tool_manager and self._tool_manager.active_tool:
            self._tool_manager.active_tool.mouse_double_click(event)
        else:
            super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if self._tool_manager and self._tool_manager.active_tool:
            self._tool_manager.active_tool.key_press(event)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if self._tool_manager and self._tool_manager.active_tool:
            self._tool_manager.active_tool.key_release(event)
        else:
            super().keyReleaseEvent(event)

    def contextMenuEvent(self, event):
        if self._tool_manager and self._tool_manager.active_tool:
            self._tool_manager.active_tool.context_menu(event)
        else:
            super().contextMenuEvent(event)

    @property
    def snap_to_grid(self) -> bool:
        return self._snap_to_grid if hasattr(self, '_snap_to_grid') else False

    @snap_to_grid.setter
    def snap_to_grid(self, value: bool):
        self._snap_to_grid = value

    def snap_point(self, pos) -> QPointF:
        """Snap a point to the grid if snap is enabled."""
        if not self.snap_to_grid:
            return pos
        spacing = self._grid_spacing
        x = round(pos.x() / spacing) * spacing
        y = round(pos.y() / spacing) * spacing
        return QPointF(x, y)

    def get_publisher_items(self):
        """Return only publisher items (not handles etc)."""
        from app.canvas.canvas_items import PublisherItemMixin
        return [item for item in self.items()
                if isinstance(item, PublisherItemMixin)]

    def get_content_rect(self, padding: float = 36) -> QRectF:
        """Return the bounding rect of all content items with padding.

        For defined-size pages, returns the page rect (with padding).
        For infinite pages, returns the union of item bounds.
        """
        if self._is_defined_size():
            r = QRectF(0, 0, self.page_width, self.page_height)
            r.adjust(-padding, -padding, padding, padding)
            return r

        items = self.get_publisher_items()
        if not items:
            # Empty canvas: return a reasonable default area
            return QRectF(-306, -396, 612, 792)  # Letter size centered at origin

        # Union of all item bounding rects in scene coords
        rect = items[0].sceneBoundingRect()
        for item in items[1:]:
            rect = rect.united(item.sceneBoundingRect())

        # Add padding
        rect.adjust(-padding, -padding, padding, padding)
        return rect

    def align_items(self, alignment: str):
        """Align selected items. alignment: left, right, top, bottom, center_h, center_v."""
        items = [i for i in self.selectedItems() if hasattr(i, 'item_data')]
        if len(items) < 2:
            return

        rects = [(item, item.sceneBoundingRect()) for item in items]

        if alignment == 'left':
            target = min(r.left() for _, r in rects)
            for item, r in rects:
                item.setPos(target, item.pos().y())
        elif alignment == 'right':
            target = max(r.right() for _, r in rects)
            for item, r in rects:
                item.setPos(target - r.width(), item.pos().y())
        elif alignment == 'top':
            target = min(r.top() for _, r in rects)
            for item, r in rects:
                item.setPos(item.pos().x(), target)
        elif alignment == 'bottom':
            target = max(r.bottom() for _, r in rects)
            for item, r in rects:
                item.setPos(item.pos().x(), target - r.height())
        elif alignment == 'center_h':
            centers = [r.center().x() for _, r in rects]
            target = sum(centers) / len(centers)
            for item, r in rects:
                item.setPos(target - r.width() / 2, item.pos().y())
        elif alignment == 'center_v':
            centers = [r.center().y() for _, r in rects]
            target = sum(centers) / len(centers)
            for item, r in rects:
                item.setPos(item.pos().x(), target - r.height() / 2)

        # Sync data
        for item, _ in rects:
            if hasattr(item, 'sync_to_data'):
                item.sync_to_data()
