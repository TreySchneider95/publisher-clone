"""Modal dialog for selecting a texture fill from bundled textures."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QToolButton, QLabel,
    QScrollArea, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

from app.models.texture_registry import list_textures, load_texture

THUMB_SIZE = 64
COLUMNS = 4


class TexturePicker(QDialog):
    """Grid dialog showing texture thumbnails. Returns selected texture_id or '' for none."""

    def __init__(self, current_texture: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Texture")
        self.setMinimumSize(340, 400)
        self._selected_id = current_texture

        layout = QVBoxLayout(self)

        # "None" button to clear texture
        none_btn = QToolButton()
        none_btn.setText("No Texture (Solid Color)")
        none_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        none_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        none_btn.setFixedHeight(32)
        none_btn.clicked.connect(self._select_none)
        layout.addWidget(none_btn)

        # Scrollable grid of textures
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(8)

        textures = list_textures()
        for i, tex in enumerate(textures):
            row, col = divmod(i, COLUMNS)
            btn = self._make_thumb_button(tex)
            grid.addWidget(btn, row, col)

        grid_widget.setLayout(grid)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

    def _make_thumb_button(self, tex: dict) -> QWidget:
        """Create a thumbnail button with label for a texture."""
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(2, 2, 2, 2)
        vbox.setSpacing(2)

        btn = QToolButton()
        btn.setFixedSize(THUMB_SIZE + 8, THUMB_SIZE + 8)
        btn.setIconSize(QSize(THUMB_SIZE, THUMB_SIZE))

        pixmap = load_texture(tex["id"])
        if pixmap and not pixmap.isNull():
            thumb = pixmap.scaled(
                THUMB_SIZE, THUMB_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            btn.setIcon(QIcon(thumb))

        # Highlight if this is the currently selected texture
        if tex["id"] == self._selected_id:
            btn.setStyleSheet("border: 2px solid #4A90D9;")

        texture_id = tex["id"]
        btn.clicked.connect(lambda checked, tid=texture_id: self._select(tid))

        label = QLabel(tex["name"])
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setMaximumWidth(THUMB_SIZE + 8)
        font = label.font()
        font.setPointSize(9)
        label.setFont(font)

        vbox.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        return container

    def _select(self, texture_id: str):
        self._selected_id = texture_id
        self.accept()

    def _select_none(self):
        self._selected_id = ""
        self.accept()

    def selected_texture_id(self) -> str:
        return self._selected_id
