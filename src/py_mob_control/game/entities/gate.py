"""Multiplier gates that clone, multiply, boost, or filter mobs passing through."""

import enum
import math
import random
from typing import List, Optional, Tuple
import pygame

from py_mob_control.config import (
    COLOR_GATE_ADD,
    COLOR_GATE_MULTIPLY,
    COLOR_GATE_SUBTRACT,
    COLOR_GATE_DIVIDE,
    COLOR_GATE_SPEED,
    VIRTUAL_WIDTH,
)
from .mob import Mob, Team


class GateOperation(enum.Enum):
    ADD = 1
    MULTIPLY = 2
    SUBTRACT = 3
    DIVIDE = 4
    SPEED = 5


class GateMotion(enum.Enum):
    STATIC = 1
    PING_PONG = 2
    OSCILLATE = 3


class MultiplierGate:
    """Multiplier gate that transforms mobs passing through its boundary."""

    _next_id: int = 1

    def __init__(
        self,
        x: float,
        y: float,
        width: float = 120.0,
        height: float = 38.0,
        operation: GateOperation = GateOperation.MULTIPLY,
        value: int = 2,
        motion: GateMotion = GateMotion.STATIC,
        motion_speed: float = 70.0,
        min_x: float = 50.0,
        max_x: float = VIRTUAL_WIDTH - 50.0,
        target_team: Optional[Team] = Team.PLAYER,
    ) -> None:
        self.id = MultiplierGate._next_id
        MultiplierGate._next_id += 1
        self.target_team = target_team

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.operation = operation
        self.value = value

        self.motion = motion
        self.motion_speed = motion_speed
        self.min_x = min_x
        self.max_x = max_x
        self.base_x = x
        self.motion_dir = 1.0
        self.motion_time = random.uniform(0.0, math.tau)

        # Pulse animation on mob interaction
        self.pulse: float = 0.0

        # Counter for division gates
        self._divide_counter: int = 0

        # Subtraction pool
        self.remaining_penalty: int = self.value if self.operation == GateOperation.SUBTRACT else 0

        # Fonts
        pygame.font.init()
        self.font = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_op = pygame.font.SysFont("Segoe UI", 16, bold=True)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - (self.width / 2.0)),
            int(self.y - (self.height / 2.0)),
            int(self.width),
            int(self.height),
        )

    def update(self, dt: float) -> None:
        """Update horizontal motion pattern and pulse decay."""
        self.pulse = max(0.0, self.pulse - (dt * 4.0))

        if self.motion == GateMotion.PING_PONG:
            self.x += self.motion_dir * self.motion_speed * dt
            half_w = self.width / 2.0
            if self.x - half_w < self.min_x:
                self.x = self.min_x + half_w
                self.motion_dir = 1.0
            elif self.x + half_w > self.max_x:
                self.x = self.max_x - half_w
                self.motion_dir = -1.0

        elif self.motion == GateMotion.OSCILLATE:
            self.motion_time += dt * (self.motion_speed / 40.0)
            amplitude = (self.max_x - self.min_x) * 0.4
            center = (self.min_x + self.max_x) / 2.0
            self.x = center + (math.sin(self.motion_time) * amplitude)

    def process_mob(self, mob: Mob) -> List[Mob]:
        """Check if mob crosses the gate and generate multiplied clones.

        Returns list of newly spawned cloned mobs.
        """
        if self.target_team is not None and mob.team != self.target_team:
            return []

        if not mob.alive or self.id in mob.passed_gate_ids:
            return []

        # Check overlap
        r = self.rect
        if not r.collidepoint(int(mob.x), int(mob.y)):
            return []

        # Mark mob as processed by this gate
        mob.passed_gate_ids.add(self.id)
        self.pulse = 1.0

        clones: List[Mob] = []

        if self.operation == GateOperation.MULTIPLY:
            # e.g. x3 creates 2 extra clones (total = 3)
            num_clones = max(0, self.value - 1)
            for _ in range(num_clones):
                # Small spread offset behind the original mob
                ox = random.uniform(-self.width * 0.25, self.width * 0.25)
                oy = -mob.dir_y * random.uniform(6.0, 18.0)
                cloned = Mob(
                    x=min(VIRTUAL_WIDTH - 20.0, max(20.0, mob.x + ox)),
                    y=mob.y + oy,
                    team=mob.team,
                    speed=mob.speed,
                    is_champion=mob.is_champion,
                    hp=mob.hp,
                )
                cloned.passed_gate_ids.add(self.id)
                clones.append(cloned)

        elif self.operation == GateOperation.ADD:
            # +N: spawns N extra clones
            for _ in range(self.value):
                ox = random.uniform(-self.width * 0.25, self.width * 0.25)
                oy = -mob.dir_y * random.uniform(6.0, 18.0)
                cloned = Mob(
                    x=min(VIRTUAL_WIDTH - 20.0, max(20.0, mob.x + ox)),
                    y=mob.y + oy,
                    team=mob.team,
                    speed=mob.speed,
                    is_champion=mob.is_champion,
                    hp=mob.hp,
                )
                cloned.passed_gate_ids.add(self.id)
                clones.append(cloned)

        elif self.operation == GateOperation.SUBTRACT:
            if self.remaining_penalty > 0:
                self.remaining_penalty -= 1
                mob.alive = False

        elif self.operation == GateOperation.DIVIDE:
            self._divide_counter += 1
            if self._divide_counter % self.value != 0:
                mob.alive = False

        elif self.operation == GateOperation.SPEED:
            mob.speed *= 1.45

        return clones

    def get_color(self) -> Tuple[int, int, int]:
        if self.operation == GateOperation.MULTIPLY:
            return COLOR_GATE_MULTIPLY
        elif self.operation == GateOperation.ADD:
            return COLOR_GATE_ADD
        elif self.operation == GateOperation.SUBTRACT:
            return COLOR_GATE_SUBTRACT
        elif self.operation == GateOperation.DIVIDE:
            return COLOR_GATE_DIVIDE
        else:
            return COLOR_GATE_SPEED

    def get_label(self) -> str:
        if self.operation == GateOperation.MULTIPLY:
            return f"x{self.value}"
        elif self.operation == GateOperation.ADD:
            return f"+{self.value}"
        elif self.operation == GateOperation.SUBTRACT:
            return f"-{self.remaining_penalty}"
        elif self.operation == GateOperation.DIVIDE:
            return f"/{self.value}"
        else:
            return "SPEED"

    def draw(self, surface: pygame.Surface) -> None:
        """Render glowing holographic gate frame and high contrast text."""
        r = self.rect
        color = self.get_color()

        # 1. Semi-transparent glass fill
        fill_alpha = int(90 + (self.pulse * 100))
        glass_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        glass_surf.fill((*color, fill_alpha))
        surface.blit(glass_surf, r.topleft)

        # 2. Glowing outer frame
        border_thickness = 3 if self.pulse > 0.1 else 2
        pygame.draw.rect(surface, color, r, border_thickness, border_radius=6)

        # 3. Side energy pillars
        pillar_w = 6
        pygame.draw.rect(surface, (255, 255, 255), (r.left, r.top, pillar_w, r.height), border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255), (r.right - pillar_w, r.top, pillar_w, r.height), border_radius=3)

        # 4. Gate Text
        label = self.get_label()
        text_surf = self.font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=r.center)

        # Subtle dark shadow behind text
        shadow = self.font.render(label, True, (15, 20, 30))
        surface.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)
