"""QGraphicsItem subclasses for each item type."""

import math
from PyQt6.QtWidgets import (
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsPathItem, QGraphicsTextItem, QGraphicsPixmapItem,
    QGraphicsPolygonItem, QGraphicsItem, QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem, QWidget
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt6.QtGui import (
    QPen, QColor, QBrush, QPainter, QPainterPath, QPainterPathStroker,
    QFont, QPolygonF, QPixmap, QImage, QTransform
)
import base64

from app.models.items import (
    ItemData, RectItemData, EllipseItemData, LineItemData,
    ArrowItemData, PolygonItemData, TextItemData, ImageItemData,
    FreehandItemData, GroupItemData
)


class PublisherItemMixin:
    """Common functionality for all publisher items."""

    def _init_publisher_item(self, data: ItemData):
        self.item_data = data
        self.setPos(data.x, data.y)
        self.setRotation(data.rotation)
        self.setZValue(data.z_value)
        self.setVisible(data.visible)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not data.locked)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not data.locked)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self._apply_flip_transform()

    def _make_pen(self) -> QPen:
        d = self.item_data
        if d.stroke_width <= 0:
            return QPen(Qt.PenStyle.NoPen)
        color = QColor(d.stroke_color)
        color.setAlphaF(d.stroke_opacity)
        pen = QPen(color, d.stroke_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        return pen

    def _make_brush(self) -> QBrush:
        d = self.item_data
        if d.fill_texture:
            from app.models.texture_registry import load_texture
            pixmap = load_texture(d.fill_texture)
            if pixmap and not pixmap.isNull():
                return QBrush(pixmap)
        if d.fill_color == "transparent":
            return QBrush(Qt.BrushStyle.NoBrush)
        color = QColor(d.fill_color)
        color.setAlphaF(d.fill_opacity)
        return QBrush(color)

    def _get_flip_rect(self) -> QRectF:
        """Return the rect to mirror around when flipping. Override in subclasses."""
        return QRectF(0, 0, self.item_data.width, self.item_data.height)

    def _apply_flip_transform(self):
        """Apply horizontal/vertical flip transform based on item data."""
        d = self.item_data
        if not d.flip_h and not d.flip_v:
            self.setTransform(QTransform())
            return
        r = self._get_flip_rect()
        cx, cy = r.center().x(), r.center().y()
        t = QTransform()
        t.translate(cx, cy)
        t.scale(-1 if d.flip_h else 1, -1 if d.flip_v else 1)
        t.translate(-cx, -cy)
        self.setTransform(t)

    def sync_from_data(self):
        """Update Qt item from data object."""
        d = self.item_data
        self.setPos(d.x, d.y)
        self.setRotation(d.rotation)
        self.setZValue(d.z_value)
        self.setVisible(d.visible)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not d.locked)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not d.locked)
        self._apply_flip_transform()

    def sync_to_data(self):
        """Update data object from Qt item position."""
        self.item_data.x = self.pos().x()
        self.item_data.y = self.pos().y()
        self.item_data.rotation = self.rotation()


class PublisherRectItem(QGraphicsRectItem, PublisherItemMixin):
    """Rectangle item on the canvas."""

    def __init__(self, data: RectItemData, parent=None):
        super().__init__(0, 0, data.width, data.height, parent)
        self._init_publisher_item(data)
        self._apply_style()

    def _apply_style(self):
        self.setPen(self._make_pen())
        self.setBrush(self._make_brush())

    def sync_from_data(self):
        super().sync_from_data()
        d = self.item_data
        self.setRect(0, 0, d.width, d.height)
        self._apply_style()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


class PublisherEllipseItem(QGraphicsEllipseItem, PublisherItemMixin):
    """Ellipse item on the canvas."""

    def __init__(self, data: EllipseItemData, parent=None):
        super().__init__(0, 0, data.width, data.height, parent)
        self._init_publisher_item(data)
        self._apply_style()

    def _apply_style(self):
        self.setPen(self._make_pen())
        self.setBrush(self._make_brush())

    def sync_from_data(self):
        super().sync_from_data()
        d = self.item_data
        self.setRect(0, 0, d.width, d.height)
        self._apply_style()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


class PublisherLineItem(QGraphicsLineItem, PublisherItemMixin):
    """Line item on the canvas."""

    def __init__(self, data: LineItemData, parent=None):
        super().__init__(0, 0, data.x2 - data.x, data.y2 - data.y, parent)
        self._init_publisher_item(data)
        self._apply_style()

    def _get_flip_rect(self) -> QRectF:
        d = self.item_data
        return QRectF(QPointF(0, 0), QPointF(d.x2 - d.x, d.y2 - d.y)).normalized()

    def _apply_style(self):
        self.setPen(self._make_pen())

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.item_data.stroke_width, 8))
        return stroker.createStroke(path)

    def sync_from_data(self):
        super().sync_from_data()
        d = self.item_data
        self.setLine(0, 0, d.x2 - d.x, d.y2 - d.y)
        self._apply_style()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


