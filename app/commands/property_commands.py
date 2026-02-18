"""Undo/redo commands for property changes."""

from PyQt6.QtGui import QUndoCommand


class ChangePropertyCommand(QUndoCommand):
    """Generic property change command."""

    def __init__(self, item, prop_name: str, old_value, new_value, text="Change Property"):
        super().__init__(text)
        self.item = item
        self.prop_name = prop_name
        self.old_value = old_value
        self.new_value = new_value

    def redo(self):
        if hasattr(self.item, 'item_data'):
            setattr(self.item.item_data, self.prop_name, self.new_value)
            self.item.sync_from_data()

    def undo(self):
        if hasattr(self.item, 'item_data'):
            setattr(self.item.item_data, self.prop_name, self.old_value)
            self.item.sync_from_data()


class ChangeFillColorCommand(ChangePropertyCommand):
    def __init__(self, item, old_color: str, new_color: str):
        super().__init__(item, "fill_color", old_color, new_color, "Change Fill Color")


class ChangeStrokeColorCommand(ChangePropertyCommand):
    def __init__(self, item, old_color: str, new_color: str):
        super().__init__(item, "stroke_color", old_color, new_color, "Change Stroke Color")


class ChangeStrokeWidthCommand(ChangePropertyCommand):
    def __init__(self, item, old_width: float, new_width: float):
        super().__init__(item, "stroke_width", old_width, new_width, "Change Stroke Width")


class ChangeFontCommand(QUndoCommand):
    """Change multiple font properties at once."""

    def __init__(self, item, old_props: dict, new_props: dict, text="Change Font"):
        super().__init__(text)
        self.item = item
        self.old_props = old_props
        self.new_props = new_props

    def redo(self):
        if hasattr(self.item, 'item_data'):
            for k, v in self.new_props.items():
                setattr(self.item.item_data, k, v)
            self.item.sync_from_data()

    def undo(self):
        if hasattr(self.item, 'item_data'):
            for k, v in self.old_props.items():
                setattr(self.item.item_data, k, v)
            self.item.sync_from_data()


class FlipItemCommand(QUndoCommand):
    """Toggle flip_h or flip_v on an item."""

    def __init__(self, item, axis: str, text="Flip Item"):
        super().__init__(text)
        self.item = item
        self.axis = axis  # "h" or "v"

    def redo(self):
        if hasattr(self.item, 'item_data'):
            if self.axis == "h":
                self.item.item_data.flip_h = not self.item.item_data.flip_h
            else:
                self.item.item_data.flip_v = not self.item.item_data.flip_v
            self.item.sync_from_data()

    def undo(self):
        # Toggle again to reverse
        self.redo()


class ChangeZOrderCommand(QUndoCommand):
    """Change z-order of an item."""

    def __init__(self, item, old_z: float, new_z: float, text="Change Z-Order"):
        super().__init__(text)
        self.item = item
        self.old_z = old_z
        self.new_z = new_z

    def redo(self):
        self.item.setZValue(self.new_z)
        if hasattr(self.item, 'item_data'):
            self.item.item_data.z_value = self.new_z

    def undo(self):
        self.item.setZValue(self.old_z)
        if hasattr(self.item, 'item_data'):
            self.item.item_data.z_value = self.old_z
