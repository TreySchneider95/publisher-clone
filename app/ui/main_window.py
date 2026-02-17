import copy

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFileDialog, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt, QPointF, QRect
from PyQt6.QtGui import QPainter, QColor, QPen

from app.canvas.canvas_scene import PublisherScene
from app.canvas.canvas_view import PublisherView
from app.canvas.canvas_items import create_item_from_data, PublisherItemMixin
from app.models.enums import PageSizePreset, ToolType
from app.models.document import Document, Page
from app.models.items import _new_id
from app.models.serialization import save_to_file, load_from_file, item_data_to_dict, dict_to_item_data
from app.models.shape_library import ShapeLibrary
from app.tools.tool_manager import ToolManager
from app.tools.select_tool import SelectTool
from app.tools.shape_tool import ShapeTool
from app.tools.text_tool import TextTool
from app.tools.image_tool import ImageTool
from app.tools.freehand_tool import FreehandTool
from app.commands.command_stack import CommandStack
from app.ui.toolbar import ToolBar
from app.ui.menu_bar import PublisherMenuBar
from app.ui.properties_panel import PropertiesPanel
from app.ui.rulers import HorizontalRuler, VerticalRuler, RULER_THICKNESS
from app.ui.layers_panel import LayersPanel
from app.ui.pages_panel import PagesPanel
from app.ui.status_bar import PublisherStatusBar


class _VerticalTab(QPushButton):
    """Thin vertical tab on the left edge for a collapsed dock panel."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._text = text
        self.setFixedWidth(20)
        self.setMinimumHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Show {text}")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(215, 215, 215) if self.underMouse() else QColor(230, 230, 230)
        p.fillRect(self.rect(), bg)
        p.setPen(QPen(QColor(180, 180, 180), 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        p.setPen(QColor(60, 60, 60))
        p.save()
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(-90)
        r = QRect(-self.height() // 2, -self.width() // 2,
                   self.height(), self.width())
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self._text)
        p.restore()
        p.end()


class _HorizontalTab(QPushButton):
    """Thin horizontal tab on the bottom edge for a collapsed dock panel."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._text = text
        self.setFixedHeight(20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Show {text}")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(215, 215, 215) if self.underMouse() else QColor(230, 230, 230)
        p.fillRect(self.rect(), bg)
        p.setPen(QPen(QColor(180, 180, 180), 1))
        p.drawLine(0, 0, self.width(), 0)
        p.setPen(QColor(60, 60, 60))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)
        p.end()


