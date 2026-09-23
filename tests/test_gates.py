"""Unit tests for MultiplierGate logic and arithmetic transformations."""

import pytest
from py_mob_control.game.entities.mob import Mob, Team
from py_mob_control.game.entities.gate import MultiplierGate, GateOperation, GateMotion


def test_gate_multiply():
    gate = MultiplierGate(x=100.0, y=100.0, width=80.0, height=40.0, operation=GateOperation.MULTIPLY, value=3)
    mob = Mob(x=100.0, y=100.0, team=Team.PLAYER, speed=200.0)

    clones = gate.process_mob(mob)
    # x3 gate creates 2 clones (total 3 mobs: 1 original + 2 clones)
    assert len(clones) == 2
    assert gate.id in mob.passed_gate_ids
    for c in clones:
        assert gate.id in c.passed_gate_ids
        assert c.team == Team.PLAYER


def test_gate_add():
    gate = MultiplierGate(x=100.0, y=100.0, width=80.0, height=40.0, operation=GateOperation.ADD, value=5)
    mob = Mob(x=100.0, y=100.0, team=Team.PLAYER, speed=200.0)

    clones = gate.process_mob(mob)
    assert len(clones) == 5


def test_gate_duplicate_prevention():
    gate = MultiplierGate(x=100.0, y=100.0, width=80.0, height=40.0, operation=GateOperation.MULTIPLY, value=2)
    mob = Mob(x=100.0, y=100.0, team=Team.PLAYER)

    clones_first = gate.process_mob(mob)
    assert len(clones_first) == 1

    # Second pass should not trigger multiplication again
    clones_second = gate.process_mob(mob)
    assert len(clones_second) == 0


def test_gate_speed_boost():
    gate = MultiplierGate(x=100.0, y=100.0, width=80.0, height=40.0, operation=GateOperation.SPEED, value=1)
    base_speed = 200.0
    mob = Mob(x=100.0, y=100.0, team=Team.PLAYER, speed=base_speed)

    clones = gate.process_mob(mob)
    assert len(clones) == 0
    assert mob.speed > base_speed


def test_gate_subtract():
    gate = MultiplierGate(x=100.0, y=100.0, width=80.0, height=40.0, operation=GateOperation.SUBTRACT, value=2)
    mob1 = Mob(x=100.0, y=100.0, team=Team.PLAYER)
    mob2 = Mob(x=100.0, y=100.0, team=Team.PLAYER)

    gate.process_mob(mob1)
    assert not mob1.alive
    assert gate.remaining_penalty == 1

    gate.process_mob(mob2)
    assert not mob2.alive
    assert gate.remaining_penalty == 0


def test_gate_ignores_enemy_mobs():
    gate = MultiplierGate(x=100.0, y=100.0, width=80.0, height=40.0, operation=GateOperation.MULTIPLY, value=4)
    enemy_mob = Mob(x=100.0, y=100.0, team=Team.ENEMY, speed=200.0)

    clones = gate.process_mob(enemy_mob)
    assert len(clones) == 0
    assert gate.id not in enemy_mob.passed_gate_ids
    assert enemy_mob.alive is True

