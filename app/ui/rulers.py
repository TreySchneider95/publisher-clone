"""Horizontal and Vertical rulers synced to the canvas view."""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from app.models.enums import UnitType, POINTS_PER_INCH, POINTS_PER_CM, POINTS_PER_FOOT

RULER_THICKNESS = 25


class BaseRuler(QWidget):
    """Base class for rulers."""

    def __init__(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent)
        self._orientation = orientation
        self._view = None
        self._unit = UnitType.INCHES
        self._cursor_pos = 0.0  # In scene coords

        self.setFont(QFont("Arial", 7))

        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(RULER_THICKNESS)
        else:
            self.setFixedWidth(RULER_THICKNESS)

    def set_view(self, view):
        self._view = view

    def set_unit(self, unit: UnitType):
        self._unit = unit
        self.update()

    def set_cursor_pos(self, pos: float):
        self._cursor_pos = pos
        self.update()

    def _get_tick_info(self):
        """Returns (major_spacing_pts, subdivisions, label_format)."""
        if self._unit == UnitType.INCHES:
            return POINTS_PER_INCH, 8, lambda v: f"{v:.0f}"
        elif self._unit == UnitType.CENTIMETERS:
            return POINTS_PER_CM, 5, lambda v: f"{v:.0f}"
        elif self._unit == UnitType.FEET:
            return POINTS_PER_FOOT, 10, lambda v: f"{v:.0f}"
        else:
            return 50.0, 5, lambda v: f"{v:.0f}"

    def _unit_label(self, value_pts: float) -> str:
        if self._unit == UnitType.INCHES:
            return f"{value_pts / POINTS_PER_INCH:.0f}"
        elif self._unit == UnitType.CENTIMETERS:
            return f"{value_pts / POINTS_PER_CM:.0f}"
        elif self._unit == UnitType.FEET:
            return f"{value_pts / POINTS_PER_FOOT:.0f}"
        else:
            return f"{value_pts:.0f}"


class HorizontalRuler(BaseRuler):
    """Horizontal ruler along the top of the canvas."""

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)

    def paintEvent(self, event):
        if not self._view:
            return

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        view = self._view
        # Map viewport edges to scene coordinates
        left_scene = view.mapToScene(0, 0).x()
        right_scene = view.mapToScene(view.viewport().width(), 0).x()

        zoom = view.transform().m11()
        major_spacing, subdivisions, _ = self._get_tick_info()
        minor_spacing = major_spacing / subdivisions

        # Find first major tick
        start = int(left_scene / major_spacing) * major_spacing - major_spacing

        painter.setPen(QPen(QColor(100, 100, 100), 0.5))

        x_scene = start
        while x_scene <= right_scene + major_spacing:
            # Convert scene x to widget x
            view_pt = view.mapFromScene(QPointF(x_scene, 0))
            wx = view_pt.x()

            # Major tick
            painter.drawLine(int(wx), RULER_THICKNESS - 10, int(wx), RULER_THICKNESS)
            label = self._unit_label(x_scene)
            painter.drawText(int(wx) + 2, RULER_THICKNESS - 12, label)

            # Minor ticks
            for i in range(1, subdivisions):
                minor_x = x_scene + i * minor_spacing
                mvp = view.mapFromScene(QPointF(minor_x, 0))
                mwx = mvp.x()
                tick_height = 4 if i == subdivisions // 2 else 2
                painter.drawLine(int(mwx), RULER_THICKNESS - tick_height,
                                 int(mwx), RULER_THICKNESS)

            x_scene += major_spacing

        # Cursor indicator
        if self._cursor_pos is not None:
            cvp = view.mapFromScene(QPointF(self._cursor_pos, 0))
            cx = cvp.x()
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawLine(int(cx), 0, int(cx), RULER_THICKNESS)

        # Bottom border
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawLine(0, RULER_THICKNESS - 1, self.width(), RULER_THICKNESS - 1)

        painter.end()


class VerticalRuler(BaseRuler):
    """Vertical ruler along the left of the canvas."""

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Vertical, parent)

    def paintEvent(self, event):
        if not self._view:
            return

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        view = self._view
        top_scene = view.mapToScene(0, 0).y()
        bottom_scene = view.mapToScene(0, view.viewport().height()).y()

        major_spacing, subdivisions, _ = self._get_tick_info()
        minor_spacing = major_spacing / subdivisions

        start = int(top_scene / major_spacing) * major_spacing - major_spacing

        painter.setPen(QPen(QColor(100, 100, 100), 0.5))

        y_scene = start
        while y_scene <= bottom_scene + major_spacing:
            view_pt = view.mapFromScene(QPointF(0, y_scene))
            wy = view_pt.y()

            painter.drawLine(RULER_THICKNESS - 10, int(wy), RULER_THICKNESS, int(wy))
            label = self._unit_label(y_scene)

            painter.save()
            painter.translate(RULER_THICKNESS - 12, int(wy) + 2)
            painter.rotate(-90)
            painter.drawText(0, 0, label)
            painter.restore()

            for i in range(1, subdivisions):
                minor_y = y_scene + i * minor_spacing
                mvp = view.mapFromScene(QPointF(0, minor_y))
                mwy = mvp.y()
                tick_width = 4 if i == subdivisions // 2 else 2
                painter.drawLine(RULER_THICKNESS - tick_width, int(mwy),
                                 RULER_THICKNESS, int(mwy))

            y_scene += major_spacing

        # Cursor indicator
        if self._cursor_pos is not None:
            cvp = view.mapFromScene(QPointF(0, self._cursor_pos))
            cy = cvp.y()
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawLine(0, int(cy), RULER_THICKNESS, int(cy))

        # Right border
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawLine(RULER_THICKNESS - 1, 0, RULER_THICKNESS - 1, self.height())

        painter.end()
