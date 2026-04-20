"""Graph presets shown inside the learning app."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

from scripts.geometry.aliases import Color


@dataclass(frozen=True)
class FunctionPreset:
    """Represents a graphable function with student-facing copy."""

    name: str
    expression: str
    description: str
    color: Color
    evaluator: Callable[[float], float] | None = None
    runtime_expression: str | None = None


def default_function_presets() -> list[FunctionPreset]:
    """Return starter graphs that connect algebra and geometry."""
    return [
        FunctionPreset(
            name="Linear",
            expression="y = 0.5x + 1",
            description="A straight line with a constant slope.",
            color=(124, 214, 167),
            evaluator=lambda x: 0.5 * x + 1,
        ),
        FunctionPreset(
            name="Parabola",
            expression="y = x^2 - 2",
            description="A quadratic curve that opens upward.",
            color=(245, 188, 91),
            evaluator=lambda x: x ** 2 - 2,
        ),
        FunctionPreset(
            name="Quadratic Lab",
            expression="y = a*x^2 + b*x + c",
            description="Use sliders a, b, and c to watch stretch, tilt, and vertical shift happen live.",
            color=(255, 136, 159),
            runtime_expression="a*x**2 + b*x + c",
        ),
        FunctionPreset(
            name="Sine",
            expression="y = sin(x)",
            description="A wave that helps students connect geometry and trigonometry.",
            color=(126, 167, 255),
            evaluator=lambda x: math.sin(x),
        ),
    ]
