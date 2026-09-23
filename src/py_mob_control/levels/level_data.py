"""Curated tutorial and introductory level configurations (Levels 1 to 5)."""

from dataclasses import dataclass, field
from typing import List, Optional

from py_mob_control.config import VIRTUAL_WIDTH
from py_mob_control.game.entities.gate import MultiplierGate, GateOperation, GateMotion


@dataclass
class LevelConfig:
    level_number: int
    title: str
    base_bricks: int
    base_spawn_rate: float
    has_enemy_cannon: bool = False
    enemy_cannon_fire_rate: float = 2.0
    gates: List[MultiplierGate] = field(default_factory=list)


def create_level_1() -> LevelConfig:
    """Level 1: First Steps - Stationary gates introducing addition and multiplication."""
    gates = [
        MultiplierGate(x=VIRTUAL_WIDTH * 0.35, y=520.0, width=130.0, operation=GateOperation.ADD, value=5),
        MultiplierGate(x=VIRTUAL_WIDTH * 0.70, y=360.0, width=120.0, operation=GateOperation.MULTIPLY, value=2),
    ]
    return LevelConfig(
        level_number=1,
        title="Training Grounds",
        base_bricks=100,
        base_spawn_rate=1.2,
        has_enemy_cannon=False,
        gates=gates,
    )


def create_level_2() -> LevelConfig:
    """Level 2: Moving Advantage - Horizontal ping-pong multiplier gate."""
    gates = [
        MultiplierGate(
            x=VIRTUAL_WIDTH * 0.5,
            y=540.0,
            width=130.0,
            operation=GateOperation.MULTIPLY,
            value=3,
            motion=GateMotion.PING_PONG,
            motion_speed=80.0,
            min_x=90.0,
            max_x=VIRTUAL_WIDTH - 90.0,
        ),
        MultiplierGate(x=VIRTUAL_WIDTH * 0.30, y=340.0, width=110.0, operation=GateOperation.ADD, value=10),
    ]
    return LevelConfig(
        level_number=2,
        title="Moving Horizons",
        base_bricks=150,
        base_spawn_rate=1.8,
        has_enemy_cannon=False,
        gates=gates,
    )


def create_level_3() -> LevelConfig:
    """Level 3: Opposing Fire - Introduces enemy cannon firing red mobs down."""
    gates = [
        MultiplierGate(
            x=VIRTUAL_WIDTH * 0.35,
            y=560.0,
            width=120.0,
            operation=GateOperation.MULTIPLY,
            value=2,
            motion=GateMotion.OSCILLATE,
            motion_speed=65.0,
        ),
        MultiplierGate(
            x=VIRTUAL_WIDTH * 0.65,
            y=400.0,
            width=120.0,
            operation=GateOperation.ADD,
            value=15,
            motion=GateMotion.PING_PONG,
            motion_speed=75.0,
        ),
    ]
    return LevelConfig(
        level_number=3,
        title="Crossfire Lane",
        base_bricks=220,
        base_spawn_rate=2.2,
        has_enemy_cannon=True,
        enemy_cannon_fire_rate=2.5,
        gates=gates,
    )


def create_level_4() -> LevelConfig:
    """Level 4: High Stakes - Speed gate and x4 multiplier alongside a hazard gate."""
    gates = [
        MultiplierGate(x=VIRTUAL_WIDTH * 0.25, y=580.0, width=100.0, operation=GateOperation.SPEED, value=1),
        MultiplierGate(
            x=VIRTUAL_WIDTH * 0.70,
            y=560.0,
            width=110.0,
            operation=GateOperation.MULTIPLY,
            value=4,
            motion=GateMotion.PING_PONG,
            motion_speed=95.0,
        ),
        MultiplierGate(x=VIRTUAL_WIDTH * 0.50, y=380.0, width=130.0, operation=GateOperation.ADD, value=20),
    ]
    return LevelConfig(
        level_number=4,
        title="Speed Corridor",
        base_bricks=300,
        base_spawn_rate=2.8,
        has_enemy_cannon=True,
        enemy_cannon_fire_rate=3.2,
        gates=gates,
    )


def create_level_5() -> LevelConfig:
    """Level 5: Fortress Siege - Big boss base with high brick durability and intense gates."""
    gates = [
        MultiplierGate(
            x=VIRTUAL_WIDTH * 0.5,
            y=600.0,
            width=140.0,
            operation=GateOperation.MULTIPLY,
            value=3,
            motion=GateMotion.PING_PONG,
            motion_speed=110.0,
        ),
        MultiplierGate(
            x=VIRTUAL_WIDTH * 0.3,
            y=440.0,
            width=110.0,
            operation=GateOperation.MULTIPLY,
            value=2,
            motion=GateMotion.OSCILLATE,
            motion_speed=85.0,
        ),
        MultiplierGate(
            x=VIRTUAL_WIDTH * 0.7,
            y=320.0,
            width=120.0,
            operation=GateOperation.ADD,
            value=25,
            motion=GateMotion.PING_PONG,
            motion_speed=100.0,
        ),
    ]
    return LevelConfig(
        level_number=5,
        title="Fortress Siege",
        base_bricks=420,
        base_spawn_rate=3.5,
        has_enemy_cannon=True,
        enemy_cannon_fire_rate=4.0,
        gates=gates,
    )


def get_level_config(level_number: int) -> LevelConfig:
    """Return handcrafted level config for levels 1-5, or procedural for level 6+."""
    if level_number == 1:
        return create_level_1()
    elif level_number == 2:
        return create_level_2()
    elif level_number == 3:
        return create_level_3()
    elif level_number == 4:
        return create_level_4()
    elif level_number == 5:
        return create_level_5()
    else:
        from .level_generator import generate_procedural_level
        return generate_procedural_level(level_number)
