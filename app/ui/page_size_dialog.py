"""Dialog for setting per-page size (Infinite, preset, or custom dimensions)."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QDoubleSpinBox, QDialogButtonBox, QLabel,
    QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt

from app.models.enums import (
    PageSizePreset, UnitType, points_to_unit, unit_to_points
)
from app.models.document import Page


class PageSizeDialog(QDialog):
    """Dialog to choose page size: Infinite, a preset, or custom dimensions."""

    def __init__(self, page: Page, unit: UnitType, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Page Size")
        self.setMinimumWidth(320)
        self._unit = unit
        self._page = page

        layout = QVBoxLayout(self)

        # Preset combo
        form = QFormLayout()
        self._preset_combo = QComboBox()
        for preset in PageSizePreset:
            self._preset_combo.addItem(preset.label, preset)
        form.addRow("Preset:", self._preset_combo)

        # Width / Height spinboxes
        unit_suffix = f" {unit.value}"
        self._width_spin = QDoubleSpinBox()
        self._width_spin.setRange(0.1, 9999)
        self._width_spin.setDecimals(2)
        self._width_spin.setSuffix(unit_suffix)
        form.addRow("Width:", self._width_spin)

        self._height_spin = QDoubleSpinBox()
        self._height_spin.setRange(0.1, 9999)
        self._height_spin.setDecimals(2)
        self._height_spin.setSuffix(unit_suffix)
        form.addRow("Height:", self._height_spin)

        layout.addLayout(form)

        # Orientation toggle
        orient_layout = QHBoxLayout()
        orient_layout.addWidget(QLabel("Orientation:"))
        self._portrait_radio = QRadioButton("Portrait")
        self._landscape_radio = QRadioButton("Landscape")
        self._orient_group = QButtonGroup(self)
        self._orient_group.addButton(self._portrait_radio)
        self._orient_group.addButton(self._landscape_radio)
        self._portrait_radio.setChecked(True)
        orient_layout.addWidget(self._portrait_radio)
        orient_layout.addWidget(self._landscape_radio)
        orient_layout.addStretch()
        layout.addLayout(orient_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Connect signals
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self._portrait_radio.toggled.connect(self._on_orientation_changed)
        self._landscape_radio.toggled.connect(self._on_orientation_changed)
        self._width_spin.valueChanged.connect(self._on_spin_edited)
        self._height_spin.valueChanged.connect(self._on_spin_edited)

        # Initialise from current page
        self._init_from_page(page)

    def _init_from_page(self, page: Page):
        """Set dialog state from the current page."""
        if page.is_infinite:
            self._preset_combo.setCurrentIndex(0)  # Infinite
            return

        # Try to match a preset
        matched = False
        for i, preset in enumerate(PageSizePreset):
            if preset is PageSizePreset.INFINITE or preset is PageSizePreset.CUSTOM:
                continue
            w, h = preset.width_pt, preset.height_pt
            if (_close(page.width_pt, w) and _close(page.height_pt, h)):
                self._preset_combo.setCurrentIndex(i)
                self._portrait_radio.setChecked(True)
                matched = True
                break
            elif (_close(page.width_pt, h) and _close(page.height_pt, w)):
                self._preset_combo.setCurrentIndex(i)
                self._landscape_radio.setChecked(True)
                matched = True
                break

        if not matched:
            # Custom
            idx = self._preset_combo.findText("Custom")
            self._preset_combo.setCurrentIndex(idx)
            self._width_spin.setValue(points_to_unit(page.width_pt, self._unit))
            self._height_spin.setValue(points_to_unit(page.height_pt, self._unit))

    def _on_preset_changed(self, index: int):
        preset = self._preset_combo.itemData(index)
        if preset is None:
            return

        is_infinite = preset is PageSizePreset.INFINITE
        is_custom = preset is PageSizePreset.CUSTOM

        self._width_spin.setEnabled(not is_infinite)
        self._height_spin.setEnabled(not is_infinite)
        self._portrait_radio.setEnabled(not is_infinite and not is_custom)
        self._landscape_radio.setEnabled(not is_infinite and not is_custom)

        if is_infinite:
            self._width_spin.setValue(0)
            self._height_spin.setValue(0)
        elif not is_custom:
            w = points_to_unit(preset.width_pt, self._unit)
            h = points_to_unit(preset.height_pt, self._unit)
            if self._landscape_radio.isChecked():
                w, h = h, w
            self._width_spin.blockSignals(True)
            self._height_spin.blockSignals(True)
            self._width_spin.setValue(w)
            self._height_spin.setValue(h)
            self._width_spin.blockSignals(False)
            self._height_spin.blockSignals(False)

    def _on_spin_edited(self):
        """Auto-switch to Custom when the user manually changes dimensions."""
        preset = self._preset_combo.currentData()
        if preset is not PageSizePreset.CUSTOM:
            idx = self._preset_combo.findText("Custom")
            self._preset_combo.blockSignals(True)
            self._preset_combo.setCurrentIndex(idx)
            self._preset_combo.blockSignals(False)
            self._width_spin.setEnabled(True)
            self._height_spin.setEnabled(True)
            self._portrait_radio.setEnabled(False)
            self._landscape_radio.setEnabled(False)

    def _on_orientation_changed(self):
        preset = self._preset_combo.currentData()
        if preset is None or preset is PageSizePreset.INFINITE or preset is PageSizePreset.CUSTOM:
            return
        w = points_to_unit(preset.width_pt, self._unit)
        h = points_to_unit(preset.height_pt, self._unit)
        if self._landscape_radio.isChecked():
            w, h = h, w
        self._width_spin.blockSignals(True)
        self._height_spin.blockSignals(True)
        self._width_spin.setValue(w)
        self._height_spin.setValue(h)
        self._width_spin.blockSignals(False)
        self._height_spin.blockSignals(False)

    def result_size_pt(self) -> tuple[float, float]:
        """Return (width_pt, height_pt). (0, 0) means Infinite."""
        preset = self._preset_combo.currentData()
        if preset is PageSizePreset.INFINITE:
            return (0, 0)
        w = unit_to_points(self._width_spin.value(), self._unit)
        h = unit_to_points(self._height_spin.value(), self._unit)
        return (w, h)


def _close(a: float, b: float, tol: float = 0.5) -> bool:
    return abs(a - b) < tol
