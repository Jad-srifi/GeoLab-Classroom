"""Interactive geometry shape models with live measurements and formulas."""

from __future__ import annotations

if __package__ in {None, ""}:
    # Allow this library module to be executed directly during quick local checks.
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from dataclasses import dataclass
import math

from scripts.geometry.math_utils import (
    almost_equal,
    distance,
    distance_to_segment,
    format_number,
    midpoint,
    point_in_polygon,
    polygon_area,
    polygon_perimeter,
)
from scripts.geometry.aliases import Color, Point


@dataclass
class GeometryShape:
    """Base model shared by all interactive shapes."""

    id: int
    label: str
    kind: str
    color: Color

    def vertices(self) -> list[Point]:
        """Return points that define the shape."""
        raise NotImplementedError

    def handle_positions(self) -> list[Point]:
        """Return the draggable handles shown to the student."""
        return self.vertices()

    def contains(self, point: Point, tolerance: float) -> bool:
        """Return True when the point should select or hover the shape."""
        raise NotImplementedError

    def drag_handle(self, index: int, new_point: Point) -> None:
        """Update one construction handle while preserving the shape rules."""
        raise NotImplementedError

    def move(self, dx: float, dy: float) -> None:
        """Translate the full shape in world space."""
        raise NotImplementedError

    def summary_lines(self) -> list[str]:
        """Return student-facing facts about the current shape."""
        raise NotImplementedError

    def formula_lines(self) -> list[str]:
        """Return live formulas tied to the current coordinates."""
        raise NotImplementedError

    def challenge_prompt(self) -> str:
        """Return a short exploration prompt for the student."""
        return "Drag a handle and watch which values change together."


@dataclass
class PointShape(GeometryShape):
    """A single point on the coordinate plane."""

    position: Point

    def vertices(self) -> list[Point]:
        return [self.position]

    def contains(self, point: Point, tolerance: float) -> bool:
        return distance(self.position, point) <= tolerance * 1.3

    def drag_handle(self, index: int, new_point: Point) -> None:
        self.position = new_point

    def move(self, dx: float, dy: float) -> None:
        self.position = (self.position[0] + dx, self.position[1] + dy)

    def summary_lines(self) -> list[str]:
        x, y = self.position
        return [
            f"Coordinates: ({format_number(x)}, {format_number(y)})",
            "Points are the anchors from which every larger construction grows.",
        ]

    def formula_lines(self) -> list[str]:
        x, y = self.position
        return [f"x = {format_number(x)}", f"y = {format_number(y)}"]

    def challenge_prompt(self) -> str:
        return "Try snapping the point to the grid and predict its coordinates before reading them."


@dataclass
class SegmentShape(GeometryShape):
    """A segment defined by two endpoints."""

    start: Point
    end: Point

    def vertices(self) -> list[Point]:
        return [self.start, self.end]

    def contains(self, point: Point, tolerance: float) -> bool:
        return distance_to_segment(point, self.start, self.end) <= tolerance

    def drag_handle(self, index: int, new_point: Point) -> None:
        if index == 0:
            self.start = new_point
        else:
            self.end = new_point

    def move(self, dx: float, dy: float) -> None:
        self.start = (self.start[0] + dx, self.start[1] + dy)
        self.end = (self.end[0] + dx, self.end[1] + dy)

    def summary_lines(self) -> list[str]:
        length = distance(self.start, self.end)
        mid = midpoint(self.start, self.end)
        delta_x = self.end[0] - self.start[0]
        slope = (
            "undefined"
            if almost_equal(delta_x, 0.0)
            else format_number((self.end[1] - self.start[1]) / delta_x)
        )
        return [
            f"A = ({format_number(self.start[0])}, {format_number(self.start[1])})",
            f"B = ({format_number(self.end[0])}, {format_number(self.end[1])})",
            f"Length: {format_number(length)} units",
            f"Midpoint: ({format_number(mid[0])}, {format_number(mid[1])})",
            f"Slope: {slope}",
        ]

    def formula_lines(self) -> list[str]:
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        length = distance(self.start, self.end)
        return [
            "Distance formula:",
            "d = sqrt((x2 - x1)^2 + (y2 - y1)^2)",
            f"d = sqrt(({format_number(dx)})^2 + ({format_number(dy)})^2) = {format_number(length)}",
        ]

    def challenge_prompt(self) -> str:
        return "Can you drag one endpoint until the segment becomes horizontal, then explain why the slope changes to 0?"


