"""Mob entity for friendly and enemy crowd units with optimized sprite caching and batch counting."""

import enum
import math
import random
from typing import Dict, Optional, Set, Tuple
import pygame

from py_mob_control.config import (
    COLOR_PLAYER_PRIMARY,
    COLOR_PLAYER_SECONDARY,
    COLOR_PLAYER_CHAMPION,
    COLOR_ENEMY_PRIMARY,
    COLOR_ENEMY_SECONDARY,
    COLOR_ENEMY_CHAMPION,
    DEFAULT_MOB_SPEED,
    DEFAULT_MOB_RADIUS,
    DEFAULT_CHAMPION_RADIUS,
    DEFAULT_CHAMPION_HP,
    VIRTUAL_WIDTH,
)


class Team(enum.Enum):
    PLAYER = 1
    ENEMY = 2


# Global sprite cache for blazing-fast 60 FPS blitting
_SPRITE_CACHE: Dict[str, pygame.Surface] = {}


def _init_sprite_cache() -> None:
    """Pre-render mob sprites once at startup to avoid 100,000+ shape draws per frame."""
    if _SPRITE_CACHE:
        return

    r = int(DEFAULT_MOB_RADIUS)
    spacing = max(2, int(r * 0.35))
    eye_size = max(1, int(r * 0.22))
    eye_offset = -int(r * 0.2)

    # 1. Regular Player Mob (26 x 26)
    surf_p = pygame.Surface((26, 26), pygame.SRCALPHA)
    cx, cy = 13, 13
    pygame.draw.ellipse(surf_p, (10, 12, 18, 160), pygame.Rect(cx - r + 1, cy + r - 3, r * 2 - 2, int(r * 0.6)))
    pygame.draw.circle(surf_p, COLOR_PLAYER_PRIMARY, (cx, cy), r)
    pygame.draw.circle(surf_p, COLOR_PLAYER_SECONDARY, (cx - int(r * 0.3), cy - int(r * 0.3)), max(2, int(r * 0.35)))
    pygame.draw.circle(surf_p, (255, 255, 255), (cx - spacing, cy + eye_offset), eye_size + 1)
    pygame.draw.circle(surf_p, (255, 255, 255), (cx + spacing, cy + eye_offset), eye_size + 1)
    pygame.draw.circle(surf_p, (15, 15, 25), (cx - spacing, cy + eye_offset - 1), max(1, eye_size - 1))
    pygame.draw.circle(surf_p, (15, 15, 25), (cx + spacing, cy + eye_offset - 1), max(1, eye_size - 1))
    _SPRITE_CACHE["player_normal"] = surf_p

    # 2. Dense Player Mob (count >= 5) with luminous cyan glow aura (32 x 32)
    surf_dense = pygame.Surface((32, 32), pygame.SRCALPHA)
    dcx, dcy, dr = 16, 16, int(DEFAULT_MOB_RADIUS * 1.25)
    pygame.draw.circle(surf_dense, (40, 220, 255, 90), (dcx, dcy), dr + 3)
    pygame.draw.circle(surf_dense, COLOR_PLAYER_PRIMARY, (dcx, dcy), dr)
    pygame.draw.circle(surf_dense, COLOR_PLAYER_SECONDARY, (dcx - int(dr * 0.3), dcy - int(dr * 0.3)), max(2, int(dr * 0.35)))
    pygame.draw.circle(surf_dense, (255, 255, 255), (dcx - spacing - 1, dcy + eye_offset), eye_size + 1)
    pygame.draw.circle(surf_dense, (255, 255, 255), (dcx + spacing + 1, dcy + eye_offset), eye_size + 1)
    pygame.draw.circle(surf_dense, (15, 15, 25), (dcx - spacing - 1, dcy + eye_offset - 1), max(1, eye_size - 1))
    pygame.draw.circle(surf_dense, (15, 15, 25), (dcx + spacing + 1, dcy + eye_offset - 1), max(1, eye_size - 1))
    _SPRITE_CACHE["player_dense"] = surf_dense

    # 3. Regular Enemy Mob (26 x 26)
    surf_e = pygame.Surface((26, 26), pygame.SRCALPHA)
    pygame.draw.ellipse(surf_e, (10, 12, 18, 160), pygame.Rect(cx - r + 1, cy + r - 3, r * 2 - 2, int(r * 0.6)))
    pygame.draw.circle(surf_e, COLOR_ENEMY_PRIMARY, (cx, cy), r)
    pygame.draw.circle(surf_e, COLOR_ENEMY_SECONDARY, (cx - int(r * 0.3), cy - int(r * 0.3)), max(2, int(r * 0.35)))
    pygame.draw.circle(surf_e, (255, 255, 255), (cx - spacing, cy - eye_offset), eye_size + 1)
    pygame.draw.circle(surf_e, (255, 255, 255), (cx + spacing, cy - eye_offset), eye_size + 1)
    pygame.draw.circle(surf_e, (15, 15, 25), (cx - spacing, cy - eye_offset + 1), max(1, eye_size - 1))
    pygame.draw.circle(surf_e, (15, 15, 25), (cx + spacing, cy - eye_offset + 1), max(1, eye_size - 1))
    _SPRITE_CACHE["enemy_normal"] = surf_e


