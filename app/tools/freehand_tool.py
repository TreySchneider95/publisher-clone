"""Freehand drawing tool using QPainterPath."""

from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QColor, QPainterPath

from app.tools.base_tool import BaseTool
from app.models.items import FreehandItemData
from app.canvas.canvas_items import PublisherFreehandItem
from app.commands.item_commands import AddItemCommand
from app.models.settings import get_settings


def simplify_points(points: list[tuple[float, float]], tolerance: float = 2.0) -> list[tuple[float, float]]:
    """Reduce point count using Ramer-Douglas-Peucker algorithm."""
    if len(points) < 3:
        return points

    # Find the point with the maximum distance from the line between first and last
    first = points[0]
    last = points[-1]

    max_dist = 0
    max_idx = 0
    for i in range(1, len(points) - 1):
        dist = _point_line_distance(points[i], first, last)
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    if max_dist > tolerance:
        left = simplify_points(points[:max_idx + 1], tolerance)
        right = simplify_points(points[max_idx:], tolerance)
        return left[:-1] + right
    else:
        return [first, last]


def _point_line_distance(point, line_start, line_end):
    """Calculate perpendicular distance from point to line."""
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end

    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy

    if length_sq == 0:
        return ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5

    t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / length_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return ((x0 - proj_x) ** 2 + (y0 - proj_y) ** 2) ** 0.5


class FreehandTool(BaseTool):
    """Draw freehand paths."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._drawing = False
        self._points: list[tuple[float, float]] = []
        self._preview_path = None

    def activate(self):
        self._drawing = False
        self._points.clear()

    def deactivate(self):
        self._remove_preview()
        self._drawing = False
        self._points.clear()

    def mouse_press(self, event):
        scene = self.canvas.get_scene()
        if not scene:
            return

        pos = event.scenePos()
        self._drawing = True
        self._points = [(pos.x(), pos.y())]

        # Create preview
        self._remove_preview()
        self._preview_path = QGraphicsPathItem()
        self._preview_path.setPen(QPen(QColor(0, 0, 0), 2))
        scene.addItem(self._preview_path)

    def mouse_move(self, event):
        if not self._drawing or not self._preview_path:
            return

        pos = event.scenePos()
        self._points.append((pos.x(), pos.y()))

        path = QPainterPath()
        if self._points:
            path.moveTo(self._points[0][0], self._points[0][1])
            for px, py in self._points[1:]:
                path.lineTo(px, py)
        self._preview_path.setPath(path)

    def mouse_release(self, event):
        if not self._drawing:
            return
        self._drawing = False
        self._remove_preview()

        if len(self._points) < 2:
            return

        scene = self.canvas.get_scene()
        if not scene:
            return

        # Simplify the path
        simplified = simplify_points(self._points, tolerance=2.0)

        # Calculate bounding box for positioning
        xs = [p[0] for p in simplified]
        ys = [p[1] for p in simplified]
        min_x, min_y = min(xs), min(ys)
        max_x, max_y = max(xs), max(ys)

        # Make points relative to origin
        local_points = [(x - min_x, y - min_y) for x, y in simplified]

        defs = get_settings().defaults
        data = FreehandItemData(
            x=min_x, y=min_y,
            width=max_x - min_x, height=max_y - min_y,
            points=local_points,
            stroke_color=defs.stroke_color,
            stroke_width=defs.stroke_width,
        )
        item = PublisherFreehandItem(data)
        cmd = AddItemCommand(scene, item, "Draw Freehand")
        self.canvas.push_command(cmd)
        self.canvas.switch_to_select()

    def _remove_preview(self):
        if self._preview_path and self._preview_path.scene():
            self._preview_path.scene().removeItem(self._preview_path)
        self._preview_path = None

    @property
    def cursor(self):
        return Qt.CursorShape.CrossCursor
