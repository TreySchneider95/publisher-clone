"""Undo/redo commands for page operations."""

from PyQt6.QtGui import QUndoCommand


class AddPageCommand(QUndoCommand):
    """Add a new page to the document."""

    def __init__(self, main_window, index: int = -1, text="Add Page"):
        super().__init__(text)
        self._mw = main_window
        self._index = index
        self._page = None
        self._scene = None

    def redo(self):
        self._page, self._scene = self._mw.add_page(self._index)
        idx = self._index if self._index >= 0 else len(self._mw.scenes) - 1
        self._mw.switch_page(idx)
        self._mw._refresh_pages_panel()

    def undo(self):
        if self._scene:
            idx = self._mw.scenes.index(self._scene)
            self._mw.scenes.remove(self._scene)
            self._mw.document.pages.remove(self._page)
            if idx >= len(self._mw.scenes):
                idx = len(self._mw.scenes) - 1
            self._mw.switch_page(max(0, idx))
            self._mw._refresh_pages_panel()


class RemovePageCommand(QUndoCommand):
    """Remove a page from the document."""

    def __init__(self, main_window, index: int, text="Remove Page"):
        super().__init__(text)
        self._mw = main_window
        self._index = index
        self._page = None
        self._scene = None

    def redo(self):
        self._page = self._mw.document.pages[self._index]
        self._scene = self._mw.scenes[self._index]
        self._mw.document.pages.pop(self._index)
        self._mw.scenes.pop(self._index)
        new_idx = min(self._index, len(self._mw.scenes) - 1)
        self._mw.switch_page(max(0, new_idx))
        self._mw._refresh_pages_panel()

    def undo(self):
        self._mw.document.pages.insert(self._index, self._page)
        self._mw.scenes.insert(self._index, self._scene)
        self._mw.switch_page(self._index)
        self._mw._refresh_pages_panel()
