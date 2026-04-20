"""Main application controller for the geometry explorer."""

from __future__ import annotations

import math

import pygame

from scripts.app.config import (
    COLOR_CYCLE,
    COMMAND_SECTIONS,
    DEFAULT_EQUATION_TEMPLATE,
    MENU_OPTIONS,
    NEXT_IMPROVEMENT_IDEAS,
    SIDEBAR_SECTIONS,
    TOOLBAR_BUTTONS,
    TOOL_HELP,
)
from scripts.app.constraints import create_constraint, describe_constraint, enforce_constraints
from scripts.app.demo_scene import create_demo_shapes
from scripts.app.equations import approximate_intersections, build_runtime_entries, compile_expression
from scripts.app.layout import AppLayout, create_layout
from scripts.app.lessons import LESSONS, check_lesson_step, lesson_by_id, lesson_lines
from scripts.app.persistence import load_scene, save_scene
from scripts.app.rendering import AppRenderer
from scripts.app.state import ConstraintLink, CustomFunctionState, InteractionState
from scripts.app.theme import Theme, build_fonts
from scripts.app.transformations import (
    apply_mirror,
    apply_rotation,
    apply_scale,
    apply_translation,
)
from scripts.geometry import (
    CircleShape,
    FunctionPreset,
    GeometryShape,
    Point,
    PointShape,
    PolygonShape,
    RectangleShape,
    SegmentShape,
    TriangleShape,
    default_function_presets,
)
from scripts.geometry.math_utils import distance, format_number
from scripts.geometry.serialization import copy_shape


