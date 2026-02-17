"""Dialog for saving a custom shape to the library."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

from app.models.shape_library import ShapeLibrary


class SaveShapeDialog(QDialog):
    """Name + folder picker for saving a custom shape."""

    def __init__(self, library: ShapeLibrary, parent=None):
        super().__init__(parent)
        self._library = library
        self.setWindowTitle("Save Custom Shape")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Name
        layout.addWidget(QLabel("Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Shaker Panel")
        layout.addWidget(self._name_edit)

        # Folder
        layout.addWidget(QLabel("Folder (optional):"))
        self._folder_combo = QComboBox()
        self._folder_combo.setEditable(True)
        self._folder_combo.addItem("")  # root / no folder
        for folder in library.list_folders():
            self._folder_combo.addItem(folder)
        layout.addWidget(self._folder_combo)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _on_save(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a shape name.")
            return

        folder = self._folder_combo.currentText().strip()
        if self._library.shape_exists(folder, name):
            result = QMessageBox.question(
                self, "Overwrite?",
                f'A shape named "{name}" already exists. Overwrite?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result != QMessageBox.StandardButton.Yes:
                return

        self.accept()

    def shape_name(self) -> str:
        return self._name_edit.text().strip()

    def folder_name(self) -> str:
        return self._folder_combo.currentText().strip()