class PublisherArrowItem(QGraphicsLineItem, PublisherItemMixin):
    """Arrow (line with arrowhead) item on the canvas."""

    def __init__(self, data: ArrowItemData, parent=None):
        super().__init__(0, 0, data.x2 - data.x, data.y2 - data.y, parent)
        self._init_publisher_item(data)
        self._apply_style()

    def _get_flip_rect(self) -> QRectF:
        d = self.item_data
        return QRectF(QPointF(0, 0), QPointF(d.x2 - d.x, d.y2 - d.y)).normalized()

    def _apply_style(self):
        self.setPen(self._make_pen())

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.item_data.stroke_width, 8))
        return stroker.createStroke(path)

    def boundingRect(self):
        extra = self.item_data.arrow_size + self.item_data.stroke_width
        return super().boundingRect().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter: QPainter, option, widget=None):
        d = self.item_data
        pen = self._make_pen()
        painter.setPen(pen)

        line = self.line()
        painter.drawLine(line)

        # Draw arrowhead
        if line.length() == 0:
            return
        angle = math.atan2(-line.dy(), line.dx())
        arrow_size = d.arrow_size
        p1 = line.p2() - QPointF(
            math.cos(angle - math.pi / 6) * arrow_size,
            -math.sin(angle - math.pi / 6) * arrow_size
        )
        p2 = line.p2() - QPointF(
            math.cos(angle + math.pi / 6) * arrow_size,
            -math.sin(angle + math.pi / 6) * arrow_size
        )
        arrow_head = QPolygonF([line.p2(), p1, p2])
        painter.setBrush(QBrush(QColor(d.stroke_color)))
        painter.drawPolygon(arrow_head)

    def sync_from_data(self):
        super().sync_from_data()
        d = self.item_data
        self.setLine(0, 0, d.x2 - d.x, d.y2 - d.y)
        self._apply_style()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


class PublisherPolygonItem(QGraphicsPolygonItem, PublisherItemMixin):
    """Polygon item on the canvas."""

    def __init__(self, data: PolygonItemData, parent=None):
        polygon = QPolygonF([QPointF(x, y) for x, y in data.points])
        super().__init__(polygon, parent)
        self._init_publisher_item(data)
        self._apply_style()

    def _get_flip_rect(self) -> QRectF:
        d = self.item_data
        if not d.points:
            return QRectF()
        xs = [p[0] for p in d.points]
        ys = [p[1] for p in d.points]
        return QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def _apply_style(self):
        self.setPen(self._make_pen())
        self.setBrush(self._make_brush())

    def sync_from_data(self):
        super().sync_from_data()
        d = self.item_data
        polygon = QPolygonF([QPointF(x, y) for x, y in d.points])
        self.setPolygon(polygon)
        self._apply_style()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


class PublisherTextItem(QGraphicsRectItem, PublisherItemMixin):
    """Text item - uses a rect as the container with text drawn inside."""

    def __init__(self, data: TextItemData, parent=None):
        super().__init__(0, 0, data.width, data.height, parent)
        self._init_publisher_item(data)
        self._editing = False
        self._apply_style()

    def _apply_style(self):
        self.setPen(self._make_pen())
        self.setBrush(self._make_brush())

    def _get_font(self) -> QFont:
        d = self.item_data
        font = QFont(d.font_family, int(d.font_size))
        font.setBold(d.bold)
        font.setItalic(d.italic)
        font.setUnderline(d.underline)
        return font

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        d = self.item_data

        painter.setFont(self._get_font())
        painter.setPen(QColor(d.text_color))

        alignment = Qt.AlignmentFlag.AlignLeft
        if d.alignment == "center":
            alignment = Qt.AlignmentFlag.AlignHCenter
        elif d.alignment == "right":
            alignment = Qt.AlignmentFlag.AlignRight

        text_rect = self.rect().adjusted(4, 2, -4, -2)
        painter.drawText(text_rect,
                         alignment | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                         d.text)

    def sync_from_data(self):
        super().sync_from_data()
        d = self.item_data
        self.setRect(0, 0, d.width, d.height)
        self._apply_style()
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


