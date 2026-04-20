"""Guided lesson definitions and progress checks."""

from __future__ import annotations

from dataclasses import dataclass

from scripts.geometry.shapes import CircleShape, SegmentShape, TriangleShape


@dataclass(frozen=True)
class Lesson:
    """A lightweight guided lesson with ordered steps."""

    id: str
    title: str
    summary: str
    steps: list[str]


LESSONS = [
    Lesson(
        id="slope_lab",
        title="Slope Lab",
        summary="Use a segment to see slope respond to movement.",
        steps=[
            "Create a segment anywhere on the plane.",
            "Make a selected segment horizontal so its slope becomes 0.",
            "Create another segment and add a parallel constraint with Shift+Click + Ctrl+1.",
        ],
    ),
    Lesson(
        id="triangle_area_lab",
        title="Triangle Area Lab",
        summary="Watch side lengths and area change together.",
        steps=[
            "Create a triangle.",
            "Make the triangle area larger than 6 square units.",
            "Drag one triangle handle and watch the live area update.",
        ],
    ),
    Lesson(
        id="circle_growth_lab",
        title="Circle Growth Lab",
        summary="Connect radius, circumference, and area.",
        steps=[
            "Create a circle.",
            "Increase its radius above 2.5 units.",
            "Rotate or scale the selected circle to compare before and after values.",
        ],
    ),
    Lesson(
        id="equation_slider_lab",
        title="Equation & Slider Lab",
        summary="Link algebra to the graphing canvas.",
        steps=[
            "Open the equation editor and save a custom function.",
            "Attach the equation to a selected point or use the default slider variables.",
            "Animate slider t with Tab and watch the graph move.",
        ],
    ),
]


def lesson_by_id(lesson_id: str | None) -> Lesson | None:
    """Return one lesson by id."""
    if lesson_id is None:
        return None
    return next((lesson for lesson in LESSONS if lesson.id == lesson_id), None)


def check_lesson_step(app) -> bool:
    """Return True when the current lesson step is complete."""
    lesson = lesson_by_id(app.state.lesson.lesson_id)
    if lesson is None:
        return False

    step = app.state.lesson.step_index
    selected = app.selected_shape

    if lesson.id == "slope_lab":
        if step == 0:
            return any(isinstance(shape, SegmentShape) for shape in app.shapes)
        if step == 1:
            return (
                isinstance(selected, SegmentShape)
                and abs(selected.end[1] - selected.start[1]) <= 0.05
            )
        if step == 2:
            return any(constraint.kind == "parallel" for constraint in app.state.constraints)

    if lesson.id == "triangle_area_lab":
        if step == 0:
            return any(isinstance(shape, TriangleShape) for shape in app.shapes)
        if step == 1:
            return (
                isinstance(selected, TriangleShape)
                and any("Area:" in line and float(line.split(":")[1].split()[0]) > 6 for line in selected.summary_lines())
            )
        if step == 2:
            return "triangle_handle_dragged" in app.state.recent_actions

    if lesson.id == "circle_growth_lab":
        if step == 0:
            return any(isinstance(shape, CircleShape) for shape in app.shapes)
        if step == 1:
            return isinstance(selected, CircleShape) and selected.radius() > 2.5
        if step == 2:
            return (
                "transform_rotate" in app.state.recent_actions
                or "transform_scale" in app.state.recent_actions
            )

    if lesson.id == "equation_slider_lab":
        if step == 0:
            return "custom_function_saved" in app.state.recent_actions
        if step == 1:
            return any(function.attached_point_id is not None for function in app.state.custom_functions)
        if step == 2:
            return app.state.sliders["t"].animated

    return False


def lesson_lines(app) -> list[str]:
    """Return the inspector lines for the current lesson."""
    lesson = lesson_by_id(app.state.lesson.lesson_id)
    if lesson is None:
        return [
            "Press J or open Lessons from the Escape menu to start a guided activity.",
            "Lessons turn the sandbox into step-by-step classroom challenges.",
        ]

    current_step = min(app.state.lesson.step_index, len(lesson.steps) - 1)
    lines = [
        lesson.summary,
        f"Step {current_step + 1} of {len(lesson.steps)}",
        lesson.steps[current_step],
    ]
    if app.state.lesson.step_index >= len(lesson.steps):
        lines.append("Lesson complete. Pick another lesson or keep exploring freely.")
    return lines
