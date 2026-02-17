"""Select tool - click/drag/resize/rotate/multi-select with rubber band."""

import math
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QMenu
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush, QPolygonF

from app.tools.base_tool import BaseTool
from app.canvas.selection_handles import (
    SelectionHandleGroup, HandleType, VertexHandleGroup,
    ResizeHandle, RotateHandle, VertexHandle,
)
from app.canvas.alignment_guides import AlignmentGuideEngine
from app.commands.item_commands import (
    MoveItemCommand, ResizeItemCommand, RotateItemCommand,
    ResizePointsItemCommand, EditVertexCommand,
)
from app.models.settings import get_settings


class SelectTool(BaseTool):
    """Handles selection, moving, resizing, and rotating items."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._handle_group = None
        self._dragging = False
        self._resizing = False
        self._rotating = False
        self._active_handle = None
        self._drag_start = QPointF()
        self._item_start_pos = QPointF()
        self._item_start_rect = QRectF()
        self._item_start_points = None  # saved for polygon/freehand resize
        self._start_rotation = 0.0
        # Multi-item drag tracking
        self._drag_items: list = []
        self._drag_start_positions: list[QPointF] = []
        # Group child tracking for resize/rotate
        self._group_child_starts: list = []
        self._rotate_child_starts: list = []  # (child, start_pos, start_rotation)
        self._rotate_group_center = QPointF()
        # Alignment guides
        self._guide_engine = AlignmentGuideEngine()
        # Rubber band
        self._rubber_band_active = False
        self._rubber_band_origin = QPointF()
        self._rubber_band_rect: QGraphicsRectItem | None = None
        self._rubber_band_additive = False  # True when Shift held at start
        # Vertex editing
        self._vertex_editing = False
        self._vertex_handles: VertexHandleGroup | None = None
        self._vertex_drag_index = -1
        self._vertex_start_state = None  # (x, y, w, h, points)

    def activate(self):
        self._ensure_handle_group()

    def _ensure_handle_group(self):
        """Lazily create or re-create the handle group for the current scene."""
        scene = self.canvas.get_scene()
        if not scene:
            return
        if self._handle_group is None or self._handle_group.scene is not scene:
            if self._handle_group:
                self._handle_group.detach()
            self._handle_group = SelectionHandleGroup(scene)

    def deactivate(self):
        self._exit_vertex_mode()
        if self._handle_group:
            self._handle_group.detach()
            self._handle_group = None
        self._guide_engine.end_drag()
        self._clear_rubber_band()

    # --- Group helpers ---

    def _find_parent_group(self, scene, item):
        """Find the group item that owns this child, or None."""
        from app.canvas.canvas_items import PublisherGroupItem
        item_id = item.item_data.id
        for gi in scene.items():
            if isinstance(gi, PublisherGroupItem) and item_id in gi.item_data.child_ids:
                return gi
        return None

    def _is_group_item(self, item):
        from app.canvas.canvas_items import PublisherGroupItem
        return isinstance(item, PublisherGroupItem)

    def _is_points_item(self, item):
        """Check if item stores its geometry as a list of points."""
        return (hasattr(item, 'item_data')
                and hasattr(item.item_data, 'points')
                and isinstance(item.item_data.points, list))

    # --- Mouse events ---

    def mouse_press(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            return  # Let contextMenuEvent handle it

        scene = self.canvas.get_scene()
        if not scene:
            return

        self._ensure_handle_group()

        pos = event.scenePos()

        # --- Vertex editing mode ---
        if self._vertex_editing and self._vertex_handles:
            vertex_idx = self._vertex_handles.handle_at(pos)
            if vertex_idx is not None:
                # Start vertex drag
                self._vertex_drag_index = vertex_idx
                target = self._vertex_handles.target
                d = target.item_data
                self._vertex_start_state = (
                    d.x, d.y, d.width, d.height, list(d.points)
                )
                return
            # Check if clicking inside the polygon body — stay in vertex mode
            target = self._vertex_handles.target
            if target and target.contains(target.mapFromScene(pos)):
                return
            # Clicked elsewhere — exit vertex mode
            self._exit_vertex_mode()
            # Fall through to normal behaviour

        # Check if clicking a handle
        if self._handle_group and self._handle_group.target:
            handle_type = self._handle_group.handle_at(pos)
            if handle_type is not None:
                target = self._handle_group.target
                self._active_handle = handle_type
                self._drag_start = pos
                self._item_start_pos = QPointF(target.pos())
                # Save start rect — use item_data dimensions for points items
                if self._is_points_item(target):
                    d = target.item_data
                    self._item_start_rect = QRectF(0, 0, d.width, d.height)
                    self._item_start_points = list(d.points)
                elif hasattr(target, 'rect'):
                    self._item_start_rect = target.rect()
                    self._item_start_points = None
                else:
                    self._item_start_points = None
                if handle_type == HandleType.ROTATE:
                    self._rotating = True
                    self._start_rotation = target.rotation()
                    # For groups, save child positions/rotations for orbital rotation
                    if self._is_group_item(target):
                        self._rotate_group_center = target.mapToScene(
                            target.boundingRect().center()
                        )
                        self._rotate_child_starts = []
                        for child in target.get_child_items(scene):
                            self._rotate_child_starts.append(
                                (child, QPointF(child.pos()), child.rotation())
                            )
                else:
                    self._resizing = True
                    # For groups, save child start positions for proportional scaling
                    if self._is_group_item(target):
                        self._group_child_starts = []
                        for child in target.get_child_items(scene):
                            self._group_child_starts.append(
                                (child, child.pos(), child.boundingRect())
                            )
                return

        # Check if clicking an item
        item = scene.itemAt(pos, self.canvas.get_view().transform())
        # Skip handles
        while item and isinstance(item, (ResizeHandle, RotateHandle, VertexHandle)):
            item = None
            break

        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

        if item and hasattr(item, 'item_data') and not item.item_data.locked:
            # If the clicked item is a child of a group, redirect to the group
            if not self._is_group_item(item):
                parent_group = self._find_parent_group(scene, item)
                if parent_group:
                    item = parent_group

            if shift:
                # Shift-click: toggle selection of this item
                item.setSelected(not item.isSelected())
            elif item.isSelected():
                # Clicked an already-selected item: drag all selected items
                pass
            else:
                # Clicked an unselected item: select only this one
                scene.clearSelection()
                item.setSelected(True)

            # Gather all selected publisher items for multi-drag
            # For groups, also include their children in the drag
            self._drag_items = []
            self._drag_start_positions = []
            selected = [
                i for i in scene.selectedItems()
                if hasattr(i, 'item_data') and not i.item_data.locked
            ]
            for sel_item in selected:
                self._drag_items.append(sel_item)
                self._drag_start_positions.append(sel_item.pos())
                # If it's a group, also drag its children
                if self._is_group_item(sel_item):
                    for child in sel_item.get_child_items(scene):
                        if child not in self._drag_items:
                            self._drag_items.append(child)
                            self._drag_start_positions.append(child.pos())

            self._drag_start = pos
            self._dragging = True
            self._guide_engine.begin_drag(scene, self._drag_items)

            # Show handles for single selection (including groups)
            if len(selected) == 1:
                self._handle_group.attach(selected[0])
            elif self._handle_group:
                self._handle_group.detach()
        else:
            # Click on empty space
            if not shift:
                scene.clearSelection()
            if self._handle_group:
                self._handle_group.detach()
            self._rubber_band_active = True
            self._rubber_band_additive = shift
            self._rubber_band_origin = pos

    def mouse_move(self, event):
        pos = event.scenePos()

        # Vertex dragging
        if self._vertex_editing and self._vertex_drag_index >= 0:
            self._do_vertex_drag(pos)
            return

        if self._dragging and self._drag_items:
            delta = pos - self._drag_start
            # Compute tentative union rect of all dragged items
            snap_cfg = get_settings().snap
            if snap_cfg.snap_distance > 0:
                # Compute union of scene bounding rects at tentative positions
                rects = []
                for item, start_pos in zip(self._drag_items, self._drag_start_positions):
                    sbr = item.sceneBoundingRect()
                    offset = (start_pos + delta) - item.pos()
                    rects.append(sbr.translated(offset))
                if rects:
                    union = rects[0]
                    for r in rects[1:]:
                        union = union.united(r)
                    # Convert snap_distance from pixels to scene units
                    view = self.canvas.get_view()
                    snap_dist = snap_cfg.snap_distance / view.transform().m11() if view else snap_cfg.snap_distance
                    dx, dy, active = self._guide_engine.compute_snap(union, snap_dist)
                    delta = QPointF(delta.x() + dx, delta.y() + dy)
                    self._guide_engine.update_visuals(active)
            for item, start_pos in zip(self._drag_items, self._drag_start_positions):
                item.setPos(start_pos + delta)
            if self._handle_group and self._handle_group.target:
                self._handle_group.update_positions()

        elif self._resizing and self._handle_group and self._handle_group.target:
            self._do_resize(pos)

        elif self._rotating and self._handle_group and self._handle_group.target:
            self._do_rotate(pos)

        elif self._rubber_band_active:
            self._update_rubber_band(pos)

    def mouse_release(self, event):
        scene = self.canvas.get_scene()
        pos = event.scenePos()

        # Vertex drag release
        if self._vertex_editing and self._vertex_drag_index >= 0:
            self._finish_vertex_drag()
            return

        if self._dragging and self._drag_items:
            delta = pos - self._drag_start
            if delta.x() != 0 or delta.y() != 0:
                # Wrap multiple move commands in a macro so undo is one step
                moved = [(item, sp, item.pos())
                         for item, sp in zip(self._drag_items, self._drag_start_positions)
                         if sp != item.pos()]
                if moved:
                    use_macro = len(moved) > 1
                    if use_macro:
                        self.canvas.begin_macro("Move Items")
                    for item, start_pos, new_pos in moved:
                        cmd = MoveItemCommand(item, start_pos, new_pos)
                        self.canvas.push_command(cmd)
                    if use_macro:
                        self.canvas.end_macro()
            # Update group bounds after drag
            if scene:
                from app.canvas.canvas_items import PublisherGroupItem
                for item in self._drag_items:
                    if isinstance(item, PublisherGroupItem):
                        item.update_bounds_from_children(scene)
            self._dragging = False
            self._drag_items.clear()
            self._drag_start_positions.clear()
            self._guide_engine.end_drag()

        elif self._resizing and self._handle_group and self._handle_group.target:
            target = self._handle_group.target
            new_pos = target.pos()

            if self._item_start_points is not None:
                # Points-based item (polygon/freehand)
                new_points = list(target.item_data.points)
                if self._item_start_points != new_points or self._item_start_pos != new_pos:
                    cmd = ResizePointsItemCommand(
                        target,
                        self._item_start_pos, QPointF(new_pos),
                        self._item_start_points, new_points,
                        (self._item_start_rect.width(), self._item_start_rect.height()),
                        (target.item_data.width, target.item_data.height),
                    )
                    self.canvas.push_command(cmd)
            else:
                new_rect = target.rect() if hasattr(target, 'rect') else QRectF()
                if self._item_start_pos != new_pos or self._item_start_rect != new_rect:
                    # For groups, wrap group + child resize/moves in a macro
                    has_children = self._is_group_item(target) and self._group_child_starts
                    if has_children:
                        self.canvas.begin_macro("Resize Group")
                    cmd = ResizeItemCommand(
                        target, self._item_start_rect, new_rect,
                        self._item_start_pos, new_pos
                    )
                    self.canvas.push_command(cmd)
                    if has_children:
                        for child, start_pos, start_rect in self._group_child_starts:
                            child_new_pos = child.pos()
                            if start_pos != child_new_pos:
                                move_cmd = MoveItemCommand(child, start_pos, child_new_pos)
                                self.canvas.push_command(move_cmd)
                            if hasattr(child, 'rect'):
                                child_new_rect = child.rect()
                                if start_rect != child_new_rect:
                                    resize_cmd = ResizeItemCommand(
                                        child, QRectF(0, 0, start_rect.width(), start_rect.height()),
                                        child_new_rect, start_pos, child_new_pos
                                    )
                                    self.canvas.push_command(resize_cmd)
                        self.canvas.end_macro()

            self._resizing = False
            self._active_handle = None
            self._item_start_points = None
            self._group_child_starts.clear()
            self._handle_group.update_positions()

        elif self._rotating and self._handle_group and self._handle_group.target:
            target = self._handle_group.target
            new_rotation = target.rotation()
            has_children = self._is_group_item(target) and self._rotate_child_starts
            if self._start_rotation != new_rotation:
                if has_children:
                    self.canvas.begin_macro("Rotate Group")
                cmd = RotateItemCommand(target, self._start_rotation, new_rotation)
                self.canvas.push_command(cmd)
                if has_children:
                    for child, start_pos, start_rot in self._rotate_child_starts:
                        child_new_pos = child.pos()
                        child_new_rot = child.rotation()
                        if start_pos != child_new_pos:
                            move_cmd = MoveItemCommand(child, start_pos, child_new_pos)
                            self.canvas.push_command(move_cmd)
                        if start_rot != child_new_rot:
                            rot_cmd = RotateItemCommand(child, start_rot, child_new_rot)
                            self.canvas.push_command(rot_cmd)
                    self.canvas.end_macro()
            # Update group bounds after rotation
            if has_children and scene:
                target.update_bounds_from_children(scene)
            self._rotating = False
            self._active_handle = None
            self._rotate_child_starts.clear()
            self._handle_group.update_positions()

        elif self._rubber_band_active and scene:
            self._finish_rubber_band(scene)

    def mouse_double_click(self, event):
        scene = self.canvas.get_scene()
        if not scene:
            return

        pos = event.scenePos()
        item = scene.itemAt(pos, self.canvas.get_view().transform())

        # Skip handles
        if item and isinstance(item, (ResizeHandle, RotateHandle, VertexHandle)):
            return

        from app.canvas.canvas_items import PublisherPolygonItem
        if item and isinstance(item, PublisherPolygonItem):
            # Don't enter vertex mode for grouped polygons
            if self._find_parent_group(scene, item):
                return
            self._enter_vertex_mode(item)
        elif self._vertex_editing:
            self._exit_vertex_mode()

    # --- Context menu ---

    def context_menu(self, event):
        scene = self.canvas.get_scene()
        if not scene:
            return

        # Exit vertex mode on right-click
        if self._vertex_editing:
            self._exit_vertex_mode()

        pos = event.scenePos()
        # If right-clicking an unselected item, select it
        item = scene.itemAt(pos, self.canvas.get_view().transform())
        while item and isinstance(item, (ResizeHandle, RotateHandle, VertexHandle)):
            item = None
            break
        if item and hasattr(item, 'item_data'):
            # Redirect group children to their parent group
            if not self._is_group_item(item):
                parent_group = self._find_parent_group(scene, item)
                if parent_group:
                    item = parent_group
            if not item.isSelected():
                scene.clearSelection()
                item.setSelected(True)

        from app.canvas.canvas_items import PublisherGroupItem

        selected = [
            i for i in scene.selectedItems()
            if hasattr(i, 'item_data')
        ]

        mw = self.canvas._mw
        menu = QMenu()

        if selected:
            menu.addAction("Cut", mw._edit_cut)
            menu.addAction("Copy", mw._edit_copy)
        menu.addAction("Paste", mw._edit_paste)
        if selected:
            menu.addAction("Delete", mw._edit_delete)

        # Group / Ungroup
        if selected:
            menu.addSeparator()
            if len(selected) == 1 and isinstance(selected[0], PublisherGroupItem):
                menu.addAction("Ungroup", lambda: self._ungroup(scene, selected[0]))
            elif len(selected) >= 2:
                ungrouped = [
                    item for item in selected
                    if not isinstance(item, PublisherGroupItem)
                    and self._find_parent_group(scene, item) is None
                ]
                if len(ungrouped) >= 2:
                    menu.addAction("Group", lambda: self._group(scene, ungrouped))

        menu.exec(event.screenPos())

    def _group(self, scene, items):
        from app.commands.group_commands import GroupItemsCommand
        cmd = GroupItemsCommand(scene, items)
        self.canvas.push_command(cmd)
        # Select the new group
        scene.clearSelection()
        cmd.group_item.setSelected(True)
        if self._handle_group:
            self._handle_group.detach()

    def _ungroup(self, scene, group_item):
        from app.commands.group_commands import UngroupItemsCommand
        cmd = UngroupItemsCommand(scene, group_item)
        self.canvas.push_command(cmd)
        if self._handle_group:
            self._handle_group.detach()

    # --- Rubber band ---

    def _update_rubber_band(self, pos: QPointF):
        """Draw/update the rubber band selection rectangle."""
        scene = self.canvas.get_scene()
        if not scene:
            return

        rect = QRectF(self._rubber_band_origin, pos).normalized()

        if self._rubber_band_rect is None:
            self._rubber_band_rect = QGraphicsRectItem(rect)
            self._rubber_band_rect.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine))
            self._rubber_band_rect.setBrush(QBrush(QColor(0, 120, 215, 30)))
            self._rubber_band_rect.setZValue(999)
            scene.addItem(self._rubber_band_rect)
        else:
            self._rubber_band_rect.setRect(rect)

    def _finish_rubber_band(self, scene):
        """Select all publisher items within the rubber band rectangle.

        If any selected child belongs to a group, select the group instead
        and deselect the individual children.
        """
        from app.canvas.canvas_items import PublisherGroupItem

        if self._rubber_band_rect:
            rect = self._rubber_band_rect.rect()
            # Only select if the rect has some size (not just a click)
            if rect.width() > 2 and rect.height() > 2:
                if not self._rubber_band_additive:
                    scene.clearSelection()
                for item in scene.get_publisher_items():
                    if isinstance(item, PublisherGroupItem):
                        continue  # Don't directly select groups via rubber band
                    if not item.item_data.locked and rect.intersects(item.sceneBoundingRect()):
                        item.setSelected(True)

                # Consolidate: if a child of a group was selected, select the group instead
                selected = list(scene.selectedItems())
                groups_to_select = set()
                children_to_deselect = set()
                for item in selected:
                    if hasattr(item, 'item_data') and not isinstance(item, PublisherGroupItem):
                        parent = self._find_parent_group(scene, item)
                        if parent:
                            groups_to_select.add(parent)
                            children_to_deselect.add(item)

                for child in children_to_deselect:
                    child.setSelected(False)
                for group in groups_to_select:
                    group.setSelected(True)

                selected = [i for i in scene.selectedItems() if hasattr(i, 'item_data')]
                if len(selected) == 1 and self._handle_group:
                    self._handle_group.attach(selected[0])
                elif self._handle_group:
                    self._handle_group.detach()

        self._clear_rubber_band()
        self._rubber_band_active = False

    def _clear_rubber_band(self):
        if self._rubber_band_rect and self._rubber_band_rect.scene():
            self._rubber_band_rect.scene().removeItem(self._rubber_band_rect)
        self._rubber_band_rect = None
        self._rubber_band_active = False

    # --- Resize / Rotate ---

    def _do_resize(self, pos: QPointF):
        target = self._handle_group.target
        if not target:
            return

        ht = self._active_handle
        dx = pos.x() - self._drag_start.x()
        dy = pos.y() - self._drag_start.y()

        old_rect = self._item_start_rect
        old_pos = self._item_start_pos
        new_x = old_pos.x()
        new_y = old_pos.y()
        new_w = old_rect.width()
        new_h = old_rect.height()

        if ht in (HandleType.TOP_LEFT, HandleType.MIDDLE_LEFT, HandleType.BOTTOM_LEFT):
            new_x = old_pos.x() + dx
            new_w = old_rect.width() - dx
        if ht in (HandleType.TOP_RIGHT, HandleType.MIDDLE_RIGHT, HandleType.BOTTOM_RIGHT):
            new_w = old_rect.width() + dx
        if ht in (HandleType.TOP_LEFT, HandleType.TOP_CENTER, HandleType.TOP_RIGHT):
            new_y = old_pos.y() + dy
            new_h = old_rect.height() - dy
        if ht in (HandleType.BOTTOM_LEFT, HandleType.BOTTOM_CENTER, HandleType.BOTTOM_RIGHT):
            new_h = old_rect.height() + dy

        # Enforce minimum size
        min_size = 10
        if new_w < min_size:
            new_w = min_size
            if ht in (HandleType.TOP_LEFT, HandleType.MIDDLE_LEFT, HandleType.BOTTOM_LEFT):
                new_x = old_pos.x() + old_rect.width() - min_size
        if new_h < min_size:
            new_h = min_size
            if ht in (HandleType.TOP_LEFT, HandleType.TOP_CENTER, HandleType.TOP_RIGHT):
                new_y = old_pos.y() + old_rect.height() - min_size

        target.setPos(new_x, new_y)

        if self._item_start_points is not None:
            # Scale points for polygon/freehand
            old_w = old_rect.width()
            old_h = old_rect.height()
            sx = new_w / old_w if old_w > 0 else 1.0
            sy = new_h / old_h if old_h > 0 else 1.0
            new_points = [(px * sx, py * sy) for px, py in self._item_start_points]
            target.item_data.points = new_points
            target.item_data.x = new_x
            target.item_data.y = new_y
            target.item_data.width = new_w
            target.item_data.height = new_h
            # Rebuild the visual directly (faster than sync_from_data)
            if hasattr(target, 'setPolygon'):
                target.setPolygon(QPolygonF([QPointF(x, y) for x, y in new_points]))
            elif hasattr(target, '_rebuild_path'):
                target._rebuild_path()
        elif hasattr(target, 'setRect'):
            target.setRect(QRectF(0, 0, new_w, new_h))
            if hasattr(target, 'item_data'):
                target.item_data.x = new_x
                target.item_data.y = new_y
                target.item_data.width = new_w
                target.item_data.height = new_h
        else:
            return

        # For groups, proportionally scale and reposition children
        if self._is_group_item(target) and self._group_child_starts:
            old_gw = self._item_start_rect.width()
            old_gh = self._item_start_rect.height()
            old_gx = self._item_start_pos.x()
            old_gy = self._item_start_pos.y()
            sx = new_w / old_gw if old_gw > 0 else 1.0
            sy = new_h / old_gh if old_gh > 0 else 1.0
            for child, start_pos, start_rect in self._group_child_starts:
                # Scale position relative to group origin
                rel_x = start_pos.x() - old_gx
                rel_y = start_pos.y() - old_gy
                child.setPos(new_x + rel_x * sx, new_y + rel_y * sy)
                child.item_data.x = child.pos().x()
                child.item_data.y = child.pos().y()
                # Scale size if item has a rect
                if hasattr(child, 'setRect'):
                    cw = start_rect.width() * sx
                    ch = start_rect.height() * sy
                    child.setRect(QRectF(0, 0, max(cw, 1), max(ch, 1)))
                    child.item_data.width = max(cw, 1)
                    child.item_data.height = max(ch, 1)

        self._handle_group.update_positions()

    def _do_rotate(self, pos: QPointF):
        target = self._handle_group.target
        if not target:
            return

        center = target.mapToScene(target.boundingRect().center())
        angle_start = math.atan2(
            self._drag_start.y() - center.y(),
            self._drag_start.x() - center.x()
        )
        angle_now = math.atan2(
            pos.y() - center.y(),
            pos.x() - center.x()
        )
        delta_angle = math.degrees(angle_now - angle_start)
        new_rotation = self._start_rotation + delta_angle

        target.setRotation(new_rotation)
        if hasattr(target, 'item_data'):
            target.item_data.rotation = new_rotation

        # For groups, rotate each child around the group center
        if self._is_group_item(target) and self._rotate_child_starts:
            delta_rad = math.radians(delta_angle)
            cos_a = math.cos(delta_rad)
            sin_a = math.sin(delta_rad)
            gc = self._rotate_group_center
            for child, start_pos, start_rot in self._rotate_child_starts:
                # Get the child's center in scene coords at start
                child_br = child.boundingRect()
                child_center_local = child_br.center()
                # Start position is top-left; compute scene center
                cx = start_pos.x() + child_center_local.x()
                cy = start_pos.y() + child_center_local.y()
                # Rotate this center point around the group center
                dx = cx - gc.x()
                dy = cy - gc.y()
                new_cx = gc.x() + dx * cos_a - dy * sin_a
                new_cy = gc.y() + dx * sin_a + dy * cos_a
                # Convert back to top-left position
                new_x = new_cx - child_center_local.x()
                new_y = new_cy - child_center_local.y()
                child.setPos(new_x, new_y)
                child.item_data.x = new_x
                child.item_data.y = new_y
                # Also rotate the child itself
                child.setRotation(start_rot + delta_angle)
                child.item_data.rotation = start_rot + delta_angle

        self._handle_group.update_positions()

    # --- Vertex editing ---

    def _enter_vertex_mode(self, item):
        # Clean up any existing vertex handles first (prevents orphaned dots
        # when double-clicking a polygon while already in vertex mode)
        if self._vertex_handles:
            self._vertex_handles.detach()
            self._vertex_handles = None
        self._vertex_editing = True
        self._vertex_drag_index = -1
        self._vertex_start_state = None
        if self._handle_group:
            self._handle_group.detach()
        scene = self.canvas.get_scene()
        if scene:
            self._vertex_handles = VertexHandleGroup(scene)
            self._vertex_handles.attach(item)

    def _exit_vertex_mode(self):
        self._vertex_editing = False
        self._vertex_drag_index = -1
        self._vertex_start_state = None
        target = None
        if self._vertex_handles:
            target = self._vertex_handles.target
            self._vertex_handles.detach()
            self._vertex_handles = None
        # Re-show selection handles
        if target and target.isSelected() and self._handle_group:
            self._handle_group.attach(target)

    def _do_vertex_drag(self, pos: QPointF):
        target = self._vertex_handles.target
        if not target:
            return
        idx = self._vertex_drag_index
        # Convert scene position to item local coords
        local_pos = target.mapFromScene(pos)
        target.item_data.points[idx] = (local_pos.x(), local_pos.y())
        # Rebuild polygon visual
        target.setPolygon(QPolygonF(
            [QPointF(x, y) for x, y in target.item_data.points]
        ))
        self._vertex_handles.update_positions()

    def _finish_vertex_drag(self):
        target = self._vertex_handles.target
        if not target or self._vertex_start_state is None:
            self._vertex_drag_index = -1
            return

        old_x, old_y, old_w, old_h, old_points = self._vertex_start_state
        current_points = target.item_data.points

        # Normalize: shift all points so minimum is at (0,0) and adjust position
        if current_points:
            xs = [p[0] for p in current_points]
            ys = [p[1] for p in current_points]
            min_x, min_y = min(xs), min(ys)
            new_points = [(px - min_x, py - min_y) for px, py in current_points]
            new_x = target.pos().x() + min_x
            new_y = target.pos().y() + min_y
            new_w = max(xs) - min_x
            new_h = max(ys) - min_y
        else:
            new_points = list(current_points)
            new_x, new_y = target.pos().x(), target.pos().y()
            new_w, new_h = 0, 0

        # Apply normalized state
        d = target.item_data
        d.points = new_points
        d.x = new_x
        d.y = new_y
        d.width = new_w
        d.height = new_h
        target.sync_from_data()

        # Create undo command
        old_state = (old_x, old_y, old_w, old_h, old_points)
        new_state = (new_x, new_y, new_w, new_h, list(new_points))
        if old_state != new_state:
            cmd = EditVertexCommand(target, old_state, new_state)
            self.canvas.push_command(cmd)

        self._vertex_drag_index = -1
        self._vertex_start_state = None
        self._vertex_handles.update_positions()

    # --- Keyboard ---

    def key_press(self, event):
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self._delete_selected()
        elif event.key() == Qt.Key.Key_Escape:
            if self._vertex_editing:
                self._exit_vertex_mode()
                return
            scene = self.canvas.get_scene()
            if scene:
                scene.clearSelection()
            if self._handle_group:
                self._handle_group.detach()

    def _delete_selected(self):
        if self._vertex_editing:
            self._exit_vertex_mode()
        scene = self.canvas.get_scene()
        if not scene:
            return
        from app.commands.item_commands import RemoveItemCommand
        from app.canvas.canvas_items import PublisherGroupItem

        items_to_remove = []
        for item in scene.selectedItems():
            if not hasattr(item, 'item_data'):
                continue
            items_to_remove.append(item)
            # If deleting a group, also delete its children
            if isinstance(item, PublisherGroupItem):
                for child in item.get_child_items(scene):
                    if child not in items_to_remove:
                        items_to_remove.append(child)

        if items_to_remove:
            use_macro = len(items_to_remove) > 1
            if use_macro:
                self.canvas.begin_macro("Delete Items")
            for item in items_to_remove:
                cmd = RemoveItemCommand(scene, item)
                self.canvas.push_command(cmd)
            if use_macro:
                self.canvas.end_macro()

        if self._handle_group:
            self._handle_group.detach()

    @property
    def cursor(self):
        return Qt.CursorShape.ArrowCursor
