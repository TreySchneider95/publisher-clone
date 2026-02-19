"""Shape tool - rect/ellipse/line/arrow via click-drag, polygon via click-click."""

import math

from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush

from app.tools.base_tool import BaseTool
from app.models.enums import ToolType
from app.models.items import (
    RectItemData, EllipseItemData, LineItemData, ArrowItemData, PolygonItemData
)
from app.canvas.canvas_items import (
    PublisherRectItem, PublisherEllipseItem, PublisherLineItem,
    PublisherArrowItem, PublisherPolygonItem
)
from app.commands.item_commands import AddItemCommand
from app.models.settings import get_settings


class ShapeTool(BaseTool):
    """Creates shapes via click-drag (rect/ellipse/line/arrow) or click-click (polygon)."""

    def __init__(self, canvas, shape_type: ToolType):
        super().__init__(canvas)
        self.shape_type = shape_type
        self._start_pos = QPointF()
        self._preview_item = None
        self._drawing = False
        # Polygon state
        self._polygon_points: list[QPointF] = []
        self._polygon_preview = None

    def activate(self):
        self._drawing = False
        self._polygon_points.clear()
        self._remove_preview()

    def deactivate(self):
        self._remove_preview()
        self._polygon_points.clear()

    def mouse_press(self, event):
        if self.shape_type == ToolType.POLYGON:
            self._polygon_click(event)
            return

        scene = self.canvas.get_scene()
        if not scene:
            return

        self._start_pos = event.scenePos()
        self._drawing = True

        # Create preview item
        self._remove_preview()
        pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)

        if self.shape_type in (ToolType.RECT,):
            self._preview_item = QGraphicsRectItem(0, 0, 0, 0)
            self._preview_item.setPen(pen)
            self._preview_item.setBrush(QBrush(QColor(74, 144, 217, 40)))
        elif self.shape_type == ToolType.ELLIPSE:
            self._preview_item = QGraphicsEllipseItem(0, 0, 0, 0)
            self._preview_item.setPen(pen)
            self._preview_item.setBrush(QBrush(QColor(74, 144, 217, 40)))
        elif self.shape_type in (ToolType.LINE, ToolType.ARROW):
            self._preview_item = QGraphicsLineItem(0, 0, 0, 0)
            self._preview_item.setPen(pen)

        if self._preview_item:
            self._preview_item.setZValue(1e9)
            scene.addItem(self._preview_item)

    def mouse_move(self, event):
        if not self._drawing or not self._preview_item:
            return

        pos = event.scenePos()
        if self.shape_type in (ToolType.RECT, ToolType.ELLIPSE):
            rect = self._make_rect(self._start_pos, pos)
            self._preview_item.setRect(rect)
        elif self.shape_type in (ToolType.LINE, ToolType.ARROW):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                pos = self._snap_angle(self._start_pos, pos)
            self._preview_item.setLine(
                self._start_pos.x(), self._start_pos.y(),
                pos.x(), pos.y()
            )

    def mouse_release(self, event):
        if self.shape_type == ToolType.POLYGON:
            return

        if not self._drawing:
            return
        self._drawing = False
        self._remove_preview()

        pos = event.scenePos()
        scene = self.canvas.get_scene()
        if not scene:
            return

        if self.shape_type in (ToolType.LINE, ToolType.ARROW):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                pos = self._snap_angle(self._start_pos, pos)

        if self.shape_type == ToolType.RECT:
            self._create_rect(self._start_pos, pos, scene)
        elif self.shape_type == ToolType.ELLIPSE:
            self._create_ellipse(self._start_pos, pos, scene)
        elif self.shape_type == ToolType.LINE:
            self._create_line(self._start_pos, pos, scene)
        elif self.shape_type == ToolType.ARROW:
            self._create_arrow(self._start_pos, pos, scene)

        self.canvas.switch_to_select()

    def mouse_double_click(self, event):
        if self.shape_type == ToolType.POLYGON:
            self._finish_polygon()

    def _polygon_click(self, event):
        pos = event.scenePos()
        self._polygon_points.append(pos)

        # Update preview
        scene = self.canvas.get_scene()
        if not scene:
            return

        if self._polygon_preview and self._polygon_preview.scene():
            scene.removeItem(self._polygon_preview)

        if len(self._polygon_points) >= 2:
            from PyQt6.QtGui import QPolygonF
            from PyQt6.QtWidgets import QGraphicsPolygonItem
            polygon = QPolygonF(self._polygon_points)
            self._polygon_preview = QGraphicsPolygonItem(polygon)
            self._polygon_preview.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine))
            self._polygon_preview.setBrush(QBrush(QColor(74, 144, 217, 40)))
            self._polygon_preview.setZValue(1e9)
            scene.addItem(self._polygon_preview)

    def _finish_polygon(self):
        scene = self.canvas.get_scene()
        if not scene or len(self._polygon_points) < 3:
            self._polygon_points.clear()
            self._remove_polygon_preview()
            return

        self._remove_polygon_preview()

        # Normalize points relative to bounding box origin
        xs = [p.x() for p in self._polygon_points]
        ys = [p.y() for p in self._polygon_points]
        min_x, min_y = min(xs), min(ys)
        max_x, max_y = max(xs), max(ys)

        local_points = [(p.x() - min_x, p.y() - min_y) for p in self._polygon_points]

        defs = get_settings().defaults
        data = PolygonItemData(
            x=min_x, y=min_y,
            width=max_x - min_x, height=max_y - min_y,
            points=local_points,
            fill_color=defs.fill_color,
            stroke_color=defs.stroke_color,
            stroke_width=defs.stroke_width,
        )
        item = PublisherPolygonItem(data)
        cmd = AddItemCommand(scene, item, "Add Polygon")
        self.canvas.push_command(cmd)

        self._polygon_points.clear()
        self.canvas.switch_to_select()

    def _remove_polygon_preview(self):
        if self._polygon_preview and self._polygon_preview.scene():
            self._polygon_preview.scene().removeItem(self._polygon_preview)
        self._polygon_preview = None

    def _create_rect(self, start: QPointF, end: QPointF, scene):
        rect = self._make_rect(start, end)
        if rect.width() < 5 and rect.height() < 5:
            return
        defs = get_settings().defaults
        data = RectItemData(
            x=rect.x(), y=rect.y(),
            width=rect.width(), height=rect.height(),
            fill_color=defs.fill_color,
            stroke_color=defs.stroke_color,
            stroke_width=defs.stroke_width,
        )
        item = PublisherRectItem(data)
        cmd = AddItemCommand(scene, item, "Add Rectangle")
        self.canvas.push_command(cmd)

    def _create_ellipse(self, start: QPointF, end: QPointF, scene):
        rect = self._make_rect(start, end)
        if rect.width() < 5 and rect.height() < 5:
            return
        defs = get_settings().defaults
        data = EllipseItemData(
            x=rect.x(), y=rect.y(),
            width=rect.width(), height=rect.height(),
            fill_color=defs.fill_color,
            stroke_color=defs.stroke_color,
            stroke_width=defs.stroke_width,
        )
        item = PublisherEllipseItem(data)
        cmd = AddItemCommand(scene, item, "Add Ellipse")
        self.canvas.push_command(cmd)

    def _create_line(self, start: QPointF, end: QPointF, scene):
        length = ((end.x() - start.x())**2 + (end.y() - start.y())**2)**0.5
        if length < 5:
            return
        defs = get_settings().defaults
        data = LineItemData(
            x=start.x(), y=start.y(),
            x2=end.x(), y2=end.y(),
            width=abs(end.x() - start.x()),
            height=abs(end.y() - start.y()),
            stroke_color=defs.stroke_color,
            stroke_width=defs.stroke_width,
        )
        item = PublisherLineItem(data)
        cmd = AddItemCommand(scene, item, "Add Line")
        self.canvas.push_command(cmd)

    def _create_arrow(self, start: QPointF, end: QPointF, scene):
        length = ((end.x() - start.x())**2 + (end.y() - start.y())**2)**0.5
        if length < 5:
            return
        defs = get_settings().defaults
        data = ArrowItemData(
            x=start.x(), y=start.y(),
            x2=end.x(), y2=end.y(),
            width=abs(end.x() - start.x()),
            height=abs(end.y() - start.y()),
            stroke_color=defs.stroke_color,
            stroke_width=defs.stroke_width,
        )
        item = PublisherArrowItem(data)
        cmd = AddItemCommand(scene, item, "Add Arrow")
        self.canvas.push_command(cmd)

    def _make_rect(self, p1: QPointF, p2: QPointF) -> QRectF:
        x = min(p1.x(), p2.x())
        y = min(p1.y(), p2.y())
        w = abs(p2.x() - p1.x())
        h = abs(p2.y() - p1.y())
        return QRectF(x, y, w, h)

    def _remove_preview(self):
        if self._preview_item and self._preview_item.scene():
            self._preview_item.scene().removeItem(self._preview_item)
        self._preview_item = None

    def _snap_angle(self, start: QPointF, end: QPointF) -> QPointF:
        """Snap the line angle to the nearest 15-degree increment."""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        dist = math.hypot(dx, dy)
        if dist == 0:
            return end
        angle = math.atan2(dy, dx)
        snap_rad = math.radians(15)
        angle = round(angle / snap_rad) * snap_rad
        return QPointF(start.x() + dist * math.cos(angle),
                       start.y() + dist * math.sin(angle))

    @property
    def cursor(self):
        return Qt.CursorShape.CrossCursor

    def key_press(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.shape_type == ToolType.POLYGON:
                self._polygon_points.clear()
                self._remove_polygon_preview()
            self._remove_preview()
            self._drawing = False