class CanvasInterface:
    """Interface passed to tools so they can interact with the canvas
    without knowing about MainWindow internals."""

    def __init__(self, main_window: 'MainWindow'):
        self._mw = main_window

    def get_scene(self) -> PublisherScene | None:
        return self._mw.current_scene

    def get_view(self) -> PublisherView:
        return self._mw.view

    def push_command(self, cmd):
        self._mw.command_stack.push(cmd)
        self._mw.document.mark_dirty()

    def get_document(self):
        return self._mw.document

    def begin_macro(self, text: str):
        self._mw.command_stack.stack.beginMacro(text)

    def end_macro(self):
        self._mw.command_stack.stack.endMacro()

    def switch_to_select(self):
        self._mw._on_tool_selected(ToolType.SELECT)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Publisher Clone")
        self.setMinimumSize(1024, 768)
        self.resize(1400, 900)

        # Clipboard for copy/paste
        self._clipboard: list = []
        self._in_selection_change = False

        # Data model
        self.document = Document()
        self.command_stack = CommandStack()

        # Scenes: one per page
        self.scenes: list[PublisherScene] = []
        self.current_page_index = 0
        self.current_scene: PublisherScene | None = None

        # Canvas interface for tools
        self.canvas_interface = CanvasInterface(self)

        # Tool manager
        self.tool_manager = ToolManager(self)

        self._setup_ui()
        self._setup_tools()
        self._create_initial_page()

        # Refresh current page thumbnail on every content change (push/undo/redo)
        self.command_stack.stack.indexChanged.connect(self._on_stack_index_changed)

    def _setup_ui(self):
        # Menu bar
        self.menu_bar = PublisherMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self._connect_menu_signals()

        # Toolbar
        self.toolbar = ToolBar()
        self.addToolBar(self.toolbar)
        self.toolbar.tool_selected.connect(self._on_tool_selected)

        # Custom shape library
        self.shape_library = ShapeLibrary()
        self.toolbar.set_shape_library(self.shape_library)
        self.toolbar.save_custom_requested.connect(self._save_custom_shape)
        self.toolbar.load_custom_requested.connect(self._place_custom_shape)
        self.toolbar.open_library_folder_requested.connect(self._open_library_folder)

        # Pages panel (left dock)
        self.pages_panel = PagesPanel()
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.pages_panel)
        self.pages_panel.page_selected.connect(self._on_page_selected)
        self.pages_panel.add_page_requested.connect(self._on_add_page)
        self.pages_panel.delete_page_requested.connect(self._on_delete_page)
        self.pages_panel.duplicate_page_requested.connect(self._on_duplicate_page)
        self.pages_panel.page_size_requested.connect(self._on_page_size)

        # Central widget: edge tabs + rulers + canvas
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        inner = QHBoxLayout()
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # Pages restore tab (left edge, hidden by default)
        self._pages_tab = _VerticalTab("Pages")
        self._pages_tab.hide()
        self._pages_tab.clicked.connect(lambda: self.pages_panel.show())
        inner.addWidget(self._pages_tab)

        # Grid with rulers + canvas
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        corner = QWidget()
        corner.setFixedSize(RULER_THICKNESS, RULER_THICKNESS)
        corner.setStyleSheet("background-color: #f0f0f0;")
        grid.addWidget(corner, 0, 0)

        self.h_ruler = HorizontalRuler()
        grid.addWidget(self.h_ruler, 0, 1)

        self.v_ruler = VerticalRuler()
        grid.addWidget(self.v_ruler, 1, 0)

        self.view = PublisherView()
        grid.addWidget(self.view, 1, 1)

        inner.addWidget(grid_widget)
        outer.addLayout(inner)

        # Layers restore tab (bottom edge, hidden by default)
        self._layers_tab = _HorizontalTab("Layers")
        self._layers_tab.hide()
        self._layers_tab.clicked.connect(lambda: self.layers_panel.show())
        outer.addWidget(self._layers_tab)

        self.setCentralWidget(wrapper)

        self.h_ruler.set_view(self.view)
        self.v_ruler.set_view(self.view)

        self.view.horizontalScrollBar().valueChanged.connect(self._update_rulers)
        self.view.verticalScrollBar().valueChanged.connect(self._update_rulers)
        self.view.zoom_changed.connect(lambda z: self._update_rulers())
        self.view.cursor_moved.connect(self._on_cursor_moved)

        self.toolbar.zoom_in_action.triggered.connect(lambda: self.view.zoom_in())
        self.toolbar.zoom_out_action.triggered.connect(lambda: self.view.zoom_out())
        self.toolbar.zoom_fit_action.triggered.connect(lambda: self.view.zoom_fit())

        # Properties panel (right dock) — hidden until something is selected
        self.properties_panel = PropertiesPanel()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_panel)
        self.properties_panel.setVisible(False)

        # Layers panel (bottom dock)
        self.layers_panel = LayersPanel()
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.layers_panel)
        self.layers_panel.item_selected.connect(self._on_layer_item_selected)

        # Status bar
        self.status_bar_widget = PublisherStatusBar()
        self.setStatusBar(self.status_bar_widget)
        self.view.zoom_changed.connect(self.status_bar_widget.update_zoom)
        self.status_bar_widget.unit_changed.connect(self._on_unit_changed)

        # Dock panel collapse/restore tabs
        self.pages_panel.visibilityChanged.connect(
            lambda vis: self._pages_tab.setVisible(not vis)
        )
        self.layers_panel.visibilityChanged.connect(
            lambda vis: self._layers_tab.setVisible(not vis)
        )

        # Add panel toggle actions to View menu
        pages_toggle = self.pages_panel.toggleViewAction()
        pages_toggle.setText("Show &Pages Panel")
        self.menu_bar.view_menu.addAction(pages_toggle)
        layers_toggle = self.layers_panel.toggleViewAction()
        layers_toggle.setText("Show &Layers Panel")
        self.menu_bar.view_menu.addAction(layers_toggle)

    def _connect_menu_signals(self):
        mb = self.menu_bar
        # File
        mb.new_requested.connect(self._file_new)
        mb.open_requested.connect(self._file_open)
        mb.save_requested.connect(self._file_save)
        mb.save_as_requested.connect(self._file_save_as)
        mb.export_pdf_requested.connect(self._export_pdf)
        mb.export_png_requested.connect(self._export_png)
        mb.export_svg_requested.connect(self._export_svg)
        # Edit
        mb.undo_requested.connect(lambda: self.command_stack.undo())
        mb.redo_requested.connect(lambda: self.command_stack.redo())
        mb.cut_requested.connect(self._edit_cut)
        mb.copy_requested.connect(self._edit_copy)
        mb.paste_requested.connect(self._edit_paste)
        mb.delete_requested.connect(self._edit_delete)
        mb.select_all_requested.connect(self._edit_select_all)
        mb.preferences_requested.connect(self._show_preferences)
        # View
        mb.zoom_in_requested.connect(lambda: self.view.zoom_in())
        mb.zoom_out_requested.connect(lambda: self.view.zoom_out())
        mb.zoom_fit_requested.connect(lambda: self.view.zoom_fit())
        mb.toggle_grid_requested.connect(self._toggle_grid)
        mb.toggle_rulers_requested.connect(self._toggle_rulers)
        mb.snap_to_grid_requested.connect(self._toggle_snap)
        # Insert (switch to appropriate tool)
        mb.insert_text_requested.connect(lambda: self.tool_manager.set_tool(ToolType.TEXT))
        mb.insert_image_requested.connect(lambda: self.tool_manager.set_tool(ToolType.IMAGE))
        mb.insert_rect_requested.connect(lambda: self.tool_manager.set_tool(ToolType.RECT))
        mb.insert_ellipse_requested.connect(lambda: self.tool_manager.set_tool(ToolType.ELLIPSE))
        # Format / Align
        mb.align_left_requested.connect(lambda: self._align('left'))
        mb.align_right_requested.connect(lambda: self._align('right'))
        mb.align_top_requested.connect(lambda: self._align('top'))
        mb.align_bottom_requested.connect(lambda: self._align('bottom'))
        mb.align_center_h_requested.connect(lambda: self._align('center_h'))
        mb.align_center_v_requested.connect(lambda: self._align('center_v'))

    def _setup_tools(self):
        ci = self.canvas_interface
        self.tool_manager.register_tool(ToolType.SELECT, SelectTool(ci))
        self.tool_manager.register_tool(ToolType.TEXT, TextTool(ci))
        self.tool_manager.register_tool(ToolType.RECT, ShapeTool(ci, ToolType.RECT))
        self.tool_manager.register_tool(ToolType.ELLIPSE, ShapeTool(ci, ToolType.ELLIPSE))
        self.tool_manager.register_tool(ToolType.LINE, ShapeTool(ci, ToolType.LINE))
        self.tool_manager.register_tool(ToolType.ARROW, ShapeTool(ci, ToolType.ARROW))
        self.tool_manager.register_tool(ToolType.POLYGON, ShapeTool(ci, ToolType.POLYGON))
        self.tool_manager.register_tool(ToolType.FREEHAND, FreehandTool(ci))
        self.tool_manager.register_tool(ToolType.IMAGE, ImageTool(ci))
        self.tool_manager.set_tool(ToolType.SELECT)

    # --- Tool / UI callbacks ---

    def _on_tool_selected(self, tool_type: ToolType):
        self.tool_manager.set_tool(tool_type)
        self.toolbar.set_active_tool(tool_type)

    def _update_rulers(self):
        self.h_ruler.update()
        self.v_ruler.update()

    def _on_cursor_moved(self, pos: QPointF):
        self.h_ruler.set_cursor_pos(pos.x())
        self.v_ruler.set_cursor_pos(pos.y())
        if hasattr(self, 'status_bar_widget'):
            self.status_bar_widget.update_cursor(pos)

    def _show_properties_panel(self):
        """Show the properties panel docked on the right (never floating)."""
        if not self.properties_panel.isVisible():
            self.properties_panel.setFloating(False)
            self.properties_panel.show()

    def _on_selection_changed(self):
        if self._in_selection_change:
            return
        self._in_selection_change = True
        try:
            scene = self.current_scene
            if not scene:
                self.properties_panel.hide()
                return
            selected = scene.selectedItems()
            # Refresh layers first, then highlight the selected row
            self.layers_panel.refresh()
            if selected:
                item = selected[0]
                if hasattr(item, 'item_data'):
                    self.properties_panel.update_from_item(item)
                    self._show_properties_panel()
                    self.layers_panel.select_item(item)
                else:
                    self.properties_panel.hide()
            else:
                self.properties_panel.hide()
        finally:
            self._in_selection_change = False

    def _on_layer_item_selected(self, item):
        if self._in_selection_change:
            return
        if self.current_scene and item:
            self._in_selection_change = True
            try:
                self.current_scene.clearSelection()
                item.setSelected(True)
                self.properties_panel.update_from_item(item)
                self._show_properties_panel()
            finally:
                self._in_selection_change = False

    # --- Page operations ---

    def _on_page_selected(self, index: int):
        if index != self.current_page_index:
            self.switch_page(index)

    def _on_add_page(self):
        from app.commands.page_commands import AddPageCommand
        cmd = AddPageCommand(self, self.current_page_index + 1)
        self.command_stack.push(cmd)

    def _on_delete_page(self, index: int):
        if len(self.scenes) <= 1:
            return
        from app.commands.page_commands import RemovePageCommand
        cmd = RemovePageCommand(self, index)
        self.command_stack.push(cmd)

    def _on_duplicate_page(self, index: int):
        from app.models.items import GroupItemData
        page, scene = self.add_page(index + 1)
        source_scene = self.scenes[index]
        # Build old->new ID map for group child_ids remapping
        old_to_new = {}
        for src_item in source_scene.get_publisher_items():
            old_to_new[src_item.item_data.id] = _new_id()
        for src_item in source_scene.get_publisher_items():
            new_data = copy.deepcopy(src_item.item_data)
            new_data.id = old_to_new[src_item.item_data.id]
            if isinstance(new_data, GroupItemData):
                new_data.child_ids = [
                    old_to_new.get(cid, cid) for cid in new_data.child_ids
                ]
            new_item = create_item_from_data(new_data)
            scene.addItem(new_item)
        # Update group bounds
        from app.canvas.canvas_items import PublisherGroupItem
        for item in scene.items():
            if isinstance(item, PublisherGroupItem):
                item.update_bounds_from_children(scene)
        self.switch_page(index + 1)
        self._refresh_pages_panel()

    def _on_page_size(self, index: int):
        from app.ui.page_size_dialog import PageSizeDialog
        page = self.document.pages[index]
        dlg = PageSizeDialog(page, self.document.unit, self)
        if dlg.exec() == PageSizeDialog.DialogCode.Accepted:
            w, h = dlg.result_size_pt()
            page.width_pt = w
            page.height_pt = h
            scene = self.scenes[index]
            scene.page_width = w
            scene.page_height = h
            scene._update_scene_rect()
            scene.update()
            self._refresh_pages_panel()
            self.document.mark_dirty()

    def _refresh_pages_panel(self):
        self.pages_panel.set_scenes(self.scenes, self.current_page_index)

    def _on_stack_index_changed(self):
        """Refresh the current page thumbnail after any command push/undo/redo."""
        if self.current_scene is not None and 0 <= self.current_page_index < len(self.scenes):
            self.pages_panel.refresh_thumbnail(self.current_page_index, self.current_scene)

    # --- View toggles ---

    def _toggle_grid(self):
        if self.current_scene:
            visible = self.menu_bar.grid_action.isChecked()
            self.current_scene.set_grid_visible(visible)

    def _toggle_rulers(self):
        visible = self.menu_bar.rulers_action.isChecked()
        self.h_ruler.setVisible(visible)
        self.v_ruler.setVisible(visible)

    def _toggle_snap(self):
        if self.current_scene:
            self.current_scene.snap_to_grid = self.menu_bar.snap_action.isChecked()

    def _show_preferences(self):
        from app.ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.exec()

    def _align(self, alignment: str):
        if self.current_scene:
            self.current_scene.align_items(alignment)

    def _on_unit_changed(self, unit):
        self.document.unit = unit
        self.h_ruler.set_unit(unit)
        self.v_ruler.set_unit(unit)
        self.properties_panel.set_unit(unit)

    def _update_status_bar(self):
        self.status_bar_widget.update_page(
            self.current_page_index, len(self.scenes)
        )

    # --- Edit operations ---

    def _edit_cut(self):
        self._edit_copy()
        self._edit_delete()

    def _edit_copy(self):
        if not self.current_scene:
            return
        from app.canvas.canvas_items import PublisherGroupItem
        self._clipboard.clear()
        selected = [i for i in self.current_scene.selectedItems() if hasattr(i, 'item_data')]
        # When copying a group, also copy its children
        all_items = []
        for item in selected:
            all_items.append(item)
            if isinstance(item, PublisherGroupItem):
                for child in item.get_child_items(self.current_scene):
                    if child not in all_items:
                        all_items.append(child)
        for item in all_items:
            self._clipboard.append(copy.deepcopy(item.item_data))

    def _edit_paste(self):
        if not self.current_scene or not self._clipboard:
            return
        from app.commands.item_commands import AddItemCommand
        from app.models.items import GroupItemData
        # Build old->new ID map so group child_ids reference new IDs
        old_to_new = {}
        for data in self._clipboard:
            old_to_new[data.id] = _new_id()
        for data in self._clipboard:
            new_data = copy.deepcopy(data)
            new_data.id = old_to_new[data.id]
            new_data.x += 20
            new_data.y += 20
            # Remap child_ids for groups
            if isinstance(new_data, GroupItemData):
                new_data.child_ids = [
                    old_to_new.get(cid, cid) for cid in new_data.child_ids
                ]
            item = create_item_from_data(new_data)
            cmd = AddItemCommand(self.current_scene, item, "Paste Item")
            self.command_stack.push(cmd)

    def _edit_delete(self):
        if not self.current_scene:
            return
        from app.commands.item_commands import RemoveItemCommand
        from app.canvas.canvas_items import PublisherGroupItem
        items_to_remove = []
        for item in self.current_scene.selectedItems():
            if not hasattr(item, 'item_data'):
                continue
            items_to_remove.append(item)
            # If deleting a group, also delete its children
            if isinstance(item, PublisherGroupItem):
                for child in item.get_child_items(self.current_scene):
                    if child not in items_to_remove:
                        items_to_remove.append(child)
        if items_to_remove:
            use_macro = len(items_to_remove) > 1
            if use_macro:
                self.command_stack.stack.beginMacro("Delete Items")
            for item in items_to_remove:
                cmd = RemoveItemCommand(self.current_scene, item, "Delete Item")
                self.command_stack.push(cmd)
            if use_macro:
                self.command_stack.stack.endMacro()

    def _edit_select_all(self):
        if not self.current_scene:
            return
        for item in self.current_scene.get_publisher_items():
            item.setSelected(True)

    # --- Custom shape library ---

    def _save_custom_shape(self):
        if not self.current_scene:
            return
        from app.canvas.canvas_items import PublisherGroupItem
        selected = [
            item for item in self.current_scene.selectedItems()
            if hasattr(item, 'item_data')
        ]
        if not selected:
            QMessageBox.information(self, "No Selection", "Select one or more shapes first.")
            return

        # When saving a group, also include its children
        all_items = []
        for item in selected:
            all_items.append(item)
            if isinstance(item, PublisherGroupItem):
                for child in item.get_child_items(self.current_scene):
                    if child not in all_items:
                        all_items.append(child)

        # Sync and serialize
        items_dicts = []
        for item in all_items:
            item.sync_to_data()
            data = copy.deepcopy(item.item_data)
            items_dicts.append(item_data_to_dict(data))

        # Normalize positions so bounding box starts at (0,0)
        min_x = min(d['x'] for d in items_dicts)
        min_y = min(d['y'] for d in items_dicts)
        for d in items_dicts:
            d['x'] -= min_x
            d['y'] -= min_y

        # Assign z-values to preserve stacking order.
        # get_child_items returns children in scene top-to-bottom order,
        # so non-group items earlier in the list should get higher z-values.
        non_group = [d for d in items_dicts if d.get('item_type') != 'GROUP']
        z = float(len(non_group))
        for d in non_group:
            d['z_value'] = z
            z -= 1.0
        for d in items_dicts:
            if d.get('item_type') == 'GROUP':
                d['z_value'] = 0.0

        from app.ui.save_shape_dialog import SaveShapeDialog
        dlg = SaveShapeDialog(self.shape_library, self)
        if dlg.exec() == SaveShapeDialog.DialogCode.Accepted:
            try:
                self.shape_library.save_shape(dlg.folder_name(), dlg.shape_name(), items_dicts)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save shape: {e}")

    def _place_custom_shape(self, folder: str, name: str):
        if not self.current_scene:
            return
        try:
            items_dicts = self.shape_library.load_shape(folder, name)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load shape: {e}")
            return

        # Deserialize, assign new IDs, offset to view center
        from app.commands.shape_commands import PlaceCustomShapeCommand
        from app.models.items import GroupItemData
        view_center = self.view.mapToScene(self.view.viewport().rect().center())

        # First pass: build old->new ID map
        old_to_new = {}
        parsed_items = []
        for d in items_dicts:
            item_data = dict_to_item_data(d)
            if item_data:
                old_id = item_data.id
                new_id = _new_id()
                old_to_new[old_id] = new_id
                parsed_items.append(item_data)

        # Second pass: assign new IDs, remap group child_ids, offset positions
        graphics_items = []
        has_group = False
        for item_data in parsed_items:
            item_data.id = old_to_new[item_data.id]
            item_data.x += view_center.x()
            item_data.y += view_center.y()
            if isinstance(item_data, GroupItemData):
                has_group = True
                item_data.child_ids = [
                    old_to_new.get(cid, cid) for cid in item_data.child_ids
                ]
            graphics_items.append(create_item_from_data(item_data))

        if graphics_items:
            # Use beginMacro/endMacro so place + auto-group is one undo step
            self.command_stack.stack.beginMacro("Place Custom Shape")
            cmd = PlaceCustomShapeCommand(self.current_scene, graphics_items)
            self.command_stack.push(cmd)
            # Auto-group if 2+ non-group items and no existing group
            if len(graphics_items) >= 2 and not has_group:
                from app.commands.group_commands import GroupItemsCommand
                group_cmd = GroupItemsCommand(self.current_scene, graphics_items)
                self.command_stack.push(group_cmd)
            self.command_stack.stack.endMacro()
            # Update group bounds after placing
            from app.canvas.canvas_items import PublisherGroupItem
            for gi in graphics_items:
                if isinstance(gi, PublisherGroupItem):
                    gi.update_bounds_from_children(self.current_scene)
            self.document.mark_dirty()

    def _open_library_folder(self):
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices
        path = self.shape_library.base_path()
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    # --- File operations ---

    def _file_new(self):
        if not self._check_unsaved():
            return
        self.document = Document()
        self.command_stack.clear()
        self.scenes.clear()
        self.current_page_index = 0
        self.current_scene = None
        self._create_initial_page()
        self._update_title()

    def _file_open(self):
        if not self._check_unsaved():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "",
            "Publisher Documents (*.pubd);;All Files (*)"
        )
        if not path:
            return
        self._load_document(path)

    def _file_save(self):
        if self.document.file_path:
            self._save_document(self.document.file_path)
        else:
            self._file_save_as()

    def _file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Document", "",
            "Publisher Documents (*.pubd);;All Files (*)"
        )
        if not path:
            return
        if not path.endswith('.pubd'):
            path += '.pubd'
        self._save_document(path)

    def _save_document(self, path: str):
        try:
            save_to_file(path, self.document, self.scenes)
            self.document.file_path = path
            self.document.mark_clean()
            self._update_title()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save: {e}")

    def _load_document(self, path: str):
        try:
            doc, pages_items = load_from_file(path)
            doc.file_path = path

            self.document = doc
            self.command_stack.clear()
            self.scenes.clear()

            from app.canvas.canvas_items import PublisherGroupItem

            for i, page in enumerate(doc.pages):
                scene = PublisherScene(page.width_pt, page.height_pt)
                scene.set_tool_manager(self.tool_manager)
                scene.item_selection_changed.connect(self._on_selection_changed)
                self.scenes.append(scene)

                if i < len(pages_items):
                    for item_data in pages_items[i]:
                        item = create_item_from_data(item_data)
                        scene.addItem(item)
                    # Update group bounds after all items are added
                    for item in scene.items():
                        if isinstance(item, PublisherGroupItem):
                            item.update_bounds_from_children(scene)

            self.current_page_index = 0
            self.current_scene = self.scenes[0]
            self.view.setScene(self.current_scene)
            # Center on content or origin
            content_rect = self.current_scene.get_content_rect()
            self.view.centerOn(content_rect.center())
            self.layers_panel.set_scene(self.current_scene)
            self._refresh_pages_panel()
            self.document.mark_clean()
            self._update_title()

        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Failed to open: {e}")

    def _check_unsaved(self) -> bool:
        """Returns True if it's OK to proceed (no unsaved changes or user chose to)."""
        if not self.document.dirty:
            return True
        result = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Do you want to save first?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        if result == QMessageBox.StandardButton.Save:
            self._file_save()
            return not self.document.dirty
        elif result == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _update_title(self):
        name = self.document.file_path or "Untitled"
        dirty = " *" if self.document.dirty else ""
        self.setWindowTitle(f"Publisher Clone - {name}{dirty}")

    def closeEvent(self, event):
        if self._check_unsaved():
            event.accept()
        else:
            event.ignore()

    # --- Export stubs (filled in Phase 10) ---

    def _export_pdf(self):
        from app.export.pdf_exporter import export_pdf
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            if not path.endswith('.pdf'):
                path += '.pdf'
            export_pdf(path, self.scenes, self.document.pages)

    def _export_png(self):
        from app.export.image_exporter import export_images
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
        )
        if path:
            export_images(path, self.scenes, self.document.pages)

    def _export_svg(self):
        from app.export.svg_exporter import export_svg
        path, _ = QFileDialog.getSaveFileName(
            self, "Export SVG", "", "SVG Files (*.svg)"
        )
        if path:
            if not path.endswith('.svg'):
                path += '.svg'
            export_svg(path, self.scenes, self.document.pages)

    # --- Page/Scene management ---

    def _create_initial_page(self):
        page = self.document.pages[0]
        scene = PublisherScene(page.width_pt, page.height_pt)
        scene.set_tool_manager(self.tool_manager)
        scene.item_selection_changed.connect(self._on_selection_changed)
        self.scenes.append(scene)
        self.current_scene = scene
        self.view.setScene(scene)
        self.view.centerOn(0, 0)
        self.layers_panel.set_scene(scene)
        self._refresh_pages_panel()
        self._update_status_bar()

    def switch_page(self, index: int):
        if 0 <= index < len(self.scenes):
            self.current_page_index = index
            self.current_scene = self.scenes[index]
            self.view.setScene(self.current_scene)
            if self.tool_manager.active_tool:
                self.tool_manager.active_tool.deactivate()
                self.tool_manager.active_tool.activate()
            self._on_selection_changed()
            self.layers_panel.set_scene(self.current_scene)
            self._update_rulers()
            self._update_status_bar()

    def add_page(self, index: int = -1):
        page = self.document.add_page(index)
        scene = PublisherScene(page.width_pt, page.height_pt)
        scene.set_tool_manager(self.tool_manager)
        scene.item_selection_changed.connect(self._on_selection_changed)
        if index < 0:
            self.scenes.append(scene)
        else:
            self.scenes.insert(index, scene)
        return page, scene
