"""Custom equation compilation, runtime evaluation, and intersections."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import lru_cache
import math
from typing import Callable

from scripts.app.state import CustomFunctionState, SliderState
from scripts.geometry.functions import FunctionPreset
from scripts.geometry.math_utils import distance, format_number
from scripts.geometry.shapes import PointShape
from scripts.geometry.aliases import Color, Point


@dataclass(frozen=True)
class RuntimeFunctionEntry:
    """Represents one drawable function at runtime."""

    token: str
    name: str
    expression: str
    description: str
    color: Color
    evaluator: Callable[[float], float]


ALLOWED_FUNCTIONS = {
    "abs": abs,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
}

ALLOWED_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}

ALLOWED_NAMES = {
    "x",
    "a",
    "b",
    "c",
    "t",
    "px",
    "py",
    *ALLOWED_FUNCTIONS.keys(),
    *ALLOWED_CONSTANTS.keys(),
}

ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.UAdd,
    ast.USub,
)


def sanitize_expression(expression: str) -> str:
    """Normalize user input into a Python-evaluable math expression."""
    return expression.replace("^", "**").strip()


def validate_expression(expression: str) -> None:
    """Raise a ValueError when the expression uses unsupported syntax."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError("Expression syntax is invalid.") from error

    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ValueError(f"Unsupported syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in ALLOWED_NAMES:
            raise ValueError(f"Unknown name: {node.id}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTIONS:
                raise ValueError("Only basic math functions like sin, cos, sqrt, and abs are allowed.")


@lru_cache(maxsize=128)
def compile_expression(expression: str):
    """Compile a validated expression and cache it for reuse."""
    validate_expression(expression)
    return compile(expression, "<geometry-equation>", "eval")


def build_custom_context(
    sliders: dict[str, SliderState],
    attached_point: Point | None,
) -> dict[str, float]:
    """Build the variable context passed into custom equations."""
    px, py = attached_point if attached_point is not None else (0.0, 0.0)
    return {
        **ALLOWED_FUNCTIONS,
        **ALLOWED_CONSTANTS,
        "a": sliders["a"].value,
        "b": sliders["b"].value,
        "c": sliders["c"].value,
        "t": sliders["t"].value,
        "px": px,
        "py": py,
    }


def build_runtime_entries(
    presets: list[FunctionPreset],
    active_preset_names: set[str],
    custom_functions: list[CustomFunctionState],
    sliders: dict[str, SliderState],
    points_by_id: dict[int, PointShape],
) -> list[RuntimeFunctionEntry]:
    """Build the combined function list for drawing and intersections."""
    entries: list[RuntimeFunctionEntry] = []

    for preset in presets:
        if preset.name not in active_preset_names:
            continue
        evaluator = preset.evaluator
        if preset.runtime_expression is not None:
            code = compile_expression(sanitize_expression(preset.runtime_expression))
            context = build_custom_context(sliders, None)

            def make_evaluator(compiled_code, local_context):
                return lambda x: eval(compiled_code, {"__builtins__": {}}, {**local_context, "x": x})

            evaluator = make_evaluator(code, context)

        if evaluator is None:
            continue
        entries.append(
            RuntimeFunctionEntry(
                token=f"preset:{preset.name}",
                name=preset.name,
                expression=preset.expression,
                description=preset.description,
                color=preset.color,
                evaluator=evaluator,
            )
        )

    for custom_function in custom_functions:
        if not custom_function.enabled or not custom_function.expression.strip():
            continue

        expression = sanitize_expression(custom_function.expression)
        try:
            code = compile_expression(expression)
            custom_function.error = None
        except ValueError as error:
            custom_function.error = str(error)
            continue

        attached_point = None
        if custom_function.attached_point_id is not None:
            attached_shape = points_by_id.get(custom_function.attached_point_id)
            if attached_shape is not None:
                attached_point = attached_shape.position

        context = build_custom_context(sliders, attached_point)

        def make_evaluator(compiled_code, local_context):
            return lambda x: eval(compiled_code, {"__builtins__": {}}, {**local_context, "x": x})

        entries.append(
            RuntimeFunctionEntry(
                token=f"custom:{custom_function.id}",
                name=custom_function.name,
                expression=expression,
                description=custom_function.description,
                color=custom_function.color,
                evaluator=make_evaluator(code, context),
            )
        )

    return entries


def approximate_intersections(
    entries: list[RuntimeFunctionEntry],
    left: float,
    right: float,
    *,
    limit: int = 8,
) -> list[tuple[Point, str]]:
    """Approximate visible intersections between active functions."""
    intersections: list[tuple[Point, str]] = []
    if len(entries) < 2:
        return intersections

    sample_count = 220
    for first_index in range(len(entries)):
        for second_index in range(first_index + 1, len(entries)):
            entry_a = entries[first_index]
            entry_b = entries[second_index]
            previous_value = None
            previous_x = None

            for sample in range(sample_count + 1):
                x = left + (right - left) * sample / sample_count
                try:
                    y_a = entry_a.evaluator(x)
                    y_b = entry_b.evaluator(x)
                except Exception:
                    previous_value = None
                    previous_x = None
                    continue

                if not (math.isfinite(y_a) and math.isfinite(y_b)):
                    previous_value = None
                    previous_x = None
                    continue

                difference = y_a - y_b
                if previous_value is not None and previous_x is not None:
                    if difference == 0 or previous_value == 0 or (difference > 0) != (previous_value > 0):
                        blend = 0.5
                        denominator = previous_value - difference
                        if denominator != 0:
                            blend = previous_value / denominator
                        intersection_x = previous_x + (x - previous_x) * blend
                        try:
                            intersection_y = entry_a.evaluator(intersection_x)
                        except Exception:
                            intersection_y = (y_a + y_b) / 2

                        point = (intersection_x, intersection_y)
                        if all(distance(point, existing[0]) > 0.18 for existing in intersections):
                            label = (
                                f"{entry_a.name} x {entry_b.name}: "
                                f"({format_number(intersection_x)}, {format_number(intersection_y)})"
                            )
                            intersections.append((point, label))
                            if len(intersections) >= limit:
                                return intersections

                previous_value = difference
                previous_x = x

    return intersections
