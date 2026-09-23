"""Mob entity for friendly and enemy crowd units."""

import enum
import math
import random
from typing import Set, Tuple
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


class Mob:
    """Individual crowd unit in battle."""

    _next_id: int = 1

    def __init__(
        self,
        x: float,
        y: float,
        team: Team,
        speed: float = DEFAULT_MOB_SPEED,
        is_champion: bool = False,
        hp: int = 1,
    ) -> None:
        self.id = Mob._next_id
        Mob._next_id += 1

        self.x = x
        self.y = y
        self.team = team
        self.is_champion = is_champion

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
        """Update mob position, bounds clamping, and animation step."""
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

        # Forward velocity
        self.vy = self.dir_y * self.speed
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Dampen horizontal sway
        self.vx *= 0.94

    def take_damage(self, amount: int = 1) -> bool:
        """Apply damage. Return True if killed."""
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Render stylized mob with eyes, shadow, and champion crown."""
        if not self.alive:
            return

        ix = int(self.x)
        iy = int(self.y)
        ir = int(self.radius)

        # 1. Shadow underneath
        shadow_rect = pygame.Rect(ix - ir + 1, iy + ir - 2, (ir * 2) - 2, int(ir * 0.6))
        pygame.draw.ellipse(surface, (10, 12, 18), shadow_rect)

        # 2. Main Body
        if self.team == Team.PLAYER:
            body_color = COLOR_PLAYER_CHAMPION if self.is_champion else COLOR_PLAYER_PRIMARY
            highlight_color = COLOR_PLAYER_SECONDARY
        else:
            body_color = COLOR_ENEMY_CHAMPION if self.is_champion else COLOR_ENEMY_PRIMARY
            highlight_color = COLOR_ENEMY_SECONDARY

        pygame.draw.circle(surface, body_color, (ix, iy), ir)
        # Inner specular highlight
        highlight_r = max(2, int(ir * 0.35))
        pygame.draw.circle(surface, highlight_color, (ix - int(ir * 0.3), iy - int(ir * 0.3)), highlight_r)

        # 3. Expressive Eyes
        eye_y_offset = -int(ir * 0.2) if self.team == Team.PLAYER else int(ir * 0.2)
        eye_spacing = max(2, int(ir * 0.35))
        eye_size = max(1, int(ir * 0.22))

        # Left & Right eyes
        pygame.draw.circle(surface, (255, 255, 255), (ix - eye_spacing, iy + eye_y_offset), eye_size + 1)
        pygame.draw.circle(surface, (255, 255, 255), (ix + eye_spacing, iy + eye_y_offset), eye_size + 1)
        # Pupils looking in movement direction
        pupil_y = iy + eye_y_offset + (int(self.dir_y * 1))
        pygame.draw.circle(surface, (15, 15, 25), (ix - eye_spacing, pupil_y), max(1, eye_size - 1))
        pygame.draw.circle(surface, (15, 15, 25), (ix + eye_spacing, pupil_y), max(1, eye_size - 1))

        # 4. Champion Special Accents (Crown & HP Bar)
        if self.is_champion:
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
            # Background
            pygame.draw.rect(surface, (20, 20, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
            # Fill
            fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
            fill_color = (40, 220, 80) if self.hp > (self.max_hp * 0.3) else (255, 50, 50)
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
            pygame.draw.rect(surface, (180, 180, 200), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=2)
