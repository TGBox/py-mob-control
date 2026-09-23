"""Procedural level generator for infinite scaling beyond Level 5."""

import random
from typing import List

from py_mob_control.config import VIRTUAL_WIDTH
from py_mob_control.game.entities.gate import MultiplierGate, GateOperation, GateMotion
from .level_data import LevelConfig


def generate_procedural_level(level_number: int) -> LevelConfig:
    """Procedurally generate balanced level configurations based on level index."""
    rng = random.Random(level_number * 1337 + 42)

    # Bricks scale with level
    bricks = 350 + (level_number - 5) * 65
    spawn_rate = min(6.5, 3.0 + (level_number - 5) * 0.3)
    enemy_cannon_rate = min(5.0, 2.5 + (level_number - 5) * 0.25)

    # Number of gates: 2 to 4
    num_gates = min(4, 2 + (level_number % 3))

    # Vertical bands for gates
    y_bands = [
        600.0 - (i * 120.0) for i in range(num_gates)
    ]

    gates: List[MultiplierGate] = []
    operations = [
        (GateOperation.MULTIPLY, 2),
        (GateOperation.MULTIPLY, 3),
        (GateOperation.MULTIPLY, 4),
        (GateOperation.ADD, 15),
        (GateOperation.ADD, 25),
        (GateOperation.ADD, 40),
        (GateOperation.SPEED, 1),
    ]

    for i, y_pos in enumerate(y_bands):
        op, val = rng.choice(operations)
        width = rng.uniform(105.0, 135.0)
        x_pos = rng.uniform(width / 2.0 + 30.0, VIRTUAL_WIDTH - width / 2.0 - 30.0)

        motion = rng.choice([GateMotion.STATIC, GateMotion.PING_PONG, GateMotion.OSCILLATE])
        speed = rng.uniform(70.0, 120.0 + min(60.0, level_number * 3.0))

        gate = MultiplierGate(
            x=x_pos,
            y=y_pos,
            width=width,
            operation=op,
            value=val,
            motion=motion,
            motion_speed=speed,
            min_x=60.0,
            max_x=VIRTUAL_WIDTH - 60.0,
        )
        gates.append(gate)

    return LevelConfig(
        level_number=level_number,
        title=f"Sector {level_number}",
        base_bricks=bricks,
        base_spawn_rate=spawn_rate,
        has_enemy_cannon=True,
        enemy_cannon_fire_rate=enemy_cannon_rate,
        gates=gates,
    )
