"""Image tool - click to place, opens file dialog."""

import base64
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QImage

from app.tools.base_tool import BaseTool
from app.models.items import ImageItemData
from app.canvas.canvas_items import PublisherImageItem
from app.commands.item_commands import AddItemCommand


class ImageTool(BaseTool):
    """Click to open file dialog and place an image."""

    def __init__(self, canvas):
        super().__init__(canvas)

    def mouse_press(self, event):
        scene = self.canvas.get_scene()
        if not scene:
            return

        pos = event.scenePos()
        view = self.canvas.get_view()

        file_path, _ = QFileDialog.getOpenFileName(
            view, "Insert Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.svg *.webp);;All Files (*)"
        )
        if not file_path:
            return

        # Load and encode image
        img = QImage(file_path)
        if img.isNull():
            return

        # Read raw file bytes for base64
        with open(file_path, 'rb') as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode('ascii')

        # Size: fit within reasonable bounds while maintaining aspect ratio
        max_dim = 400
        w = img.width()
        h = img.height()
        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            w = int(w * scale)
            h = int(h * scale)

        data = ImageItemData(
            x=pos.x(), y=pos.y(),
            width=w, height=h,
            image_data_b64=b64,
            source_path=file_path
        )
        item = PublisherImageItem(data)
        cmd = AddItemCommand(scene, item, "Add Image")
        self.canvas.push_command(cmd)
        self.canvas.switch_to_select()

    @property
    def cursor(self):
        return Qt.CursorShape.CrossCursor
