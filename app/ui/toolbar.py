"""Tool selection toolbar."""

from PyQt6.QtWidgets import (
    QToolBar, QToolButton, QButtonGroup, QWidget, QHBoxLayout, QMenu,
    QWidgetAction, QLabel, QVBoxLayout, QGraphicsScene,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QIcon, QAction, QPixmap, QImage, QPainter, QColor, QFont

from app.models.enums import ToolType

_THUMB_SIZE = 96


_TOOL_LABELS = {
    ToolType.SELECT: ("Select", "V"),
    ToolType.TEXT: ("Text", "T"),
    ToolType.RECT: ("Rectangle", "R"),
    ToolType.ELLIPSE: ("Ellipse", "E"),
    ToolType.LINE: ("Line", "L"),
    ToolType.ARROW: ("Arrow", "A"),
    ToolType.POLYGON: ("Polygon", "P"),
    ToolType.FREEHAND: ("Freehand", "F"),
    ToolType.IMAGE: ("Image", "I"),
}


class _ShapeEntry(QWidget):
    """Widget showing a thumbnail + name for a custom shape menu entry."""

    clicked = pyqtSignal()

    def __init__(self, pixmap: QPixmap, name: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        thumb_label = QLabel()
        thumb_label.setPixmap(pixmap)
        thumb_label.setFixedSize(_THUMB_SIZE, _THUMB_SIZE)
        thumb_label.setStyleSheet(
            "border: 1px solid #ccc; background: white; border-radius: 3px;"
        )
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(thumb_label)

        name_label = QLabel(name)
        name_label.setMinimumWidth(100)
        layout.addWidget(name_label, 1)

    def enterEvent(self, event):
        self.setStyleSheet("background: palette(highlight);")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class ToolBar(QToolBar):
    """Toolbar with tool buttons."""

    tool_selected = pyqtSignal(ToolType)
    save_custom_requested = pyqtSignal()
    load_custom_requested = pyqtSignal(str, str)  # folder, name
    open_library_folder_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Tools", parent)
        self.setMovable(False)
        self.setIconSize(QSize(24, 24))

        self._buttons: dict[ToolType, QToolButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        # Tool buttons
        tool_order = [
            ToolType.SELECT, ToolType.TEXT, None,  # separator
            ToolType.RECT, ToolType.ELLIPSE, ToolType.LINE,
            ToolType.ARROW, ToolType.POLYGON, None,
            ToolType.FREEHAND, None,
            ToolType.IMAGE,
        ]

        for tool in tool_order:
            if tool is None:
                self.addSeparator()
                continue
            btn = QToolButton()
            label, shortcut = _TOOL_LABELS[tool]
            btn.setText(label)
            btn.setToolTip(f"{label} ({shortcut})")
            btn.setCheckable(True)
            btn.setMinimumWidth(70)
            btn.clicked.connect(lambda checked, t=tool: self._on_tool_clicked(t))
            self._group.addButton(btn)
            self._buttons[tool] = btn
            self.addWidget(btn)

        # Select tool active by default
        if ToolType.SELECT in self._buttons:
            self._buttons[ToolType.SELECT].setChecked(True)

        # Separator + Custom shape library button
        self.addSeparator()
        self._custom_btn = QToolButton()
        self._custom_btn.setText("Custom")
        self._custom_btn.setToolTip("Custom Shape Library")
        self._custom_btn.setMinimumWidth(70)
        self._custom_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._custom_menu = QMenu(self._custom_btn)
        self._custom_menu.aboutToShow.connect(self._rebuild_custom_menu)
        self._custom_btn.setMenu(self._custom_menu)
        self.addWidget(self._custom_btn)
        self._shape_library = None

        # Separator before zoom controls
        self.addSeparator()

        # Zoom buttons
        self.zoom_in_action = self.addAction("+")
        self.zoom_in_action.setToolTip("Zoom In (Ctrl++)")
        self.zoom_out_action = self.addAction("-")
        self.zoom_out_action.setToolTip("Zoom Out (Ctrl+-)")
        self.zoom_fit_action = self.addAction("Fit")
        self.zoom_fit_action.setToolTip("Zoom to Fit (Ctrl+0)")

    def _on_tool_clicked(self, tool_type: ToolType):
        self.tool_selected.emit(tool_type)

    def set_active_tool(self, tool_type: ToolType):
        btn = self._buttons.get(tool_type)
        if btn:
            btn.setChecked(True)

    def set_shape_library(self, library):
        self._shape_library = library

    def _rebuild_custom_menu(self):
        self._custom_menu.clear()

        # Save selection action
        save_action = self._custom_menu.addAction("Save Selection...")
        save_action.triggered.connect(self.save_custom_requested.emit)

        self._custom_menu.addSeparator()

        if self._shape_library:
            all_shapes = self._shape_library.get_all_shapes()

            # Root-level shapes
            for name in all_shapes.get('', []):
                self._add_shape_entry(self._custom_menu, '', name)

            # Folder submenus
            for folder, names in all_shapes.items():
                if folder == '':
                    continue
                submenu = self._custom_menu.addMenu(folder)
                for name in names:
                    self._add_shape_entry(submenu, folder, name)

        self._custom_menu.addSeparator()
        open_action = self._custom_menu.addAction("Open Library Folder...")
        open_action.triggered.connect(self.open_library_folder_requested.emit)

    def _add_shape_entry(self, menu: QMenu, folder: str, name: str):
        """Add a shape entry with large thumbnail to a menu."""
        pixmap = self._shape_thumbnail(folder, name)
        widget = _ShapeEntry(pixmap, name)
        widget.clicked.connect(
            lambda f=folder, n=name: self._on_shape_clicked(f, n)
        )
        action = QWidgetAction(menu)
        action.setDefaultWidget(widget)
        menu.addAction(action)

    def _on_shape_clicked(self, folder: str, name: str):
        self._custom_menu.close()
        self.load_custom_requested.emit(folder, name)

    def _shape_thumbnail(self, folder: str, name: str) -> QPixmap:
        """Render a thumbnail pixmap for a saved custom shape."""
        if not self._shape_library:
            return QPixmap(_THUMB_SIZE, _THUMB_SIZE)
        try:
            items_dicts = self._shape_library.load_shape(folder, name)
        except Exception:
            return QPixmap(_THUMB_SIZE, _THUMB_SIZE)

        from app.models.serialization import dict_to_item_data
        from app.canvas.canvas_items import create_item_from_data

        scene = QGraphicsScene()
        for d in items_dicts:
            item_data = dict_to_item_data(d)
            if item_data:
                gi = create_item_from_data(item_data)
                scene.addItem(gi)

        # Compute bounding rect of all items
        items = [i for i in scene.items() if hasattr(i, 'item_data')]
        if not items:
            pm = QPixmap(_THUMB_SIZE, _THUMB_SIZE)
            pm.fill(QColor(255, 255, 255))
            return pm
        bounds = items[0].sceneBoundingRect()
        for i in items[1:]:
            bounds = bounds.united(i.sceneBoundingRect())

        # Add a little padding
        pad = max(bounds.width(), bounds.height()) * 0.08
        bounds.adjust(-pad, -pad, pad, pad)

        img = QImage(_THUMB_SIZE, _THUMB_SIZE, QImage.Format.Format_ARGB32)
        img.fill(QColor(255, 255, 255))
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter, QRectF(0, 0, _THUMB_SIZE, _THUMB_SIZE), bounds)
        painter.end()

        return QPixmap.fromImage(img)
