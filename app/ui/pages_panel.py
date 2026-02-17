"""Left dock: page thumbnails and management."""

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QPixmap, QIcon, QImage, QPainter, QColor


THUMB_WIDTH = 120
THUMB_HEIGHT = 155


class PagesPanel(QDockWidget):
    """Left dock panel with page thumbnails."""

    page_selected = pyqtSignal(int)
    add_page_requested = pyqtSignal()
    delete_page_requested = pyqtSignal(int)
    duplicate_page_requested = pyqtSignal(int)
    page_size_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("Pages", parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setMinimumWidth(150)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        self._list = QListWidget()
        self._list.setIconSize(QSize(THUMB_WIDTH, THUMB_HEIGHT))
        self._list.setViewMode(QListWidget.ViewMode.IconMode)
        self._list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list.setSpacing(8)
        self._list.setMovement(QListWidget.Movement.Static)
        self._list.currentRowChanged.connect(self._on_row_changed)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._list)

        # Buttons
        btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("+")
        self._add_btn.setToolTip("Add Page")
        self._add_btn.setFixedWidth(30)
        self._add_btn.clicked.connect(lambda: self.add_page_requested.emit())
        btn_layout.addWidget(self._add_btn)

        self._del_btn = QPushButton("-")
        self._del_btn.setToolTip("Delete Page")
        self._del_btn.setFixedWidth(30)
        self._del_btn.clicked.connect(self._delete_current)
        btn_layout.addWidget(self._del_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setWidget(container)
        self._scenes = []

    def set_scenes(self, scenes: list, current_index: int = 0):
        """Rebuild thumbnail list from scenes."""
        self._scenes = scenes
        self._list.blockSignals(True)
        self._list.clear()

        for i, scene in enumerate(scenes):
            thumb = self._render_thumbnail(scene)
            item = QListWidgetItem(QIcon(thumb), f"Page {i + 1}")
            item.setSizeHint(QSize(THUMB_WIDTH + 16, THUMB_HEIGHT + 30))
            self._list.addItem(item)

        if 0 <= current_index < self._list.count():
            self._list.setCurrentRow(current_index)
        self._list.blockSignals(False)

    def _render_thumbnail(self, scene) -> QPixmap:
        """Render a small thumbnail of the scene's content."""
        content_rect = scene.get_content_rect(padding=18)
        img = QImage(THUMB_WIDTH, THUMB_HEIGHT, QImage.Format.Format_ARGB32)
        img.fill(QColor(255, 255, 255))

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter, QRectF(0, 0, THUMB_WIDTH, THUMB_HEIGHT), content_rect)
        painter.end()

        return QPixmap.fromImage(img)

    def refresh_thumbnail(self, index: int, scene):
        """Update a single thumbnail."""
        if 0 <= index < self._list.count():
            thumb = self._render_thumbnail(scene)
            self._list.item(index).setIcon(QIcon(thumb))

    def _on_row_changed(self, row: int):
        if row >= 0:
            self.page_selected.emit(row)

    def _delete_current(self):
        row = self._list.currentRow()
        if row >= 0 and self._list.count() > 1:
            self.delete_page_requested.emit(row)

    def _show_context_menu(self, pos):
        row = self._list.currentRow()
        if row < 0:
            return

        menu = QMenu(self)
        add_action = menu.addAction("Add Page After")
        dup_action = menu.addAction("Duplicate Page")
        size_action = menu.addAction("Page Size...")
        menu.addSeparator()
        del_action = menu.addAction("Delete Page")
        del_action.setEnabled(self._list.count() > 1)

        action = menu.exec(self._list.mapToGlobal(pos))
        if action == add_action:
            self.add_page_requested.emit()
        elif action == dup_action:
            self.duplicate_page_requested.emit(row)
        elif action == size_action:
            self.page_size_requested.emit(row)
        elif action == del_action:
            self.delete_page_requested.emit(row)

    def select_page(self, index: int):
        self._list.blockSignals(True)
        if 0 <= index < self._list.count():
            self._list.setCurrentRow(index)
        self._list.blockSignals(False)
