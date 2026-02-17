"""Manages the active tool and routes events to it."""

from PyQt6.QtCore import QObject, pyqtSignal
from app.models.enums import ToolType
from app.tools.base_tool import BaseTool


class ToolManager(QObject):
    """Holds the active tool and dispatches events to it."""

    tool_changed = pyqtSignal(ToolType)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: dict[ToolType, BaseTool] = {}
        self._active_tool: BaseTool | None = None
        self._active_type: ToolType | None = None

    def register_tool(self, tool_type: ToolType, tool: BaseTool):
        self._tools[tool_type] = tool

    def set_tool(self, tool_type: ToolType):
        if self._active_type == tool_type:
            return
        if self._active_tool:
            self._active_tool.deactivate()
        self._active_tool = self._tools.get(tool_type)
        self._active_type = tool_type
        if self._active_tool:
            self._active_tool.activate()
        self.tool_changed.emit(tool_type)

    @property
    def active_tool(self) -> BaseTool | None:
        return self._active_tool

    @property
    def active_type(self) -> ToolType | None:
        return self._active_type
