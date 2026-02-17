"""SVG export using QSvgGenerator."""

import os
from PyQt6.QtCore import QRectF, QSize
from PyQt6.QtGui import QPainter
from PyQt6.QtSvg import QSvgGenerator


def export_svg(file_path: str, scenes: list, pages: list):
    """Export each page as a separate SVG file.

    Uses the content bounding rect of each scene to determine SVG size.
    For multi-page documents, filenames are: base_1.svg, base_2.svg, etc.
    """
    if not scenes:
        return

    base, ext = os.path.splitext(file_path)
    if not ext:
        ext = '.svg'

    for i, scene in enumerate(scenes):
        if len(scenes) == 1:
            out_path = base + ext
        else:
            out_path = f"{base}_{i + 1}{ext}"

        # Use content bounds for the export area
        content_rect = scene.get_content_rect(padding=18)

        generator = QSvgGenerator()
        generator.setFileName(out_path)
        generator.setSize(QSize(int(content_rect.width()), int(content_rect.height())))
        generator.setViewBox(QRectF(0, 0, content_rect.width(), content_rect.height()))
        generator.setTitle(f"Page {i + 1}")
        generator.setDescription("Exported from Publisher Clone")

        painter = QPainter()
        if painter.begin(generator):
            target_rect = QRectF(0, 0, content_rect.width(), content_rect.height())
            scene.clearSelection()
            scene.render(painter, target_rect, content_rect)
            painter.end()