@dataclass
class TriangleShape(GeometryShape):
    """A three-vertex polygon with live classifications."""

    points: list[Point]

    def vertices(self) -> list[Point]:
        return list(self.points)

    def contains(self, point: Point, tolerance: float) -> bool:
        if point_in_polygon(point, self.points):
            return True
        return any(
            distance_to_segment(
                point,
                self.points[index],
                self.points[(index + 1) % 3],
            )
            <= tolerance
            for index in range(3)
        )

    def drag_handle(self, index: int, new_point: Point) -> None:
        self.points[index] = new_point

    def move(self, dx: float, dy: float) -> None:
        self.points = [(x + dx, y + dy) for x, y in self.points]

    def triangle_type(self) -> str:
        """Return a simple side-based classification."""
        sides = [
            distance(self.points[0], self.points[1]),
            distance(self.points[1], self.points[2]),
            distance(self.points[2], self.points[0]),
        ]
        if almost_equal(sides[0], sides[1]) and almost_equal(sides[1], sides[2]):
            return "Equilateral"
        if (
            almost_equal(sides[0], sides[1])
            or almost_equal(sides[1], sides[2])
            or almost_equal(sides[2], sides[0])
        ):
            return "Isosceles"
        return "Scalene"

    def summary_lines(self) -> list[str]:
        side_ab = distance(self.points[0], self.points[1])
        side_bc = distance(self.points[1], self.points[2])
        side_ca = distance(self.points[2], self.points[0])
        perimeter = side_ab + side_bc + side_ca
        area = polygon_area(self.points)
        return [
            f"Type: {self.triangle_type()} triangle",
            f"AB = {format_number(side_ab)}, BC = {format_number(side_bc)}, CA = {format_number(side_ca)}",
            f"Perimeter: {format_number(perimeter)} units",
            f"Area: {format_number(area)} square units",
        ]

    def formula_lines(self) -> list[str]:
        p1, p2, p3 = self.points
        area = polygon_area(self.points)
        return [
            "Coordinate area formula:",
            "Area = |x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2)| / 2",
            (
                "Area = |"
                f"{format_number(p1[0])}({format_number(p2[1])} - {format_number(p3[1])}) + "
                f"{format_number(p2[0])}({format_number(p3[1])} - {format_number(p1[1])}) + "
                f"{format_number(p3[0])}({format_number(p1[1])} - {format_number(p2[1])})"
                f"| / 2 = {format_number(area)}"
            ),
        ]

    def challenge_prompt(self) -> str:
        return "Try dragging one vertex straight up. Which side lengths change, and why might the area change faster than the perimeter?"


@dataclass
class RectangleShape(GeometryShape):
    """An axis-aligned rectangle defined by opposite corners."""

    corner_a: Point
    corner_b: Point

    def width(self) -> float:
        return abs(self.corner_b[0] - self.corner_a[0])

    def height(self) -> float:
        return abs(self.corner_b[1] - self.corner_a[1])

    def corners(self) -> list[Point]:
        left = min(self.corner_a[0], self.corner_b[0])
        right = max(self.corner_a[0], self.corner_b[0])
        bottom = min(self.corner_a[1], self.corner_b[1])
        top = max(self.corner_a[1], self.corner_b[1])
        return [
            (left, bottom),
            (left, top),
            (right, top),
            (right, bottom),
        ]

    def vertices(self) -> list[Point]:
        return self.corners()

    def contains(self, point: Point, tolerance: float) -> bool:
        left = min(self.corner_a[0], self.corner_b[0]) - tolerance
        right = max(self.corner_a[0], self.corner_b[0]) + tolerance
        bottom = min(self.corner_a[1], self.corner_b[1]) - tolerance
        top = max(self.corner_a[1], self.corner_b[1]) + tolerance
        return left <= point[0] <= right and bottom <= point[1] <= top

    def drag_handle(self, index: int, new_point: Point) -> None:
        corners = self.corners()
        opposite_index = {0: 2, 1: 3, 2: 0, 3: 1}[index]
        opposite_corner = corners[opposite_index]
        self.corner_a = opposite_corner
        self.corner_b = new_point

    def move(self, dx: float, dy: float) -> None:
        self.corner_a = (self.corner_a[0] + dx, self.corner_a[1] + dy)
        self.corner_b = (self.corner_b[0] + dx, self.corner_b[1] + dy)

    def summary_lines(self) -> list[str]:
        width = self.width()
        height = self.height()
        area = width * height
        perimeter = 2 * (width + height)
        return [
            f"Width: {format_number(width)} units",
            f"Height: {format_number(height)} units",
            f"Area: {format_number(area)} square units",
            f"Perimeter: {format_number(perimeter)} units",
        ]

    def formula_lines(self) -> list[str]:
        width = self.width()
        height = self.height()
        return [
            f"Width = |x2 - x1| = {format_number(width)}",
            f"Height = |y2 - y1| = {format_number(height)}",
            f"Area = width * height = {format_number(width)} * {format_number(height)} = {format_number(width * height)}",
            f"Perimeter = 2(width + height) = {format_number(2 * (width + height))}",
        ]

    def challenge_prompt(self) -> str:
        return "Drag one corner and look for two different rectangles that have the same perimeter but different areas."


