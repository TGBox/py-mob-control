"""Cannon entity representing player or enemy mob launcher."""

import math
from typing import Optional, Tuple
import pygame

from py_mob_control.config import (
    VIRTUAL_WIDTH,
    TRACK_Y_PLAYER,
    TRACK_MARGIN_X,
    COLOR_PLAYER_PRIMARY,
    COLOR_PLAYER_SECONDARY,
    COLOR_ENEMY_PRIMARY,
    COLOR_ENEMY_SECONDARY,
    COLOR_ACCENT_GOLD,
    CHAMPION_CHARGE_REQUIRED,
)
from .mob import Mob, Team


class Cannon:
    """Controllable cannon that fires mobs and charges ultimate."""

    def __init__(
        self,
        y: float = TRACK_Y_PLAYER,
        team: Team = Team.PLAYER,
        fire_rate: float = 6.0,
        move_speed: float = 480.0,
    ) -> None:
        self.x: float = VIRTUAL_WIDTH / 2.0
        self.y: float = y
        self.team: Team = team

        self.fire_rate: float = fire_rate  # mobs per second
        self.move_speed: float = move_speed

        self.cooldown_timer: float = 0.0
        self.recoil: float = 0.0

        # Ultimate charge (0.0 to 1.0)
        self.ultimate_progress: float = 0.0
        self.shots_fired: int = 0

        # Visual barrel recoil
        self.barrel_length: float = 34.0
        self.barrel_width: float = 18.0
        self.base_radius: float = 24.0

    @property
    def is_ultimate_ready(self) -> bool:
        return self.ultimate_progress >= 1.0

    def move_toward(self, target_x: float, dt: float) -> None:
        """Smoothly move cannon toward target horizontal position."""
        dx = target_x - self.x
        max_step = self.move_speed * dt
        if abs(dx) <= max_step:
            self.x = target_x
        else:
            self.x += math.copysign(max_step, dx)

        # Clamp to track margins
        min_x = TRACK_MARGIN_X + self.base_radius
        max_x = VIRTUAL_WIDTH - TRACK_MARGIN_X - self.base_radius
        self.x = max(min_x, min(max_x, self.x))

    def move_axis(self, axis: float, dt: float) -> None:
        """Move using horizontal input axis (-1.0 to 1.0)."""
        self.x += axis * self.move_speed * dt
        min_x = TRACK_MARGIN_X + self.base_radius
        max_x = VIRTUAL_WIDTH - TRACK_MARGIN_X - self.base_radius
        self.x = max(min_x, min(max_x, self.x))

    def update(self, dt: float) -> None:
        """Update cooldown timers and spring recoil."""
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        # Decay recoil
        self.recoil = max(0.0, self.recoil - (dt * 50.0))

    def try_fire(self, mob_speed: float) -> Optional[Mob]:
        """Fire a regular mob if cooldown has elapsed."""
        if self.cooldown_timer > 0.0:
            return None

        self.cooldown_timer = 1.0 / max(1.0, self.fire_rate)
        self.recoil = 8.0
        self.shots_fired += 1

        # Charge ultimate
        self.add_ultimate_charge(1.0 / CHAMPION_CHARGE_REQUIRED)

        # Spawn mob slightly ahead of cannon barrel
        spawn_dir = -1.0 if self.team == Team.PLAYER else 1.0
        spawn_y = self.y + (spawn_dir * (self.barrel_length + 4.0))

        return Mob(x=self.x, y=spawn_y, team=self.team, speed=mob_speed)

    def add_ultimate_charge(self, amount: float) -> None:
        """Add charge to the ultimate meter."""
        self.ultimate_progress = min(1.0, self.ultimate_progress + amount)

    def try_summon_champion(self, mob_speed: float) -> Optional[Mob]:
        """Summon giant champion if ultimate meter is fully charged."""
        if not self.is_ultimate_ready:
            return None

        self.ultimate_progress = 0.0
        self.recoil = 14.0

        spawn_dir = -1.0 if self.team == Team.PLAYER else 1.0
        spawn_y = self.y + (spawn_dir * (self.barrel_length + 18.0))

        return Mob(x=self.x, y=spawn_y, team=self.team, speed=mob_speed * 0.9, is_champion=True)

    def draw(self, surface: pygame.Surface) -> None:
        """Render stylized sci-fi cannon with metallic barrel, glowing core and recoil."""
        ix = int(self.x)
        iy = int(self.y)
        primary_col = COLOR_PLAYER_PRIMARY if self.team == Team.PLAYER else COLOR_ENEMY_PRIMARY
        sec_col = COLOR_PLAYER_SECONDARY if self.team == Team.PLAYER else COLOR_ENEMY_SECONDARY

        dir_sign = -1 if self.team == Team.PLAYER else 1

        # 1. Track Rails underneath
        rail_y = iy + (dir_sign * 14)
        pygame.draw.line(surface, (40, 48, 70), (TRACK_MARGIN_X, rail_y), (VIRTUAL_WIDTH - TRACK_MARGIN_X, rail_y), 4)
        pygame.draw.line(surface, (25, 30, 45), (TRACK_MARGIN_X, rail_y + 3), (VIRTUAL_WIDTH - TRACK_MARGIN_X, rail_y + 3), 2)

        # 2. Cannon Barrel (with recoil slide)
        barrel_h = self.barrel_length - self.recoil
        half_w = self.barrel_width / 2.0
        barrel_top_y = iy + (dir_sign * barrel_h)

        if self.team == Team.PLAYER:
            barrel_rect = pygame.Rect(ix - half_w, barrel_top_y, self.barrel_width, barrel_h)
        else:
            barrel_rect = pygame.Rect(ix - half_w, iy, self.barrel_width, barrel_h)

        pygame.draw.rect(surface, (60, 70, 90), barrel_rect, border_radius=4)
        pygame.draw.rect(surface, sec_col, barrel_rect, 2, border_radius=4)

        # Muzzle ring
        muzzle_y = barrel_top_y if self.team == Team.PLAYER else barrel_top_y
        muzzle_rect = pygame.Rect(ix - half_w - 2, muzzle_y - 2, self.barrel_width + 4, 6)
        pygame.draw.rect(surface, sec_col, muzzle_rect, border_radius=2)

        # 3. Turret Base Sphere
        pygame.draw.circle(surface, (30, 36, 52), (ix, iy), int(self.base_radius))
        pygame.draw.circle(surface, primary_col, (ix, iy), int(self.base_radius - 4))

        # 4. Energy Core / Ultimate Meter Glow
        core_radius = int(self.base_radius * 0.45)
        core_color = COLOR_ACCENT_GOLD if self.is_ultimate_ready else sec_col
        pygame.draw.circle(surface, core_color, (ix, iy), core_radius)

        if self.is_ultimate_ready:
            # Pulsing golden aura when champion is ready!
            pygame.draw.circle(surface, (255, 230, 100), (ix, iy), int(self.base_radius + 3), 2)
