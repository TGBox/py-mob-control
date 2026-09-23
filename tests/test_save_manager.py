"""Unit tests for SaveManager JSON persistence."""

import os
import pytest
from py_mob_control.meta.save_manager import SaveManager


def test_save_manager_lifecycle(tmp_path):
    save_file = str(tmp_path / "test_save.json")
    mgr = SaveManager(filepath=save_file)

    # Initial defaults
    assert mgr.data["coins"] == 250
    assert mgr.data["bricks"] == 100
    assert mgr.data["current_level"] == 1

    # Add currency
    mgr.add_coins(150)
    mgr.add_bricks(50)
    assert mgr.data["coins"] == 400
    assert mgr.data["bricks"] == 150

    # Spend currency
    assert mgr.spend_coins(200) is True
    assert mgr.data["coins"] == 200
    assert mgr.spend_coins(9999) is False
    assert mgr.data["coins"] == 200

    # Advance level
    mgr.advance_level(1)
    assert mgr.data["current_level"] == 2
    assert mgr.data["highest_level_beaten"] == 1

    # Reload from disk
    mgr2 = SaveManager(filepath=save_file)
    assert mgr2.data["coins"] == 200
    assert mgr2.data["bricks"] == 150
    assert mgr2.data["current_level"] == 2
    assert mgr2.data["highest_level_beaten"] == 1

    # Reset progress
    mgr2.reset_progress()
    assert mgr2.data["coins"] == 250
    assert mgr2.data["bricks"] == 100
    assert mgr2.data["current_level"] == 1
    assert mgr2.data["highest_level_beaten"] == 0

