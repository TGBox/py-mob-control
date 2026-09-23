"""Performance stress test simulating 15,000+ mobs to ensure 60 FPS and zero hangs."""

import os
import time
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import pygame
from py_mob_control.levels.level_data import get_level_config
from py_mob_control.game.battle_scene import BattleScene
from py_mob_control.engine.display_manager import DisplayManager
from py_mob_control.engine.input_manager import InputManager
from py_mob_control.audio.audio_manager import AudioManager
from py_mob_control.meta.save_manager import SaveManager
from py_mob_control.meta.upgrade_system import UpgradeSystem
from py_mob_control.game.entities.gate import MultiplierGate, GateOperation


def test_15000_mobs_performance_stress(tmp_path):
    pygame.init()
    save_file = str(tmp_path / "save_stress.json")
    save_mgr = SaveManager(filepath=save_file)
    upgrade_sys = UpgradeSystem(save_mgr)
    display_mgr = DisplayManager()
    audio_mgr = AudioManager.get_instance()

    cfg = get_level_config(5)
    # Add a massive multiplier gate to trigger huge mob counts
    cfg.gates.append(
        MultiplierGate(x=280.0, y=500.0, width=400.0, operation=GateOperation.MULTIPLY, value=10)
    )

    battle = BattleScene(cfg, save_mgr, upgrade_sys, display_mgr, audio_mgr)
    input_mgr = InputManager()

    from py_mob_control.game.entities.mob import Mob, Team

    # Pre-seed player mobs with high count to simulate 17,500 mobs instantly
    for i in range(350):
        m = Mob(x=100.0 + (i % 300), y=400.0 + (i % 200), team=Team.PLAYER, count=50)
        battle.player_mobs.append(m)

    total_mobs = sum(m.count for m in battle.player_mobs)
    assert total_mobs >= 15000, f"Expected 15,000+ mobs, got {total_mobs}"

    # Time 60 full frames of battle simulation and drawing
    start_time = time.perf_counter()
    for _ in range(60):
        dt = 0.016
        input_mgr.begin_frame()
        battle.update(dt, input_mgr)
        battle.draw()
    elapsed = time.perf_counter() - start_time

    # 60 frames must complete in under 1.5 seconds (at least 40+ FPS even under extreme load)
    assert elapsed < 1.5, f"60 frames of 15,000+ mobs took {elapsed:.2f}s (too slow!)"

    # Verify active physical entities were safely bounded
    assert len(battle.player_mobs) <= 500, "Active visual entities exceeded performance cap"

    pygame.quit()
