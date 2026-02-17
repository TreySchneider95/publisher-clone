"""Layer list with z-order, visibility, and lock controls."""

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QCheckBox, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction

from app.canvas.canvas_items import PublisherItemMixin, PublisherGroupItem


class LayerListWidget(QListWidget):
    """QListWidget subclass that emits order_changed after drag-and-drop."""

    order_changed = pyqtSignal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self.order_changed.emit()


class LayerItemWidget(QWidget):
    """Widget for a single layer entry."""

    visibility_toggled = pyqtSignal(bool)
    lock_toggled = pyqtSignal(bool)
    selected = pyqtSignal()

    def __init__(self, name: str, indent: int = 0, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4 + indent * 16, 2, 4, 2)

        self._visible_cb = QCheckBox()
        self._visible_cb.setChecked(True)
        self._visible_cb.setToolTip("Visibility")
        self._visible_cb.toggled.connect(self.visibility_toggled.emit)
        layout.addWidget(self._visible_cb)

        self._lock_cb = QCheckBox()
        self._lock_cb.setChecked(False)
        self._lock_cb.setToolTip("Lock")
        self._lock_cb.toggled.connect(self.lock_toggled.emit)
        layout.addWidget(self._lock_cb)

        self._label = QLabel(name)
        self._label.setMinimumWidth(80)
        layout.addWidget(self._label, 1)

    def set_name(self, name: str):
        self._label.setText(name)

    def set_visible(self, visible: bool):
        self._visible_cb.setChecked(visible)

    def set_locked(self, locked: bool):
        self._lock_cb.setChecked(locked)


