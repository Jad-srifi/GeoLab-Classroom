"""Utilities for wrapped and clipped text rendering."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class WrappedText:
    """Represents wrapped lines and the height they require."""

    lines: list[str]
    height: int


def break_long_token(token: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Split one long token into chunks that fit inside the available width."""
    if max_width <= 0 or font.size(token)[0] <= max_width:
        return [token]

    pieces: list[str] = []
    remaining = token
    while remaining:
        split_index = len(remaining)
        while split_index > 1 and font.size(remaining[:split_index] + "-")[0] > max_width:
            split_index -= 1

        if split_index <= 1:
            pieces.append(ellipsize(remaining, font, max_width))
            break

        if split_index < len(remaining):
            pieces.append(remaining[:split_index] + "-")
            remaining = remaining[split_index:]
        else:
            pieces.append(remaining)
            break

    return pieces


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wrap a paragraph into lines that fit within max_width."""
    if max_width <= 0:
        return [text]

    paragraphs = text.split("\n")
    wrapped_lines: list[str] = []
    for paragraph in paragraphs:
        if not paragraph.strip():
            wrapped_lines.append("")
            continue

        words = paragraph.split()
        current_line = ""

        for word in words:
            parts = break_long_token(word, font, max_width)
            for part_index, part in enumerate(parts):
                candidate = part if not current_line else f"{current_line} {part}"
                if current_line and font.size(candidate)[0] <= max_width:
                    current_line = candidate
                    continue

                if current_line:
                    wrapped_lines.append(current_line)

                current_line = part
                if part_index < len(parts) - 1:
                    wrapped_lines.append(current_line)
                    current_line = ""

        if current_line:
            wrapped_lines.append(current_line)

    return wrapped_lines


def wrap_items(
    items: str | Iterable[str],
    font: pygame.font.Font,
    max_width: int,
) -> list[str]:
    """Wrap a string or multiple lines into a flat list of display lines."""
    if isinstance(items, str):
        return wrap_text(items, font, max_width)

    wrapped: list[str] = []
    for item in items:
        wrapped.extend(wrap_text(item, font, max_width))
    return wrapped


def line_height(font: pygame.font.Font, line_spacing: int) -> int:
    """Return the height of one rendered line plus spacing."""
    return font.get_linesize() + line_spacing


def ellipsize(text: str, font: pygame.font.Font, max_width: int) -> str:
    """Trim a string to fit inside max_width and end it with an ellipsis."""
    ellipsis = "..."
    if font.size(text)[0] <= max_width:
        return text

    trimmed = text
    while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + ellipsis) if trimmed else ellipsis


def clamp_lines_to_rect(
    lines: list[str],
    font: pygame.font.Font,
    max_width: int,
    max_height: int,
    line_spacing: int = 4,
) -> list[str]:
    """Clamp lines to a rectangle height and ellipsize the last visible line if needed."""
    if max_height <= 0:
        return []

    visible_line_count = (max_height + line_spacing) // line_height(font, line_spacing)
    if visible_line_count <= 0:
        return []
    if len(lines) <= visible_line_count:
        return [ellipsize(line, font, max_width) for line in lines]

    visible_lines = list(lines[:visible_line_count])
    visible_lines[-1] = ellipsize(visible_lines[-1], font, max_width)
    return [ellipsize(line, font, max_width) for line in visible_lines]


def measure_wrapped_items(
    items: str | Iterable[str],
    font: pygame.font.Font,
    max_width: int,
    line_spacing: int = 4,
) -> WrappedText:
    """Measure the wrapped height for a block of text."""
    lines = wrap_items(items, font, max_width)
    total_height = 0 if not lines else len(lines) * line_height(font, line_spacing) - line_spacing
    return WrappedText(lines=lines, height=total_height)


def draw_wrapped_items(
    surface: pygame.Surface,
    items: str | Iterable[str],
    font: pygame.font.Font,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    line_spacing: int = 4,
    align: str = "left",
    clip: bool = True,
) -> int:
    """Draw wrapped text inside a rect and keep it clipped to that rect."""
    wrapped = wrap_items(items, font, rect.width)
    visible_lines = clamp_lines_to_rect(
        wrapped,
        font,
        rect.width,
        rect.height,
        line_spacing=line_spacing,
    )

    old_clip = surface.get_clip()
    if clip:
        surface.set_clip(rect)

    y = rect.y
    for line in visible_lines:
        safe_line = ellipsize(line, font, rect.width)
        rendered = font.render(safe_line, True, color)
        if align == "center":
            x = rect.x + (rect.width - rendered.get_width()) // 2
        elif align == "right":
            x = rect.right - rendered.get_width()
        else:
            x = rect.x
        surface.blit(rendered, (x, y))
        y += line_height(font, line_spacing)

    if clip:
        surface.set_clip(old_clip)

    return y - rect.y
