"""Static configuration for tools, menus, commands, and roadmap ideas."""

from __future__ import annotations

from dataclasses import dataclass

from scripts.geometry.aliases import Color


@dataclass(frozen=True)
class ToolbarButton:
    """Describes a toolbar action in the app."""

    key: str
    title: str
    hotkey: str
    description: str


@dataclass(frozen=True)
class SidebarSection:
    """Describes one expandable section in the right-side rail."""

    key: str
    label: str
    description: str


TOOLBAR_BUTTONS = [
    ToolbarButton("select", "Select", "V", "Hover to spotlight shapes, then click, drag, or compare them."),
    ToolbarButton("point", "Point", "A", "Drop an anchor you can reference in other ideas."),
    ToolbarButton("segment", "Segment", "L", "Place two endpoints and study length and slope."),
    ToolbarButton("triangle", "Triangle", "T", "Build three vertices and watch area change live."),
    ToolbarButton("rectangle", "Rectangle", "R", "Choose opposite corners to compare width and height."),
    ToolbarButton("circle", "Circle", "C", "Pick a center, then stretch the radius."),
    ToolbarButton("polygon", "Polygon", "P", "Add vertices one by one, then press Enter to close."),
]

SIDEBAR_SECTIONS = [
    SidebarSection(
        "details",
        "DETAILS",
        "Measurements, formulas, constraints, and transform notes for the current selection.",
    ),
    SidebarSection(
        "graphs",
        "GRAPHS",
        "Starter graphs, custom equations, and live sliders for a, b, c, and t.",
    ),
    SidebarSection(
        "learn",
        "LEARN",
        "Guided lesson steps, project goals, and next classroom improvements.",
    ),
]

TOOL_HELP = {
    "select": "Hover to spotlight shapes. Click to inspect, drag to move, drag handles to reshape, or Shift+Click a second shape to compare.",
    "point": "Click once on the canvas to place a point.",
    "segment": "Click two locations to build a segment.",
    "triangle": "Click three locations to build a triangle.",
    "rectangle": "Click one corner, then the opposite corner.",
    "circle": "Click the center, then click a point on the radius.",
    "polygon": "Click to add vertices. Press Enter to finish the polygon.",
}

COLOR_CYCLE: list[Color] = [
    (102, 198, 227),
    (245, 188, 91),
    (124, 214, 167),
    (187, 140, 255),
    (255, 136, 159),
    (255, 206, 124),
    (145, 235, 225),
    (255, 216, 117),
]

DEFAULT_STATUS_MESSAGE = (
    "Hover, build, drag, and compare. The picture and the formulas should teach the same idea. "
    "Press Space for a demo scene or Esc for the menu."
)

DEFAULT_SAVE_PATH = "geometry_lab_scene.json"
DEFAULT_EQUATION_TEMPLATE = "a*x**2 + b*x + c"

MENU_OPTIONS = [
    ("continue", "Continue"),
    ("commands", "Commands & Keymaps"),
    ("lessons", "Guided Lessons"),
    ("equations", "Equation Editor"),
    ("save", "Save Scene"),
    ("load", "Load Scene"),
    ("cancel", "Cancel Current Action"),
]

COMMAND_SECTIONS = [
    (
        "Build Shapes",
        [
            ("A", "Point"),
            ("L", "Segment"),
            ("T", "Triangle"),
            ("R", "Rectangle"),
            ("C", "Circle"),
            ("P", "Polygon"),
            ("V", "Select mode"),
        ],
    ),
    (
        "Menu & Learn",
        [
            ("Esc", "Open menu"),
            ("/", "Open commands"),
            ("J", "Open guided lessons"),
            ("F", "Open equation editor"),
            ("Space", "Load demo scene"),
        ],
    ),
    (
        "View & Scene",
        [
            ("Ctrl+S", "Save scene"),
            ("Ctrl+O", "Load scene"),
            ("0", "Reset camera"),
            ("G", "Toggle snap"),
            ("H", "Toggle help"),
        ],
    ),
    (
        "Transform",
        [
            ("Arrow keys", "Translate selected shape"),
            ("Q / E", "Rotate selected shape"),
            ("- / =", "Scale selected shape"),
            ("X / Y / O", "Mirror across x-axis, y-axis, or origin"),
        ],
    ),
    (
        "Compare & Constrain",
        [
            ("Shift+Click", "Pick a comparison shape"),
            ("Ctrl+1", "Parallel constraint"),
            ("Ctrl+2", "Perpendicular constraint"),
            ("Ctrl+3", "Equal-length constraint"),
            ("Ctrl+4", "Midpoint lock"),
        ],
    ),
    (
        "Function Lab",
        [
            ("1 / 2 / 3 / 4", "Toggle starter graphs"),
            ("F", "Edit a custom equation"),
            ("Tab", "Animate slider t"),
            ("Pulse buttons", "Animate a, b, c, or t"),
            ("Drag sliders", "Adjust a, b, c, and t"),
        ],
    ),
]

NEXT_IMPROVEMENT_IDEAS = [
    "Add proof-style prompts that ask students to explain what they observed after each construction.",
    "Support exporting a scene as an image or printable worksheet for class handouts.",
    "Add a table view that tracks side lengths, slopes, and coordinates as the scene changes.",
    "Let students record multiple solution attempts and compare them side by side.",
    "Add collaborative modes so two students can solve one geometry challenge together.",
    "Introduce a theorem playground where the app suggests conjectures based on the current construction.",
]
