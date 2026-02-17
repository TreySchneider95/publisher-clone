"""PNG/JPEG export using QImage rendering."""

import os
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QImage, QColor


def export_images(file_path: str, scenes: list, pages: list, dpi: int = 300):
    """Export each page as a separate image file.

    Uses the content bounding rect of each scene to determine image size.
    For multi-page documents, filenames are: base_1.ext, base_2.ext, etc.
    For single page, uses the filename as-is.
    """
    if not scenes:
        return

    base, ext = os.path.splitext(file_path)
    if not ext:
        ext = '.png'

    for i, scene in enumerate(scenes):
        if len(scenes) == 1:
            out_path = base + ext
        else:
            out_path = f"{base}_{i + 1}{ext}"

        # Use content bounds for the export area
        content_rect = scene.get_content_rect(padding=18)

        # Calculate pixel dimensions at the given DPI
        scale = dpi / 72.0  # Points to pixels at this DPI
        width_px = max(1, int(content_rect.width() * scale))
        height_px = max(1, int(content_rect.height() * scale))

        img = QImage(width_px, height_px, QImage.Format.Format_ARGB32)
        img.fill(QColor(255, 255, 255))

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        target_rect = QRectF(0, 0, width_px, height_px)

        scene.clearSelection()
        scene.render(painter, target_rect, content_rect)
        painter.end()

        # Determine format from extension
        fmt = ext.lstrip('.').upper()
        if fmt in ('JPG', 'JPEG'):
            img.save(out_path, 'JPEG', 95)
        else:
            img.save(out_path, 'PNG')
