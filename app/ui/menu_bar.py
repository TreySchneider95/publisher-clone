"""Menu bar with File/Edit/View/Insert/Format/Help menus."""

from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence


class PublisherMenuBar(QMenuBar):
    """Application menu bar."""

    # File signals
    new_requested = pyqtSignal()
    open_requested = pyqtSignal()
    save_requested = pyqtSignal()
    save_as_requested = pyqtSignal()
    export_pdf_requested = pyqtSignal()
    export_png_requested = pyqtSignal()
    export_svg_requested = pyqtSignal()

    # Edit signals
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    cut_requested = pyqtSignal()
    copy_requested = pyqtSignal()
    paste_requested = pyqtSignal()
    delete_requested = pyqtSignal()
    select_all_requested = pyqtSignal()
    preferences_requested = pyqtSignal()

    # View signals
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_fit_requested = pyqtSignal()
    toggle_grid_requested = pyqtSignal()
    toggle_rulers_requested = pyqtSignal()
    snap_to_grid_requested = pyqtSignal()

    # Format signals
    align_left_requested = pyqtSignal()
    align_right_requested = pyqtSignal()
    align_top_requested = pyqtSignal()
    align_bottom_requested = pyqtSignal()
    align_center_h_requested = pyqtSignal()
    align_center_v_requested = pyqtSignal()

    # Insert signals
    insert_text_requested = pyqtSignal()
    insert_image_requested = pyqtSignal()
    insert_rect_requested = pyqtSignal()
    insert_ellipse_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_file_menu()
        self._build_edit_menu()
        self._build_view_menu()
        self._build_insert_menu()
        self._build_format_menu()
        self._build_help_menu()

    def _build_file_menu(self):
        menu = self.addMenu("&File")

        self.new_action = menu.addAction("&New")
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_requested.emit)

        self.open_action = menu.addAction("&Open...")
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_requested.emit)

        menu.addSeparator()

        self.save_action = menu.addAction("&Save")
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_requested.emit)

        self.save_as_action = menu.addAction("Save &As...")
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self.save_as_requested.emit)

        menu.addSeparator()

        export_menu = menu.addMenu("&Export")
        self.export_pdf_action = export_menu.addAction("Export as &PDF...")
        self.export_pdf_action.triggered.connect(self.export_pdf_requested.emit)
        self.export_png_action = export_menu.addAction("Export as P&NG/JPEG...")
        self.export_png_action.triggered.connect(self.export_png_requested.emit)
        self.export_svg_action = export_menu.addAction("Export as &SVG...")
        self.export_svg_action.triggered.connect(self.export_svg_requested.emit)

        menu.addSeparator()

        quit_action = menu.addAction("&Quit")
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(lambda: self.parent().close() if self.parent() else None)

    def _build_edit_menu(self):
        menu = self.addMenu("&Edit")

        self.undo_action = menu.addAction("&Undo")
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo_requested.emit)

        self.redo_action = menu.addAction("&Redo")
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo_requested.emit)

        menu.addSeparator()

        self.cut_action = menu.addAction("Cu&t")
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.cut_action.triggered.connect(self.cut_requested.emit)

        self.copy_action = menu.addAction("&Copy")
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.copy_requested.emit)

        self.paste_action = menu.addAction("&Paste")
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.paste_requested.emit)

        self.delete_action = menu.addAction("&Delete")
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.triggered.connect(self.delete_requested.emit)

        menu.addSeparator()

        self.select_all_action = menu.addAction("Select &All")
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.select_all_action.triggered.connect(self.select_all_requested.emit)

        menu.addSeparator()

        self.preferences_action = menu.addAction("&Preferences...")
        self.preferences_action.setShortcut("Ctrl+,")
        self.preferences_action.triggered.connect(self.preferences_requested.emit)

    def _build_view_menu(self):
        menu = self.addMenu("&View")

        self.zoom_in_action = menu.addAction("Zoom &In")
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.zoom_in_action.triggered.connect(self.zoom_in_requested.emit)

        self.zoom_out_action = menu.addAction("Zoom &Out")
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.zoom_out_action.triggered.connect(self.zoom_out_requested.emit)

        self.zoom_fit_action = menu.addAction("Zoom to &Fit")
        self.zoom_fit_action.setShortcut("Ctrl+0")
        self.zoom_fit_action.triggered.connect(self.zoom_fit_requested.emit)

        menu.addSeparator()

        self.grid_action = menu.addAction("Show &Grid")
        self.grid_action.setCheckable(True)
        self.grid_action.triggered.connect(self.toggle_grid_requested.emit)

        self.rulers_action = menu.addAction("Show &Rulers")
        self.rulers_action.setCheckable(True)
        self.rulers_action.setChecked(True)
        self.rulers_action.triggered.connect(self.toggle_rulers_requested.emit)

        menu.addSeparator()

        self.snap_action = menu.addAction("&Snap to Grid")
        self.snap_action.setCheckable(True)
        self.snap_action.triggered.connect(self.snap_to_grid_requested.emit)

        menu.addSeparator()
        # Panel toggles — actions are added by MainWindow using dock toggleViewAction()
        self.view_menu = menu

    def _build_insert_menu(self):
        menu = self.addMenu("&Insert")

        menu.addAction("&Text Box").triggered.connect(self.insert_text_requested.emit)
        menu.addAction("&Image...").triggered.connect(self.insert_image_requested.emit)
        menu.addSeparator()
        menu.addAction("&Rectangle").triggered.connect(self.insert_rect_requested.emit)
        menu.addAction("&Ellipse").triggered.connect(self.insert_ellipse_requested.emit)

    def _build_format_menu(self):
        self._format_menu = self.addMenu("F&ormat")

        align_menu = self._format_menu.addMenu("&Align")
        align_menu.addAction("Align &Left").triggered.connect(self.align_left_requested.emit)
        align_menu.addAction("Align &Right").triggered.connect(self.align_right_requested.emit)
        align_menu.addAction("Align &Top").triggered.connect(self.align_top_requested.emit)
        align_menu.addAction("Align &Bottom").triggered.connect(self.align_bottom_requested.emit)
        align_menu.addSeparator()
        align_menu.addAction("Center &Horizontally").triggered.connect(self.align_center_h_requested.emit)
        align_menu.addAction("Center &Vertically").triggered.connect(self.align_center_v_requested.emit)

    def _build_help_menu(self):
        menu = self.addMenu("&Help")
        about_action = menu.addAction("&About Publisher Clone")
        about_action.triggered.connect(self._show_about)

    def _show_about(self):
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                                     QTextEdit, QDialogButtonBox)
        from PyQt6.QtCore import Qt
        from app.version import VERSION, RELEASE_NOTES

        dlg = QDialog(self.parent() if self.parent() else None)
        dlg.setWindowTitle("About Publisher Clone")
        dlg.setFixedSize(420, 360)
        layout = QVBoxLayout(dlg)

        title = QLabel(f"<h2>Publisher Clone</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version_label = QLabel(f"Version {VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        desc = QLabel("A desktop publishing application built with Python and PyQt6.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addWidget(QLabel("<b>Release Notes</b>"))

        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        lines = []
        for ver, changes in RELEASE_NOTES.items():
            lines.append(f"v{ver}")
            for change in changes:
                lines.append(f"  - {change}")
            lines.append("")
        notes_text.setPlainText("\n".join(lines))
        layout.addWidget(notes_text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)

        dlg.exec()
