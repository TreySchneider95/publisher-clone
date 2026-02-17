"""PDF export using QPdfWriter."""

from PyQt6.QtCore import QMarginsF, QRectF, QSizeF
from PyQt6.QtGui import QPainter, QPageSize, QPageLayout


def export_pdf(file_path: str, scenes: list, pages: list, dpi: int = 300):
    """Export all pages to a single PDF file.

    Uses the content bounding rect of each scene to determine page size.
    """
    from PyQt6.QtGui import QPdfWriter

    if not scenes:
        return

    writer = QPdfWriter(file_path)
    writer.setResolution(dpi)

    painter = QPainter()
    if not painter.begin(writer):
        return

    for i, scene in enumerate(scenes):
        if i > 0:
            writer.newPage()

        # Use content bounds for the page area
        content_rect = scene.get_content_rect(padding=18)

        # Set page size to match content
        page_size = QPageSize(
            QSizeF(content_rect.width(), content_rect.height()),
            QPageSize.Unit.Point
        )
        layout = QPageLayout(
            page_size,
            QPageLayout.Orientation.Portrait,
            QMarginsF(0, 0, 0, 0)
        )
        writer.setPageLayout(layout)

        target_rect = QRectF(0, 0, writer.width(), writer.height())

        # Clear selection to avoid rendering handles
        scene.clearSelection()
        scene.render(painter, target_rect, content_rect)

    painter.end()