class PublisherImageItem(QGraphicsRectItem, PublisherItemMixin):
    """Image item on the canvas."""

    def __init__(self, data: ImageItemData, parent=None):
        super().__init__(0, 0, data.width, data.height, parent)
        self._init_publisher_item(data)
        self._pixmap = None
        self._load_image()
        self._apply_style()

    def _load_image(self):
        d = self.item_data
        if d.image_data_b64:
            img_bytes = base64.b64decode(d.image_data_b64)
            img = QImage()
            img.loadFromData(img_bytes)
            self._pixmap = QPixmap.fromImage(img)

    def _apply_style(self):
        self.setPen(self._make_pen())
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def paint(self, painter: QPainter, option, widget=None):
        if self._pixmap and not self._pixmap.isNull():
            painter.drawPixmap(self.rect().toRect(), self._pixmap)
        else:
            # Placeholder
            painter.fillRect(self.rect(), QColor(220, 220, 220))
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Image")
        # Draw border
        if self.item_data.stroke_width > 0:
            painter.setPen(self._make_pen())
            painter.drawRect(self.rect())

    def sync_from_data(self):
        super().sync_from_data()
        d = self.item_data
        self.setRect(0, 0, d.width, d.height)
        self._load_image()
        self._apply_style()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


class PublisherFreehandItem(QGraphicsPathItem, PublisherItemMixin):
    """Freehand drawing path item."""

    def __init__(self, data: FreehandItemData, parent=None):
        super().__init__(parent)
        self._init_publisher_item(data)
        self._rebuild_path()
        self._apply_style()

    def _get_flip_rect(self) -> QRectF:
        d = self.item_data
        if not d.points:
            return QRectF()
        xs = [p[0] for p in d.points]
        ys = [p[1] for p in d.points]
        return QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def _rebuild_path(self):
        d = self.item_data
        path = QPainterPath()
        if d.points:
            path.moveTo(d.points[0][0], d.points[0][1])
            for px, py in d.points[1:]:
                path.lineTo(px, py)
        self.setPath(path)

    def _apply_style(self):
        self.setPen(self._make_pen())
        self.setBrush(self._make_brush())

    def sync_from_data(self):
        super().sync_from_data()
        self._rebuild_path()
        self._apply_style()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


class PublisherGroupItem(QGraphicsRectItem, PublisherItemMixin):
    """Invisible group overlay that references children by ID."""

    def __init__(self, data: GroupItemData, parent=None):
        super().__init__(0, 0, data.width, data.height, parent)
        self.setTransformOriginPoint(self.rect().center())
        self._init_publisher_item(data)
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        # Group items should not intercept mouse clicks on children
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def paint(self, painter: QPainter, option, widget=None):
        """Draw nothing normally; dashed outline when selected."""
        if self.isSelected():
            pen = QPen(QColor(0, 120, 215), 1.0, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawRect(self.rect())

    def shape(self) -> QPainterPath:
        """Return empty path so group doesn't intercept clicks."""
        return QPainterPath()

    def get_child_items(self, scene):
        """Look up child items by ID from the scene."""
        child_ids = set(self.item_data.child_ids)
        children = []
        for item in scene.items():
            if hasattr(item, 'item_data') and item.item_data.id in child_ids:
                children.append(item)
        return children

    def update_bounds_from_children(self, scene):
        """Recompute bounding rect from children's scene positions."""
        children = self.get_child_items(scene)
        if not children:
            return
        rect = children[0].sceneBoundingRect()
        for child in children[1:]:
            rect = rect.united(child.sceneBoundingRect())
        # Set group position and size to encompass children
        self.item_data.x = rect.x()
        self.item_data.y = rect.y()
        self.item_data.width = rect.width()
        self.item_data.height = rect.height()
        self.setPos(rect.x(), rect.y())
        self.setRect(0, 0, rect.width(), rect.height())
        self.setTransformOriginPoint(self.rect().center())

    def sync_from_data(self):
        super().sync_from_data()
        d = self.item_data
        self.setRect(0, 0, d.width, d.height)
        self.setTransformOriginPoint(self.rect().center())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.item_data.x = value.x()
            self.item_data.y = value.y()
        return super().itemChange(change, value)


def create_item_from_data(data: ItemData):
    """Factory function to create the right QGraphicsItem for given data."""
    from app.models.items import (
        RectItemData, EllipseItemData, LineItemData, ArrowItemData,
        PolygonItemData, TextItemData, ImageItemData, FreehandItemData,
        GroupItemData
    )
    if isinstance(data, GroupItemData):
        return PublisherGroupItem(data)
    elif isinstance(data, RectItemData):
        return PublisherRectItem(data)
    elif isinstance(data, EllipseItemData):
        return PublisherEllipseItem(data)
    elif isinstance(data, LineItemData):
        return PublisherLineItem(data)
    elif isinstance(data, ArrowItemData):
        return PublisherArrowItem(data)
    elif isinstance(data, PolygonItemData):
        return PublisherPolygonItem(data)
    elif isinstance(data, TextItemData):
        return PublisherTextItem(data)
    elif isinstance(data, ImageItemData):
        return PublisherImageItem(data)
    elif isinstance(data, FreehandItemData):
        return PublisherFreehandItem(data)
    raise ValueError(f"Unknown data type: {type(data)}")
