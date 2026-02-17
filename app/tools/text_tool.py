"""Text tool - click to create text box, double-click to edit."""

from PyQt6.QtWidgets import QGraphicsItem, QInputDialog
from PyQt6.QtCore import Qt, QPointF, QRectF

from app.tools.base_tool import BaseTool
from app.models.items import TextItemData
from app.canvas.canvas_items import PublisherTextItem
from app.commands.item_commands import AddItemCommand


class TextTool(BaseTool):
    """Click to place a text box. Double-click existing text to edit."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._start_pos = QPointF()
        self._drawing = False
        self._preview = None

    def activate(self):
        pass

    def deactivate(self):
        self._remove_preview()
        self._drawing = False

    def mouse_press(self, event):
        scene = self.canvas.get_scene()
        if not scene:
            return

        pos = event.scenePos()

        # Check if clicking an existing text item
        item = scene.itemAt(pos, self.canvas.get_view().transform())
        if item and isinstance(item, PublisherTextItem):
            self._edit_text(item)
            return

        self._start_pos = pos
        self._drawing = True

        # Create preview
        from PyQt6.QtWidgets import QGraphicsRectItem
        from PyQt6.QtGui import QPen, QColor, QBrush
        self._remove_preview()
        self._preview = QGraphicsRectItem(0, 0, 0, 0)
        self._preview.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine))
        self._preview.setBrush(QBrush(QColor(74, 144, 217, 20)))
        scene.addItem(self._preview)

    def mouse_move(self, event):
        if not self._drawing or not self._preview:
            return
        pos = event.scenePos()
        x = min(self._start_pos.x(), pos.x())
        y = min(self._start_pos.y(), pos.y())
        w = abs(pos.x() - self._start_pos.x())
        h = abs(pos.y() - self._start_pos.y())
        self._preview.setRect(QRectF(x, y, w, h))

    def mouse_release(self, event):
        if not self._drawing:
            return
        self._drawing = False
        self._remove_preview()

        scene = self.canvas.get_scene()
        if not scene:
            return

        pos = event.scenePos()
        x = min(self._start_pos.x(), pos.x())
        y = min(self._start_pos.y(), pos.y())
        w = abs(pos.x() - self._start_pos.x())
        h = abs(pos.y() - self._start_pos.y())

        # Minimum size for click-to-create
        if w < 20:
            w = 150
        if h < 20:
            h = 40

        data = TextItemData(
            x=x, y=y, width=w, height=h,
            text="Double-click to edit"
        )
        item = PublisherTextItem(data)
        cmd = AddItemCommand(scene, item, "Add Text")
        self.canvas.push_command(cmd)
        self.canvas.switch_to_select()

    def mouse_double_click(self, event):
        scene = self.canvas.get_scene()
        if not scene:
            return
        pos = event.scenePos()
        item = scene.itemAt(pos, self.canvas.get_view().transform())
        if item and isinstance(item, PublisherTextItem):
            self._edit_text(item)

    def _edit_text(self, item: PublisherTextItem):
        view = self.canvas.get_view()
        text, ok = QInputDialog.getMultiLineText(
            view, "Edit Text", "Text:", item.item_data.text
        )
        if ok:
            item.item_data.text = text
            item.update()

    def _remove_preview(self):
        if self._preview and self._preview.scene():
            self._preview.scene().removeItem(self._preview)
        self._preview = None

    @property
    def cursor(self):
        return Qt.CursorShape.IBeamCursor
