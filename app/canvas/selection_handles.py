"""Resize and rotate handles for selected items."""

import math
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter, QCursor


class HandleType:
    TOP_LEFT = 0
    TOP_CENTER = 1
    TOP_RIGHT = 2
    MIDDLE_LEFT = 3
    MIDDLE_RIGHT = 4
    BOTTOM_LEFT = 5
    BOTTOM_CENTER = 6
    BOTTOM_RIGHT = 7
    ROTATE = 8


_CURSORS = {
    HandleType.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
    HandleType.TOP_CENTER: Qt.CursorShape.SizeVerCursor,
    HandleType.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
    HandleType.MIDDLE_LEFT: Qt.CursorShape.SizeHorCursor,
    HandleType.MIDDLE_RIGHT: Qt.CursorShape.SizeHorCursor,
    HandleType.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
    HandleType.BOTTOM_CENTER: Qt.CursorShape.SizeVerCursor,
    HandleType.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
    HandleType.ROTATE: Qt.CursorShape.CrossCursor,
}

HANDLE_SIZE = 8


class ResizeHandle(QGraphicsRectItem):
    """A single resize handle."""

    def __init__(self, handle_type: int, parent=None):
        super().__init__(-HANDLE_SIZE / 2, -HANDLE_SIZE / 2,
                         HANDLE_SIZE, HANDLE_SIZE, parent)
        self.handle_type = handle_type
        self.setPen(QPen(QColor(0, 120, 215), 1))
        self.setBrush(QBrush(QColor(255, 255, 255)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(_CURSORS.get(handle_type, Qt.CursorShape.ArrowCursor))
        self.setZValue(1000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRect(self.rect())


class RotateHandle(QGraphicsEllipseItem):
    """Rotation handle displayed above the item."""

    def __init__(self, parent=None):
        size = HANDLE_SIZE + 2
        super().__init__(-size / 2, -size / 2, size, size, parent)
        self.handle_type = HandleType.ROTATE
        self.setPen(QPen(QColor(0, 180, 0), 1))
        self.setBrush(QBrush(QColor(200, 255, 200)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setZValue(1000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)


class SelectionHandleGroup:
    """Manages resize/rotate handles around a selected item."""

    def __init__(self, scene):
        self.scene = scene
        self._handles: list[ResizeHandle | RotateHandle] = []
        self._target: QGraphicsItem | None = None

    def attach(self, item: QGraphicsItem):
        self.detach()
        self._target = item

        # Create 8 resize handles + 1 rotate
        for ht in range(8):
            h = ResizeHandle(ht)
            self.scene.addItem(h)
            self._handles.append(h)

        rh = RotateHandle()
        self.scene.addItem(rh)
        self._handles.append(rh)

        self.update_positions()

    def detach(self):
        for h in self._handles:
            if h.scene():
                self.scene.removeItem(h)
        self._handles.clear()
        self._target = None

    def update_positions(self):
        if not self._target:
            return

        rect = self._target.boundingRect()
        pos = self._target.pos()

        corners = [
            rect.topLeft(),       # TOP_LEFT
            QPointF(rect.center().x(), rect.top()),  # TOP_CENTER
            rect.topRight(),      # TOP_RIGHT
            QPointF(rect.left(), rect.center().y()),  # MIDDLE_LEFT
            QPointF(rect.right(), rect.center().y()), # MIDDLE_RIGHT
            rect.bottomLeft(),    # BOTTOM_LEFT
            QPointF(rect.center().x(), rect.bottom()), # BOTTOM_CENTER
            rect.bottomRight(),   # BOTTOM_RIGHT
        ]

        transform = self._target.sceneTransform()
        for i, h in enumerate(self._handles[:8]):
            scene_pt = transform.map(corners[i])
            h.setPos(scene_pt)

        # Rotate handle above top center
        top_center = transform.map(QPointF(rect.center().x(), rect.top()))
        rotate_offset = QPointF(0, -25)
        if len(self._handles) > 8:
            self._handles[8].setPos(top_center + rotate_offset)

    @property
    def handles(self):
        return self._handles

    @property
    def target(self):
        return self._target

    def handle_at(self, scene_pos: QPointF) -> int | None:
        """Return handle type at the given scene position, or None."""
        for h in self._handles:
            if h.contains(h.mapFromScene(scene_pos)):
                return h.handle_type
        return None


VERTEX_HANDLE_SIZE = 8


class VertexHandle(QGraphicsEllipseItem):
    """A draggable dot at a polygon vertex."""

    def __init__(self, vertex_index: int, parent=None):
        half = VERTEX_HANDLE_SIZE / 2
        super().__init__(-half, -half, VERTEX_HANDLE_SIZE, VERTEX_HANDLE_SIZE, parent)
        self.vertex_index = vertex_index
        self.setPen(QPen(QColor(0, 120, 215), 1))
        self.setBrush(QBrush(QColor(0, 120, 215)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setZValue(1001)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)


class VertexHandleGroup:
    """Manages vertex handles for polygon point editing."""

    def __init__(self, scene):
        self.scene = scene
        self._handles: list[VertexHandle] = []
        self._target = None

    def attach(self, item):
        self.detach()
        self._target = item
        if not hasattr(item, 'item_data') or not hasattr(item.item_data, 'points'):
            return
        for i in range(len(item.item_data.points)):
            h = VertexHandle(i)
            self.scene.addItem(h)
            self._handles.append(h)
        self.update_positions()

    def detach(self):
        for h in self._handles:
            if h.scene():
                self.scene.removeItem(h)
        self._handles.clear()
        self._target = None

    def update_positions(self):
        if not self._target:
            return
        transform = self._target.sceneTransform()
        points = self._target.item_data.points
        for h in self._handles:
            i = h.vertex_index
            if i < len(points):
                px, py = points[i]
                scene_pt = transform.map(QPointF(px, py))
                h.setPos(scene_pt)

    @property
    def target(self):
        return self._target

    def handle_at(self, scene_pos: QPointF) -> int | None:
        """Return vertex index at scene position, or None."""
        for h in self._handles:
            if h.contains(h.mapFromScene(scene_pos)):
                return h.vertex_index
        return None
