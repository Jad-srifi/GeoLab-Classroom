"""Transformation helpers for selected shapes."""

from __future__ import annotations

import math

from scripts.geometry.serialization import copy_shape
from scripts.geometry.shapes import (
    CircleShape,
    GeometryShape,
    PointShape,
    PolygonShape,
    RectangleShape,
    SegmentShape,
    TriangleShape,
)
from scripts.geometry.aliases import Point


def centroid(shape: GeometryShape) -> Point:
    """Return the best available pivot point for a shape."""
    if isinstance(shape, PointShape):
        return shape.position
    if isinstance(shape, SegmentShape):
        return ((shape.start[0] + shape.end[0]) / 2, (shape.start[1] + shape.end[1]) / 2)
    if isinstance(shape, CircleShape):
        return shape.center
    if isinstance(shape, RectangleShape):
        corners = shape.corners()
        return (
            sum(point[0] for point in corners) / len(corners),
            sum(point[1] for point in corners) / len(corners),
        )
    points = shape.vertices()
    return (
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def rotate_point(point: Point, pivot: Point, angle_radians: float) -> Point:
    """Rotate one point around a pivot."""
    translated_x = point[0] - pivot[0]
    translated_y = point[1] - pivot[1]
    rotated_x = translated_x * math.cos(angle_radians) - translated_y * math.sin(angle_radians)
    rotated_y = translated_x * math.sin(angle_radians) + translated_y * math.cos(angle_radians)
    return (pivot[0] + rotated_x, pivot[1] + rotated_y)


def scale_point(point: Point, pivot: Point, factor: float) -> Point:
    """Scale one point uniformly around a pivot."""
    return (
        pivot[0] + (point[0] - pivot[0]) * factor,
        pivot[1] + (point[1] - pivot[1]) * factor,
    )


def mirror_point(point: Point, axis: str) -> Point:
    """Mirror one point across a simple classroom axis."""
    if axis == "x":
        return (point[0], -point[1])
    if axis == "y":
        return (-point[0], point[1])
    return (-point[0], -point[1])


def transformed_points(shape: GeometryShape) -> list[Point]:
    """Return the points used to rebuild a transformed shape."""
    if isinstance(shape, PointShape):
        return [shape.position]
    if isinstance(shape, SegmentShape):
        return [shape.start, shape.end]
    if isinstance(shape, TriangleShape):
        return list(shape.points)
    if isinstance(shape, RectangleShape):
        return shape.corners()
    if isinstance(shape, CircleShape):
        return [shape.center, shape.radius_point]
    if isinstance(shape, PolygonShape):
        return list(shape.points)
    raise TypeError(f"Unsupported shape type: {type(shape)!r}")


def rebuild_shape(shape: GeometryShape, points: list[Point]) -> GeometryShape:
    """Rebuild a shape from transformed points."""
    if isinstance(shape, PointShape):
        return PointShape(shape.id, shape.label, "point", shape.color, points[0])
    if isinstance(shape, SegmentShape):
        return SegmentShape(shape.id, shape.label, "segment", shape.color, points[0], points[1])
    if isinstance(shape, TriangleShape):
        return TriangleShape(shape.id, shape.label, "triangle", shape.color, points[:3])
    if isinstance(shape, CircleShape):
        return CircleShape(shape.id, shape.label, "circle", shape.color, points[0], points[1])
    if isinstance(shape, RectangleShape):
        return PolygonShape(shape.id, f"{shape.label} (transformed)", "polygon", shape.color, points)
    if isinstance(shape, PolygonShape):
        return PolygonShape(shape.id, shape.label, "polygon", shape.color, points)
    raise TypeError(f"Unsupported shape type: {type(shape)!r}")


def apply_translation(shape: GeometryShape, dx: float, dy: float) -> tuple[GeometryShape, list[str], str]:
    """Translate a shape by a fixed vector."""
    updated_shape = copy_shape(shape)
    updated_shape.move(dx, dy)
    matrix = [
        "Translation matrix",
        f"[1 0 {dx:.2f}]",
        f"[0 1 {dy:.2f}]",
        "[0 0 1]",
    ]
    return updated_shape, matrix, f"Translated by ({dx:.2f}, {dy:.2f})"


def apply_rotation(shape: GeometryShape, angle_degrees: float) -> tuple[GeometryShape, list[str], str]:
    """Rotate a shape around its centroid."""
    pivot = centroid(shape)
    angle_radians = math.radians(angle_degrees)
    points = [rotate_point(point, pivot, angle_radians) for point in transformed_points(shape)]
    updated_shape = rebuild_shape(shape, points)
    matrix = [
        f"Rotation matrix ({angle_degrees:.0f} deg)",
        f"[cos {angle_degrees:.0f}  -sin {angle_degrees:.0f}  0]",
        f"[sin {angle_degrees:.0f}   cos {angle_degrees:.0f}  0]",
        "[0 0 1]",
    ]
    return updated_shape, matrix, f"Rotated {angle_degrees:.0f} degrees around the shape center"


def apply_scale(shape: GeometryShape, factor: float) -> tuple[GeometryShape, list[str], str]:
    """Scale a shape uniformly around its centroid."""
    pivot = centroid(shape)
    points = [scale_point(point, pivot, factor) for point in transformed_points(shape)]
    updated_shape = rebuild_shape(shape, points)
    matrix = [
        f"Scale matrix ({factor:.2f}x)",
        f"[{factor:.2f} 0 0]",
        f"[0 {factor:.2f} 0]",
        "[0 0 1]",
    ]
    return updated_shape, matrix, f"Scaled by {factor:.2f}x around the shape center"


def apply_mirror(shape: GeometryShape, axis: str) -> tuple[GeometryShape, list[str], str]:
    """Mirror a shape across the x-axis, y-axis, or origin."""
    points = [mirror_point(point, axis) for point in transformed_points(shape)]
    updated_shape = rebuild_shape(shape, points)
    matrices = {
        "x": ["Mirror across x-axis", "[1 0 0]", "[0 -1 0]", "[0 0 1]"],
        "y": ["Mirror across y-axis", "[-1 0 0]", "[0 1 0]", "[0 0 1]"],
        "origin": ["Mirror across origin", "[-1 0 0]", "[0 -1 0]", "[0 0 1]"],
    }
    descriptions = {
        "x": "Mirrored across the x-axis",
        "y": "Mirrored across the y-axis",
        "origin": "Mirrored across the origin",
    }
    return updated_shape, matrices[axis], descriptions[axis]
