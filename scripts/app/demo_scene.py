"""Starter content for students who want an immediate example scene."""

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
from scripts.geometry.aliases import Color


def create_demo_shapes(color_cycle: list[Color]) -> list[GeometryShape]:
    """Return a small scene that shows the app's main learning modes."""
    return [
        PointShape(1, "Point 1", "point", color_cycle[0], (1, 2)),
        SegmentShape(2, "Segment 2", "segment", color_cycle[1], (-2, -1), (3, 2)),
        TriangleShape(
            3,
            "Triangle 3",
            "triangle",
            color_cycle[2],
            [(-4, -1), (-1, 3), (1, -2)],
        ),
        RectangleShape(4, "Rectangle 4", "rectangle", color_cycle[3], (2, -1), (5, 2)),
        CircleShape(5, "Circle 5", "circle", color_cycle[4], (-3, 2), (-1, 2)),
        PolygonShape(
            6,
            "Polygon 6",
            "polygon",
            color_cycle[5],
            [(2, 3), (4, 4), (5, 2), (3, 1)],
        ),
    ]
