"""Status bar showing cursor position, zoom %, and page info."""

from PyQt6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout, QComboBox
from PyQt6.QtCore import Qt, QPointF, pyqtSignal

from app.models.enums import UnitType, points_to_unit
from app.version import VERSION


class PublisherStatusBar(QStatusBar):
    """Custom status bar with cursor position, zoom, and page info."""

    unit_changed = pyqtSignal(UnitType)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit = UnitType.INCHES

        # Cursor position
        self._pos_label = QLabel("X: 0.00  Y: 0.00")
        self._pos_label.setMinimumWidth(180)
        self.addWidget(self._pos_label)

        # Separator
        self.addWidget(QLabel("|"))

        # Zoom
        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(60)
        self.addWidget(self._zoom_label)

        # Separator
        self.addWidget(QLabel("|"))

        # Page info
        self._page_label = QLabel("Page 1 of 1")
        self._page_label.setMinimumWidth(100)
        self.addWidget(self._page_label)

        # Version label (right side)
        self._version_label = QLabel(f"v{VERSION}")
        self._version_label.setStyleSheet("color: gray;")
        self.addPermanentWidget(self._version_label)

        # Unit selector (right side)
        self._unit_combo = QComboBox()
        self._unit_combo.addItem("Inches", UnitType.INCHES)
        self._unit_combo.addItem("Centimeters", UnitType.CENTIMETERS)
        self._unit_combo.addItem("Pixels", UnitType.PIXELS)
        self._unit_combo.addItem("Feet", UnitType.FEET)
        self._unit_combo.currentIndexChanged.connect(self._on_unit_changed)
        self.addPermanentWidget(self._unit_combo)

    def update_cursor(self, pos: QPointF):
        x = points_to_unit(pos.x(), self._unit)
        y = points_to_unit(pos.y(), self._unit)
        suffix = self._unit.value
        self._pos_label.setText(f"X: {x:.2f}{suffix}  Y: {y:.2f}{suffix}")

    def update_zoom(self, zoom: float):
        self._zoom_label.setText(f"{zoom * 100:.0f}%")

    def update_page(self, current: int, total: int):
        self._page_label.setText(f"Page {current + 1} of {total}")

    def _on_unit_changed(self, index: int):
        unit = self._unit_combo.itemData(index)
        if unit:
            self._unit = unit
            self.unit_changed.emit(unit)
