from enum import Enum, auto


class ToolType(Enum):
    SELECT = auto()
    TEXT = auto()
    RECT = auto()
    ELLIPSE = auto()
    LINE = auto()
    ARROW = auto()
    POLYGON = auto()
    FREEHAND = auto()
    IMAGE = auto()


class UnitType(Enum):
    INCHES = "in"
    CENTIMETERS = "cm"
    PIXELS = "px"
    FEET = "ft"


class PageSizePreset(Enum):
    INFINITE = ("Infinite", 0, 0)
    LETTER = ("Letter", 612, 792)          # 8.5 x 11 in
    A4 = ("A4", 595.28, 841.89)            # 210 x 297 mm
    LEGAL = ("Legal", 612, 1008)           # 8.5 x 14 in
    TABLOID = ("Tabloid", 792, 1224)       # 11 x 17 in
    A3 = ("A3", 841.89, 1190.55)           # 297 x 420 mm
    A5 = ("A5", 419.53, 595.28)            # 148 x 210 mm
    CUSTOM = ("Custom", 0, 0)

    def __init__(self, label, width_pt, height_pt):
        self.label = label
        self.width_pt = width_pt
        self.height_pt = height_pt


class ItemType(Enum):
    RECT = auto()
    ELLIPSE = auto()
    LINE = auto()
    ARROW = auto()
    POLYGON = auto()
    TEXT = auto()
    IMAGE = auto()
    FREEHAND = auto()
    GROUP = auto()


# Conversion helpers
POINTS_PER_INCH = 72.0
POINTS_PER_CM = 72.0 / 2.54
POINTS_PER_PIXEL = 1.0  # 1:1 at 72 DPI
POINTS_PER_FOOT = 100.0


def points_to_unit(points: float, unit: UnitType) -> float:
    if unit == UnitType.INCHES:
        return points / POINTS_PER_INCH
    elif unit == UnitType.CENTIMETERS:
        return points / POINTS_PER_CM
    elif unit == UnitType.FEET:
        return points / POINTS_PER_FOOT
    else:
        return points / POINTS_PER_PIXEL


def unit_to_points(value: float, unit: UnitType) -> float:
    if unit == UnitType.INCHES:
        return value * POINTS_PER_INCH
    elif unit == UnitType.CENTIMETERS:
        return value * POINTS_PER_CM
    elif unit == UnitType.FEET:
        return value * POINTS_PER_FOOT
    else:
        return value * POINTS_PER_PIXEL
