"""Unit tests for curated and procedural level configurations."""

import pytest
from py_mob_control.levels.level_data import get_level_config
from py_mob_control.levels.level_generator import generate_procedural_level


def test_curated_levels_1_to_5():
    for lvl in range(1, 6):
        cfg = get_level_config(lvl)
        assert cfg.level_number == lvl
        assert cfg.base_bricks > 0
        assert cfg.base_spawn_rate > 0
        assert len(cfg.gates) >= 2


def test_procedural_generation():
    cfg6 = get_level_config(6)
    assert cfg6.level_number == 6
    assert cfg6.base_bricks > 300
    assert len(cfg6.gates) >= 2

    cfg10 = get_level_config(10)
    assert cfg10.level_number == 10
    assert cfg10.base_bricks > cfg6.base_bricks
    assert cfg10.base_spawn_rate >= cfg6.base_spawn_rate
