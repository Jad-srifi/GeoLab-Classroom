"""Theme and font setup for the geometry explorer."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from scripts.geometry.aliases import Color


@dataclass(frozen=True)
class Theme:
    """Centralized color theme so the UI feels intentional and consistent."""

    background_top: Color = (14, 20, 31)
    background_bottom: Color = (8, 12, 19)
    panel: Color = (18, 26, 41)
    panel_alt: Color = (24, 34, 53)
    canvas_fill: Color = (10, 16, 27)
    canvas_border: Color = (89, 112, 154)
    accent: Color = (102, 198, 227)
    accent_warm: Color = (245, 188, 91)
    text: Color = (239, 244, 255)
    muted_text: Color = (172, 187, 220)
    success: Color = (124, 214, 167)
    selection: Color = (255, 236, 173)
    creation_glow: Color = (255, 232, 120)
    comparison: Color = (255, 175, 104)
    handle: Color = (252, 136, 102)
    overlay_backdrop: Color = (6, 9, 15)
    grid_minor: Color = (28, 42, 69)
    grid_major: Color = (43, 63, 102)
    axis_x: Color = (238, 119, 99)
    axis_y: Color = (118, 208, 156)
    intersection: Color = (255, 230, 154)


def choose_font(
    candidates: list[str],
    size: int,
    *,
    bold: bool = False,
    italic: bool = False,
) -> pygame.font.Font:
    """Pick the first installed font from a curated list and fall back safely."""
    for name in candidates:
        path = pygame.font.match_font(name, bold=bold, italic=italic)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont(None, size, bold=bold, italic=italic)


def build_fonts() -> dict[str, pygame.font.Font]:
    """Create a more intentional font hierarchy for the UI."""
    return {
        "hero": choose_font(
            ["Bahnschrift", "Franklin Gothic Medium", "Segoe UI"],
            36,
            bold=True,
        ),
        "section": choose_font(
            ["Bahnschrift", "Segoe UI", "Franklin Gothic Medium"],
            23,
            bold=True,
        ),
        "body": choose_font(
            ["Segoe UI", "Bahnschrift", "Calibri", "Verdana"],
            18,
            bold=True,
        ),
        "small": choose_font(
            ["Segoe UI", "Bahnschrift", "Calibri", "Verdana"],
            16,
            bold=True,
        ),
        "mono": choose_font(
            ["Cascadia Code", "Consolas", "Courier New"],
            15,
        ),
        "command": choose_font(
            ["Cascadia Code", "Consolas", "Courier New"],
            16,
            bold=True,
        ),
    }
