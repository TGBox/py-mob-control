"""Display and layout manager with adaptive widescreen, ultrawide (21:9), and fullscreen support."""

from typing import Tuple, Optional
import pygame

from py_mob_control.config import (
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    COLOR_BG_DARK,
    COLOR_BG_SIDEBAR,
    COLOR_BORDER,
    COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GOLD,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
)


class DisplayManager:
    """Manages window creation, fullscreen toggling, virtual-to-screen coordinate mapping,

    and adaptive sidebars for 16:9 and 21:9 ultrawide screens.
    """

    def __init__(self, width: int = DEFAULT_WINDOW_WIDTH, height: int = DEFAULT_WINDOW_HEIGHT) -> None:
        self.window_width: int = width
        self.window_height: int = height
        self.is_fullscreen: bool = False

        # Create window
        self.flags = pygame.RESIZABLE | pygame.DOUBLEBUF
        self.screen: pygame.Surface = pygame.display.set_mode((self.window_width, self.window_height), self.flags)
        pygame.display.set_caption("Mob Control - Python Desktop Edition")

        # Virtual game surface (drawn at crisp internal resolution)
        self.virtual_surface: pygame.Surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        # Fonts
        self._init_fonts()

        # Layout rects
        self.battlefield_rect: pygame.Rect = pygame.Rect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        self.left_panel_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.right_panel_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.scale: float = 1.0

        self.recalculate_layout(self.window_width, self.window_height)

    def _init_fonts(self) -> None:
        """Initialize standard UI fonts."""
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.font_header = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 15)
        self.font_mono = pygame.font.SysFont("Consolas", 14)
        self.font_big = pygame.font.SysFont("Segoe UI", 36, bold=True)

    def toggle_fullscreen(self) -> None:
        """Toggle between windowed and native display fullscreen."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            # Use desktop resolution for fullscreen
            info = pygame.display.Info()
            self.window_width = info.current_w
            self.window_height = info.current_h
            self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        else:
            self.window_width = DEFAULT_WINDOW_WIDTH
            self.window_height = DEFAULT_WINDOW_HEIGHT
            self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE | pygame.DOUBLEBUF)

        self.recalculate_layout(self.window_width, self.window_height)

    def handle_resize(self, width: int, height: int) -> None:
        """Handle window resize event."""
        self.window_width = max(800, width)
        self.window_height = max(600, height)
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), self.flags)
        actual_w, actual_h = self.screen.get_size()
        self.window_width = actual_w
        self.window_height = actual_h
        self.recalculate_layout(self.window_width, self.window_height)

    def recalculate_layout(self, w: int, h: int) -> None:
        """Calculate battlefield and dynamic widescreen/ultrawide sidebar dimensions."""
        padding_y = 30
        available_h = max(200, h - (padding_y * 2))
        self.scale = available_h / float(VIRTUAL_HEIGHT)

        scaled_bw = int(VIRTUAL_WIDTH * self.scale)
        scaled_bh = int(VIRTUAL_HEIGHT * self.scale)

        center_x = w // 2
        bf_x = center_x - (scaled_bw // 2)
        bf_y = (h - scaled_bh) // 2

        self.battlefield_rect = pygame.Rect(bf_x, bf_y, scaled_bw, scaled_bh)

        # Sidebars for wide screens (16:9, 21:9 ultrawide)
        margin = 16
        left_w = max(0, bf_x - (margin * 2))
        right_w = max(0, w - (bf_x + scaled_bw) - (margin * 2))

        self.left_panel_rect = pygame.Rect(margin, margin, left_w, h - (margin * 2))
        self.right_panel_rect = pygame.Rect(bf_x + scaled_bw + margin, margin, right_w, h - (margin * 2))

    def screen_to_virtual(self, screen_pos: Tuple[int, int]) -> Tuple[float, float]:
        """Convert screen pixel coordinates to virtual battlefield coordinates (clamped)."""
        sx, sy = screen_pos
        vx = (sx - self.battlefield_rect.x) / self.scale
        vy = (sy - self.battlefield_rect.y) / self.scale
        vx = max(0.0, min(float(VIRTUAL_WIDTH), vx))
        vy = max(0.0, min(float(VIRTUAL_HEIGHT), vy))
        return vx, vy

    def virtual_to_screen(self, virtual_pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convert virtual battlefield coordinates to screen coordinates."""
        vx, vy = virtual_pos
        sx = int(self.battlefield_rect.x + (vx * self.scale))
        sy = int(self.battlefield_rect.y + (vy * self.scale))
        return sx, sy

    def render_frame(self, screen_shake_offset: Tuple[float, float] = (0.0, 0.0)) -> None:
        """Scale and blit the virtual surface into the center of the window with border and shake."""
        # Scale battlefield surface
        scaled_surface = pygame.transform.smoothscale(
            self.virtual_surface, (self.battlefield_rect.width, self.battlefield_rect.height)
        )

        ox = int(screen_shake_offset[0] * self.scale)
        oy = int(screen_shake_offset[1] * self.scale)
        dest_rect = self.battlefield_rect.move(ox, oy)

        self.screen.blit(scaled_surface, dest_rect)

        # Draw glowing framing border around battlefield
        pygame.draw.rect(self.screen, COLOR_BORDER, dest_rect, 2, border_radius=6)
        # Corner accent highlights
        c_len = 16
        pygame.draw.line(self.screen, COLOR_ACCENT_CYAN, dest_rect.topleft, (dest_rect.left + c_len, dest_rect.top), 3)
        pygame.draw.line(self.screen, COLOR_ACCENT_CYAN, dest_rect.topleft, (dest_rect.left, dest_rect.top + c_len), 3)
        pygame.draw.line(self.screen, COLOR_ACCENT_CYAN, dest_rect.topright, (dest_rect.right - c_len, dest_rect.top), 3)
        pygame.draw.line(self.screen, COLOR_ACCENT_CYAN, dest_rect.topright, (dest_rect.right, dest_rect.top + c_len), 3)
        pygame.draw.line(self.screen, COLOR_ACCENT_CYAN, dest_rect.bottomleft, (dest_rect.left + c_len, dest_rect.bottom), 3)
        pygame.draw.line(self.screen, COLOR_ACCENT_CYAN, dest_rect.bottomleft, (dest_rect.left, dest_rect.bottom - c_len), 3)
        pygame.draw.line(self.screen, COLOR_ACCENT_CYAN, dest_rect.bottomright, (dest_rect.right - c_len, dest_rect.bottom), 3)
        pygame.draw.line(self.screen, COLOR_ACCENT_CYAN, dest_rect.bottomright, (dest_rect.right, dest_rect.bottom - c_len), 3)
