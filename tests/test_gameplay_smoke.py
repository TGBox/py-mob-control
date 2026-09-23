"""End-to-end headless gameplay smoke test simulating frames across all scenes."""

import os
import pytest

# Force dummy video and audio drivers for headless test
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from py_mob_control.main import GameApp


def test_full_gameplay_headless_cycle(tmp_path):
    save_file = str(tmp_path / "smoke_save.json")
    app = GameApp()
    app.save_mgr.filepath = save_file

    # 1. Simulate frames in Shop State
    for _ in range(5):
        dt = 0.016
        app.input_mgr.begin_frame()
        app.shop_scene.update(dt, app.input_mgr)
        app.shop_scene.draw()

    # 2. Trigger Battle
    app.start_battle()
    assert app.state == app.STATE_BATTLE
    assert app.battle_scene is not None

    # Simulate player holding fire and moving cannon
    app.input_mgr.mouse_left_down = True
    app.input_mgr.mouse_screen_pos = (500, 400)

    for frame in range(40):
        dt = 0.016
        app.input_mgr.begin_frame()
        # Periodically fire champion
        if frame == 20:
            app.battle_scene.player_cannon.ultimate_progress = 1.0
            app.input_mgr.mouse_right_clicked_this_frame = True

        app.battle_scene.update(dt, app.input_mgr)
        app.battle_scene.draw()

    assert len(app.battle_scene.player_mobs) > 0

    # 3. Simulate victory and transition to Loot Scene
    app.battle_scene.enemy_base.bricks = 0
    app.battle_scene.enemy_base.is_destroyed = True
    app.battle_scene.is_victory = True

    # Update to transition
    action = app.battle_scene.update(0.8, app.input_mgr)
    assert action == "LOOT"
    app.start_looting()
    assert app.state == app.STATE_LOOT
    assert app.loot_scene is not None

    # Run loot frames with mouse held down (fast-forward test)
    for _ in range(35):
        dt = 0.03
        app.input_mgr.begin_frame()
        app.input_mgr.mouse_left_down = True
        app.loot_scene.update(dt, app.input_mgr)
        app.loot_scene.draw()

    # Bricks should be rapidly harvested
    assert app.loot_scene.is_speeding_up is True
    assert app.loot_scene.bricks_looted > 0

    # Finish looting and return to shop
    app.loot_scene.looting_finished = True
    app.loot_scene.phase_time = 2.0
    app.input_mgr.mouse_left_down = False
    app.input_mgr.mouse_clicked_this_frame = True
    action = app.loot_scene.update(0.1, app.input_mgr)
    assert action == "SHOP"

    # Clean shutdown
    pygame.quit()
