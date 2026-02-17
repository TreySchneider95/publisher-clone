"""Undo/redo commands for item manipulation."""

from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QGraphicsItem


class AddItemCommand(QUndoCommand):
    """Add an item to the scene."""

    def __init__(self, scene, item, text="Add Item"):
        super().__init__(text)
        self.scene = scene
        self.item = item
        # Place new items on top of all existing items
        max_z = 0.0
        for i in scene.items():
            if hasattr(i, 'item_data'):
                max_z = max(max_z, i.zValue())
        top_z = max_z + 1.0
        item.setZValue(top_z)
        if hasattr(item, 'item_data'):
            item.item_data.z_value = top_z

    def redo(self):
        self.scene.addItem(self.item)

    def undo(self):
        self.scene.removeItem(self.item)


class RemoveItemCommand(QUndoCommand):
    """Remove an item from the scene."""

    def __init__(self, scene, item, text="Remove Item"):
        super().__init__(text)
        self.scene = scene
        self.item = item

    def redo(self):
        self.scene.removeItem(self.item)

    def undo(self):
        self.scene.addItem(self.item)


class MoveItemCommand(QUndoCommand):
    """Move an item to a new position."""

    def __init__(self, item, old_pos: QPointF, new_pos: QPointF, text="Move Item"):
        super().__init__(text)
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.item.setPos(self.new_pos)
        if hasattr(self.item, 'item_data'):
            self.item.item_data.x = self.new_pos.x()
            self.item.item_data.y = self.new_pos.y()

    def undo(self):
        self.item.setPos(self.old_pos)
        if hasattr(self.item, 'item_data'):
            self.item.item_data.x = self.old_pos.x()
            self.item.item_data.y = self.old_pos.y()


class ResizeItemCommand(QUndoCommand):
    """Resize an item."""

    def __init__(self, item, old_rect, new_rect, old_pos, new_pos, text="Resize Item"):
        super().__init__(text)
        self.item = item
        self.old_rect = old_rect
        self.new_rect = new_rect
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.item.setPos(self.new_pos)
        if hasattr(self.item, 'setRect'):
            self.item.setRect(self.new_rect)
        if hasattr(self.item, 'item_data'):
            self.item.item_data.x = self.new_pos.x()
            self.item.item_data.y = self.new_pos.y()
            self.item.item_data.width = self.new_rect.width()
            self.item.item_data.height = self.new_rect.height()

    def undo(self):
        self.item.setPos(self.old_pos)
        if hasattr(self.item, 'setRect'):
            self.item.setRect(self.old_rect)
        if hasattr(self.item, 'item_data'):
            self.item.item_data.x = self.old_pos.x()
            self.item.item_data.y = self.old_pos.y()
            self.item.item_data.width = self.old_rect.width()
            self.item.item_data.height = self.old_rect.height()


class ResizePointsItemCommand(QUndoCommand):
    """Resize a points-based item (polygon, freehand) by storing old/new points."""

    def __init__(self, item, old_pos, new_pos, old_points, new_points,
                 old_size, new_size, text="Resize Item"):
        super().__init__(text)
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.old_points = old_points
        self.new_points = new_points
        self.old_w, self.old_h = old_size
        self.new_w, self.new_h = new_size

    def _apply(self, pos, points, w, h):
        d = self.item.item_data
        d.x = pos.x()
        d.y = pos.y()
        d.width = w
        d.height = h
        d.points = list(points)
        self.item.sync_from_data()

    def redo(self):
        self._apply(self.new_pos, self.new_points, self.new_w, self.new_h)

    def undo(self):
        self._apply(self.old_pos, self.old_points, self.old_w, self.old_h)


class EditVertexCommand(QUndoCommand):
    """Edit polygon vertices. Stores full old/new state (pos, size, points)."""

    def __init__(self, item, old_state, new_state, text="Edit Vertex"):
        super().__init__(text)
        self.item = item
        self.old_state = old_state  # (x, y, width, height, points)
        self.new_state = new_state

    def _apply(self, state):
        x, y, w, h, points = state
        d = self.item.item_data
        d.x = x
        d.y = y
        d.width = w
        d.height = h
        d.points = list(points)
        self.item.sync_from_data()

    def redo(self):
        self._apply(self.new_state)

    def undo(self):
        self._apply(self.old_state)


class RotateItemCommand(QUndoCommand):
    """Rotate an item."""

    def __init__(self, item, old_rotation: float, new_rotation: float, text="Rotate Item"):
        super().__init__(text)
        self.item = item
        self.old_rotation = old_rotation
        self.new_rotation = new_rotation

    def redo(self):
        self.item.setRotation(self.new_rotation)
        if hasattr(self.item, 'item_data'):
            self.item.item_data.rotation = self.new_rotation

    def undo(self):
        self.item.setRotation(self.old_rotation)
        if hasattr(self.item, 'item_data'):
            self.item.item_data.rotation = self.old_rotation
