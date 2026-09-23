"""Animated floating combat text for multipliers, brick gains, and impact labels."""

from typing import List, Tuple
import pygame


class FloatingText:
    """Individual floating text popup."""
    __slots__ = ("text", "x", "y", "vy", "life", "max_life", "color", "size_multiplier")

    def __init__(
        self,
        text: str,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (255, 255, 255),
        life: float = 0.65,
        vy: float = -65.0,
        size_multiplier: float = 1.0,
    ) -> None:
        self.text = text
        self.x = x
        self.y = y
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size_multiplier = size_multiplier

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.y += self.vy * dt
        self.vy *= 0.96  # gradual deceleration
        return self.life > 0.0


class FloatingTextManager:
    """Manages active floating text messages and draws them."""

    def __init__(self) -> None:
        self.items: List[FloatingText] = []
        pygame.font.init()
        self.font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_large = pygame.font.SysFont("Segoe UI", 22, bold=True)

    def spawn(
        self,
        text: str,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (255, 255, 255),
        large: bool = False,
    ) -> None:
        """Create a new floating text item."""
        life = 0.8 if large else 0.55
        self.items.append(
            FloatingText(text, x, y, color=color, life=life, size_multiplier=1.4 if large else 1.0)
        )

    def update(self, dt: float) -> None:
        """Update positions and remove expired text."""
        self.items = [item for item in self.items if item.update(dt)]

    def draw(self, surface: pygame.Surface) -> None:
        """Draw floating text items."""
        for item in self.items:
            f = self.font_large if item.size_multiplier > 1.1 else self.font
            # Render text
            text_surf = f.render(item.text, True, item.color)

            # Optional alpha fade
            alpha_ratio = max(0.0, min(1.0, item.life / (item.max_life * 0.7)))
            if alpha_ratio < 1.0:
                text_surf.set_alpha(int(alpha_ratio * 255))

            # Center text on (x, y)
            rect = text_surf.get_rect(center=(int(item.x), int(item.y)))

            # Subtle dark outline for contrast
            outline_surf = f.render(item.text, True, (10, 10, 15))
            if alpha_ratio < 1.0:
                outline_surf.set_alpha(int(alpha_ratio * 255))
            surface.blit(outline_surf, (rect.x + 1, rect.y + 1))
            surface.blit(text_surf, rect)
