"""Unit tests for UpgradeSystem attribute scaling and cost calculations."""

import pytest
from py_mob_control.meta.save_manager import SaveManager
from py_mob_control.meta.upgrade_system import UpgradeSystem


def test_upgrade_system_combat_scaling(tmp_path):
    save_file = str(tmp_path / "test_upgrades.json")
    mgr = SaveManager(filepath=save_file)
    mgr.data["coins"] = 1000
    mgr.data["bricks"] = 1000

    upgrades = UpgradeSystem(mgr)

    # Initial level 1
    init_fr = upgrades.get_fire_rate()
    init_ms = upgrades.get_mob_speed()
    init_ch = upgrades.get_champion_hp()

    # Upgrade fire rate
    cost = upgrades.get_fire_rate_cost()
    assert upgrades.upgrade_fire_rate() is True
    assert mgr.data["coins"] == 1000 - cost
    assert upgrades.get_fire_rate() > init_fr

    # Upgrade mob speed
    cost_ms = upgrades.get_mob_speed_cost()
    assert upgrades.upgrade_mob_speed() is True
    assert upgrades.get_mob_speed() > init_ms

    # Upgrade champion
    assert upgrades.upgrade_champion() is True
    assert upgrades.get_champion_hp() > init_ch


def test_upgrade_system_town_bonuses(tmp_path):
    save_file = str(tmp_path / "test_town.json")
    mgr = SaveManager(filepath=save_file)
    mgr.data["bricks"] = 1000

    upgrades = UpgradeSystem(mgr)

    assert upgrades.get_coin_reward_multiplier() == 1.0
    assert upgrades.get_brick_looting_multiplier() == 1.0

    # Upgrade town hall
    assert upgrades.upgrade_town_hall() is True
    assert upgrades.get_coin_reward_multiplier() > 1.0

    # Upgrade brick factory
    assert upgrades.upgrade_brick_factory() is True
    assert upgrades.get_brick_looting_multiplier() > 1.0
