"""Wraps QUndoStack for undo/redo."""

from PyQt6.QtGui import QUndoStack


class CommandStack:
    """Central undo/redo stack for the application."""

    def __init__(self):
        self.stack = QUndoStack()

    def push(self, command):
        self.stack.push(command)

    def undo(self):
        self.stack.undo()

    def redo(self):
        self.stack.redo()

    def clear(self):
        self.stack.clear()

    @property
    def can_undo(self) -> bool:
        return self.stack.canUndo()

    @property
    def can_redo(self) -> bool:
        return self.stack.canRedo()

    @property
    def undo_text(self) -> str:
        return self.stack.undoText()

    @property
    def redo_text(self) -> str:
        return self.stack.redoText()
