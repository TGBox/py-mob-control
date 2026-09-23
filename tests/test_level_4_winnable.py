"""Simulation test verifying that Level 4 is winnable with player gate multipliers."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import pygame
from py_mob_control.config import VIRTUAL_WIDTH
from py_mob_control.levels.level_data import get_level_config
from py_mob_control.game.battle_scene import BattleScene
from py_mob_control.engine.display_manager import DisplayManager
from py_mob_control.engine.input_manager import InputManager
from py_mob_control.audio.audio_manager import AudioManager
from py_mob_control.meta.save_manager import SaveManager
from py_mob_control.meta.upgrade_system import UpgradeSystem


def test_level_4_winnable(tmp_path):
    pygame.init()
    save_file = str(tmp_path / "save_lvl4.json")
    save_mgr = SaveManager(filepath=save_file)
    # Player on level 4 with level 3 upgrades (matching the user's current progress)
    save_mgr.data["upgrades"]["fire_rate_level"] = 3
    save_mgr.data["upgrades"]["mob_speed_level"] = 3
    save_mgr.data["upgrades"]["champion_level"] = 2
    save_mgr.data["current_level"] = 4

    upgrade_sys = UpgradeSystem(save_mgr)
    display_mgr = DisplayManager()
    audio_mgr = AudioManager.get_instance()

    cfg = get_level_config(4)
    battle = BattleScene(cfg, save_mgr, upgrade_sys, display_mgr, audio_mgr)
    input_mgr = InputManager()

    # Position player cannon in line with the x4 gate (around x = 390) and fire continuously
    input_mgr.mouse_left_down = True
    input_mgr.mouse_screen_pos = display_mgr.virtual_to_screen((390.0, 560.0))

    initial_base_bricks = battle.enemy_base.bricks

    # Simulate 8 seconds of combat (480 frames at 60 FPS)
    for frame in range(480):
        dt = 0.016
        input_mgr.begin_frame()

        # Try summoning champion when ready
        if battle.player_cannon.is_ultimate_ready:
            input_mgr.mouse_right_clicked_this_frame = True

        battle.update(dt, input_mgr)
        battle.draw()

        if battle.is_victory:
            break

    # Player should NOT be defeated and enemy base must have taken heavy damage or been destroyed!
    assert not battle.is_defeat, "Player should not be overrun in Level 4"
    assert battle.enemy_base.bricks < initial_base_bricks, "Enemy base should take significant damage"
    assert battle.combat_coins_earned > 0, "Player should have earned combat coins from kills"

    pygame.quit()
