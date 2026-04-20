"""Save and load scenes for the geometry app."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.geometry.serialization import shape_from_record, shape_to_record


def save_scene(app, path: str) -> str:
    """Save the current scene to disk and return a status message."""
    target = Path(path)
    payload = {
        "camera": {
            "center": list(app.camera.center),
            "zoom": app.camera.zoom,
        },
        "selected_shape_id": app.state.selected_shape_id,
        "comparison_shape_id": app.state.comparison_shape_id,
        "active_tool": app.state.active_tool,
        "active_function_names": sorted(app.state.active_function_names),
        "custom_functions": [
            {
                "id": function.id,
                "name": function.name,
                "expression": function.expression,
                "color": list(function.color),
                "enabled": function.enabled,
                "attached_point_id": function.attached_point_id,
                "description": function.description,
            }
            for function in app.state.custom_functions
        ],
        "sliders": {
            name: {
                "value": slider.value,
                "animated": slider.animated,
                "direction": slider.direction,
            }
            for name, slider in app.state.sliders.items()
        },
        "constraints": [
            {
                "kind": constraint.kind,
                "reference_shape_id": constraint.reference_shape_id,
                "target_shape_id": constraint.target_shape_id,
            }
            for constraint in app.state.constraints
        ],
        "lesson": {
            "lesson_id": app.state.lesson.lesson_id,
            "step_index": app.state.lesson.step_index,
        },
        "shapes": [shape_to_record(shape) for shape in app.shapes],
    }

    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return f"Saved the scene to {target.name}."


def load_scene(app, path: str) -> str:
    """Load a scene from disk and return a status message."""
    target = Path(path)
    if not target.exists():
        return f"Could not find {target.name}."

    payload = json.loads(target.read_text(encoding="utf-8"))
    app.shapes = [shape_from_record(record) for record in payload.get("shapes", [])]
    app.next_shape_id = max((shape.id for shape in app.shapes), default=0) + 1
    app.camera.center = tuple(payload.get("camera", {}).get("center", [0.0, 0.0]))
    app.camera.zoom = payload.get("camera", {}).get("zoom", 1.0)
    app.state.selected_shape_id = payload.get("selected_shape_id")
    app.state.comparison_shape_id = payload.get("comparison_shape_id")
    app.state.active_tool = payload.get("active_tool", "select")
    app.state.active_function_names = set(payload.get("active_function_names", []))

    app.state.custom_functions.clear()
    for record in payload.get("custom_functions", []):
        app.state.custom_functions.append(
            app.build_custom_function(
                name=record["name"],
                expression=record["expression"],
                color=tuple(record["color"]),
                enabled=record.get("enabled", True),
                attached_point_id=record.get("attached_point_id"),
                description=record.get("description", "Student-defined function."),
                function_id=record["id"],
            )
        )
    app.state.next_custom_function_id = max(
        (function.id for function in app.state.custom_functions),
        default=0,
    ) + 1

    for slider_name, slider_data in payload.get("sliders", {}).items():
        if slider_name in app.state.sliders:
            app.state.sliders[slider_name].value = slider_data.get(
                "value",
                app.state.sliders[slider_name].value,
            )
            app.state.sliders[slider_name].animated = slider_data.get("animated", False)
            app.state.sliders[slider_name].direction = slider_data.get("direction", 1)

    app.state.constraints = [
        app.build_constraint(
            record["kind"],
            record["reference_shape_id"],
            record["target_shape_id"],
        )
        for record in payload.get("constraints", [])
    ]
    app.state.constraints = [constraint for constraint in app.state.constraints if constraint is not None]

    lesson = payload.get("lesson", {})
    app.state.lesson.lesson_id = lesson.get("lesson_id")
    app.state.lesson.step_index = lesson.get("step_index", 0)

    app.state.pending_points.clear()
    app.state.preview_point = None
    app.state.overlay = None
    return f"Loaded the scene from {target.name}."
