"""Undo/redo command for placing a custom shape group."""

from PyQt6.QtGui import QUndoCommand


class PlaceCustomShapeCommand(QUndoCommand):
    """Add a group of items to the scene as one undoable step."""

    def __init__(self, scene, items, text="Place Custom Shape"):
        super().__init__(text)
        self.scene = scene
        self.items = items

    def redo(self):
        for item in self.items:
            self.scene.addItem(item)

    def undo(self):
        for item in self.items:
            self.scene.removeItem(item)
