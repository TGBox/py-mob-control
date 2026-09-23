"""Upgrade system computing attribute scaling, costs, and gameplay modifiers."""

import math
from typing import Dict, Any
from .save_manager import SaveManager


class UpgradeSystem:
    """Manages player upgrades and stats scaling."""

    def __init__(self, save_mgr: SaveManager) -> None:
        self.save_mgr = save_mgr

    # --- Player Combat Stats ---

    def get_fire_rate(self) -> float:
        lvl = self.save_mgr.data["upgrades"].get("fire_rate_level", 1)
        # Base 6.0 mobs/sec, +1.2 per level
        return 6.0 + (lvl - 1) * 1.2

    def get_fire_rate_cost(self) -> int:
        lvl = self.save_mgr.data["upgrades"].get("fire_rate_level", 1)
        return int(100 * math.pow(1.38, lvl - 1))

    def upgrade_fire_rate(self) -> bool:
        cost = self.get_fire_rate_cost()
        if self.save_mgr.spend_coins(cost):
            self.save_mgr.data["upgrades"]["fire_rate_level"] += 1
            self.save_mgr.save()
            return True
        return False

    def get_mob_speed(self) -> float:
        lvl = self.save_mgr.data["upgrades"].get("mob_speed_level", 1)
        # Base 230.0, +16.0 per level
        return 230.0 + (lvl - 1) * 16.0

    def get_mob_speed_cost(self) -> int:
        lvl = self.save_mgr.data["upgrades"].get("mob_speed_level", 1)
        return int(80 * math.pow(1.32, lvl - 1))

    def upgrade_mob_speed(self) -> bool:
        cost = self.get_mob_speed_cost()
        if self.save_mgr.spend_coins(cost):
            self.save_mgr.data["upgrades"]["mob_speed_level"] += 1
            self.save_mgr.save()
            return True
        return False

    def get_champion_hp(self) -> int:
        lvl = self.save_mgr.data["upgrades"].get("champion_level", 1)
        # Base 40 HP, +15 per level
        return 40 + (lvl - 1) * 15

    def get_champion_cost(self) -> int:
        lvl = self.save_mgr.data["upgrades"].get("champion_level", 1)
        return int(150 * math.pow(1.42, lvl - 1))

    def upgrade_champion(self) -> bool:
        cost = self.get_champion_cost()
        if self.save_mgr.spend_coins(cost):
            self.save_mgr.data["upgrades"]["champion_level"] += 1
            self.save_mgr.save()
            return True
        return False

    # --- Town Base Building (Brick Investment) ---

    def get_town_hall_level(self) -> int:
        return self.save_mgr.data["town"].get("town_hall", 1)

    def get_town_hall_cost(self) -> int:
        lvl = self.get_town_hall_level()
        return int(60 * math.pow(1.45, lvl - 1))

    def upgrade_town_hall(self) -> bool:
        cost = self.get_town_hall_cost()
        if self.save_mgr.spend_bricks(cost):
            self.save_mgr.data["town"]["town_hall"] += 1
            self.save_mgr.save()
            return True
        return False

    def get_brick_factory_level(self) -> int:
        return self.save_mgr.data["town"].get("brick_factory", 1)

    def get_brick_factory_cost(self) -> int:
        lvl = self.get_brick_factory_level()
        return int(80 * math.pow(1.45, lvl - 1))

    def upgrade_brick_factory(self) -> bool:
        cost = self.get_brick_factory_cost()
        if self.save_mgr.spend_bricks(cost):
            self.save_mgr.data["town"]["brick_factory"] += 1
            self.save_mgr.save()
            return True
        return False

    def get_coin_reward_multiplier(self) -> float:
        """Bonus coins from Town Hall investment (+15% per level beyond 1)."""
        th_lvl = self.get_town_hall_level()
        return 1.0 + (th_lvl - 1) * 0.15

    def get_brick_looting_multiplier(self) -> float:
        """Bonus bricks looted from Brick Factory (+20% per level beyond 1)."""
        fac_lvl = self.get_brick_factory_level()
        return 1.0 + (fac_lvl - 1) * 0.20