class Mob:
    """Individual crowd unit in battle supporting multi-unit batching and sprite caching."""

    _next_id: int = 1

    def __init__(
        self,
        x: float,
        y: float,
        team: Team,
        speed: float = DEFAULT_MOB_SPEED,
        is_champion: bool = False,
        hp: int = 1,
        count: int = 1,
    ) -> None:
        self.id = Mob._next_id
        Mob._next_id += 1

        self.x = x
        self.y = y
        self.team = team
        self.is_champion = is_champion
        self.count = count

        self.radius = DEFAULT_CHAMPION_RADIUS if is_champion else DEFAULT_MOB_RADIUS
        self.base_speed = speed * (0.85 if is_champion else 1.0)
        self.speed = self.base_speed
        self.max_hp = DEFAULT_CHAMPION_HP if is_champion else hp
        self.hp = self.max_hp

        # Direction: player moves UP (negative y), enemy moves DOWN (positive y)
        self.dir_y = -1.0 if team == Team.PLAYER else 1.0
        self.vx = random.uniform(-10.0, 10.0)
        self.vy = self.dir_y * self.speed

        self.alive = True
        self.passed_gate_ids: Set[int] = set()

        # Visual animation timer
        self.anim_time = random.uniform(0.0, math.tau)

    def update(self, dt: float) -> None:
        """Update mob position, bounds clamping, and funneling towards base."""
        if not self.alive:
            return

        self.anim_time += dt * 14.0

        # Gentle drift toward center if nearing walls
        wall_margin = self.radius + 6.0
        if self.x < wall_margin:
            self.x = wall_margin
            self.vx = abs(self.vx) * 0.5
        elif self.x > VIRTUAL_WIDTH - wall_margin:
            self.x = VIRTUAL_WIDTH - wall_margin
            self.vx = -abs(self.vx) * 0.5

        # Funnel friendly mobs toward base entrance when nearing the top
        if self.team == Team.PLAYER and self.y < 350.0:
            target_x = VIRTUAL_WIDTH / 2.0
            dx = target_x - self.x
            self.vx += dx * dt * 1.5

        # Forward velocity
        self.vy = self.dir_y * self.speed
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Dampen horizontal sway
        self.vx *= 0.92

    def take_damage(self, amount: int = 1) -> bool:
        """Apply damage. Returns True if killed."""
        if self.is_champion:
            self.hp -= amount
            if self.hp <= 0:
                self.alive = False
                return True
            return False
        else:
            if self.count > 1:
                self.count -= amount
                if self.count <= 0:
                    self.alive = False
                    return True
                return False
            else:
                self.hp -= amount
                if self.hp <= 0:
                    self.alive = False
                    return True
                return False

    def draw(self, surface: pygame.Surface) -> None:
        """Render mob with lightning-fast cached sprite blits."""
        if not self.alive:
            return

        if not _SPRITE_CACHE:
            _init_sprite_cache()

        ix = int(self.x)
        iy = int(self.y)

        if self.is_champion:
            self._draw_champion(surface, ix, iy)
            return

        if self.team == Team.PLAYER:
            is_dense = self.count >= 5
            sprite = _SPRITE_CACHE.get("player_dense" if is_dense else "player_normal")
            offset = 16 if is_dense else 13
        else:
            sprite = _SPRITE_CACHE.get("enemy_normal")
            offset = 13

        if sprite:
            surface.blit(sprite, (ix - offset, iy - offset))

    def _draw_champion(self, surface: pygame.Surface, ix: int, iy: int) -> None:
        """Render heavy champion unit with crown and HP bar."""
        ir = int(self.radius)

        # Shadow
        shadow_rect = pygame.Rect(ix - ir + 1, iy + ir - 2, (ir * 2) - 2, int(ir * 0.6))
        pygame.draw.ellipse(surface, (10, 12, 18), shadow_rect)

        # Body
        body_color = COLOR_PLAYER_CHAMPION if self.team == Team.PLAYER else COLOR_ENEMY_CHAMPION
        highlight_color = COLOR_PLAYER_SECONDARY if self.team == Team.PLAYER else COLOR_ENEMY_SECONDARY
        pygame.draw.circle(surface, body_color, (ix, iy), ir)
        pygame.draw.circle(surface, highlight_color, (ix - int(ir * 0.3), iy - int(ir * 0.3)), max(2, int(ir * 0.35)))

        # Eyes
        eye_y_offset = -int(ir * 0.2) if self.team == Team.PLAYER else int(ir * 0.2)
        eye_spacing = max(2, int(ir * 0.35))
        eye_size = max(1, int(ir * 0.22))
        pygame.draw.circle(surface, (255, 255, 255), (ix - eye_spacing, iy + eye_y_offset), eye_size + 1)
        pygame.draw.circle(surface, (255, 255, 255), (ix + eye_spacing, iy + eye_y_offset), eye_size + 1)

        # Crown
        crown_y = iy - ir - 3 if self.team == Team.PLAYER else iy + ir + 3
        crown_points = [
            (ix - 12, crown_y),
            (ix - 8, crown_y - 6),
            (ix - 4, crown_y - 2),
            (ix, crown_y - 8),
            (ix + 4, crown_y - 2),
            (ix + 8, crown_y - 6),
            (ix + 12, crown_y),
        ]
        pygame.draw.polygon(surface, (255, 215, 0), crown_points)
        pygame.draw.polygon(surface, (200, 150, 0), crown_points, 1)

        # Mini HP Bar
        bar_w = 34
        bar_h = 5
        bar_x = ix - (bar_w // 2)
        bar_y = iy - ir - 12 if self.team == Team.PLAYER else iy + ir + 10
        pygame.draw.rect(surface, (20, 20, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
        fill_color = (40, 220, 80) if self.hp > (self.max_hp * 0.3) else (255, 50, 50)
        pygame.draw.rect(surface, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
        pygame.draw.rect(surface, (180, 180, 200), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=2)
