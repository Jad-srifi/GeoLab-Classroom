"""Window layout helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from scripts.app.config import TOOLBAR_BUTTONS


@dataclass
class AppLayout:
    """Stores all major panel rectangles for the current window size."""

    header_rect: pygame.Rect
    toolbar_rect: pygame.Rect
    inspector_rect: pygame.Rect
    inspector_panel_rect: pygame.Rect
    inspector_tabs_rect: pygame.Rect
    canvas_rect: pygame.Rect
    footer_rect: pygame.Rect
    button_rects: dict[str, pygame.Rect]


def create_layout(
    screen_size: tuple[int, int],
    *,
    inspector_expanded: bool = True,
) -> AppLayout:
    """Compute a responsive layout for the current window."""
    width, height = screen_size
    margin = 18
    header_height = 82
    footer_height = 74
    toolbar_width = min(170, max(136, width // 7))
    inspector_tabs_width = min(94, max(74, width // 17))
    inspector_panel_width = min(332, max(248, width // 4))

    available_content_width = max(240, width - margin * 4)
    minimum_canvas_width = 260
    max_side_total = max(0, available_content_width - minimum_canvas_width)
    desired_side_total = toolbar_width + inspector_tabs_width + (
        inspector_panel_width if inspector_expanded else 0
    )
    if desired_side_total > max_side_total:
        overflow = desired_side_total - max_side_total
        if inspector_expanded:
            panel_reduction = min(max(inspector_panel_width - 220, 0), overflow)
            inspector_panel_width -= panel_reduction
            overflow -= panel_reduction
        toolbar_reduction = min(max(toolbar_width - 110, 0), overflow)
        toolbar_width -= toolbar_reduction
        overflow -= toolbar_reduction
        if overflow > 0:
            inspector_tabs_width = max(64, inspector_tabs_width - overflow)

    inspector_width = inspector_tabs_width + (inspector_panel_width if inspector_expanded else 0)

    header_rect = pygame.Rect(0, 0, width, header_height)
    footer_rect = pygame.Rect(0, height - footer_height, width, footer_height)

    content_top = header_rect.bottom + margin
    content_height = max(320, height - content_top - footer_height - margin)

    toolbar_rect = pygame.Rect(margin, content_top, toolbar_width, content_height)
    inspector_rect = pygame.Rect(
        width - inspector_width - margin,
        content_top,
        inspector_width,
        content_height,
    )
    inspector_tabs_rect = pygame.Rect(
        inspector_rect.right - inspector_tabs_width,
        content_top,
        inspector_tabs_width,
        content_height,
    )
    inspector_panel_rect = pygame.Rect(
        inspector_rect.x,
        content_top,
        max(0, inspector_rect.width - inspector_tabs_width),
        content_height,
    )
    canvas_rect = pygame.Rect(
        toolbar_rect.right + margin,
        content_top,
        inspector_rect.left - toolbar_rect.right - margin * 2,
        content_height,
    )

    button_rects: dict[str, pygame.Rect] = {}
    total_gaps = (len(TOOLBAR_BUTTONS) - 1) * 10
    toolbar_button_top = 56
    available_button_height = max(320, toolbar_rect.height - (toolbar_button_top + 26) - total_gaps)
    button_height = max(60, min(78, available_button_height // len(TOOLBAR_BUTTONS)))
    button_width = toolbar_rect.width - 24
    for index, button in enumerate(TOOLBAR_BUTTONS):
        button_rects[button.key] = pygame.Rect(
            toolbar_rect.x + 12,
            toolbar_rect.y + toolbar_button_top + index * (button_height + 10),
            button_width,
            button_height,
        )

    return AppLayout(
        header_rect=header_rect,
        toolbar_rect=toolbar_rect,
        inspector_rect=inspector_rect,
        inspector_panel_rect=inspector_panel_rect,
        inspector_tabs_rect=inspector_tabs_rect,
        canvas_rect=canvas_rect,
        footer_rect=footer_rect,
        button_rects=button_rects,
    )
