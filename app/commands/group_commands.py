"""Undo/redo commands for grouping and ungrouping items."""

from PyQt6.QtGui import QUndoCommand

from app.models.items import GroupItemData, _new_id
from app.canvas.canvas_items import PublisherGroupItem, create_item_from_data


class GroupItemsCommand(QUndoCommand):
    """Create a group item that references the given children by ID."""

    def __init__(self, scene, child_items, text="Group Items"):
        super().__init__(text)
        self.scene = scene
        self.child_items = child_items

        # Build the GroupItemData
        child_ids = [item.item_data.id for item in child_items]
        self.group_data = GroupItemData(
            id=_new_id(),
            child_ids=child_ids,
            name="Group",
        )
        self.group_item = PublisherGroupItem(self.group_data)

    def redo(self):
        self.scene.addItem(self.group_item)
        self.group_item.update_bounds_from_children(self.scene)
        # Make children non-selectable/non-movable so only group is manipulated
        for child in self.child_items:
            child.setSelected(False)

    def undo(self):
        self.scene.removeItem(self.group_item)


class UngroupItemsCommand(QUndoCommand):
    """Remove a group item from the scene. Children stay."""

    def __init__(self, scene, group_item, text="Ungroup Items"):
        super().__init__(text)
        self.scene = scene
        self.group_item = group_item

    def redo(self):
        self.scene.removeItem(self.group_item)

    def undo(self):
        self.scene.addItem(self.group_item)
        self.group_item.update_bounds_from_children(self.scene)
