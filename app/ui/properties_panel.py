"""Right dock: context-sensitive property editing panel."""

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox, QLineEdit,
    QGroupBox, QFormLayout, QPushButton, QFontComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.canvas.canvas_items import PublisherTextItem, PublisherGroupItem
from app.models.items import TextItemData
from app.models.enums import UnitType, points_to_unit, unit_to_points
from app.ui.color_button import ColorButton


class PropertiesPanel(QDockWidget):
    """Right-side dock for editing selected item properties."""

    property_changed = pyqtSignal()
    send_to_front_requested = pyqtSignal()
    send_to_back_requested = pyqtSignal()
    flip_h_requested = pyqtSignal()
    flip_v_requested = pyqtSignal()
    align_left_requested = pyqtSignal()
    align_right_requested = pyqtSignal()
    align_center_h_requested = pyqtSignal()
    align_top_requested = pyqtSignal()
    align_bottom_requested = pyqtSignal()
    align_center_v_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Properties", parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setMinimumWidth(240)

        self._current_item = None
        self._updating = False
        self._unit = UnitType.INCHES

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._build_transform_group()
        self._build_appearance_group()
        self._build_layer_order_group()
        self._build_flip_group()
        self._build_align_group()
        self._build_text_group()

        # No selection label
        self._no_selection_label = QLabel("No item selected")
        self._no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._no_selection_label)

        self._layout.addStretch()

        scroll.setWidget(container)
        self.setWidget(scroll)

        self._set_enabled(False)

    def _unit_suffix(self) -> str:
        return f" {self._unit.value}"

    def _to_display(self, points: float) -> float:
        return points_to_unit(points, self._unit)

    def _to_points(self, value: float) -> float:
        return unit_to_points(value, self._unit)

    def _build_transform_group(self):
        self._transform_group = QGroupBox("Transform")
        form = QFormLayout()

        suffix = self._unit_suffix()

        self._x_spin = QDoubleSpinBox()
        self._x_spin.setRange(-10000, 10000)
        self._x_spin.setDecimals(2)
        self._x_spin.setSuffix(suffix)
        self._x_spin.valueChanged.connect(self._on_transform_changed)
        form.addRow("X:", self._x_spin)

        self._y_spin = QDoubleSpinBox()
        self._y_spin.setRange(-10000, 10000)
        self._y_spin.setDecimals(2)
        self._y_spin.setSuffix(suffix)
        self._y_spin.valueChanged.connect(self._on_transform_changed)
        form.addRow("Y:", self._y_spin)

        self._w_spin = QDoubleSpinBox()
        self._w_spin.setRange(0.01, 10000)
        self._w_spin.setDecimals(2)
        self._w_spin.setSuffix(suffix)
        self._w_spin.valueChanged.connect(self._on_transform_changed)
        form.addRow("W:", self._w_spin)

        self._h_spin = QDoubleSpinBox()
        self._h_spin.setRange(0.01, 10000)
        self._h_spin.setDecimals(2)
        self._h_spin.setSuffix(suffix)
        self._h_spin.valueChanged.connect(self._on_transform_changed)
        form.addRow("H:", self._h_spin)

        self._rot_spin = QDoubleSpinBox()
        self._rot_spin.setRange(-360, 360)
        self._rot_spin.setDecimals(1)
        self._rot_spin.setSuffix("\u00b0")
        self._rot_spin.valueChanged.connect(self._on_transform_changed)
        form.addRow("Rotation:", self._rot_spin)

        self._transform_group.setLayout(form)
        self._layout.addWidget(self._transform_group)

    def _build_appearance_group(self):
        self._appearance_group = QGroupBox("Appearance")
        form = QFormLayout()

        # Fill color
        self._fill_btn = ColorButton("#4A90D9")
        self._fill_btn.set_allow_transparent(True)
        self._fill_btn.color_changed.connect(self._on_fill_changed)
        form.addRow("Fill:", self._fill_btn)

        # Stroke color
        self._stroke_btn = ColorButton("#000000")
        self._stroke_btn.color_changed.connect(self._on_stroke_changed)
        form.addRow("Stroke:", self._stroke_btn)

        # Stroke width
        self._stroke_width = QDoubleSpinBox()
        self._stroke_width.setRange(0, 50)
        self._stroke_width.setDecimals(1)
        self._stroke_width.setSuffix(" pt")
        self._stroke_width.valueChanged.connect(self._on_stroke_width_changed)
        form.addRow("Stroke W:", self._stroke_width)

        # Opacity
        self._opacity_spin = QDoubleSpinBox()
        self._opacity_spin.setRange(0, 1.0)
        self._opacity_spin.setDecimals(2)
        self._opacity_spin.setSingleStep(0.1)
        self._opacity_spin.valueChanged.connect(self._on_opacity_changed)
        form.addRow("Opacity:", self._opacity_spin)

        self._appearance_group.setLayout(form)
        self._layout.addWidget(self._appearance_group)

    def _build_layer_order_group(self):
        self._layer_order_group = QGroupBox("Layer Order")
        layout = QHBoxLayout()

        self._send_front_btn = QPushButton("Send to Front")
        self._send_front_btn.clicked.connect(self.send_to_front_requested.emit)
        layout.addWidget(self._send_front_btn)

        self._send_back_btn = QPushButton("Send to Back")
        self._send_back_btn.clicked.connect(self.send_to_back_requested.emit)
        layout.addWidget(self._send_back_btn)

        self._layer_order_group.setLayout(layout)
        self._layout.addWidget(self._layer_order_group)

    def _build_flip_group(self):
        self._flip_group = QGroupBox("Flip")
        layout = QHBoxLayout()

        self._flip_h_btn = QPushButton("Flip Horizontal")
        self._flip_h_btn.clicked.connect(self.flip_h_requested.emit)
        layout.addWidget(self._flip_h_btn)

        self._flip_v_btn = QPushButton("Flip Vertical")
        self._flip_v_btn.clicked.connect(self.flip_v_requested.emit)
        layout.addWidget(self._flip_v_btn)

        self._flip_group.setLayout(layout)
        self._layout.addWidget(self._flip_group)

    def _build_align_group(self):
        self._align_group = QGroupBox("Align")
        layout = QVBoxLayout()

        row1 = QHBoxLayout()
        left_btn = QPushButton("Left")
        left_btn.clicked.connect(self.align_left_requested.emit)
        row1.addWidget(left_btn)
        center_h_btn = QPushButton("Center")
        center_h_btn.clicked.connect(self.align_center_h_requested.emit)
        row1.addWidget(center_h_btn)
        right_btn = QPushButton("Right")
        right_btn.clicked.connect(self.align_right_requested.emit)
        row1.addWidget(right_btn)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        top_btn = QPushButton("Top")
        top_btn.clicked.connect(self.align_top_requested.emit)
        row2.addWidget(top_btn)
        middle_btn = QPushButton("Middle")
        middle_btn.clicked.connect(self.align_center_v_requested.emit)
        row2.addWidget(middle_btn)
        bottom_btn = QPushButton("Bottom")
        bottom_btn.clicked.connect(self.align_bottom_requested.emit)
        row2.addWidget(bottom_btn)
        layout.addLayout(row2)

        self._align_group.setLayout(layout)
        self._layout.addWidget(self._align_group)

    def _build_text_group(self):
        self._text_group = QGroupBox("Text")
        form = QFormLayout()

        self._font_combo = QFontComboBox()
        self._font_combo.currentFontChanged.connect(self._on_font_changed)
        form.addRow("Font:", self._font_combo)

        self._font_size = QSpinBox()
        self._font_size.setRange(6, 200)
        self._font_size.setValue(12)
        self._font_size.setSuffix(" pt")
        self._font_size.valueChanged.connect(self._on_font_changed)
        form.addRow("Size:", self._font_size)

        # Style buttons row
        style_row = QHBoxLayout()
        self._bold_btn = QPushButton("B")
        self._bold_btn.setCheckable(True)
        self._bold_btn.setFixedWidth(30)
        self._bold_btn.setStyleSheet("font-weight: bold;")
        self._bold_btn.toggled.connect(self._on_font_changed)
        style_row.addWidget(self._bold_btn)

        self._italic_btn = QPushButton("I")
        self._italic_btn.setCheckable(True)
        self._italic_btn.setFixedWidth(30)
        self._italic_btn.setStyleSheet("font-style: italic;")
        self._italic_btn.toggled.connect(self._on_font_changed)
        style_row.addWidget(self._italic_btn)

        self._underline_btn = QPushButton("U")
        self._underline_btn.setCheckable(True)
        self._underline_btn.setFixedWidth(30)
        self._underline_btn.setStyleSheet("text-decoration: underline;")
        self._underline_btn.toggled.connect(self._on_font_changed)
        style_row.addWidget(self._underline_btn)

        style_row.addStretch()
        form.addRow("Style:", style_row)

        # Text color
        self._text_color_btn = ColorButton("#000000")
        self._text_color_btn.color_changed.connect(self._on_text_color_changed)
        form.addRow("Color:", self._text_color_btn)

        # Alignment
        self._align_combo = QComboBox()
        self._align_combo.addItems(["left", "center", "right"])
        self._align_combo.currentTextChanged.connect(self._on_alignment_changed)
        form.addRow("Align:", self._align_combo)

        self._text_group.setLayout(form)
        self._layout.addWidget(self._text_group)

    def _set_enabled(self, enabled: bool):
        self._transform_group.setVisible(enabled)
        self._appearance_group.setVisible(enabled)
        self._layer_order_group.setVisible(enabled)
        self._flip_group.setVisible(enabled)
        self._align_group.setVisible(enabled)
        self._text_group.setVisible(False)
        self._no_selection_label.setVisible(not enabled)

    def update_from_item(self, item):
        """Update panel to reflect the given item's properties."""
        self._current_item = item
        if item is None or not hasattr(item, 'item_data'):
            self._set_enabled(False)
            return

        self._set_enabled(True)
        self._updating = True

        data = item.item_data
        self._x_spin.setValue(self._to_display(data.x))
        self._y_spin.setValue(self._to_display(data.y))
        self._w_spin.setValue(self._to_display(data.width))
        self._h_spin.setValue(self._to_display(data.height))
        self._rot_spin.setValue(data.rotation)

        # For groups, show first child's appearance rather than the invisible overlay
        appearance_data = data
        if isinstance(item, PublisherGroupItem) and item.scene():
            children = item.get_child_items(item.scene())
            if children:
                appearance_data = children[0].item_data

        # Appearance
        self._fill_btn.set_color(appearance_data.fill_color)
        self._stroke_btn.set_color(appearance_data.stroke_color)
        self._stroke_width.setValue(appearance_data.stroke_width)
        self._opacity_spin.setValue(appearance_data.fill_opacity)

        # Text-specific
        is_text = isinstance(data, TextItemData)
        self._text_group.setVisible(is_text)
        if is_text:
            self._font_combo.setCurrentFont(QFont(data.font_family))
            self._font_size.setValue(int(data.font_size))
            self._bold_btn.setChecked(data.bold)
            self._italic_btn.setChecked(data.italic)
            self._underline_btn.setChecked(data.underline)
            self._text_color_btn.set_color(data.text_color)
            idx = self._align_combo.findText(data.alignment)
            if idx >= 0:
                self._align_combo.setCurrentIndex(idx)

        self._updating = False

    def set_unit(self, unit: UnitType):
        """Change the display unit and refresh spin box suffixes/values."""
        if unit == self._unit:
            return
        self._unit = unit
        suffix = self._unit_suffix()
        for spin in (self._x_spin, self._y_spin, self._w_spin, self._h_spin):
            spin.setSuffix(suffix)
        # Re-display current item in the new unit
        if self._current_item:
            self.update_from_item(self._current_item)

    def _on_transform_changed(self):
        if self._updating or not self._current_item:
            return
        data = self._current_item.item_data
        data.x = self._to_points(self._x_spin.value())
        data.y = self._to_points(self._y_spin.value())
        data.width = self._to_points(self._w_spin.value())
        data.height = self._to_points(self._h_spin.value())
        data.rotation = self._rot_spin.value()
        self._current_item.sync_from_data()
        self.property_changed.emit()

    def _get_target_items(self):
        """Return the items that should be modified.

        For groups, returns the children so appearance changes
        affect the visible items rather than the invisible overlay.
        """
        item = self._current_item
        if isinstance(item, PublisherGroupItem) and item.scene():
            return item.get_child_items(item.scene())
        return [item]

    def _on_fill_changed(self, color: str):
        if self._updating or not self._current_item:
            return
        for item in self._get_target_items():
            item.item_data.fill_color = color
            item.sync_from_data()
        self.property_changed.emit()

    def _on_stroke_changed(self, color: str):
        if self._updating or not self._current_item:
            return
        for item in self._get_target_items():
            item.item_data.stroke_color = color
            item.sync_from_data()
        self.property_changed.emit()

    def _on_stroke_width_changed(self, value: float):
        if self._updating or not self._current_item:
            return
        for item in self._get_target_items():
            item.item_data.stroke_width = value
            item.sync_from_data()
        self.property_changed.emit()

    def _on_opacity_changed(self, value: float):
        if self._updating or not self._current_item:
            return
        for item in self._get_target_items():
            item.item_data.fill_opacity = value
            item.sync_from_data()
        self.property_changed.emit()

    def _on_font_changed(self, *args):
        if self._updating or not self._current_item:
            return
        data = self._current_item.item_data
        if not isinstance(data, TextItemData):
            return
        data.font_family = self._font_combo.currentFont().family()
        data.font_size = self._font_size.value()
        data.bold = self._bold_btn.isChecked()
        data.italic = self._italic_btn.isChecked()
        data.underline = self._underline_btn.isChecked()
        self._current_item.sync_from_data()
        self.property_changed.emit()

    def _on_text_color_changed(self, color: str):
        if self._updating or not self._current_item:
            return
        data = self._current_item.item_data
        if isinstance(data, TextItemData):
            data.text_color = color
            self._current_item.sync_from_data()
            self.property_changed.emit()

    def _on_alignment_changed(self, alignment: str):
        if self._updating or not self._current_item:
            return
        data = self._current_item.item_data
        if isinstance(data, TextItemData):
            data.alignment = alignment
            self._current_item.sync_from_data()
            self.property_changed.emit()

    def clear(self):
        self._current_item = None
        self._set_enabled(False)
