"""Rendering helpers for the geometry explorer."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from scripts.app.config import MENU_OPTIONS, TOOLBAR_BUTTONS, TOOL_HELP
from scripts.app.lessons import LESSONS
from scripts.app.text_tools import draw_wrapped_items, ellipsize, measure_wrapped_items
from scripts.geometry.math_utils import format_number
from scripts.geometry.shapes import CircleShape, GeometryShape, RectangleShape

if TYPE_CHECKING:
    from scripts.app.application import GeometryLearningApp


class AppRenderer:
    """Draws the complete UI and geometry scene."""

    def __init__(self, app: "GeometryLearningApp") -> None:
        self.app = app

    def draw(self) -> None:
        """Render the full interface in layers."""
        self.app.overlay_button_rects.clear()
        self.app.sidebar_tab_rects.clear()
        self.app.sidebar_close_rect = None
        self.draw_gradient_background()
        self.draw_header()
        self.draw_toolbar()
        self.draw_canvas()
        self.draw_inspector()
        self.draw_footer()
        self.draw_overlay()

    def draw_gradient_background(self) -> None:
        """Paint a soft top-to-bottom gradient behind every panel."""
        width, height = self.app.screen.get_size()
        for y in range(height):
            blend = y / max(height - 1, 1)
            color = self.lerp_color(
                self.app.theme.background_top,
                self.app.theme.background_bottom,
                blend,
            )
            pygame.draw.line(self.app.screen, color, (0, y), (width, y))

    def draw_panel(
        self,
        rect: pygame.Rect,
        fill: tuple[int, int, int],
        border: tuple[int, int, int],
    ) -> None:
        """Draw a rounded panel with a subtle shadow."""
        shadow_surface = pygame.Surface((rect.width + 18, rect.height + 18), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surface,
            (0, 0, 0, 70),
            shadow_surface.get_rect(),
            border_radius=24,
        )
        self.app.screen.blit(shadow_surface, (rect.x + 6, rect.y + 10))
        pygame.draw.rect(self.app.screen, fill, rect, border_radius=24)
        pygame.draw.rect(self.app.screen, border, rect, width=2, border_radius=24)

    def draw_header(self) -> None:
        """Render the title, subtitle, and active tool summary."""
        rect = self.app.layout.header_rect.inflate(-20, -12)
        self.draw_panel(rect, self.app.theme.panel, self.app.theme.canvas_border)

        title = self.app.fonts["hero"].render("GeoLab Classroom", True, self.app.theme.text)
        self.app.screen.blit(title, (rect.x + 18, rect.y + 10))

        subtitle_rect = pygame.Rect(rect.x + 20, rect.y + 46, rect.width - 430, 34)
        draw_wrapped_items(
            self.app.screen,
            "See the math move: build shapes, compare them, graph them, and let the picture explain the formula.",
            self.app.fonts["body"],
            self.app.theme.muted_text,
            subtitle_rect,
            line_spacing=2,
        )

        tool_card = pygame.Rect(rect.right - 328, rect.y + 10, 308, rect.height - 20)
        pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, tool_card, border_radius=18)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            tool_card,
            width=2,
            border_radius=18,
        )

        tool_title = self.app.fonts["section"].render(
            self.app.state.active_tool.title(),
            True,
            self.app.theme.accent_warm,
        )
        self.app.screen.blit(tool_title, (tool_card.x + 14, tool_card.y + 10))
        draw_wrapped_items(
            self.app.screen,
            TOOL_HELP[self.app.state.active_tool],
            self.app.fonts["small"],
            self.app.theme.text,
            pygame.Rect(tool_card.x + 14, tool_card.y + 40, tool_card.width - 28, tool_card.height - 50),
            line_spacing=2,
        )

    def draw_toolbar(self) -> None:
        """Render the vertical tool palette."""
        self.draw_panel(
            self.app.layout.toolbar_rect,
            self.app.theme.panel,
            self.app.theme.canvas_border,
        )

        label = self.app.fonts["section"].render("Tools", True, self.app.theme.text)
        self.app.screen.blit(label, (self.app.layout.toolbar_rect.x + 18, self.app.layout.toolbar_rect.y + 16))

        for button in TOOLBAR_BUTTONS:
            rect = self.app.layout.button_rects[button.key]
            is_active = self.app.state.active_tool == button.key
            fill = self.app.theme.selection if is_active else self.app.theme.panel_alt
            border_color = self.app.theme.accent_warm if is_active else self.app.theme.canvas_border
            text_color = self.app.theme.background_bottom if is_active else self.app.theme.text

            pygame.draw.rect(self.app.screen, fill, rect, border_radius=16)
            pygame.draw.rect(
                self.app.screen,
                border_color,
                rect,
                width=2,
                border_radius=16,
            )

            title = self.app.fonts["body"].render(button.title, True, text_color)
            hotkey = self.app.fonts["command"].render(button.hotkey, True, text_color)
            self.app.screen.blit(title, (rect.x + 14, rect.y + 10))
            self.app.screen.blit(hotkey, (rect.right - hotkey.get_width() - 12, rect.y + 10))

            description_rect = pygame.Rect(rect.x + 14, rect.y + 36, rect.width - 28, rect.height - 44)
            draw_wrapped_items(
                self.app.screen,
                button.description,
                self.app.fonts["small"],
                text_color,
                description_rect,
                line_spacing=1,
            )

    def draw_canvas(self) -> None:
        """Render the central graphing area, its grid, graphs, shapes, and overlays."""
        self.draw_panel(
            self.app.layout.canvas_rect,
            self.app.theme.canvas_fill,
            self.app.theme.canvas_border,
        )

        old_clip = self.app.screen.get_clip()
        self.app.screen.set_clip(self.app.layout.canvas_rect)

        self.draw_grid()
        self.draw_function_graphs()
        self.draw_transform_ghost()
        self.draw_shape_fills()
        self.draw_shape_outlines()
        self.draw_function_intersections()
        self.draw_pending_preview()
        self.draw_selected_shape_badge()
        self.draw_help_overlay()
        self.draw_cursor_pill()

        self.app.screen.set_clip(old_clip)

    def draw_grid(self) -> None:
        """Draw a responsive graph-paper grid with axis labels."""
        left, right, bottom, top = self.app.visible_world_bounds()
        step = self.app.current_grid_step()

        start_x = math.floor(left / step) - 1
        end_x = math.ceil(right / step) + 1
        start_y = math.floor(bottom / step) - 1
        end_y = math.ceil(top / step) + 1

        for x_index in range(start_x, end_x + 1):
            world_x = x_index * step
            screen_x, _ = self.app.world_to_screen((world_x, 0))
            color = self.app.theme.grid_major if x_index % 5 == 0 else self.app.theme.grid_minor
            pygame.draw.line(
                self.app.screen,
                color,
                (screen_x, self.app.layout.canvas_rect.top),
                (screen_x, self.app.layout.canvas_rect.bottom),
                1,
            )

        for y_index in range(start_y, end_y + 1):
            world_y = y_index * step
            _, screen_y = self.app.world_to_screen((0, world_y))
            color = self.app.theme.grid_major if y_index % 5 == 0 else self.app.theme.grid_minor
            pygame.draw.line(
                self.app.screen,
                color,
                (self.app.layout.canvas_rect.left, screen_y),
                (self.app.layout.canvas_rect.right, screen_y),
                1,
            )

        axis_x, axis_y = self.app.world_to_screen((0, 0))
        pygame.draw.line(
            self.app.screen,
            self.app.theme.axis_x,
            (self.app.layout.canvas_rect.left, axis_y),
            (self.app.layout.canvas_rect.right, axis_y),
            2,
        )
        pygame.draw.line(
            self.app.screen,
            self.app.theme.axis_y,
            (axis_x, self.app.layout.canvas_rect.top),
            (axis_x, self.app.layout.canvas_rect.bottom),
            2,
        )

        self.draw_axis_numbers(step)

    def draw_axis_numbers(self, step: float) -> None:
        """Label the major grid lines without overcrowding the canvas."""
        left, right, bottom, top = self.app.visible_world_bounds()
        font = self.app.fonts["small"]
        axis_x, axis_y = self.app.world_to_screen((0, 0))

        for x_index in range(math.floor(left / step), math.ceil(right / step) + 1):
            if x_index == 0 or x_index % 5 != 0:
                continue
            world_x = x_index * step
            screen_x, _ = self.app.world_to_screen((world_x, 0))
            label = font.render(format_number(world_x), True, self.app.theme.muted_text)
            self.app.screen.blit(
                label,
                (screen_x + 4, min(self.app.layout.canvas_rect.bottom - 18, axis_y + 6)),
            )

        for y_index in range(math.floor(bottom / step), math.ceil(top / step) + 1):
            if y_index == 0 or y_index % 5 != 0:
                continue
            world_y = y_index * step
            _, screen_y = self.app.world_to_screen((0, world_y))
            label = font.render(format_number(world_y), True, self.app.theme.muted_text)
            self.app.screen.blit(
                label,
                (max(self.app.layout.canvas_rect.left + 6, axis_x + 6), screen_y - 8),
            )

    def draw_function_graphs(self) -> None:
        """Plot enabled graph presets and custom equations behind the geometry."""
        for entry in self.app.runtime_function_entries():
            for segment in self.sample_function_segments(entry.evaluator):
                if len(segment) >= 2:
                    pygame.draw.lines(self.app.screen, entry.color, False, segment, 3)

    def sample_function_segments(self, evaluator) -> list[list[tuple[int, int]]]:
        """Sample a function into screen-space segments while skipping discontinuities."""
        left, right, _, _ = self.app.visible_world_bounds()
        step = max(0.03, 3.0 / self.app.scale)
        max_vertical_jump = self.app.layout.canvas_rect.height * 0.65
        current_segment: list[tuple[int, int]] = []
        finished_segments: list[list[tuple[int, int]]] = []

        x = left
        while x <= right:
            try:
                y = evaluator(x)
                if math.isfinite(y):
                    screen_point = self.app.world_to_screen((x, y))
                    if current_segment and abs(screen_point[1] - current_segment[-1][1]) > max_vertical_jump:
                        if len(current_segment) >= 2:
                            finished_segments.append(current_segment)
                        current_segment = []
                    current_segment.append(screen_point)
                else:
                    if len(current_segment) >= 2:
                        finished_segments.append(current_segment)
                    current_segment = []
            except Exception:
                if len(current_segment) >= 2:
                    finished_segments.append(current_segment)
                current_segment = []
            x += step

        if len(current_segment) >= 2:
            finished_segments.append(current_segment)
        return finished_segments

    def draw_transform_ghost(self) -> None:
        """Draw a translucent overlay for the shape before the last transform."""
        if self.app.state.transform_ghost is None:
            return
        self.draw_shape(
            self.app.state.transform_ghost,
            outline_color=(190, 201, 230),
            line_width=2,
            fill_alpha=24,
        )

    def draw_shape_fills(self) -> None:
        """Draw transparent fills on a separate surface for a softer visual style."""
        overlay = pygame.Surface(self.app.screen.get_size(), pygame.SRCALPHA)
        overlay.set_clip(self.app.layout.canvas_rect)

        for shape in self.app.shapes:
            is_selected = self.app.state.selected_shape_id == shape.id
            is_hovered = (
                self.app.state.active_tool == "select"
                and self.app.state.hovered_shape_id == shape.id
                and not is_selected
            )
            is_comparison = self.app.state.comparison_shape_id == shape.id

            fill_base = shape.color
            fill_alpha = 48
            if is_selected:
                fill_base = self.lerp_color(shape.color, self.app.theme.selection, 0.48)
                fill_alpha = 66
            elif is_comparison:
                fill_base = self.lerp_color(shape.color, self.app.theme.comparison, 0.4)
                fill_alpha = 60
            elif is_hovered:
                fill_base = self.emphasize_color(shape.color, 0.22)
                fill_alpha = 72

            fill_color = (*fill_base, fill_alpha)
            if shape.kind == "circle":
                circle = shape
                radius = max(1, int(circle.radius() * self.app.scale))
                pygame.draw.circle(
                    overlay,
                    fill_color,
                    self.app.world_to_screen(circle.center),
                    radius,
                )
            elif shape.kind in {"triangle", "rectangle", "polygon"}:
                points = [self.app.world_to_screen(point) for point in shape.vertices()]
                if len(points) >= 3:
                    pygame.draw.polygon(overlay, fill_color, points)

        self.app.screen.blit(overlay, (0, 0))

    def draw_shape_outlines(self) -> None:
        """Render the visible shape boundaries and their selection handles."""
        for shape in self.app.shapes:
            is_selected = self.app.state.selected_shape_id == shape.id
            is_hovered = (
                self.app.state.hovered_shape_id == shape.id
                and self.app.state.active_tool == "select"
                and not is_selected
            )
            is_comparison = self.app.state.comparison_shape_id == shape.id

            outline_color = shape.color
            line_width = 3
            if is_selected:
                outline_color = self.lerp_color(shape.color, self.app.theme.selection, 0.62)
                line_width = 4
            elif is_comparison:
                outline_color = self.lerp_color(shape.color, self.app.theme.comparison, 0.58)
                line_width = 4
            elif is_hovered:
                outline_color = self.emphasize_color(shape.color, 0.28)
                line_width = 4

            self.draw_shape(shape, outline_color, line_width)

            if is_comparison:
                self.draw_selection_ring(shape, self.app.theme.comparison)

            if is_selected:
                self.draw_selection_ring(shape, self.app.theme.selection)
                for handle_point in shape.handle_positions():
                    handle_screen = self.app.world_to_screen(handle_point)
                    pygame.draw.circle(self.app.screen, self.app.theme.handle, handle_screen, 6)
                    pygame.draw.circle(self.app.screen, self.app.theme.text, handle_screen, 6, 2)

    def draw_shape(
        self,
        shape: GeometryShape,
        outline_color: tuple[int, int, int],
        line_width: int,
        fill_alpha: int = 0,
    ) -> None:
        """Draw one shape with optional translucent fill."""
        if fill_alpha > 0 and shape.kind in {"triangle", "rectangle", "polygon"}:
            overlay = pygame.Surface(self.app.screen.get_size(), pygame.SRCALPHA)
            overlay.set_clip(self.app.layout.canvas_rect)
            points = [self.app.world_to_screen(point) for point in shape.vertices()]
            if len(points) >= 3:
                pygame.draw.polygon(overlay, (*outline_color, fill_alpha), points)
                self.app.screen.blit(overlay, (0, 0))

        if shape.kind == "point":
            pygame.draw.circle(
                self.app.screen,
                outline_color,
                self.app.world_to_screen(shape.position),
                7,
            )
        elif shape.kind == "segment":
            pygame.draw.line(
                self.app.screen,
                outline_color,
                self.app.world_to_screen(shape.start),
                self.app.world_to_screen(shape.end),
                line_width,
            )
        elif shape.kind == "circle":
            radius = max(1, int(shape.radius() * self.app.scale))
            pygame.draw.circle(
                self.app.screen,
                outline_color,
                self.app.world_to_screen(shape.center),
                radius,
                line_width,
            )
        else:
            points = [self.app.world_to_screen(point) for point in shape.vertices()]
            if len(points) >= 2:
                pygame.draw.lines(
                    self.app.screen,
                    outline_color,
                    True,
                    points,
                    line_width,
                )

    def draw_selection_ring(self, shape: GeometryShape, color: tuple[int, int, int]) -> None:
        """Draw a soft extra outline around a highlighted shape."""
        if shape.kind == "circle":
            radius = max(1, int(shape.radius() * self.app.scale) + 7)
            pygame.draw.circle(
                self.app.screen,
                color,
                self.app.world_to_screen(shape.center),
                radius,
                2,
            )
            return

        points = [self.app.world_to_screen(point) for point in shape.vertices()]
        if len(points) == 1:
            pygame.draw.circle(self.app.screen, color, points[0], 12, 2)
        elif len(points) == 2 and shape.kind == "segment":
            pygame.draw.line(self.app.screen, color, points[0], points[1], 1)
        else:
            pygame.draw.lines(self.app.screen, color, True, points, 2)

    def draw_function_intersections(self) -> None:
        """Mark visible intersections between active functions."""
        if not self.app.state.show_intersections:
            return

        intersections = self.app.function_intersections()
        for point, label in intersections[:6]:
            screen_point = self.app.world_to_screen(point)
            pygame.draw.circle(self.app.screen, self.app.theme.intersection, screen_point, 5)
            pygame.draw.circle(self.app.screen, self.app.theme.background_bottom, screen_point, 2)

            padding = 6
            preferred_width = 214
            label_x = screen_point[0] + 8
            if label_x + preferred_width > self.app.layout.canvas_rect.right - 8:
                label_x = max(
                    self.app.layout.canvas_rect.left + 8,
                    screen_point[0] - preferred_width - 8,
                )

            max_width = min(
                preferred_width,
                self.app.layout.canvas_rect.right - label_x - 8,
            )
            wrapped = measure_wrapped_items(
                label,
                self.app.fonts["small"],
                max(40, max_width - padding * 2),
                line_spacing=1,
            )
            label_height = min(
                72,
                max(self.app.fonts["small"].get_linesize() + padding * 2, wrapped.height + padding * 2),
            )
            label_y = max(
                self.app.layout.canvas_rect.top + 8,
                min(
                    screen_point[1] - label_height + 6,
                    self.app.layout.canvas_rect.bottom - label_height - 8,
                ),
            )
            label_rect = pygame.Rect(
                label_x,
                label_y,
                max(40, max_width),
                label_height,
            )
            pygame.draw.rect(self.app.screen, (15, 22, 34), label_rect, border_radius=10)
            pygame.draw.rect(
                self.app.screen,
                self.app.theme.intersection,
                label_rect,
                width=1,
                border_radius=10,
            )
            draw_wrapped_items(
                self.app.screen,
                label,
                self.app.fonts["small"],
                self.app.theme.intersection,
                pygame.Rect(
                    label_rect.x + padding,
                    label_rect.y + padding - 1,
                    label_rect.width - padding * 2,
                    label_rect.height - padding * 2 + 2,
                ),
                line_spacing=1,
            )

    def draw_pending_preview(self) -> None:
        """Draw the in-progress construction with glowing guide points."""
        if self.app.state.active_tool == "select":
            return

        preview_point = self.app.state.preview_point
        if preview_point is None and not self.app.state.pending_points:
            return

        preview_points = list(self.app.state.pending_points)
        if preview_point is not None and self.app.state.active_tool != "point":
            preview_points.append(preview_point)

        preview_color = self.app.theme.accent

        if self.app.state.active_tool == "point" and preview_point is not None:
            self.draw_glow_marker(preview_point, "A")
        elif self.app.state.active_tool == "segment" and len(preview_points) == 2:
            pygame.draw.line(
                self.app.screen,
                preview_color,
                self.app.world_to_screen(preview_points[0]),
                self.app.world_to_screen(preview_points[1]),
                2,
            )
        elif self.app.state.active_tool == "triangle" and len(preview_points) >= 2:
            pygame.draw.lines(
                self.app.screen,
                preview_color,
                len(preview_points) >= 3,
                [self.app.world_to_screen(point) for point in preview_points],
                2,
            )
        elif self.app.state.active_tool == "rectangle" and len(preview_points) == 2:
            rectangle = RectangleShape(
                id=-1,
                label="Preview",
                kind="rectangle",
                color=preview_color,
                corner_a=preview_points[0],
                corner_b=preview_points[1],
            )
            pygame.draw.lines(
                self.app.screen,
                preview_color,
                True,
                [self.app.world_to_screen(point) for point in rectangle.vertices()],
                2,
            )
        elif self.app.state.active_tool == "circle" and len(preview_points) == 2:
            circle = CircleShape(
                id=-1,
                label="Preview",
                kind="circle",
                color=preview_color,
                center=preview_points[0],
                radius_point=preview_points[1],
            )
            pygame.draw.circle(
                self.app.screen,
                preview_color,
                self.app.world_to_screen(circle.center),
                max(1, int(circle.radius() * self.app.scale)),
                2,
            )
        elif self.app.state.active_tool == "polygon" and len(preview_points) >= 2:
            pygame.draw.lines(
                self.app.screen,
                preview_color,
                False,
                [self.app.world_to_screen(point) for point in preview_points],
                2,
            )

        for index, point in enumerate(self.app.state.pending_points):
            self.draw_glow_marker(point, chr(65 + index))
        if preview_point is not None and self.app.state.active_tool != "point":
            self.draw_glow_marker(preview_point, chr(65 + len(self.app.state.pending_points)))

    def draw_glow_marker(self, point, label: str) -> None:
        """Draw the glowing yellow construction marker used during shape creation."""
        screen_point = self.app.world_to_screen(point)
        glow_surface = pygame.Surface((48, 48), pygame.SRCALPHA)
        center = (24, 24)
        pygame.draw.circle(glow_surface, (*self.app.theme.creation_glow, 40), center, 18)
        pygame.draw.circle(glow_surface, (*self.app.theme.creation_glow, 90), center, 11)
        pygame.draw.circle(glow_surface, self.app.theme.creation_glow, center, 5)
        self.app.screen.blit(glow_surface, (screen_point[0] - 24, screen_point[1] - 24))

        text = self.app.fonts["command"].render(label, True, self.app.theme.background_bottom)
        self.app.screen.blit(text, (screen_point[0] - text.get_width() // 2, screen_point[1] - 9))

    def draw_help_overlay(self) -> None:
        """Render a compact teaching overlay on the canvas when enabled."""
        if not self.app.state.show_help:
            return

        tips = [
            TOOL_HELP[self.app.state.active_tool],
            "Esc opens the menu. / opens commands. F opens the function builder. J opens lessons.",
            "Shift+Click picks a comparison shape. Use the pulse buttons to animate a, b, c, or t.",
        ]
        padding = 14
        max_width = min(390, self.app.layout.canvas_rect.width - 36)
        text_height = measure_wrapped_items(
            tips,
            self.app.fonts["small"],
            max_width - padding * 2,
            line_spacing=2,
        ).height
        overlay_rect = pygame.Rect(
            self.app.layout.canvas_rect.x + 18,
            self.app.layout.canvas_rect.y + 18,
            max_width,
            padding * 2 + self.app.fonts["section"].get_linesize() + 12 + text_height,
        )
        pygame.draw.rect(self.app.screen, (12, 18, 29), overlay_rect, border_radius=18)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            overlay_rect,
            width=2,
            border_radius=18,
        )

        title = self.app.fonts["section"].render("Quick Help", True, self.app.theme.text)
        self.app.screen.blit(title, (overlay_rect.x + 14, overlay_rect.y + 12))
        draw_wrapped_items(
            self.app.screen,
            tips,
            self.app.fonts["small"],
            self.app.theme.muted_text,
            pygame.Rect(
                overlay_rect.x + padding,
                overlay_rect.y + padding + self.app.fonts["section"].get_linesize() + 10,
                overlay_rect.width - padding * 2,
                overlay_rect.height - padding * 2 - self.app.fonts["section"].get_linesize() - 10,
            ),
            line_spacing=2,
        )

    def draw_selected_shape_badge(self) -> None:
        """Show a small floating card near the selected shape."""
        anchor = self.app.selected_shape_anchor()
        lines = self.app.selected_shape_badge_lines()
        if anchor is None or not lines:
            return

        padding = 12
        card_width = min(300, max(220, self.longest_line_width(lines, self.app.fonts["small"]) + padding * 2))
        body_height = measure_wrapped_items(
            lines[1:],
            self.app.fonts["small"],
            card_width - padding * 2,
            line_spacing=2,
        ).height
        card_height = padding * 2 + self.app.fonts["body"].get_linesize() + 8 + body_height
        x = min(
            max(self.app.layout.canvas_rect.left + 12, anchor[0] + 14),
            self.app.layout.canvas_rect.right - card_width - 12,
        )
        y = min(
            max(self.app.layout.canvas_rect.top + 12, anchor[1] - card_height - 12),
            self.app.layout.canvas_rect.bottom - card_height - 12,
        )
        rect = pygame.Rect(x, y, card_width, card_height)

        pygame.draw.rect(self.app.screen, (14, 21, 33), rect, border_radius=16)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.selection,
            rect,
            width=2,
            border_radius=16,
        )

        title = self.app.fonts["body"].render(lines[0], True, self.app.theme.selection)
        self.app.screen.blit(title, (rect.x + padding, rect.y + padding - 2))
        draw_wrapped_items(
            self.app.screen,
            lines[1:],
            self.app.fonts["small"],
            self.app.theme.text,
            pygame.Rect(
                rect.x + padding,
                rect.y + padding + self.app.fonts["body"].get_linesize() + 6,
                rect.width - padding * 2,
                rect.height - padding * 2 - self.app.fonts["body"].get_linesize() - 6,
            ),
            line_spacing=2,
        )

    def draw_cursor_pill(self) -> None:
        """Show the current cursor coordinates inside the canvas."""
        label = (
            f"Cursor ({format_number(self.app.state.cursor_world[0])}, "
            f"{format_number(self.app.state.cursor_world[1])})"
        )
        rendered = self.app.fonts["small"].render(label, True, self.app.theme.text)
        rect = pygame.Rect(
            self.app.layout.canvas_rect.right - rendered.get_width() - 28,
            self.app.layout.canvas_rect.bottom - 44,
            rendered.get_width() + 16,
            28,
        )
        pygame.draw.rect(self.app.screen, (14, 20, 31), rect, border_radius=14)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            rect,
            width=2,
            border_radius=14,
        )
        self.app.screen.blit(rendered, (rect.x + 8, rect.y + 6))

    def draw_inspector(self) -> None:
        """Render the collapsible right rail plus the active section panel."""
        self.app.graph_chip_rects.clear()
        self.app.slider_bar_rects.clear()
        self.app.slider_toggle_rects.clear()

        self.draw_panel(
            self.app.layout.inspector_rect,
            self.app.theme.panel,
            self.app.theme.canvas_border,
        )
        self.draw_sidebar_rail()

        if self.app.state.sidebar_section is None or self.app.layout.inspector_panel_rect.width <= 0:
            return

        panel_rect = self.app.layout.inspector_panel_rect.inflate(-10, -10)
        pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, panel_rect, border_radius=22)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            panel_rect,
            width=2,
            border_radius=22,
        )

        section = self.active_sidebar_section()
        if section is None:
            return

        header_padding = 16
        close_rect = pygame.Rect(panel_rect.right - 38, panel_rect.y + 14, 24, 24)
        self.app.sidebar_close_rect = close_rect
        pygame.draw.rect(self.app.screen, self.app.theme.panel, close_rect, border_radius=10)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            close_rect,
            width=1,
            border_radius=10,
        )
        close_text = self.app.fonts["command"].render(">", True, self.app.theme.text)
        self.app.screen.blit(
            close_text,
            (close_rect.x + (close_rect.width - close_text.get_width()) // 2, close_rect.y + 2),
        )

        title = self.app.fonts["section"].render(section.label, True, self.app.theme.accent_warm)
        self.app.screen.blit(title, (panel_rect.x + header_padding, panel_rect.y + 12))

        description_rect = pygame.Rect(
            panel_rect.x + header_padding,
            panel_rect.y + 42,
            panel_rect.width - header_padding * 2 - close_rect.width - 10,
            42,
        )
        draw_wrapped_items(
            self.app.screen,
            section.description,
            self.app.fonts["small"],
            self.app.theme.muted_text,
            description_rect,
            line_spacing=1,
        )

        content_rect = pygame.Rect(
            panel_rect.x + header_padding,
            panel_rect.y + 92,
            panel_rect.width - header_padding * 2,
            panel_rect.height - 106,
        )
        if section.key == "details":
            self.draw_details_section(content_rect)
        elif section.key == "graphs":
            self.draw_graphs_section(content_rect)
        elif section.key == "learn":
            self.draw_learning_section(content_rect)

    def draw_sidebar_rail(self) -> None:
        """Draw the always-visible section rail on the far right."""
        rail_rect = self.app.layout.inspector_tabs_rect.inflate(-8, -10)
        pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, rail_rect, border_radius=20)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            rail_rect,
            width=2,
            border_radius=20,
        )

        header_rect = pygame.Rect(rail_rect.x + 8, rail_rect.y + 12, rail_rect.width - 16, 24)
        draw_wrapped_items(
            self.app.screen,
            "PANELS",
            self.app.fonts["command"],
            self.app.theme.accent_warm,
            header_rect,
            line_spacing=0,
            align="center",
        )

        button_y = rail_rect.y + 52
        button_height = 52
        for section in self.app.sidebar_sections():
            button_rect = pygame.Rect(rail_rect.x + 8, button_y, rail_rect.width - 16, button_height)
            self.app.sidebar_tab_rects[section.key] = button_rect
            is_active = self.app.state.sidebar_section == section.key
            fill = self.app.theme.accent_warm if is_active else self.app.theme.panel
            border_color = self.app.theme.selection if is_active else self.app.theme.accent_warm
            text_color = self.app.theme.background_bottom if is_active else self.app.theme.selection

            pygame.draw.rect(self.app.screen, fill, button_rect, border_radius=16)
            pygame.draw.rect(
                self.app.screen,
                border_color,
                button_rect,
                width=2,
                border_radius=16,
            )

            label_rect = pygame.Rect(button_rect.x + 6, button_rect.y + 8, button_rect.width - 12, button_rect.height - 16)
            draw_wrapped_items(
                self.app.screen,
                section.label,
                self.app.fonts["command"],
                text_color,
                label_rect,
                line_spacing=0,
                align="center",
            )
            button_y += button_height + 12

    def active_sidebar_section(self):
        """Return the currently open right-side section definition."""
        return next(
            (section for section in self.app.sidebar_sections() if section.key == self.app.state.sidebar_section),
            None,
        )

    def draw_details_section(self, content_rect: pygame.Rect) -> None:
        """Render measurement and formula cards for the selected object."""
        y = content_rect.y
        if self.app.selected_shape is None:
            cards = [
                (
                    "Scene Focus",
                    [
                        "Select any shape to inspect its measurements, formulas, and constraints here.",
                        "Close this rail any time if you want the graph canvas to take the full width.",
                    ],
                    self.app.fonts["small"],
                ),
                (
                    "Transform Notes",
                    self.app.transform_summary_lines(),
                    self.app.fonts["small"],
                ),
            ]
        else:
            cards = [
                (
                    "Measurements",
                    self.app.selected_shape.summary_lines(),
                    self.app.fonts["small"],
                ),
                (
                    "Live Formula",
                    self.app.selected_shape.formula_lines(),
                    self.app.fonts["mono"],
                ),
                (
                    "Constraints",
                    self.app.constraint_summary_lines(),
                    self.app.fonts["small"],
                ),
                (
                    "Transform Notes",
                    self.app.transform_summary_lines(),
                    self.app.fonts["small"],
                ),
            ]

        for title, lines, font in cards:
            available_height = content_rect.bottom - y
            if available_height < 72:
                break
            card_height = self.draw_text_card(
                title,
                lines,
                font,
                pygame.Rect(content_rect.x, y, content_rect.width, available_height),
            )
            y += card_height + 12

    def draw_graphs_section(self, content_rect: pygame.Rect) -> None:
        """Render the graph presets plus the live parameter controls."""
        y = content_rect.y
        remaining_height = content_rect.bottom - y
        if remaining_height >= 150:
            slider_budget = remaining_height
            if remaining_height >= 250:
                slider_budget = min(
                    remaining_height - 92,
                    max(176, remaining_height // 2),
                )
            slider_height = self.draw_slider_card(
                pygame.Rect(content_rect.x, y, content_rect.width, slider_budget)
            )
            y += slider_height + 12
            remaining_height = content_rect.bottom - y

        if remaining_height >= 80:
            self.draw_graph_toggle_card(
                pygame.Rect(content_rect.x, y, content_rect.width, remaining_height)
            )

    def draw_learning_section(self, content_rect: pygame.Rect) -> None:
        """Render lesson guidance and project-direction cards."""
        y = content_rect.y
        cards = [
            (
                "Guided Lesson",
                self.app.lesson_summary_lines(),
                self.app.fonts["small"],
            ),
            (
                "Project Goal",
                [
                    "Make geometry visual enough that students explore ideas instead of memorizing isolated formulas.",
                    "Use the graph canvas, the collapsible panels, and the live formulas together like one lesson surface.",
                ],
                self.app.fonts["small"],
            ),
            (
                "Next Improvements",
                self.app.active_roadmap_ideas(),
                self.app.fonts["small"],
            ),
        ]

        for title, lines, font in cards:
            available_height = content_rect.bottom - y
            if available_height < 72:
                break
            card_height = self.draw_text_card(
                title,
                lines,
                font,
                pygame.Rect(content_rect.x, y, content_rect.width, available_height),
            )
            y += card_height + 12

    def draw_text_card(
        self,
        title: str,
        lines: list[str],
        font: pygame.font.Font,
        bounds: pygame.Rect,
    ) -> int:
        """Draw one text card and return the height it consumed."""
        padding = 14
        title_height = self.app.fonts["body"].get_linesize()
        measured = measure_wrapped_items(lines, font, bounds.width - padding * 2, line_spacing=2)
        natural_height = padding * 2 + title_height + 8 + measured.height
        card_height = min(max(80, natural_height), bounds.height)
        rect = pygame.Rect(bounds.x, bounds.y, bounds.width, card_height)

        pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, rect, border_radius=18)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            rect,
            width=2,
            border_radius=18,
        )

        title_surface = self.app.fonts["body"].render(title, True, self.app.theme.accent_warm)
        self.app.screen.blit(title_surface, (rect.x + padding, rect.y + padding))

        draw_wrapped_items(
            self.app.screen,
            lines,
            font,
            self.app.theme.text if font == self.app.fonts["mono"] else self.app.theme.muted_text,
            pygame.Rect(
                rect.x + padding,
                rect.y + padding + title_height + 8,
                rect.width - padding * 2,
                rect.height - padding * 2 - title_height - 8,
            ),
            line_spacing=2,
        )
        return card_height

    def draw_slider_card(self, bounds: pygame.Rect) -> int:
        """Draw the slider card used by custom equations."""
        padding = 14
        row_height = 34
        title_height = self.app.fonts["body"].get_linesize()
        help_text = (
            "Drag a parameter or hit its pulse button to animate it. "
            "Quadratic Lab uses a, b, and c, while Tab still toggles t."
        )
        help_height = measure_wrapped_items(
            help_text,
            self.app.fonts["small"],
            bounds.width - padding * 2,
            line_spacing=2,
        ).height
        natural_height = padding * 2 + title_height + 10 + len(self.app.state.sliders) * row_height + 8 + help_height
        rect = pygame.Rect(bounds.x, bounds.y, bounds.width, min(max(176, natural_height), bounds.height))
        pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, rect, border_radius=18)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            rect,
            width=2,
            border_radius=18,
        )

        title = self.app.fonts["body"].render("Parameters", True, self.app.theme.accent_warm)
        self.app.screen.blit(title, (rect.x + padding, rect.y + padding))

        self.app.slider_bar_rects.clear()
        self.app.slider_toggle_rects.clear()

        y = rect.y + padding + title_height + 12
        for slider_name, slider in self.app.state.sliders.items():
            label = self.app.fonts["small"].render(
                f"{slider_name} = {format_number(slider.value)}",
                True,
                self.app.theme.text,
            )
            self.app.screen.blit(label, (rect.x + padding, y))

            toggle_rect = pygame.Rect(rect.right - 34, y - 1, 20, 20)
            self.app.slider_toggle_rects[slider_name] = toggle_rect
            pygame.draw.rect(
                self.app.screen,
                self.app.theme.success if slider.animated else (56, 64, 84),
                toggle_rect,
                border_radius=7,
            )
            icon = "||" if slider.animated else ">"
            icon_color = self.app.theme.background_bottom if slider.animated else self.app.theme.text
            icon_surface = self.app.fonts["small"].render(icon, True, icon_color)
            self.app.screen.blit(icon_surface, (toggle_rect.x + 4, toggle_rect.y + 1))

            bar_rect = pygame.Rect(rect.x + 122, y + 6, rect.width - 182, 8)
            self.app.slider_bar_rects[slider_name] = bar_rect
            pygame.draw.rect(self.app.screen, (42, 55, 78), bar_rect, border_radius=4)
            ratio = (slider.value - slider.min_value) / (slider.max_value - slider.min_value)
            ratio = max(0.0, min(1.0, ratio))
            fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * ratio), bar_rect.height)
            pygame.draw.rect(self.app.screen, self.app.theme.accent, fill_rect, border_radius=4)
            knob_x = bar_rect.x + int(bar_rect.width * ratio)
            pygame.draw.circle(self.app.screen, self.app.theme.selection, (knob_x, bar_rect.centery), 7)
            pygame.draw.circle(self.app.screen, self.app.theme.background_bottom, (knob_x, bar_rect.centery), 3)

            y += row_height

        help_rect = pygame.Rect(rect.x + padding, y + 4, rect.width - padding * 2, rect.bottom - y - padding)
        draw_wrapped_items(
            self.app.screen,
            help_text,
            self.app.fonts["small"],
            self.app.theme.muted_text,
            help_rect,
            line_spacing=2,
        )
        return rect.height

    def draw_graph_toggle_card(self, bounds: pygame.Rect) -> int:
        """Render clickable function chips in a dedicated card."""
        padding = 14
        title_height = self.app.fonts["body"].get_linesize()
        token_and_labels = []
        for preset in self.app.function_presets:
            token_and_labels.append((f"preset:{preset.name}", f"{preset.name} ({preset.expression})", preset.color, preset.name in self.app.state.active_function_names))
        for custom_function in self.app.state.custom_functions:
            token_and_labels.append(
                (
                    f"custom:{custom_function.id}",
                    f"{custom_function.name}: {custom_function.expression}",
                    custom_function.color,
                    custom_function.enabled,
                )
            )

        chip_height = 34
        chip_layouts: list[tuple[str, pygame.Rect, tuple[int, int, int], bool, str]] = []
        chip_x = bounds.x + padding
        chip_y = bounds.y + padding + title_height + 14
        max_chip_right = bounds.right - padding
        for token, label, color, active in token_and_labels:
            rendered = self.app.fonts["small"].render(label, True, self.app.theme.background_bottom)
            chip_width = min(bounds.width - padding * 2, rendered.get_width() + 26)
            if chip_x + chip_width > max_chip_right:
                chip_x = bounds.x + padding
                chip_y += chip_height + 8
            chip_rect = pygame.Rect(chip_x, chip_y, chip_width, chip_height)
            chip_layouts.append((token, chip_rect, color, active, label))
            chip_x += chip_width + 8

        description_lines = [
            "Use 1, 2, 3, or 4 for starter graphs. Quadratic Lab responds directly to sliders a, b, and c.",
            "Press F to build your own function. If it is attached to a point, px and py inherit that point's coordinates.",
        ]
        description_top = chip_y + chip_height + 12
        description_height = measure_wrapped_items(
            description_lines,
            self.app.fonts["small"],
            bounds.width - padding * 2,
            line_spacing=2,
        ).height
        natural_height = description_top - bounds.y + description_height + padding
        rect = pygame.Rect(bounds.x, bounds.y, bounds.width, min(max(150, natural_height), bounds.height))
        pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, rect, border_radius=18)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            rect,
            width=2,
            border_radius=18,
        )

        title = self.app.fonts["body"].render("Graphs & Parameters", True, self.app.theme.accent_warm)
        self.app.screen.blit(title, (rect.x + padding, rect.y + padding))

        self.app.graph_chip_rects.clear()
        for token, chip_rect, color, active, label in chip_layouts:
            self.app.graph_chip_rects[token] = chip_rect

            fill = color if active else self.app.theme.panel
            text_color = self.app.theme.background_bottom if active else self.app.theme.text

            pygame.draw.rect(self.app.screen, fill, chip_rect, border_radius=14)
            pygame.draw.rect(
                self.app.screen,
                self.app.theme.canvas_border,
                chip_rect,
                width=2,
                border_radius=14,
            )

            label_surface = self.app.fonts["small"].render(
                ellipsize(label, self.app.fonts["small"], chip_rect.width - 20),
                True,
                text_color,
            )
            self.app.screen.blit(label_surface, (chip_rect.x + 10, chip_rect.y + 9))

        description_rect = pygame.Rect(
            rect.x + padding,
            min(rect.bottom - 54, description_top),
            rect.width - padding * 2,
            rect.bottom - min(rect.bottom - 54, description_top) - padding,
        )
        draw_wrapped_items(
            self.app.screen,
            description_lines,
            self.app.fonts["small"],
            self.app.theme.muted_text,
            description_rect,
            line_spacing=2,
        )
        return rect.height

    def draw_footer(self) -> None:
        """Render the status bar with controls and camera info."""
        rect = self.app.layout.footer_rect.inflate(-20, -12)
        self.draw_panel(rect, self.app.theme.panel, self.app.theme.canvas_border)

        left_rect = pygame.Rect(rect.x + 16, rect.y + 10, rect.width - 32, 28)
        draw_wrapped_items(
            self.app.screen,
            self.app.state.status_message,
            self.app.fonts["small"],
            self.app.theme.text,
            left_rect,
            line_spacing=0,
        )

        lower_rect = pygame.Rect(rect.x + 16, rect.y + 38, rect.width - 32, rect.height - 46)
        draw_wrapped_items(
            self.app.screen,
            self.app.camera_label(),
            self.app.fonts["small"],
            self.app.theme.muted_text,
            lower_rect,
            line_spacing=0,
        )

    def draw_overlay(self) -> None:
        """Draw the active menu, commands, lesson, or equation overlay."""
        if self.app.state.overlay is None:
            return

        backdrop = pygame.Surface(self.app.screen.get_size(), pygame.SRCALPHA)
        backdrop.fill((*self.app.theme.overlay_backdrop, 165))
        self.app.screen.blit(backdrop, (0, 0))

        if self.app.state.overlay == "menu":
            self.draw_menu_overlay()
        elif self.app.state.overlay == "commands":
            self.draw_commands_overlay()
        elif self.app.state.overlay == "lessons":
            self.draw_lessons_overlay()
        elif self.app.state.overlay == "equations":
            self.draw_equation_overlay()

    def draw_menu_overlay(self) -> None:
        """Draw the Escape menu."""
        rect = pygame.Rect(
            self.app.screen.get_width() // 2 - 210,
            self.app.screen.get_height() // 2 - 210,
            420,
            430,
        )
        self.draw_panel(rect, self.app.theme.panel, self.app.theme.canvas_border)

        title = self.app.fonts["hero"].render("Pause Menu", True, self.app.theme.text)
        self.app.screen.blit(title, (rect.x + 22, rect.y + 20))

        subtitle_rect = pygame.Rect(rect.x + 22, rect.y + 58, rect.width - 44, 40)
        draw_wrapped_items(
            self.app.screen,
            "Jump back into the scene, review the shortcuts, start a lesson, or manage your saved work.",
            self.app.fonts["small"],
            self.app.theme.muted_text,
            subtitle_rect,
            line_spacing=2,
        )

        y = rect.y + 118
        for index, (option_key, label) in enumerate(MENU_OPTIONS):
            button_rect = pygame.Rect(rect.x + 22, y, rect.width - 44, 40)
            self.app.overlay_button_rects[f"menu:{option_key}"] = button_rect
            fill = self.app.theme.accent if index == self.app.state.menu_index else self.app.theme.panel_alt
            text_color = self.app.theme.background_bottom if index == self.app.state.menu_index else self.app.theme.text
            pygame.draw.rect(self.app.screen, fill, button_rect, border_radius=14)
            pygame.draw.rect(
                self.app.screen,
                self.app.theme.canvas_border,
                button_rect,
                width=2,
                border_radius=14,
            )
            rendered = self.app.fonts["body"].render(label, True, text_color)
            self.app.screen.blit(rendered, (button_rect.x + 14, button_rect.y + 8))
            y += 48

    def draw_commands_overlay(self) -> None:
        """Draw the commands and keymap reference overlay."""
        rect = pygame.Rect(110, 68, self.app.screen.get_width() - 220, self.app.screen.get_height() - 136)
        self.draw_panel(rect, self.app.theme.panel, self.app.theme.canvas_border)

        title = self.app.fonts["hero"].render("Shortcuts & Commands", True, self.app.theme.text)
        self.app.screen.blit(title, (rect.x + 22, rect.y + 20))

        column_gap = 22
        column_width = (rect.width - 66) // 2
        top_y = rect.y + 74

        for index, (section_title, rows) in enumerate(self.app.command_sections()):
            column = index % 2
            row = index // 2
            section_rect = pygame.Rect(
                rect.x + 22 + column * (column_width + column_gap),
                top_y + row * 164,
                column_width,
                150,
            )
            pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, section_rect, border_radius=16)
            pygame.draw.rect(
                self.app.screen,
                self.app.theme.canvas_border,
                section_rect,
                width=2,
                border_radius=16,
            )

            heading = self.app.fonts["body"].render(section_title, True, self.app.theme.accent_warm)
            self.app.screen.blit(heading, (section_rect.x + 12, section_rect.y + 10))

            y = section_rect.y + 38
            for command, description in rows:
                command_surface = self.app.fonts["command"].render(command, True, self.app.theme.selection)
                self.app.screen.blit(command_surface, (section_rect.x + 12, y))
                draw_wrapped_items(
                    self.app.screen,
                    description,
                    self.app.fonts["small"],
                    self.app.theme.muted_text,
                    pygame.Rect(section_rect.x + 112, y - 1, section_rect.width - 124, 34),
                    line_spacing=0,
                )
                y += 24

        button_y = rect.bottom - 54
        buttons = [
            ("command:back", "Back"),
            ("command:lessons", "Lessons"),
            ("command:equations", "Equation Editor"),
            ("command:save", "Save Scene"),
            ("command:load", "Load Scene"),
        ]
        x = rect.x + 22
        for button_id, label in buttons:
            button_rect = pygame.Rect(x, button_y, 126, 34)
            self.app.overlay_button_rects[button_id] = button_rect
            pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, button_rect, border_radius=12)
            pygame.draw.rect(
                self.app.screen,
                self.app.theme.canvas_border,
                button_rect,
                width=2,
                border_radius=12,
            )
            rendered = self.app.fonts["small"].render(label, True, self.app.theme.text)
            self.app.screen.blit(rendered, (button_rect.x + 12, button_rect.y + 8))
            x += 134

    def draw_lessons_overlay(self) -> None:
        """Draw the guided lesson picker."""
        rect = pygame.Rect(170, 76, self.app.screen.get_width() - 340, self.app.screen.get_height() - 152)
        self.draw_panel(rect, self.app.theme.panel, self.app.theme.canvas_border)

        title = self.app.fonts["hero"].render("Lesson Paths", True, self.app.theme.text)
        self.app.screen.blit(title, (rect.x + 22, rect.y + 20))
        draw_wrapped_items(
            self.app.screen,
            "Choose a lesson to turn the sandbox into a guided challenge. The lesson advances when your scene meets the current goal.",
            self.app.fonts["small"],
            self.app.theme.muted_text,
            pygame.Rect(rect.x + 22, rect.y + 58, rect.width - 44, 36),
            line_spacing=2,
        )

        y = rect.y + 108
        for index, lesson in enumerate(LESSONS):
            lesson_rect = pygame.Rect(rect.x + 22, y, rect.width - 44, 92)
            self.app.overlay_button_rects[f"lesson:{lesson.id}"] = lesson_rect
            is_active = lesson.id == self.app.state.lesson.lesson_id
            is_focused = index == self.app.state.lesson_menu_index
            fill = self.app.theme.accent if is_active else self.app.theme.panel_alt
            pygame.draw.rect(self.app.screen, fill, lesson_rect, border_radius=16)
            pygame.draw.rect(
                self.app.screen,
                self.app.theme.selection if is_focused else self.app.theme.canvas_border,
                lesson_rect,
                width=2,
                border_radius=16,
            )

            title_surface = self.app.fonts["body"].render(
                lesson.title,
                True,
                self.app.theme.background_bottom if is_active else self.app.theme.text,
            )
            self.app.screen.blit(title_surface, (lesson_rect.x + 14, lesson_rect.y + 10))
            draw_wrapped_items(
                self.app.screen,
                lesson.summary,
                self.app.fonts["small"],
                self.app.theme.background_bottom if is_active else self.app.theme.muted_text,
                pygame.Rect(lesson_rect.x + 14, lesson_rect.y + 38, lesson_rect.width - 28, 40),
                line_spacing=2,
            )
            y += 102

    def draw_equation_overlay(self) -> None:
        """Draw the custom equation editor overlay."""
        rect = pygame.Rect(130, 86, self.app.screen.get_width() - 260, self.app.screen.get_height() - 172)
        self.draw_panel(rect, self.app.theme.panel, self.app.theme.canvas_border)

        title = self.app.fonts["hero"].render("Function Builder", True, self.app.theme.text)
        self.app.screen.blit(title, (rect.x + 22, rect.y + 20))

        info_lines = [
            "Use x plus sliders a, b, c, t and optional point coordinates px, py.",
            "Try: a*x**2 + b*x + c, a*(x-px)+py+t, or sin(x+t) + b",
        ]
        draw_wrapped_items(
            self.app.screen,
            info_lines,
            self.app.fonts["small"],
            self.app.theme.muted_text,
            pygame.Rect(rect.x + 22, rect.y + 58, rect.width - 44, 44),
            line_spacing=2,
        )

        input_rect = pygame.Rect(rect.x + 22, rect.y + 116, rect.width - 44, 50)
        pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, input_rect, border_radius=14)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            input_rect,
            width=2,
            border_radius=14,
        )
        input_text = ellipsize(self.app.state.equation_input or "", self.app.fonts["command"], input_rect.width - 20)
        input_surface = self.app.fonts["command"].render(input_text, True, self.app.theme.selection)
        self.app.screen.blit(input_surface, (input_rect.x + 10, input_rect.y + 15))

        attach_text = (
            f"Attach to selected point: {'yes' if self.app.state.equation_attach_to_selected_point and self.app.selected_shape is not None and self.app.selected_shape.kind == 'point' else 'no'}"
        )
        if self.app.selected_shape is not None and self.app.selected_shape.kind == "point":
            attach_text += f" ({self.app.selected_shape.label})"
        draw_wrapped_items(
            self.app.screen,
            [attach_text, self.app.state.equation_status],
            self.app.fonts["small"],
            self.app.theme.muted_text,
            pygame.Rect(rect.x + 22, rect.y + 176, rect.width - 44, 42),
            line_spacing=2,
        )

        list_rect = pygame.Rect(rect.x + 22, rect.y + 228, rect.width - 44, rect.height - 320)
        pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, list_rect, border_radius=16)
        pygame.draw.rect(
            self.app.screen,
            self.app.theme.canvas_border,
            list_rect,
            width=2,
            border_radius=16,
        )
        heading = self.app.fonts["body"].render("Saved Student Functions", True, self.app.theme.accent_warm)
        self.app.screen.blit(heading, (list_rect.x + 12, list_rect.y + 10))

        if not self.app.state.custom_functions:
            draw_wrapped_items(
                self.app.screen,
                "No custom functions yet. Save the current expression to create the first one.",
                self.app.fonts["small"],
                self.app.theme.muted_text,
                pygame.Rect(list_rect.x + 12, list_rect.y + 38, list_rect.width - 24, list_rect.height - 48),
                line_spacing=2,
            )
        else:
            y = list_rect.y + 40
            for function in self.app.state.custom_functions[-6:]:
                color_rect = pygame.Rect(list_rect.x + 12, y + 2, 10, 10)
                pygame.draw.rect(self.app.screen, function.color, color_rect, border_radius=4)
                text = f"{function.name}: {function.expression}"
                if function.attached_point_id is not None:
                    text += " [attached]"
                draw_wrapped_items(
                    self.app.screen,
                    text,
                    self.app.fonts["small"],
                    self.app.theme.text if function.id == self.app.state.equation_editing_id else self.app.theme.muted_text,
                    pygame.Rect(list_rect.x + 30, y, list_rect.width - 42, 32),
                    line_spacing=0,
                )
                y += 24

        button_y = rect.bottom - 54
        buttons = [
            ("equation:save", "Save"),
            ("equation:new", "New"),
            ("equation:delete", "Delete"),
            ("equation:attach", "Attach Toggle"),
            ("equation:back", "Back"),
        ]
        x = rect.x + 22
        for button_id, label in buttons:
            button_rect = pygame.Rect(x, button_y, 126, 34)
            self.app.overlay_button_rects[button_id] = button_rect
            pygame.draw.rect(self.app.screen, self.app.theme.panel_alt, button_rect, border_radius=12)
            pygame.draw.rect(
                self.app.screen,
                self.app.theme.canvas_border,
                button_rect,
                width=2,
                border_radius=12,
            )
            rendered = self.app.fonts["small"].render(label, True, self.app.theme.text)
            self.app.screen.blit(rendered, (button_rect.x + 12, button_rect.y + 8))
            x += 134

    @staticmethod
    def lerp_color(
        start: tuple[int, int, int],
        end: tuple[int, int, int],
        amount: float,
    ) -> tuple[int, int, int]:
        """Blend two RGB colors."""
        return (
            int(start[0] + (end[0] - start[0]) * amount),
            int(start[1] + (end[1] - start[1]) * amount),
            int(start[2] + (end[2] - start[2]) * amount),
        )

    def emphasize_color(
        self,
        color: tuple[int, int, int],
        amount: float = 0.22,
    ) -> tuple[int, int, int]:
        """Lighten dark colors and darken light colors for hover feedback."""
        luminance = color[0] * 0.2126 + color[1] * 0.7152 + color[2] * 0.0722
        target = (255, 255, 255) if luminance < 154 else (10, 16, 27)
        return self.lerp_color(color, target, amount)

    def longest_line_width(self, lines: list[str], font: pygame.font.Font) -> int:
        """Return the widest raw line in a list for simple adaptive cards."""
        if not lines:
            return 0
        return max(font.size(line)[0] for line in lines)
