"""Color swatch button that opens QColorDialog."""

from PyQt6.QtWidgets import QPushButton, QColorDialog
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen


class ColorButton(QPushButton):
    """A button that displays a color swatch and opens a color picker."""

    color_changed = pyqtSignal(str)  # Emits hex color string

    def __init__(self, color: str = "#000000", parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._allow_transparent = False
        self.setFixedSize(QSize(32, 24))
        self.clicked.connect(self._pick_color)

    @property
    def color(self) -> str:
        if self._color.alpha() == 0:
            return "transparent"
        return self._color.name()

    def set_color(self, color: str):
        if color == "transparent":
            self._color = QColor(0, 0, 0, 0)
        else:
            self._color = QColor(color)
        self.update()

    def set_allow_transparent(self, allow: bool):
        self._allow_transparent = allow

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(4, 4, -4, -4)

        if self._color.alpha() == 0:
            # Draw checkerboard for transparent
            painter.fillRect(rect, QColor(255, 255, 255))
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            mid_x = rect.center().x()
            mid_y = rect.center().y()
            painter.fillRect(rect.x(), rect.y(),
                             int(rect.width() / 2), int(rect.height() / 2),
                             QColor(200, 200, 200))
            painter.fillRect(int(mid_x), int(mid_y),
                             int(rect.width() / 2), int(rect.height() / 2),
                             QColor(200, 200, 200))
            # Red line through for "no color"
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawLine(rect.topLeft(), rect.bottomRight())
        else:
            painter.fillRect(rect, self._color)

        painter.setPen(QPen(QColor(128, 128, 128), 1))
        painter.drawRect(rect)
        painter.end()

    def _pick_color(self):
        options = QColorDialog.ColorDialogOption(0)
        if self._allow_transparent:
            options = QColorDialog.ColorDialogOption.ShowAlphaChannel

        initial = self._color if self._color.alpha() > 0 else QColor(255, 255, 255)
        color = QColorDialog.getColor(initial, self, "Select Color", options)
        if color.isValid():
            self._color = color
            self.update()
            self.color_changed.emit(self.color)