@dataclass
class CircleShape(GeometryShape):
    """A circle defined by its center and one point on the radius."""

    center: Point
    radius_point: Point

    def radius(self) -> float:
        return distance(self.center, self.radius_point)

    def vertices(self) -> list[Point]:
        return [self.center, self.radius_point]

    def handle_positions(self) -> list[Point]:
        return [self.center, self.radius_point]

    def contains(self, point: Point, tolerance: float) -> bool:
        return distance(self.center, point) <= self.radius() + tolerance

    def drag_handle(self, index: int, new_point: Point) -> None:
        if index == 0:
            dx = new_point[0] - self.center[0]
            dy = new_point[1] - self.center[1]
            self.center = new_point
            self.radius_point = (
                self.radius_point[0] + dx,
                self.radius_point[1] + dy,
            )
        else:
            self.radius_point = new_point

    def move(self, dx: float, dy: float) -> None:
        self.center = (self.center[0] + dx, self.center[1] + dy)
        self.radius_point = (self.radius_point[0] + dx, self.radius_point[1] + dy)

    def summary_lines(self) -> list[str]:
        radius = self.radius()
        diameter = radius * 2
        circumference = 2 * math.pi * radius
        area = math.pi * radius ** 2
        return [
            f"Center: ({format_number(self.center[0])}, {format_number(self.center[1])})",
            f"Radius: {format_number(radius)} units",
            f"Diameter: {format_number(diameter)} units",
            f"Circumference: {format_number(circumference)} units",
            f"Area: {format_number(area)} square units",
        ]

    def formula_lines(self) -> list[str]:
        radius = self.radius()
        return [
            f"r = distance(center, point) = {format_number(radius)}",
            f"Circumference = 2pi r = {format_number(2 * math.pi * radius)}",
            f"Area = pi r^2 = {format_number(math.pi * radius ** 2)}",
        ]

    def challenge_prompt(self) -> str:
        return "Can you double the radius and predict what happens to the area before the app tells you?"


@dataclass
class PolygonShape(GeometryShape):
    """A freeform polygon used for exploratory constructions."""

    points: list[Point]

    def vertices(self) -> list[Point]:
        return list(self.points)

    def contains(self, point: Point, tolerance: float) -> bool:
        if point_in_polygon(point, self.points):
            return True
        return any(
            distance_to_segment(
                point,
                self.points[index],
                self.points[(index + 1) % len(self.points)],
            )
            <= tolerance
            for index in range(len(self.points))
        )

    def drag_handle(self, index: int, new_point: Point) -> None:
        self.points[index] = new_point

    def move(self, dx: float, dy: float) -> None:
        self.points = [(x + dx, y + dy) for x, y in self.points]

    def summary_lines(self) -> list[str]:
        return [
            f"Vertices: {len(self.points)}",
            f"Perimeter: {format_number(polygon_perimeter(self.points))} units",
            f"Area: {format_number(polygon_area(self.points))} square units",
        ]

    def formula_lines(self) -> list[str]:
        area = polygon_area(self.points)
        perimeter = polygon_perimeter(self.points)
        return [
            "Shoelace idea: multiply cross-pairs around the polygon, subtract, then divide by 2.",
            f"Area = {format_number(area)}",
            f"Perimeter = sum of all side lengths = {format_number(perimeter)}",
        ]

    def challenge_prompt(self) -> str:
        return "Move one vertex while keeping the others fixed. Which changes faster for your polygon: area or perimeter?"


if __name__ == "__main__":
    print("This module defines geometry shape models. Run Main.py to launch the app.")
