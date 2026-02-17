"""Abstract base class for all tools."""

from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QGraphicsSceneMouseEvent
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QKeyEvent


class BaseTool(ABC):
    """Strategy interface for input handling tools."""

    def __init__(self, canvas):
        self.canvas = canvas

    def activate(self):
        """Called when this tool becomes active."""
        pass

    def deactivate(self):
        """Called when switching away from this tool."""
        pass

    def mouse_press(self, event: QGraphicsSceneMouseEvent):
        pass

    def mouse_move(self, event: QGraphicsSceneMouseEvent):
        pass

    def mouse_release(self, event: QGraphicsSceneMouseEvent):
        pass

    def mouse_double_click(self, event: QGraphicsSceneMouseEvent):
        pass

    def key_press(self, event: QKeyEvent):
        pass

    def key_release(self, event: QKeyEvent):
        pass

    def context_menu(self, event):
        """Called on right-click. Override in subclasses to show context menus."""
        pass

    @property
    def cursor(self) -> Qt.CursorShape:
        return Qt.CursorShape.ArrowCursor
