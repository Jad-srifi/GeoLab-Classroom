"""Serialization helpers for geometry shapes."""

from __future__ import annotations

from scripts.geometry.shapes import (
    CircleShape,
    GeometryShape,
    PointShape,
    PolygonShape,
    RectangleShape,
    SegmentShape,
    TriangleShape,
)


def shape_to_record(shape: GeometryShape) -> dict:
    """Convert a shape instance into a JSON-safe dictionary."""
    base = {
        "id": shape.id,
        "label": shape.label,
        "kind": shape.kind,
        "color": list(shape.color),
    }

    if isinstance(shape, PointShape):
        base["position"] = list(shape.position)
    elif isinstance(shape, SegmentShape):
        base["start"] = list(shape.start)
        base["end"] = list(shape.end)
    elif isinstance(shape, TriangleShape):
        base["points"] = [list(point) for point in shape.points]
    elif isinstance(shape, RectangleShape):
        base["corner_a"] = list(shape.corner_a)
        base["corner_b"] = list(shape.corner_b)
    elif isinstance(shape, CircleShape):
        base["center"] = list(shape.center)
        base["radius_point"] = list(shape.radius_point)
    elif isinstance(shape, PolygonShape):
        base["points"] = [list(point) for point in shape.points]
    else:
        raise TypeError(f"Unsupported shape type: {type(shape)!r}")

    return base


def shape_from_record(record: dict) -> GeometryShape:
    """Rebuild a shape instance from a serialized record."""
    common = {
        "id": record["id"],
        "label": record["label"],
        "kind": record["kind"],
        "color": tuple(record["color"]),
    }
    kind = record["kind"]

    if kind == "point":
        return PointShape(position=tuple(record["position"]), **common)
    if kind == "segment":
        return SegmentShape(
            start=tuple(record["start"]),
            end=tuple(record["end"]),
            **common,
        )
    if kind == "triangle":
        return TriangleShape(points=[tuple(point) for point in record["points"]], **common)
    if kind == "rectangle":
        return RectangleShape(
            corner_a=tuple(record["corner_a"]),
            corner_b=tuple(record["corner_b"]),
            **common,
        )
    if kind == "circle":
        return CircleShape(
            center=tuple(record["center"]),
            radius_point=tuple(record["radius_point"]),
            **common,
        )
    if kind == "polygon":
        return PolygonShape(points=[tuple(point) for point in record["points"]], **common)

    raise ValueError(f"Unknown shape kind: {kind}")


def copy_shape(shape: GeometryShape) -> GeometryShape:
    """Return a detached copy of a shape."""
    return shape_from_record(shape_to_record(shape))