class GeometryLearningApp:
    """Interactive geometry explorer designed around learning by manipulation."""

    def __init__(self, screen_size: tuple[int, int] = (1480, 920)) -> None:
        """Initialize the window, theme, state, and renderer."""
        pygame.init()
        pygame.display.set_caption("Intuitive Geometry Lab")

        self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.theme = Theme()
        self.fonts = build_fonts()
        self.state = InteractionState()
        self.layout: AppLayout = create_layout(
            self.screen.get_size(),
            inspector_expanded=self.state.sidebar_section is not None,
        )
        self.renderer = AppRenderer(self)

        self.shapes: list[GeometryShape] = []
        self.next_shape_id = 1
        self.function_presets: list[FunctionPreset] = default_function_presets()
        self.graph_chip_rects: dict[str, pygame.Rect] = {}
        self.slider_bar_rects: dict[str, pygame.Rect] = {}
        self.slider_toggle_rects: dict[str, pygame.Rect] = {}
        self.overlay_button_rects: dict[str, pygame.Rect] = {}
        self.sidebar_tab_rects: dict[str, pygame.Rect] = {}
        self.sidebar_close_rect: pygame.Rect | None = None

        self.camera = self.build_camera()

    @property
    def scale(self) -> float:
        """Return the current world-to-screen scale in pixels."""
        return self.camera.scale

    def build_camera(self):
        """Create a fresh camera instance."""
        from scripts.app.state import CameraState

        return CameraState()

    def run(self) -> None:
        """Drive the main event loop until the user closes the app."""
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                running = self.handle_event(event)

            self.update_live_state(dt)
            self.renderer.draw()
            pygame.display.flip()

        pygame.quit()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Route keyboard, mouse, and resize events to the right behavior."""
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            self.update_layout()
            return True

        if event.type == pygame.KEYDOWN:
            if self.state.overlay is not None:
                self.handle_overlay_keydown(event)
            else:
                self.handle_keydown(event)

        if event.type == pygame.MOUSEWHEEL and self.state.overlay is None:
            self.zoom_at(1.1 if event.y > 0 else 0.9, pygame.mouse.get_pos())

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state.overlay is not None:
                self.handle_overlay_click(event.pos)
            else:
                self.handle_mouse_down(event)

        if event.type == pygame.MOUSEBUTTONUP:
            self.handle_mouse_up(event)

        if event.type == pygame.MOUSEMOTION and self.state.overlay is None:
            self.handle_mouse_motion(event)

        return True

    def handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle shortcuts that make the app fast to use in class."""
        modifiers = event.mod
        hotkey_map = {
            pygame.K_v: "select",
            pygame.K_a: "point",
            pygame.K_l: "segment",
            pygame.K_t: "triangle",
            pygame.K_r: "rectangle",
            pygame.K_c: "circle",
            pygame.K_p: "polygon",
        }

        if modifiers & pygame.KMOD_CTRL:
            if event.key == pygame.K_s:
                self.state.status_message = save_scene(self, self.state.save_path)
                self.state.recent_actions.add("scene_saved")
                return
            if event.key == pygame.K_o:
                self.state.status_message = load_scene(self, self.state.save_path)
                self.state.recent_actions.add("scene_loaded")
                return
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                self.try_create_constraint_from_shortcut(event.key)
                return

        if event.key == pygame.K_ESCAPE:
            self.open_menu()
            return

        if event.key == pygame.K_SLASH:
            self.open_commands()
            return

        if event.key == pygame.K_j:
            self.open_lessons()
            return

        if event.key == pygame.K_f:
            self.open_equation_editor()
            return

        if event.key == pygame.K_TAB:
            self.toggle_slider_animation("t")
            return

        if self.try_handle_transformation_shortcut(event):
            return

        if event.key in hotkey_map:
            self.set_active_tool(hotkey_map[event.key])
            return

        if event.key == pygame.K_DELETE and self.selected_shape is not None:
            self.shapes = [shape for shape in self.shapes if shape.id != self.selected_shape.id]
            self.state.selected_shape_id = None
            self.state.hovered_shape_id = None
            self.state.comparison_shape_id = None
            self.state.status_message = "Deleted the selected shape."
            return

        if event.key == pygame.K_RETURN and self.state.active_tool == "polygon":
            self.try_finalize_polygon()
            return

        if event.key == pygame.K_g:
            self.state.snap_to_grid = not self.state.snap_to_grid
            self.state.status_message = (
                f"Snap to grid: {'on' if self.state.snap_to_grid else 'off'}"
            )
            return

        if event.key == pygame.K_h:
            self.state.show_help = not self.state.show_help
            self.state.status_message = (
                f"Help overlay: {'shown' if self.state.show_help else 'hidden'}"
            )
            return

        if event.key == pygame.K_i:
            self.state.show_intersections = not self.state.show_intersections
            self.state.status_message = (
                f"Function intersections: {'shown' if self.state.show_intersections else 'hidden'}"
            )
            return

        if event.key == pygame.K_1:
            self.toggle_function("preset:Linear")
            return

        if event.key == pygame.K_2:
            self.toggle_function("preset:Parabola")
            return

        if event.key == pygame.K_3:
            self.toggle_function("preset:Sine")
            return

        if event.key == pygame.K_4:
            self.toggle_function("preset:Quadratic Lab")
            return

        if event.key == pygame.K_0:
            self.camera.zoom = 1.0
            self.camera.center = (0.0, 0.0)
            self.state.status_message = "Reset the camera view."
            return

        if event.key == pygame.K_SPACE:
            self.load_demo_scene()
            return

        if event.key == pygame.K_n:
            self.state.roadmap_index = (
                self.state.roadmap_index + 1
            ) % len(NEXT_IMPROVEMENT_IDEAS)
            self.state.status_message = "Showing the next improvement idea."

    def handle_overlay_keydown(self, event: pygame.event.Event) -> None:
        """Handle keyboard input while an overlay is open."""
        if self.state.overlay == "menu":
            if event.key == pygame.K_ESCAPE:
                self.close_overlay()
            elif event.key == pygame.K_UP:
                self.state.menu_index = (self.state.menu_index - 1) % len(MENU_OPTIONS)
            elif event.key == pygame.K_DOWN:
                self.state.menu_index = (self.state.menu_index + 1) % len(MENU_OPTIONS)
            elif event.key == pygame.K_RETURN:
                self.activate_menu_option(MENU_OPTIONS[self.state.menu_index][0])
            return

        if self.state.overlay == "commands":
            if event.key == pygame.K_ESCAPE:
                self.open_menu()
            elif event.key == pygame.K_j:
                self.open_lessons()
            elif event.key == pygame.K_f:
                self.open_equation_editor()
            return

        if self.state.overlay == "lessons":
            if event.key == pygame.K_ESCAPE:
                self.open_menu()
            elif event.key == pygame.K_UP:
                self.state.lesson_menu_index = (self.state.lesson_menu_index - 1) % len(LESSONS)
            elif event.key == pygame.K_DOWN:
                self.state.lesson_menu_index = (self.state.lesson_menu_index + 1) % len(LESSONS)
            elif event.key == pygame.K_RETURN:
                self.start_lesson(LESSONS[self.state.lesson_menu_index].id)
            return

        if self.state.overlay == "equations":
            if event.key == pygame.K_ESCAPE:
                self.open_menu()
                return
            if event.key == pygame.K_RETURN:
                self.save_equation_input()
                return
            if event.key == pygame.K_BACKSPACE:
                self.state.equation_input = self.state.equation_input[:-1]
                return
            if event.key == pygame.K_TAB:
                self.state.equation_attach_to_selected_point = (
                    not self.state.equation_attach_to_selected_point
                )
                return
            if event.key == pygame.K_UP:
                self.cycle_equation_target(-1)
                return
            if event.key == pygame.K_DOWN:
                self.cycle_equation_target(1)
                return
            if event.unicode and event.unicode.isprintable():
                self.state.equation_input += event.unicode

    def handle_overlay_click(self, position: tuple[int, int]) -> None:
        """Handle button clicks inside overlays."""
        for button_id, rect in self.overlay_button_rects.items():
            if rect.collidepoint(position):
                self.activate_overlay_button(button_id)
                return

    def activate_overlay_button(self, button_id: str) -> None:
        """Dispatch an overlay button action."""
        if button_id.startswith("menu:"):
            self.activate_menu_option(button_id.split(":", 1)[1])
            return
        if button_id.startswith("command:"):
            action = button_id.split(":", 1)[1]
            if action == "back":
                self.open_menu()
            elif action == "lessons":
                self.open_lessons()
            elif action == "equations":
                self.open_equation_editor()
            elif action == "save":
                self.state.status_message = save_scene(self, self.state.save_path)
                self.close_overlay()
            elif action == "load":
                self.state.status_message = load_scene(self, self.state.save_path)
                self.close_overlay()
            return
        if button_id.startswith("lesson:"):
            self.start_lesson(button_id.split(":", 1)[1])
            return
        if button_id.startswith("equation:"):
            action = button_id.split(":", 1)[1]
            if action == "save":
                self.save_equation_input()
            elif action == "new":
                self.start_new_custom_function()
            elif action == "delete":
                self.delete_current_custom_function()
            elif action == "back":
                self.open_menu()
            elif action == "attach":
                self.state.equation_attach_to_selected_point = (
                    not self.state.equation_attach_to_selected_point
                )
            return

    def activate_menu_option(self, option_key: str) -> None:
        """Execute a menu option from the Escape menu."""
        if option_key == "continue":
            self.close_overlay()
        elif option_key == "commands":
            self.open_commands()
        elif option_key == "lessons":
            self.open_lessons()
        elif option_key == "equations":
            self.open_equation_editor()
        elif option_key == "save":
            self.state.status_message = save_scene(self, self.state.save_path)
            self.close_overlay()
        elif option_key == "load":
            self.state.status_message = load_scene(self, self.state.save_path)
            self.close_overlay()
        elif option_key == "cancel":
            self.cancel_current_action()
            self.close_overlay()

    def open_menu(self) -> None:
        """Open the Escape menu."""
        self.state.overlay = "menu"
        self.state.menu_index = 0

    def open_commands(self) -> None:
        """Open the command and keymap overlay."""
        self.state.overlay = "commands"

    def open_lessons(self) -> None:
        """Open the guided lesson chooser."""
        self.state.overlay = "lessons"
        lesson_id = self.state.lesson.lesson_id
        if lesson_id is not None:
            for index, lesson in enumerate(LESSONS):
                if lesson.id == lesson_id:
                    self.state.lesson_menu_index = index
                    break

    def open_equation_editor(self) -> None:
        """Open the custom equation editor."""
        self.state.overlay = "equations"
        if self.state.equation_editing_id is None:
            if self.state.custom_functions:
                current = self.state.custom_functions[-1]
                self.state.equation_editing_id = current.id
                self.state.equation_input = current.expression
            else:
                self.start_new_custom_function()
        else:
            current = self.get_custom_function(self.state.equation_editing_id)
            if current is not None:
                self.state.equation_input = current.expression
                self.state.equation_attach_to_selected_point = current.attached_point_id is not None

    def close_overlay(self) -> None:
        """Close the active overlay."""
        self.state.overlay = None
        self.overlay_button_rects.clear()

    def handle_mouse_down(self, event: pygame.event.Event) -> None:
        """Handle clicks on panels, sliders, or the geometry canvas."""
        self.state.last_mouse_pos = event.pos

        if event.button == 4:
            self.zoom_at(1.1, event.pos)
            return
        if event.button == 5:
            self.zoom_at(0.9, event.pos)
            return

        if event.button == 1 and self.try_handle_sidebar_click(event.pos):
            return

        if event.button == 1 and self.try_handle_slider_click(event.pos):
            return

        if event.button == 1 and self.try_handle_toolbar_click(event.pos):
            return

        if event.button == 1 and self.try_handle_function_chip_click(event.pos):
            return

        if not self.layout.canvas_rect.collidepoint(event.pos):
            return

        world_point = self.prepare_world_point(self.screen_to_world(event.pos))
        self.state.cursor_world = world_point

        if event.button == 3:
            self.state.dragging_canvas = True
            return

        if event.button != 1:
            return

        if self.state.active_tool == "select":
            self.handle_select_click(event, world_point)
            return

        self.handle_tool_canvas_click(world_point)

    def handle_select_click(self, event: pygame.event.Event, world_point: Point) -> None:
        """Handle selection-mode clicks on the canvas."""
        handle_index = self.handle_at_screen_pos(event.pos)
        if handle_index is not None and self.selected_shape is not None:
            self.state.dragging_handle_index = handle_index
            self.state.previous_drag_world = world_point
            self.state.status_message = (
                f"Editing {self.selected_shape.label}. Drag a handle to change the geometry."
            )
            return

        hit_shape = self.shape_at_world_point(world_point)
        if hit_shape is not None:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                if self.selected_shape is None or self.selected_shape.id == hit_shape.id:
                    self.state.selected_shape_id = hit_shape.id
                    self.state.status_message = f"Selected {hit_shape.label} as the main shape."
                else:
                    self.state.comparison_shape_id = hit_shape.id
                    self.state.status_message = f"{hit_shape.label} is now the comparison shape."
                return

            self.state.selected_shape_id = hit_shape.id
            self.state.dragging_shape = True
            self.state.previous_drag_world = world_point
            if self.state.comparison_shape_id == hit_shape.id:
                self.state.comparison_shape_id = None
            self.state.status_message = (
                f"Selected {hit_shape.label}. Move it or drag one of its handles."
            )
        else:
            self.state.selected_shape_id = None
            self.state.comparison_shape_id = None
            self.state.dragging_canvas = True
            self.state.status_message = (
                "Panning the view. Right-click drag also works anywhere on the canvas."
            )

    def handle_mouse_up(self, event: pygame.event.Event) -> None:
        """End drag interactions cleanly."""
        if event.button in (1, 3):
            self.state.dragging_canvas = False
            self.state.dragging_shape = False
            self.state.dragging_handle_index = None
            self.state.dragging_slider_name = None

    def handle_mouse_motion(self, event: pygame.event.Event) -> None:
        """Update hover state, previews, sliders, and drag targets."""
        if self.state.dragging_slider_name is not None:
            self.update_slider_from_screen(self.state.dragging_slider_name, event.pos[0])
            self.state.last_mouse_pos = event.pos
            return

        world_point: Point | None = None
        if self.layout.canvas_rect.collidepoint(event.pos):
            world_point = self.prepare_world_point(self.screen_to_world(event.pos))
            self.state.cursor_world = world_point
            if self.state.active_tool == "select":
                self.state.preview_point = None
                self.state.hovered_shape_id = self.id_of_shape_at_world_point(world_point)
            else:
                self.state.preview_point = world_point
                self.state.hovered_shape_id = None
        else:
            self.state.preview_point = None
            self.state.hovered_shape_id = None

        if self.state.dragging_canvas:
            dx_pixels = event.pos[0] - self.state.last_mouse_pos[0]
            dy_pixels = event.pos[1] - self.state.last_mouse_pos[1]
            self.camera.center = (
                self.camera.center[0] - dx_pixels / self.scale,
                self.camera.center[1] + dy_pixels / self.scale,
            )

        if (
            world_point is not None
            and self.state.dragging_shape
            and self.selected_shape is not None
            and self.layout.canvas_rect.collidepoint(event.pos)
        ):
            dx_world = world_point[0] - self.state.previous_drag_world[0]
            dy_world = world_point[1] - self.state.previous_drag_world[1]
            self.selected_shape.move(dx_world, dy_world)
            self.state.previous_drag_world = world_point

        if (
            world_point is not None
            and self.state.dragging_handle_index is not None
            and self.selected_shape is not None
            and self.layout.canvas_rect.collidepoint(event.pos)
        ):
            if isinstance(self.selected_shape, TriangleShape):
                self.state.recent_actions.add("triangle_handle_dragged")
            self.selected_shape.drag_handle(self.state.dragging_handle_index, world_point)
            self.state.previous_drag_world = world_point

        self.state.last_mouse_pos = event.pos

    def update_layout(self) -> None:
        """Recompute panel rectangles after a resize."""
        self.layout = create_layout(
            self.screen.get_size(),
            inspector_expanded=self.state.sidebar_section is not None,
        )

    def update_live_state(self, dt: float) -> None:
        """Update animation, constraints, overlays, and lesson progress."""
        self.update_animated_sliders(dt)
        enforce_constraints(self)
        self.update_transform_feedback(dt)
        self.update_lesson_progress()

    def update_animated_sliders(self, dt: float) -> None:
        """Advance any animated sliders."""
        for slider in self.state.sliders.values():
            if not slider.animated:
                continue
            slider.value += slider.direction * slider.speed * dt * (slider.max_value - slider.min_value)
            if slider.value >= slider.max_value:
                slider.value = slider.max_value
                slider.direction = -1
            elif slider.value <= slider.min_value:
                slider.value = slider.min_value
                slider.direction = 1

    def update_transform_feedback(self, dt: float) -> None:
        """Fade the transform ghost over time."""
        if self.state.transform_ghost is None:
            return
        self.state.transform_ghost_ttl -= dt
        if self.state.transform_ghost_ttl <= 0:
            self.state.transform_ghost = None
            self.state.transform_description = None
            self.state.transform_matrix_lines.clear()

    def update_lesson_progress(self) -> None:
        """Advance the current guided lesson when a step is completed."""
        lesson = lesson_by_id(self.state.lesson.lesson_id)
        if lesson is None:
            return

        if self.state.lesson.step_index >= len(lesson.steps):
            return

        if check_lesson_step(self):
            self.state.lesson.step_index += 1
            if self.state.lesson.step_index >= len(lesson.steps):
                self.state.status_message = f"Lesson complete: {lesson.title}"
            else:
                next_step = lesson.steps[self.state.lesson.step_index]
                self.state.status_message = f"Lesson progress: {next_step}"

    def cancel_current_action(self) -> None:
        """Clear temporary construction or drag state."""
        self.state.pending_points.clear()
        self.state.preview_point = None
        self.state.dragging_canvas = False
        self.state.dragging_shape = False
        self.state.dragging_handle_index = None
        self.state.dragging_slider_name = None
        self.state.status_message = "Cancelled the current construction."

    def try_handle_toolbar_click(self, screen_pos: tuple[int, int]) -> bool:
        """Return True when a toolbar button consumed the click."""
        for button in TOOLBAR_BUTTONS:
            rect = self.layout.button_rects[button.key]
            if rect.collidepoint(screen_pos):
                self.set_active_tool(button.key)
                return True
        return False

    def try_handle_sidebar_click(self, screen_pos: tuple[int, int]) -> bool:
        """Open, switch, or collapse the right-side section rail."""
        if self.sidebar_close_rect is not None and self.sidebar_close_rect.collidepoint(screen_pos):
            self.set_sidebar_section(None)
            return True

        for section_key, rect in self.sidebar_tab_rects.items():
            if rect.collidepoint(screen_pos):
                next_section = None if self.state.sidebar_section == section_key else section_key
                self.set_sidebar_section(next_section)
                return True
        return False

    def try_handle_function_chip_click(self, screen_pos: tuple[int, int]) -> bool:
        """Toggle graph presets and custom functions from the inspector panel."""
        for token, rect in self.graph_chip_rects.items():
            if rect.collidepoint(screen_pos):
                self.toggle_function(token)
                return True
        return False

    def try_handle_slider_click(self, screen_pos: tuple[int, int]) -> bool:
        """Handle clicks on slider bars and animation toggles."""
        for slider_name, rect in self.slider_toggle_rects.items():
            if rect.collidepoint(screen_pos):
                self.toggle_slider_animation(slider_name)
                return True

        for slider_name, rect in self.slider_bar_rects.items():
            if rect.collidepoint(screen_pos):
                self.state.dragging_slider_name = slider_name
                self.update_slider_from_screen(slider_name, screen_pos[0])
                return True
        return False

    def update_slider_from_screen(self, slider_name: str, screen_x: int) -> None:
        """Move one slider value based on a dragged screen position."""
        rect = self.slider_bar_rects.get(slider_name)
        slider = self.state.sliders.get(slider_name)
        if rect is None or slider is None:
            return

        ratio = (screen_x - rect.x) / max(rect.width, 1)
        ratio = max(0.0, min(1.0, ratio))
        slider.value = slider.min_value + ratio * (slider.max_value - slider.min_value)
        self.state.status_message = f"{slider.label}: {format_number(slider.value)}"

    def toggle_slider_animation(self, slider_name: str) -> None:
        """Toggle animation on one slider."""
        slider = self.state.sliders[slider_name]
        slider.animated = not slider.animated
        self.state.recent_actions.add("slider_animation_toggled")
        self.state.status_message = (
            f"{slider.label} animation: {'on' if slider.animated else 'off'}"
        )

    def toggle_function(self, token: str) -> None:
        """Show or hide one preset or custom function."""
        if token.startswith("preset:"):
            name = token.split(":", 1)[1]
            if name in self.state.active_function_names:
                self.state.active_function_names.remove(name)
                self.state.status_message = f"Hid the {name} graph."
            else:
                self.state.active_function_names.add(name)
                self.state.status_message = f"Showing the {name} graph."
            return

        if token.startswith("custom:"):
            function = self.get_custom_function(int(token.split(":", 1)[1]))
            if function is None:
                return
            function.enabled = not function.enabled
            self.state.status_message = (
                f"{'Showing' if function.enabled else 'Hid'} {function.name}."
            )

    def set_sidebar_section(self, section_key: str | None) -> None:
        """Open one right-side section or collapse the rail back to icon-only mode."""
        self.state.sidebar_section = section_key
        self.graph_chip_rects.clear()
        self.slider_bar_rects.clear()
        self.slider_toggle_rects.clear()
        self.sidebar_close_rect = None
        self.state.dragging_slider_name = None
        self.update_layout()

        if section_key is None:
            self.state.status_message = "Collapsed the right panel so the graph can use that space."
            return

        section = next(
            (item for item in SIDEBAR_SECTIONS if item.key == section_key),
            None,
        )
        label = section.label.title() if section is not None else section_key.title()
        self.state.status_message = f"Opened the {label.lower()} panel."

    def set_active_tool(self, tool_key: str) -> None:
        """Switch tools and clear unfinished geometry from the previous mode."""
        self.state.active_tool = tool_key
        self.state.pending_points.clear()
        self.state.preview_point = None
        self.state.hovered_shape_id = None
        self.state.status_message = TOOL_HELP[tool_key]

    def prepare_world_point(self, world_point: Point) -> Point:
        """Snap points to the current grid step when snapping is enabled."""
        if not self.state.snap_to_grid:
            return world_point

        grid_step = self.current_grid_step()
        return (
            round(world_point[0] / grid_step) * grid_step,
            round(world_point[1] / grid_step) * grid_step,
        )

    def handle_tool_canvas_click(self, world_point: Point) -> None:
        """Create or extend a construction based on the active tool."""
        if self.state.active_tool == "point":
            self.add_shape(
                PointShape(
                    id=self.next_shape_id,
                    label=f"Point {self.next_shape_id}",
                    kind="point",
                    color=self.next_color(),
                    position=world_point,
                )
            )
            return

        if self.state.active_tool == "segment":
            self.state.pending_points.append(world_point)
            if len(self.state.pending_points) == 2:
                self.add_shape(
                    SegmentShape(
                        id=self.next_shape_id,
                        label=f"Segment {self.next_shape_id}",
                        kind="segment",
                        color=self.next_color(),
                        start=self.state.pending_points[0],
                        end=self.state.pending_points[1],
                    )
                )
            else:
                self.state.status_message = "Segment started. Click the second endpoint."
            return

        if self.state.active_tool == "triangle":
            self.state.pending_points.append(world_point)
            if len(self.state.pending_points) == 3:
                self.add_shape(
                    TriangleShape(
                        id=self.next_shape_id,
                        label=f"Triangle {self.next_shape_id}",
                        kind="triangle",
                        color=self.next_color(),
                        points=list(self.state.pending_points),
                    )
                )
            else:
                remaining = 3 - len(self.state.pending_points)
                self.state.status_message = (
                    f"Triangle started. Add {remaining} more point{'s' if remaining > 1 else ''}."
                )
            return

        if self.state.active_tool == "rectangle":
            self.state.pending_points.append(world_point)
            if len(self.state.pending_points) == 2:
                self.add_shape(
                    RectangleShape(
                        id=self.next_shape_id,
                        label=f"Rectangle {self.next_shape_id}",
                        kind="rectangle",
                        color=self.next_color(),
                        corner_a=self.state.pending_points[0],
                        corner_b=self.state.pending_points[1],
                    )
                )
            else:
                self.state.status_message = "Rectangle started. Click the opposite corner."
            return

        if self.state.active_tool == "circle":
            self.state.pending_points.append(world_point)
            if len(self.state.pending_points) == 2:
                self.add_shape(
                    CircleShape(
                        id=self.next_shape_id,
                        label=f"Circle {self.next_shape_id}",
                        kind="circle",
                        color=self.next_color(),
                        center=self.state.pending_points[0],
                        radius_point=self.state.pending_points[1],
                    )
                )
            else:
                self.state.status_message = (
                    "Circle started. Click a point that sets the radius."
                )
            return

        if self.state.active_tool == "polygon":
            if (
                len(self.state.pending_points) >= 3
                and distance(self.state.pending_points[0], world_point)
                <= self.current_grid_step()
            ):
                self.try_finalize_polygon()
            else:
                self.state.pending_points.append(world_point)
                self.state.status_message = (
                    f"Polygon has {len(self.state.pending_points)} point(s). "
                    "Press Enter when you're ready to close it."
                )

    def try_finalize_polygon(self) -> None:
        """Close a polygon when enough vertices have been placed."""
        if len(self.state.pending_points) < 3:
            self.state.status_message = "A polygon needs at least three points."
            return

        self.add_shape(
            PolygonShape(
                id=self.next_shape_id,
                label=f"Polygon {self.next_shape_id}",
                kind="polygon",
                color=self.next_color(),
                points=list(self.state.pending_points),
            )
        )

    def add_shape(self, shape: GeometryShape) -> None:
        """Insert a new shape, clear temporary state, and select it immediately."""
        self.shapes.append(shape)
        self.state.selected_shape_id = shape.id
        self.next_shape_id += 1
        self.state.pending_points.clear()
        self.state.preview_point = None
        self.state.recent_actions.add(f"created_{shape.kind}")
        self.state.status_message = (
            f"Created {shape.label}. Drag it or inspect the formulas on the right."
        )

    def load_demo_scene(self) -> None:
        """Load a ready-made example scene for faster exploration."""
        self.shapes = create_demo_shapes(COLOR_CYCLE)
        self.next_shape_id = len(self.shapes) + 1
        self.state.selected_shape_id = 3
        self.state.comparison_shape_id = 2
        self.state.active_function_names = {"Linear", "Parabola", "Sine"}
        self.camera.zoom = 1.0
        self.camera.center = (0.5, 0.4)
        self.state.pending_points.clear()
        self.state.preview_point = None
        self.state.constraints.clear()
        self.state.status_message = (
            "Loaded a demo scene. Select any object and compare the formulas."
        )

    def next_color(self) -> tuple[int, int, int]:
        """Cycle through a compact palette so shapes stay visually distinct."""
        return COLOR_CYCLE[(self.next_shape_id - 1) % len(COLOR_CYCLE)]

    def zoom_at(self, factor: float, anchor_screen_pos: tuple[int, int]) -> None:
        """Zoom toward the mouse position so exploration feels natural."""
        if not self.layout.canvas_rect.collidepoint(anchor_screen_pos):
            return

        world_before = self.screen_to_world(anchor_screen_pos)
        self.camera.zoom = max(0.35, min(3.6, self.camera.zoom * factor))
        world_after = self.screen_to_world(anchor_screen_pos)
        self.camera.center = (
            self.camera.center[0] + (world_before[0] - world_after[0]),
            self.camera.center[1] + (world_before[1] - world_after[1]),
        )

    def world_to_screen(self, point: Point) -> tuple[int, int]:
        """Project a world-space coordinate into the central canvas."""
        center_x, center_y = self.layout.canvas_rect.center
        screen_x = center_x + (point[0] - self.camera.center[0]) * self.scale
        screen_y = center_y - (point[1] - self.camera.center[1]) * self.scale
        return (int(round(screen_x)), int(round(screen_y)))

    def screen_to_world(self, point: tuple[int, int]) -> Point:
        """Turn a mouse position back into mathematical coordinates."""
        center_x, center_y = self.layout.canvas_rect.center
        world_x = self.camera.center[0] + (point[0] - center_x) / self.scale
        world_y = self.camera.center[1] - (point[1] - center_y) / self.scale
        return (world_x, world_y)

    def current_grid_step(self) -> float:
        """Choose a grid density that stays readable at any zoom level."""
        target_pixels = 40
        raw_step = target_pixels / self.scale
        options = [0.25, 0.5, 1, 2, 5, 10, 20]
        for option in options:
            if option >= raw_step:
                return option
        return options[-1]

    def visible_world_bounds(self) -> tuple[float, float, float, float]:
        """Return the world-space limits visible in the canvas."""
        left = self.screen_to_world((self.layout.canvas_rect.left, self.layout.canvas_rect.centery))[0]
        right = self.screen_to_world((self.layout.canvas_rect.right, self.layout.canvas_rect.centery))[0]
        top = self.screen_to_world((self.layout.canvas_rect.centerx, self.layout.canvas_rect.top))[1]
        bottom = self.screen_to_world((self.layout.canvas_rect.centerx, self.layout.canvas_rect.bottom))[1]
        return left, right, bottom, top

    @property
    def selected_shape(self) -> GeometryShape | None:
        """Convenience getter for the current selection."""
        return self.shape_by_id(self.state.selected_shape_id)

    @property
    def comparison_shape(self) -> GeometryShape | None:
        """Convenience getter for the comparison selection."""
        return self.shape_by_id(self.state.comparison_shape_id)

    def shape_by_id(self, shape_id: int | None) -> GeometryShape | None:
        """Return a shape by id."""
        if shape_id is None:
            return None
        return next((shape for shape in self.shapes if shape.id == shape_id), None)

    def points_by_id(self) -> dict[int, PointShape]:
        """Return all point shapes by id."""
        return {
            shape.id: shape
            for shape in self.shapes
            if isinstance(shape, PointShape)
        }

    def runtime_function_entries(self):
        """Return all currently active graph functions."""
        return build_runtime_entries(
            self.function_presets,
            self.state.active_function_names,
            self.state.custom_functions,
            self.state.sliders,
            self.points_by_id(),
        )

    def function_intersections(self):
        """Return visible function intersections and keep lesson state updated."""
        entries = self.runtime_function_entries()
        left, right, _, _ = self.visible_world_bounds()
        intersections = approximate_intersections(entries, left, right)
        self.state.last_intersection_count = len(intersections)
        if intersections:
            self.state.recent_actions.add("function_intersection_seen")
        return intersections

    def shape_at_world_point(self, point: Point) -> GeometryShape | None:
        """Return the top-most shape under the cursor."""
        tolerance = 12 / self.scale
        for shape in reversed(self.shapes):
            if shape.contains(point, tolerance):
                return shape
        return None

    def id_of_shape_at_world_point(self, point: Point) -> int | None:
        """Return only the hovered id when the full shape is not needed."""
        hit_shape = self.shape_at_world_point(point)
        return None if hit_shape is None else hit_shape.id

    def handle_at_screen_pos(self, screen_pos: tuple[int, int]) -> int | None:
        """Return the selected handle index if the cursor is near one."""
        if self.selected_shape is None:
            return None

        for index, handle_point in enumerate(self.selected_shape.handle_positions()):
            handle_screen = self.world_to_screen(handle_point)
            if math.dist(screen_pos, handle_screen) <= 10:
                return index
        return None

    def selected_shape_badge_lines(self) -> list[str]:
        """Return compact lines for the floating on-canvas badge."""
        if self.selected_shape is None:
            return []
        summary = self.selected_shape.summary_lines()
        return [self.selected_shape.label, *summary[:2]]

    def selected_shape_anchor(self) -> tuple[int, int] | None:
        """Return a stable screen anchor near the selected shape."""
        if self.selected_shape is None:
            return None

        if self.selected_shape.kind == "circle":
            return self.world_to_screen(self.selected_shape.center)

        vertices = self.selected_shape.vertices()
        screen_points = [self.world_to_screen(point) for point in vertices]
        min_x = min(point[0] for point in screen_points)
        min_y = min(point[1] for point in screen_points)
        return (min_x, min_y)

    def active_roadmap_ideas(self, count: int = 3) -> list[str]:
        """Return a rotating slice of future app ideas."""
        ideas: list[str] = []
        total = len(NEXT_IMPROVEMENT_IDEAS)
        for offset in range(count):
            ideas.append(NEXT_IMPROVEMENT_IDEAS[(self.state.roadmap_index + offset) % total])
        return ideas

    def constraint_summary_lines(self) -> list[str]:
        """Return descriptions for constraints touching the current selection."""
        shape_id_set = {shape_id for shape_id in (self.state.selected_shape_id, self.state.comparison_shape_id) if shape_id is not None}
        lines = [
            describe_constraint(constraint, self)
            for constraint in self.state.constraints
            if constraint.reference_shape_id in shape_id_set or constraint.target_shape_id in shape_id_set
        ]
        return lines or ["No live constraints yet. Use Shift+Click + Ctrl+1..4 to add one."]

    def transform_summary_lines(self) -> list[str]:
        """Return the last transformation explanation and matrix."""
        if self.state.transform_description is None:
            return [
                "Use arrows to translate, Q/E to rotate, -/= to scale, and X/Y/O to mirror.",
            ]
        return [self.state.transform_description, *self.state.transform_matrix_lines]

    def lesson_summary_lines(self) -> list[str]:
        """Return the current lesson copy for the inspector."""
        return lesson_lines(self)

    def command_sections(self):
        """Expose the command reference for the commands overlay."""
        return COMMAND_SECTIONS

    def sidebar_sections(self):
        """Expose the collapsible right-rail sections to the renderer."""
        return SIDEBAR_SECTIONS

    def start_lesson(self, lesson_id: str) -> None:
        """Activate one guided lesson."""
        lesson = lesson_by_id(lesson_id)
        if lesson is None:
            return
        self.state.lesson.lesson_id = lesson_id
        self.state.lesson.step_index = 0
        self.state.status_message = f"Started lesson: {lesson.title}"
        self.close_overlay()

    def try_create_constraint_from_shortcut(self, key: int) -> None:
        """Create a constraint from the selected and comparison shapes."""
        if self.selected_shape is None or self.comparison_shape is None:
            self.state.status_message = "Choose a main shape and a comparison shape first."
            return

        constraint_map = {
            pygame.K_1: "parallel",
            pygame.K_2: "perpendicular",
            pygame.K_3: "equal_length",
            pygame.K_4: "midpoint_lock",
        }
        kind = constraint_map[key]
        constraint = create_constraint(kind, self.selected_shape, self.comparison_shape)
        if constraint is None:
            self.state.status_message = "Those two shapes do not support that constraint."
            return

        if any(
            existing.kind == constraint.kind
            and existing.reference_shape_id == constraint.reference_shape_id
            and existing.target_shape_id == constraint.target_shape_id
            for existing in self.state.constraints
        ):
            self.state.status_message = "That constraint is already active."
            return

        self.state.constraints.append(constraint)
        self.state.recent_actions.add(f"constraint_{kind}")
        self.state.status_message = describe_constraint(constraint, self)

    def build_constraint(self, kind: str, reference_shape_id: int, target_shape_id: int) -> ConstraintLink | None:
        """Rebuild a persisted constraint."""
        if kind not in {"parallel", "perpendicular", "equal_length", "midpoint_lock"}:
            return None
        return ConstraintLink(kind=kind, reference_shape_id=reference_shape_id, target_shape_id=target_shape_id)

    def build_custom_function(
        self,
        *,
        name: str,
        expression: str,
        color: tuple[int, int, int],
        enabled: bool = True,
        attached_point_id: int | None = None,
        description: str = "Student-defined function.",
        function_id: int | None = None,
    ) -> CustomFunctionState:
        """Create a custom function state object."""
        resolved_id = self.state.next_custom_function_id if function_id is None else function_id
        return CustomFunctionState(
            id=resolved_id,
            name=name,
            expression=expression,
            color=color,
            enabled=enabled,
            attached_point_id=attached_point_id,
            description=description,
        )

    def get_custom_function(self, function_id: int | None) -> CustomFunctionState | None:
        """Return one custom function by id."""
        if function_id is None:
            return None
        return next((function for function in self.state.custom_functions if function.id == function_id), None)

    def start_new_custom_function(self) -> None:
        """Prepare the editor for a brand-new custom function."""
        self.state.equation_editing_id = None
        self.state.equation_input = DEFAULT_EQUATION_TEMPLATE
        self.state.equation_attach_to_selected_point = isinstance(self.selected_shape, PointShape)
        self.state.equation_status = "New function draft. Try a*x**2 + b*x + c, or add px and py to anchor it to a point."

    def cycle_equation_target(self, direction: int) -> None:
        """Cycle through saved custom functions while editing."""
        if not self.state.custom_functions:
            self.start_new_custom_function()
            return

        ordered = sorted(self.state.custom_functions, key=lambda function: function.id)
        ids = [function.id for function in ordered]
        if self.state.equation_editing_id not in ids:
            self.state.equation_editing_id = ids[0]
        else:
            current_index = ids.index(self.state.equation_editing_id)
            self.state.equation_editing_id = ids[(current_index + direction) % len(ids)]

        current = self.get_custom_function(self.state.equation_editing_id)
        if current is not None:
            self.state.equation_input = current.expression
            self.state.equation_attach_to_selected_point = current.attached_point_id is not None
            self.state.equation_status = f"Editing {current.name}"

    def save_equation_input(self) -> None:
        """Validate and save the current equation editor text."""
        expression = self.state.equation_input.strip()
        if not expression:
            self.state.equation_status = "The equation cannot be empty."
            return

        try:
            compile_expression(expression.replace("^", "**"))
        except ValueError as error:
            self.state.equation_status = str(error)
            return

        attached_point_id = self.selected_shape.id if (
            self.state.equation_attach_to_selected_point and isinstance(self.selected_shape, PointShape)
        ) else None

        existing = self.get_custom_function(self.state.equation_editing_id)
        if existing is None:
            function = self.build_custom_function(
                name=f"Custom {self.state.next_custom_function_id}",
                expression=expression,
                color=self.next_color(),
                attached_point_id=attached_point_id,
            )
            self.state.custom_functions.append(function)
            self.state.equation_editing_id = function.id
            self.state.next_custom_function_id += 1
        else:
            existing.expression = expression
            existing.enabled = True
            existing.attached_point_id = attached_point_id
            function = existing

        function.description = (
            "Attached to the selected point."
            if attached_point_id is not None
            else "Driven by the current slider values."
        )
        self.state.equation_status = f"Saved {function.name}."
        self.state.recent_actions.add("custom_function_saved")
        self.state.status_message = f"Saved {function.name}: y = {expression}"

    def delete_current_custom_function(self) -> None:
        """Delete the currently edited custom function."""
        current = self.get_custom_function(self.state.equation_editing_id)
        if current is None:
            self.state.equation_status = "Nothing to delete."
            return
        self.state.custom_functions = [
            function for function in self.state.custom_functions if function.id != current.id
        ]
        self.state.equation_editing_id = None
        self.state.equation_input = DEFAULT_EQUATION_TEMPLATE
        self.state.equation_status = f"Deleted {current.name}."
        self.state.status_message = f"Deleted {current.name}."

    def try_handle_transformation_shortcut(self, event: pygame.event.Event) -> bool:
        """Apply a teaching-focused transform to the selected shape."""
        if self.selected_shape is None:
            return False

        if event.key == pygame.K_LEFT:
            self.apply_transform(*apply_translation(self.selected_shape, -self.current_grid_step(), 0), tag="transform_translate")
            return True
        if event.key == pygame.K_RIGHT:
            self.apply_transform(*apply_translation(self.selected_shape, self.current_grid_step(), 0), tag="transform_translate")
            return True
        if event.key == pygame.K_UP:
            self.apply_transform(*apply_translation(self.selected_shape, 0, self.current_grid_step()), tag="transform_translate")
            return True
        if event.key == pygame.K_DOWN:
            self.apply_transform(*apply_translation(self.selected_shape, 0, -self.current_grid_step()), tag="transform_translate")
            return True
        if event.key == pygame.K_q:
            self.apply_transform(*apply_rotation(self.selected_shape, -15), tag="transform_rotate")
            return True
        if event.key == pygame.K_e:
            self.apply_transform(*apply_rotation(self.selected_shape, 15), tag="transform_rotate")
            return True
        if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.apply_transform(*apply_scale(self.selected_shape, 0.9), tag="transform_scale")
            return True
        if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.apply_transform(*apply_scale(self.selected_shape, 1.1), tag="transform_scale")
            return True
        if event.key == pygame.K_x:
            self.apply_transform(*apply_mirror(self.selected_shape, "x"), tag="transform_mirror")
            return True
        if event.key == pygame.K_y:
            self.apply_transform(*apply_mirror(self.selected_shape, "y"), tag="transform_mirror")
            return True
        if event.key == pygame.K_o:
            self.apply_transform(*apply_mirror(self.selected_shape, "origin"), tag="transform_mirror")
            return True
        return False

    def apply_transform(
        self,
        updated_shape: GeometryShape,
        matrix_lines: list[str],
        description: str,
        *,
        tag: str,
    ) -> None:
        """Replace the selected shape with its transformed version and store feedback."""
        if self.selected_shape is None:
            return
        original = copy_shape(self.selected_shape)
        self.shapes = [
            updated_shape if shape.id == updated_shape.id else shape
            for shape in self.shapes
        ]
        self.state.transform_ghost = original
        self.state.transform_description = description
        self.state.transform_matrix_lines = matrix_lines
        self.state.transform_ghost_ttl = 5.0
        self.state.recent_actions.add(tag)
        self.state.status_message = description

    def camera_label(self) -> str:
        """Return the compact camera summary shown in the footer."""
        return (
            f"Zoom {format_number(self.camera.zoom, 2)}x   |   Center "
            f"({format_number(self.camera.center[0])}, {format_number(self.camera.center[1])})   |   "
            f"Cursor ({format_number(self.state.cursor_world[0])}, {format_number(self.state.cursor_world[1])})   |   "
            f"Snap {'on' if self.state.snap_to_grid else 'off'}   |   "
            f"Intersections {'on' if self.state.show_intersections else 'off'}"
        )
