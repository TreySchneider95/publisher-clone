"""Dialog for Duplicate Along Line (array duplicate) feature."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QRadioButton, QSpinBox, QDoubleSpinBox,
    QDialogButtonBox, QGroupBox,
)

from app.models.enums import UnitType, unit_to_points


class DuplicateArrayDialog(QDialog):
    """Modal dialog to configure array duplication parameters."""

    def __init__(self, unit: UnitType = UnitType.INCHES, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Along Line")
        self._unit = unit

        layout = QVBoxLayout(self)

        # Direction
        dir_group = QGroupBox("Direction")
        dir_layout = QHBoxLayout(dir_group)
        self._horizontal_rb = QRadioButton("Horizontal")
        self._vertical_rb = QRadioButton("Vertical")
        self._horizontal_rb.setChecked(True)
        dir_layout.addWidget(self._horizontal_rb)
        dir_layout.addWidget(self._vertical_rb)
        layout.addWidget(dir_group)

        # Count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Number of copies:"))
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 100)
        self._count_spin.setValue(3)
        count_layout.addWidget(self._count_spin)
        layout.addLayout(count_layout)

        # Spacing
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("Spacing:"))
        self._spacing_spin = QDoubleSpinBox()
        self._spacing_spin.setRange(0.01, 1000.0)
        self._spacing_spin.setValue(1.00)
        self._spacing_spin.setDecimals(2)
        self._spacing_spin.setSuffix(f" {unit.value}")
        spacing_layout.addWidget(self._spacing_spin)
        layout.addLayout(spacing_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setFixedWidth(300)

    def result_values(self):
        """Return (direction, count, spacing_pts) from the dialog."""
        direction = "horizontal" if self._horizontal_rb.isChecked() else "vertical"
        count = self._count_spin.value()
        spacing_pts = unit_to_points(self._spacing_spin.value(), self._unit)
        return direction, count, spacing_pts
