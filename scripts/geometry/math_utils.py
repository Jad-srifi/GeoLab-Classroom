"""Math helpers used by the geometry explorer."""

from __future__ import annotations

import math

from scripts.geometry.aliases import Point


def format_number(value: float, digits: int = 2) -> str:
    """Format values cleanly so students see meaning, not floating-point noise."""
    if abs(value) < 1e-9:
        value = 0.0

    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def distance(a: Point, b: Point) -> float:
    """Return the Euclidean distance between two points."""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def midpoint(a: Point, b: Point) -> Point:
    """Return the midpoint of a segment."""
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def polygon_area(points: list[Point]) -> float:
    """Return polygon area using the shoelace formula."""
    if len(points) < 3:
        return 0.0

    signed_area = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        signed_area += point[0] * next_point[1] - next_point[0] * point[1]
    return abs(signed_area) / 2.0


def polygon_perimeter(points: list[Point]) -> float:
    """Return the total edge length of a polygon."""
    if len(points) < 2:
        return 0.0

    total = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        total += distance(point, next_point)
    return total


def distance_to_segment(point: Point, start: Point, end: Point) -> float:
    """Return the shortest distance from a point to a segment."""
    segment_dx = end[0] - start[0]
    segment_dy = end[1] - start[1]
    segment_length_squared = segment_dx ** 2 + segment_dy ** 2

    if segment_length_squared == 0:
        return distance(point, start)

    projection = (
        ((point[0] - start[0]) * segment_dx) + ((point[1] - start[1]) * segment_dy)
    ) / segment_length_squared
    clamped_projection = max(0.0, min(1.0, projection))

    closest_point = (
        start[0] + segment_dx * clamped_projection,
        start[1] + segment_dy * clamped_projection,
    )
    return distance(point, closest_point)


def point_in_polygon(point: Point, polygon: list[Point]) -> bool:
    """Return True when a point is inside a polygon using ray casting."""
    x, y = point
    inside = False

    for index, current_point in enumerate(polygon):
        next_point = polygon[(index + 1) % len(polygon)]
        x1, y1 = current_point
        x2, y2 = next_point

        intersects = ((y1 > y) != (y2 > y)) and (
            x < ((x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1)
        )
        if intersects:
            inside = not inside

    return inside


def almost_equal(a: float, b: float, tolerance: float = 1e-5) -> bool:
    """Return True when two values are close enough for classroom classifications."""
    return abs(a - b) <= tolerance
