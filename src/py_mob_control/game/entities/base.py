"""Enemy base and defensive towers with brick structure and damage states."""

import random
from typing import List, Optional, Tuple
import pygame

from py_mob_control.config import (
    VIRTUAL_WIDTH,
    COLOR_ENEMY_PRIMARY,
    COLOR_ENEMY_SECONDARY,
    COLOR_BRICK_BASE,
    COLOR_BRICK_GOLD,
    COLOR_TEXT_PRIMARY,
)
from .mob import Mob, Team


class EnemyBase:
    """Enemy fortress at the top of the battlefield composed of bricks."""

    def __init__(
        self,
        max_bricks: int = 150,
        spawn_rate: float = 1.8,
        y: float = 65.0,
    ) -> None:
        self.x: float = VIRTUAL_WIDTH / 2.0
        self.y: float = y
        self.width: float = 280.0
        self.height: float = 90.0

        self.max_bricks: int = max_bricks
        self.bricks: int = max_bricks

        self.spawn_rate: float = spawn_rate  # enemy mobs per second
        self.spawn_timer: float = 0.0

        self.is_destroyed: bool = False
        self.hit_flash: float = 0.0

        # Fonts
        pygame.font.init()
        self.font = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 13)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - (self.width / 2.0)),
            int(self.y - (self.height / 2.0)),
            int(self.width),
            int(self.height),
        )

    def update(self, dt: float) -> Optional[Mob]:
        """Update spawn timers and hit flash. May return an enemy mob to spawn."""
        if self.is_destroyed:
            return None

        self.hit_flash = max(0.0, self.hit_flash - (dt * 6.0))

        # Enemy mob spawning
        if self.spawn_rate > 0.0:
            self.spawn_timer += dt
            interval = 1.0 / self.spawn_rate
            if self.spawn_timer >= interval:
                self.spawn_timer -= interval
                # Spawn an enemy mob heading down
                spawn_x = self.x + random.uniform(-self.width * 0.35, self.width * 0.35)
                return Mob(x=spawn_x, y=self.y + (self.height / 2.0) + 10.0, team=Team.ENEMY)

        return None

    def take_damage(self, amount: int = 1) -> Tuple[int, bool]:
        """Deal damage (remove bricks).

        Returns (bricks_lost, base_newly_destroyed).
        """
        if self.is_destroyed:
            return 0, False

        self.hit_flash = 1.0
        actual_loss = min(self.bricks, amount)
        self.bricks -= actual_loss

        if self.bricks <= 0:
            self.bricks = 0
            self.is_destroyed = True
            return actual_loss, True

        return actual_loss, False

    def check_mob_attack(self, mob: Mob) -> Tuple[int, bool]:
        """If a friendly mob reaches the base line, it attacks the base."""
        if not mob.alive or mob.team != Team.PLAYER:
            return 0, False

        # Collision with bottom line of base
        base_bottom = self.y + (self.height / 2.0)
        if mob.y <= base_bottom + mob.radius:
            mob.alive = False
            cnt = getattr(mob, "count", 1)
            damage = (10 * cnt) if mob.is_champion else cnt
            return self.take_damage(damage)

        return 0, False

    def draw(self, surface: pygame.Surface) -> None:
        """Render fortress with battlements, brick health bar and damage states."""
        r = self.rect

        # 1. Main Fortress Body
        base_color = (180, 50, 60) if self.hit_flash > 0.1 else (50, 25, 35)
        pygame.draw.rect(surface, base_color, r, border_radius=8)
        pygame.draw.rect(surface, COLOR_ENEMY_PRIMARY, r, 2, border_radius=8)

        # 2. Battlements / Towers
        tower_w = 40
        tower_h = 30
        left_tower = pygame.Rect(r.left - 10, r.top - 12, tower_w, tower_h)
        right_tower = pygame.Rect(r.right - tower_w + 10, r.top - 12, tower_w, tower_h)
        center_turret = pygame.Rect(int(self.x - 22), r.top - 16, 44, tower_h)

        for tower in (left_tower, right_tower, center_turret):
            pygame.draw.rect(surface, (70, 30, 42), tower, border_radius=4)
            pygame.draw.rect(surface, COLOR_ENEMY_PRIMARY, tower, 2, border_radius=4)

        # 3. Decorative Brick Grid Pattern
        grid_rows = 3
        grid_cols = 6
        cell_w = (r.width - 24) / grid_cols
        cell_h = (r.height - 36) / grid_rows
        start_x = r.left + 12
        start_y = r.top + 28

        for row in range(grid_rows):
            for col in range(grid_cols):
                bx = start_x + (col * cell_w)
                by = start_y + (row * cell_h)
                brick_rect = pygame.Rect(int(bx) + 2, int(by) + 2, int(cell_w) - 4, int(cell_h) - 4)
                pygame.draw.rect(surface, (85, 38, 50), brick_rect, border_radius=2)

        # 4. Brick Counter Bar & Health Badge
        bar_w = int(r.width * 0.75)
        bar_h = 16
        bar_x = int(self.x - (bar_w / 2.0))
        bar_y = r.bottom - 22

        # Bar background
        pygame.draw.rect(surface, (20, 20, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=4)

        # Fill
        ratio = max(0.0, self.bricks / float(self.max_bricks))
        fill_w = int(bar_w * ratio)
        fill_color = COLOR_BRICK_BASE if ratio > 0.3 else (255, 60, 60)
        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, (200, 200, 220), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

        # Health / Brick Count Text
        label = f"BASE: {self.bricks} BRICKS"
        text_surf = self.font_small.render(label, True, COLOR_TEXT_PRIMARY)
        text_rect = text_surf.get_rect(center=(int(self.x), bar_y + (bar_h // 2)))
        surface.blit(text_surf, text_rect)
