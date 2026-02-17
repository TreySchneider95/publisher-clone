"""Preferences dialog for snap/guide settings and default colors."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,
    QSlider, QLabel, QDoubleSpinBox, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt

from app.models.settings import get_settings
from app.ui.color_button import ColorButton


class SettingsDialog(QDialog):
    """Application preferences dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(360)
        self._settings = get_settings()
        self._build_ui()
        self._load_from_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Snap section ---
        snap_group = QGroupBox("Alignment Guides && Snapping")
        snap_layout = QVBoxLayout(snap_group)

        # Snap distance slider
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Snap distance:"))
        self._snap_slider = QSlider(Qt.Orientation.Horizontal)
        self._snap_slider.setRange(0, 30)
        self._snap_slider.setTickInterval(5)
        self._snap_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider_row.addWidget(self._snap_slider)
        self._snap_label = QLabel("8px")
        self._snap_label.setFixedWidth(36)
        slider_row.addWidget(self._snap_label)
        snap_layout.addLayout(slider_row)
        self._snap_slider.valueChanged.connect(self._update_snap_label)

        # Guide checkboxes
        self._cb_center = QCheckBox("Center guides")
        self._cb_edges = QCheckBox("Edge guides")
        self._cb_thirds = QCheckBox("Third guides")
        self._cb_quarters = QCheckBox("Quarter guides")
        for cb in (self._cb_center, self._cb_edges, self._cb_thirds, self._cb_quarters):
            snap_layout.addWidget(cb)

        layout.addWidget(snap_group)

        # --- Default colors section ---
        color_group = QGroupBox("Default Shape Colors")
        color_layout = QFormLayout(color_group)

        self._fill_btn = ColorButton("#4A90D9")
        self._fill_btn.set_allow_transparent(True)
        color_layout.addRow("Fill color:", self._fill_btn)

        self._stroke_btn = ColorButton("#000000")
        color_layout.addRow("Stroke color:", self._stroke_btn)

        self._stroke_spin = QDoubleSpinBox()
        self._stroke_spin.setRange(0, 50)
        self._stroke_spin.setSingleStep(0.5)
        self._stroke_spin.setSuffix(" px")
        color_layout.addRow("Stroke width:", self._stroke_spin)

        layout.addWidget(color_group)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_snap_label(self, value: int):
        self._snap_label.setText("Off" if value == 0 else f"{value}px")

    def _load_from_settings(self):
        s = self._settings
        self._snap_slider.setValue(s.snap.snap_distance)
        self._update_snap_label(s.snap.snap_distance)
        self._cb_center.setChecked(s.snap.guides.center)
        self._cb_edges.setChecked(s.snap.guides.edges)
        self._cb_thirds.setChecked(s.snap.guides.thirds)
        self._cb_quarters.setChecked(s.snap.guides.quarters)
        self._fill_btn.set_color(s.defaults.fill_color)
        self._stroke_btn.set_color(s.defaults.stroke_color)
        self._stroke_spin.setValue(s.defaults.stroke_width)

    def _save_and_accept(self):
        s = self._settings
        s.snap.snap_distance = self._snap_slider.value()
        s.snap.guides.center = self._cb_center.isChecked()
        s.snap.guides.edges = self._cb_edges.isChecked()
        s.snap.guides.thirds = self._cb_thirds.isChecked()
        s.snap.guides.quarters = self._cb_quarters.isChecked()
        s.defaults.fill_color = self._fill_btn.color
        s.defaults.stroke_color = self._stroke_btn.color
        s.defaults.stroke_width = self._stroke_spin.value()
        s.save()
        self.accept()
