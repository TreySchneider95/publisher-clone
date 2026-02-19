"""Single source of truth for application version and release notes."""

VERSION = "1.1.0"

RELEASE_NOTES = {
    "1.1.0": [
        "Texture fills for shapes (wood, marble, stone, metal, fabric, paper)",
        "Line/arrow angle snapping (hold Shift), easier selection, and copy/paste fix",
        "Constrain scrolling to page bounds for defined-size pages",
        "Page size dialog auto-switches to Custom when editing dimensions",
        "Properties panel auto-shows on selection and hides when nothing is selected",
        "Layer Order controls (Send to Front / Send to Back) in properties panel",
        "Flip Horizontal / Flip Vertical controls in properties panel",
        "Layers panel hidden by default (click tab to show)",
        "Alignment controls in properties panel",
        "Distribute evenly (horizontal/vertical) in properties panel",
    ],
    "1.0.0": [
        "Initial release",
        "Multi-page document support with customizable page sizes",
        "Shape tools: rectangle, ellipse, freehand drawing",
        "Text boxes with rich text editing",
        "Image import with drag-and-drop support",
        "Object grouping and alignment",
        "Undo/redo for all operations",
        "Export to PDF, PNG/JPEG, and SVG",
        "Grid, rulers, and snap-to-grid",
        "Save/load documents (.pubd format)",
    ],
}
