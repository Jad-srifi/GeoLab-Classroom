"""Constraint creation and live enforcement."""

from __future__ import annotations

import math

from scripts.app.state import ConstraintLink
from scripts.geometry.math_utils import distance, midpoint
from scripts.geometry.shapes import PointShape, SegmentShape
from scripts.geometry.aliases import Point


def normalize(vector: Point) -> Point:
    """Return a normalized 2D vector."""
    length = math.hypot(vector[0], vector[1])
    if length == 0:
        return (1.0, 0.0)
    return (vector[0] / length, vector[1] / length)


def orientation_like(reference: Point, preferred: Point) -> Point:
    """Choose the vector orientation closest to the preferred direction."""
    dot = reference[0] * preferred[0] + reference[1] * preferred[1]
    return reference if dot >= 0 else (-reference[0], -reference[1])


def create_constraint(
    kind: str,
    selected_shape,
    comparison_shape,
) -> ConstraintLink | None:
    """Create a normalized constraint when the shape types are compatible."""
    if kind in {"parallel", "perpendicular", "equal_length"}:
        if isinstance(selected_shape, SegmentShape) and isinstance(comparison_shape, SegmentShape):
            return ConstraintLink(
                kind=kind,
                reference_shape_id=comparison_shape.id,
                target_shape_id=selected_shape.id,
            )
        return None

    if kind == "midpoint_lock":
        if isinstance(selected_shape, PointShape) and isinstance(comparison_shape, SegmentShape):
            return ConstraintLink(
                kind=kind,
                reference_shape_id=comparison_shape.id,
                target_shape_id=selected_shape.id,
            )
        if isinstance(selected_shape, SegmentShape) and isinstance(comparison_shape, PointShape):
            return ConstraintLink(
                kind=kind,
                reference_shape_id=selected_shape.id,
                target_shape_id=comparison_shape.id,
            )
    return None


def enforce_constraints(app) -> None:
    """Apply all live constraints to the current scene."""
    valid_constraints: list[ConstraintLink] = []
    shapes_by_id = {shape.id: shape for shape in app.shapes}

    for constraint in app.state.constraints:
        reference_shape = shapes_by_id.get(constraint.reference_shape_id)
        target_shape = shapes_by_id.get(constraint.target_shape_id)
        if reference_shape is None or target_shape is None:
            continue

        if constraint.kind == "midpoint_lock":
            if isinstance(reference_shape, SegmentShape) and isinstance(target_shape, PointShape):
                target_shape.position = midpoint(reference_shape.start, reference_shape.end)
                valid_constraints.append(constraint)
            continue

        if not isinstance(reference_shape, SegmentShape) or not isinstance(target_shape, SegmentShape):
            continue

        reference_vector = (
            reference_shape.end[0] - reference_shape.start[0],
            reference_shape.end[1] - reference_shape.start[1],
        )
        reference_direction = normalize(reference_vector)
        target_vector = (
            target_shape.end[0] - target_shape.start[0],
            target_shape.end[1] - target_shape.start[1],
        )
        target_direction = normalize(target_vector)
        target_length = distance(target_shape.start, target_shape.end)

        if constraint.kind == "parallel":
            new_direction = orientation_like(reference_direction, target_direction)
            target_shape.end = (
                target_shape.start[0] + new_direction[0] * target_length,
                target_shape.start[1] + new_direction[1] * target_length,
            )
            valid_constraints.append(constraint)
            continue

        if constraint.kind == "perpendicular":
            perpendicular = (-reference_direction[1], reference_direction[0])
            new_direction = orientation_like(perpendicular, target_direction)
            target_shape.end = (
                target_shape.start[0] + new_direction[0] * target_length,
                target_shape.start[1] + new_direction[1] * target_length,
            )
            valid_constraints.append(constraint)
            continue

        if constraint.kind == "equal_length":
            if target_length == 0:
                target_direction = reference_direction
            new_length = distance(reference_shape.start, reference_shape.end)
            new_direction = orientation_like(target_direction, reference_direction)
            target_shape.end = (
                target_shape.start[0] + new_direction[0] * new_length,
                target_shape.start[1] + new_direction[1] * new_length,
            )
            valid_constraints.append(constraint)

    app.state.constraints = valid_constraints


def describe_constraint(constraint: ConstraintLink, app) -> str:
    """Return a student-friendly constraint summary."""
    shapes_by_id = {shape.id: shape for shape in app.shapes}
    reference_shape = shapes_by_id.get(constraint.reference_shape_id)
    target_shape = shapes_by_id.get(constraint.target_shape_id)
    if reference_shape is None or target_shape is None:
        return "Broken constraint"

    labels = {
        "parallel": "stays parallel to",
        "perpendicular": "stays perpendicular to",
        "equal_length": "matches the length of",
        "midpoint_lock": "sticks to the midpoint of",
    }
    return f"{target_shape.label} {labels.get(constraint.kind, 'depends on')} {reference_shape.label}"
