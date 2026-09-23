"""Input manager handling keyboard and mouse events cleanly."""

from typing import Set, Tuple
import pygame

from py_mob_control.config import (
    KEY_LEFT,
    KEY_RIGHT,
    KEY_FIRE,
    KEY_CHAMPION,
    KEY_FULLSCREEN,
    KEY_MUTE,
    KEY_PAUSE,
)


class InputManager:
    """Consolidates keyboard, mouse position, and button states."""

    def __init__(self) -> None:
        self.mouse_screen_pos: Tuple[int, int] = (0, 0)
        self.mouse_left_down: bool = False
        self.mouse_right_down: bool = False

        self.keys_down_this_frame: Set[int] = set()
        self.keys_held: Set[int] = set()
        self.mouse_clicked_this_frame: bool = False
        self.mouse_right_clicked_this_frame: bool = False
        self.quit_requested: bool = False
        self.resize_event: Tuple[int, int] = None

    def begin_frame(self) -> None:
        """Reset single-frame triggers before event polling."""
        self.keys_down_this_frame.clear()
        self.mouse_clicked_this_frame = False
        self.mouse_right_clicked_this_frame = False
        self.resize_event = None

    def process_event(self, event: pygame.event.Event) -> None:
        """Process a single Pygame event."""
        if event.type == pygame.QUIT:
            self.quit_requested = True

        elif event.type == pygame.KEYDOWN:
            self.keys_down_this_frame.add(event.key)
            self.keys_held.add(event.key)

        elif event.type == pygame.KEYUP:
            self.keys_held.discard(event.key)

        elif event.type == pygame.MOUSEMOTION:
            self.mouse_screen_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.mouse_left_down = True
                self.mouse_clicked_this_frame = True
            elif event.button == 3:
                self.mouse_right_down = True
                self.mouse_right_clicked_this_frame = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_left_down = False
            elif event.button == 3:
                self.mouse_right_down = False

        elif event.type == pygame.VIDEORESIZE:
            self.resize_event = (event.w, event.h)

    def is_key_just_pressed(self, key_list) -> bool:
        """Return True if any of the keys in key_list was pressed down this frame."""
        return any(k in self.keys_down_this_frame for k in key_list)

    def is_key_held(self, key_list) -> bool:
        """Return True if any of the keys in key_list is currently held."""
        return any(k in self.keys_held for k in key_list)

    def is_firing(self) -> bool:
        """Firing is triggered by holding Left Mouse Button or Space/Up."""
        return self.mouse_left_down or self.is_key_held(KEY_FIRE)

    def is_champion_summon_triggered(self) -> bool:
        """Champion summon triggered by Right Click or Q/E/1/2 keys."""
        return self.mouse_right_clicked_this_frame or self.is_key_just_pressed(KEY_CHAMPION)

    def get_horizontal_keyboard_axis(self) -> float:
        """Returns -1.0 (left), 1.0 (right), or 0.0."""
        axis = 0.0
        if self.is_key_held(KEY_LEFT):
            axis -= 1.0
        if self.is_key_held(KEY_RIGHT):
            axis += 1.0
        return axis

    def is_fullscreen_toggle_pressed(self) -> bool:
        return self.is_key_just_pressed(KEY_FULLSCREEN)

    def is_mute_toggle_pressed(self) -> bool:
        return self.is_key_just_pressed(KEY_MUTE)

    def is_pause_pressed(self) -> bool:
        return self.is_key_just_pressed(KEY_PAUSE)
