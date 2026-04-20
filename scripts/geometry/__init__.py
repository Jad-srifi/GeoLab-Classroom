"""Geometry primitives, formulas, and interactive shape models."""

from scripts.geometry.functions import FunctionPreset, default_function_presets
from scripts.geometry.shapes import (
    CircleShape,
    GeometryShape,
    PointShape,
    PolygonShape,
    RectangleShape,
    SegmentShape,
    TriangleShape,
)
from scripts.geometry.aliases import Color, Point

__all__ = [
    "CircleShape",
    "Color",
    "FunctionPreset",
    "GeometryShape",
    "Point",
    "PointShape",
    "PolygonShape",
    "RectangleShape",
    "SegmentShape",
    "TriangleShape",
    "default_function_presets",
]