class LayersPanel(QDockWidget):
    """Bottom dock panel showing layer list with z-order management."""

    item_selected = pyqtSignal(object)  # Emits the canvas item
    z_order_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Layers", parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        # Column headers
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)
        vis_label = QLabel("Vis")
        vis_label.setToolTip("Visibility")
        vis_label.setFixedWidth(22)
        vis_label.setStyleSheet("font-size: 10px; color: #666;")
        header_layout.addWidget(vis_label)
        lock_label = QLabel("Lock")
        lock_label.setToolTip("Lock")
        lock_label.setFixedWidth(28)
        lock_label.setStyleSheet("font-size: 10px; color: #666;")
        header_layout.addWidget(lock_label)
        name_label = QLabel("Layer")
        name_label.setStyleSheet("font-size: 10px; color: #666;")
        header_layout.addWidget(name_label, 1)
        layout.addLayout(header_layout)

        # Layer list
        self._list = LayerListWidget()
        self._list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list.currentRowChanged.connect(self._on_row_changed)
        self._list.order_changed.connect(self._on_drag_reorder)
        layout.addWidget(self._list)

        # Buttons
        btn_layout = QHBoxLayout()
        self._up_btn = QPushButton("Up")
        self._up_btn.setToolTip("Move layer up (higher z)")
        self._up_btn.clicked.connect(self._move_up)
        btn_layout.addWidget(self._up_btn)

        self._down_btn = QPushButton("Down")
        self._down_btn.setToolTip("Move layer down (lower z)")
        self._down_btn.clicked.connect(self._move_down)
        btn_layout.addWidget(self._down_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setWidget(container)

        self._items_list: list = []  # Parallel list of canvas items
        self._scene = None

    def set_scene(self, scene):
        self._scene = scene
        self.refresh()

    def refresh(self):
        """Rebuild the layer list from the current scene."""
        self._list.blockSignals(True)
        self._list.clear()
        self._items_list.clear()

        if not self._scene:
            self._list.blockSignals(False)
            return

        items = self._scene.get_publisher_items()
        # Sort by z-value (highest first = top of list)
        items.sort(key=lambda it: it.zValue(), reverse=True)

        # Collect IDs that are children of a group
        grouped_ids = set()
        group_children_map = {}  # group_id -> [child_items in order]
        id_to_item = {item.item_data.id: item for item in items}

        for item in items:
            if isinstance(item, PublisherGroupItem):
                grouped_ids.update(item.item_data.child_ids)
                children = []
                for cid in item.item_data.child_ids:
                    child = id_to_item.get(cid)
                    if child:
                        children.append(child)
                group_children_map[item.item_data.id] = children

        for item in items:
            data = item.item_data
            # Skip items that are children of a group (they appear indented below)
            if data.id in grouped_ids:
                continue

            name = data.name or f"{data.item_type.name.title()} ({data.id[:6]})"
            self._add_layer_row(item, name, indent=0)

            # If this is a group, show its children indented below
            if isinstance(item, PublisherGroupItem):
                for child in group_children_map.get(data.id, []):
                    cd = child.item_data
                    child_name = cd.name or f"{cd.item_type.name.title()} ({cd.id[:6]})"
                    self._add_layer_row(child, f"↳ {child_name}", indent=1)

        self._list.blockSignals(False)

    def _add_layer_row(self, item, name, indent=0):
        """Add a single row to the layer list."""
        data = item.item_data
        widget = LayerItemWidget(name, indent=indent)
        widget.set_visible(data.visible)
        widget.set_locked(data.locked)
        widget.visibility_toggled.connect(
            lambda v, it=item: self._toggle_visibility(it, v)
        )
        widget.lock_toggled.connect(
            lambda v, it=item: self._toggle_lock(it, v)
        )

        list_item = QListWidgetItem()
        list_item.setSizeHint(QSize(0, 30))
        list_item.setData(Qt.ItemDataRole.UserRole, data.id)
        # Grouped children should not be individually draggable
        if indent > 0:
            list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self._list.addItem(list_item)
        self._list.setItemWidget(list_item, widget)
        self._items_list.append(item)

    def _on_drag_reorder(self):
        """Called after a drag-and-drop reorder. Update z-values to match new visual order."""
        # Build lookup from item data ID to canvas item
        id_to_item = {item.item_data.id: item for item in self._items_list}

        new_order = []
        for row in range(self._list.count()):
            item_id = self._list.item(row).data(Qt.ItemDataRole.UserRole)
            if item_id and item_id in id_to_item:
                new_order.append(id_to_item[item_id])

        if len(new_order) != len(self._items_list):
            # Something went wrong, just refresh from current state
            self.refresh()
            return

        # Assign z-values: highest z for first item (top of list), decreasing
        count = len(new_order)
        for i, item in enumerate(new_order):
            z = float(count - i)
            item.setZValue(z)
            item.item_data.z_value = z

        # Rebuild with the updated z-values (widgets get recreated cleanly)
        self.refresh()
        self.z_order_changed.emit()

    def _on_row_changed(self, row: int):
        if 0 <= row < len(self._items_list):
            self.item_selected.emit(self._items_list[row])

    def _toggle_visibility(self, item, visible: bool):
        item.item_data.visible = visible
        item.setVisible(visible)

    def _toggle_lock(self, item, locked: bool):
        from PyQt6.QtWidgets import QGraphicsItem
        item.item_data.locked = locked
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not locked)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not locked)

    def _move_up(self):
        row = self._list.currentRow()
        if row <= 0 or row >= len(self._items_list):
            return
        # Don't move grouped children
        item_a = self._items_list[row]
        item_b = self._items_list[row - 1]
        if self._is_grouped_child(item_a):
            return
        za = item_a.zValue()
        zb = item_b.zValue()
        item_a.setZValue(zb)
        item_b.setZValue(za)
        item_a.item_data.z_value = zb
        item_b.item_data.z_value = za
        self.refresh()
        self._list.blockSignals(True)
        self._list.setCurrentRow(row - 1)
        self._list.blockSignals(False)
        self.z_order_changed.emit()

    def _move_down(self):
        row = self._list.currentRow()
        if row < 0 or row >= len(self._items_list) - 1:
            return
        item_a = self._items_list[row]
        item_b = self._items_list[row + 1]
        if self._is_grouped_child(item_a):
            return
        za = item_a.zValue()
        zb = item_b.zValue()
        item_a.setZValue(zb)
        item_b.setZValue(za)
        item_a.item_data.z_value = zb
        item_b.item_data.z_value = za
        self.refresh()
        self._list.blockSignals(True)
        self._list.setCurrentRow(row + 1)
        self._list.blockSignals(False)
        self.z_order_changed.emit()

    def _is_grouped_child(self, item):
        """Check if an item is a child of a group in the current scene."""
        if not self._scene:
            return False
        item_id = item.item_data.id
        for gi in self._scene.get_publisher_items():
            if isinstance(gi, PublisherGroupItem) and item_id in gi.item_data.child_ids:
                return True
        return False

    def select_item(self, item):
        """Highlight the row matching the given canvas item."""
        self._list.blockSignals(True)
        for i, it in enumerate(self._items_list):
            if it is item:
                self._list.setCurrentRow(i)
                break
        self._list.blockSignals(False)
