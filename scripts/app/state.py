"""Mutable runtime state for the geometry explorer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.app.config import DEFAULT_EQUATION_TEMPLATE, DEFAULT_SAVE_PATH, DEFAULT_STATUS_MESSAGE
from scripts.geometry.aliases import Color, Point


@dataclass
class CameraState:
    """Stores the camera position and zoom in world-space terms."""

    base_pixels_per_unit: float = 56.0
    zoom: float = 1.0
    center: Point = (0.0, 0.0)

    @property
    def scale(self) -> float:
        """Convert one world-space unit into pixels for the current zoom level."""
        return self.base_pixels_per_unit * self.zoom


@dataclass
class CustomFunctionState:
    """Stores one user-authored function."""

    id: int
    name: str
    expression: str
    color: Color
    enabled: bool = True
    attached_point_id: int | None = None
    description: str = "Student-defined function."
    error: str | None = None


@dataclass
class SliderState:
    """Stores one adjustable numeric parameter."""

    name: str
    label: str
    min_value: float
    max_value: float
    value: float
    default: float
    speed: float = 0.4
    animated: bool = False
    direction: int = 1


@dataclass
class ConstraintLink:
    """Represents a live geometric constraint between shapes."""

    kind: str
    reference_shape_id: int
    target_shape_id: int


@dataclass
class LessonProgress:
    """Tracks the current guided lesson and its step."""

    lesson_id: str | None = None
    step_index: int = 0


def default_sliders() -> dict[str, SliderState]:
    """Return the standard slider set used by custom equations."""
    return {
        "a": SliderState("a", "Quadratic stretch (a)", -5.0, 5.0, 1.0, 1.0, speed=0.25),
        "b": SliderState("b", "Slope shift (b)", -8.0, 8.0, 0.0, 0.0, speed=0.22),
        "c": SliderState("c", "Vertical move (c)", -8.0, 8.0, 0.0, 0.0, speed=0.18),
        "t": SliderState("t", "Time offset (t)", -6.0, 6.0, 0.0, 0.0, speed=0.7),
    }


@dataclass
class InteractionState:
    """Stores transient interaction state, overlays, and learning tools."""

    active_tool: str = "select"
    snap_to_grid: bool = True
    show_help: bool = True
    show_intersections: bool = True
    status_message: str = DEFAULT_STATUS_MESSAGE
    active_function_names: set[str] = field(default_factory=lambda: {"Linear", "Parabola"})
    pending_points: list[Point] = field(default_factory=list)
    preview_point: Point | None = None
    cursor_world: Point = (0.0, 0.0)
    selected_shape_id: int | None = None
    hovered_shape_id: int | None = None
    comparison_shape_id: int | None = None
    dragging_handle_index: int | None = None
    dragging_shape: bool = False
    dragging_canvas: bool = False
    dragging_slider_name: str | None = None
    last_mouse_pos: tuple[int, int] = (0, 0)
    previous_drag_world: Point = (0.0, 0.0)
    roadmap_index: int = 0
    sidebar_section: str | None = "details"
    overlay: str | None = None
    menu_index: int = 0
    lesson_menu_index: int = 0
    equation_input: str = DEFAULT_EQUATION_TEMPLATE
    equation_editing_id: int | None = None
    equation_attach_to_selected_point: bool = True
    equation_status: str = "Type an expression in x. You can also use a, b, c, t, px, and py."
    custom_functions: list[CustomFunctionState] = field(default_factory=list)
    next_custom_function_id: int = 1
    sliders: dict[str, SliderState] = field(default_factory=default_sliders)
    constraints: list[ConstraintLink] = field(default_factory=list)
    lesson: LessonProgress = field(default_factory=LessonProgress)
    recent_actions: set[str] = field(default_factory=set)
    last_intersection_count: int = 0
    transform_ghost: Any | None = None
    transform_description: str | None = None
    transform_matrix_lines: list[str] = field(default_factory=list)
    transform_ghost_ttl: float = 0.0
    save_path: str = DEFAULT_SAVE_PATH
