"""High-performance 2D particle system for juice, impacts, sparks, brick fragments and confetti."""

import math
import random
from typing import List, Tuple
import pygame


class Particle:
    """Individual particle instance."""
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "drag", "gravity", "shape")

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        life: float,
        color: Tuple[int, int, int],
        size: float = 3.0,
        drag: float = 0.94,
        gravity: float = 0.0,
        shape: str = "circle",
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.drag = drag
        self.gravity = gravity
        self.shape = shape


class FlyingBrick:
    """Special particle representing a brick flying toward the currency counter in an arc."""
    __slots__ = ("start_x", "start_y", "target_x", "target_y", "progress", "speed", "curve_height", "color", "arrived")

    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], color: Tuple[int, int, int] = (255, 180, 40)) -> None:
        self.start_x, self.start_y = start_pos
        self.target_x, self.target_y = target_pos
        self.progress = 0.0
        self.speed = random.uniform(1.8, 2.5)
        self.curve_height = random.uniform(-120.0, -50.0)
        self.color = color
        self.arrived = False

    def update(self, dt: float) -> bool:
        self.progress += self.speed * dt
        if self.progress >= 1.0:
            self.progress = 1.0
            self.arrived = True
            return True
        return False

    def get_pos(self) -> Tuple[float, float]:
        t = self.progress
        curr_x = (1.0 - t) * self.start_x + t * self.target_x
        # Parabolic arc
        linear_y = (1.0 - t) * self.start_y + t * self.target_y
        arc = 4.0 * self.curve_height * t * (1.0 - t)
        return curr_x, linear_y + arc


class ParticleSystem:
    """Manages active particles and flying brick animations."""

    def __init__(self) -> None:
        self.particles: List[Particle] = []
        self.flying_bricks: List[FlyingBrick] = []

    def emit_mob_pop(self, x: float, y: float, color: Tuple[int, int, int], count: int = 6) -> None:
        """Splash of small droplets when a mob dies."""
        for _ in range(count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(30.0, 110.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.18, 0.35)
            self.particles.append(Particle(x, y, vx, vy, life, color, size=random.uniform(2.5, 4.0)))

    def emit_sparks(self, x: float, y: float, count: int = 10, color: Tuple[int, int, int] = (255, 230, 100)) -> None:
        """Bright sparks on gate passage or metal impact."""
        for _ in range(count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(60.0, 180.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.15, 0.3)
            self.particles.append(Particle(x, y, vx, vy, life, color, size=2.5, drag=0.91))

    def emit_brick_fragments(self, x: float, y: float, count: int = 12) -> None:
        """Debris when enemy tower/base takes damage."""
        colors = [(240, 140, 40), (210, 110, 30), (255, 200, 70), (160, 80, 20)]
        for _ in range(count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(50.0, 160.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 40.0
            life = random.uniform(0.3, 0.6)
            c = random.choice(colors)
            self.particles.append(
                Particle(x, y, vx, vy, life, c, size=random.uniform(3.0, 6.0), drag=0.92, gravity=180.0, shape="rect")
            )

    def emit_confetti(self, x: float, y: float, count: int = 40) -> None:
        """Celebratory victory confetti."""
        confetti_colors = [
            (255, 60, 90), (40, 200, 255), (255, 220, 40),
            (70, 240, 120), (200, 80, 255), (255, 140, 30)
        ]
        for _ in range(count):
            angle = random.uniform(-math.pi * 0.8, -math.pi * 0.2)
            speed = random.uniform(140.0, 320.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(1.0, 2.0)
            c = random.choice(confetti_colors)
            self.particles.append(
                Particle(x, y, vx, vy, life, c, size=random.uniform(4.0, 7.0), drag=0.96, gravity=120.0, shape="rect")
            )

    def spawn_flying_brick(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float]) -> None:
        """Launch an animated brick flying toward the currency bank."""
        self.flying_bricks.append(FlyingBrick(start_pos, target_pos))

    def update(self, dt: float) -> int:
        """Update all active particles. Returns count of bricks that arrived at the target this frame."""
        arrived_bricks = 0

        # Update flying bricks
        alive_bricks: List[FlyingBrick] = []
        for fb in self.flying_bricks:
            if fb.update(dt):
                arrived_bricks += 1
            else:
                alive_bricks.append(fb)
        self.flying_bricks = alive_bricks

        # Update regular particles
        alive_particles: List[Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vx *= p.drag
            p.vy *= p.drag
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive_particles.append(p)
        self.particles = alive_particles

        return arrived_bricks

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all active particles onto surface."""
        for p in self.particles:
            alpha_ratio = max(0.0, p.life / p.max_life)
            current_size = max(1.0, p.size * alpha_ratio)
            if p.shape == "rect":
                rect = pygame.Rect(p.x - current_size, p.y - current_size, current_size * 2, current_size * 2)
                pygame.draw.rect(surface, p.color, rect)
            else:
                pygame.draw.circle(surface, p.color, (int(p.x), int(p.y)), int(current_size))

        # Draw flying bricks with glowing outline
        for fb in self.flying_bricks:
            bx, by = fb.get_pos()
            rect = pygame.Rect(int(bx) - 5, int(by) - 4, 10, 8)
            pygame.draw.rect(surface, fb.color, rect, border_radius=2)
            pygame.draw.rect(surface, (255, 240, 160), rect, 1, border_radius=2)
