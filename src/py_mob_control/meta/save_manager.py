"""Persistent JSON savegame manager with atomic writing and corruption protection."""

import json
import os
from typing import Any, Dict


class SaveManager:
    """Handles loading and saving persistent player progression in JSON format."""

    DEFAULT_DATA: Dict[str, Any] = {
        "coins": 250,
        "bricks": 100,
        "current_level": 1,
        "highest_level_beaten": 0,
        "upgrades": {
            "fire_rate_level": 1,
            "mob_speed_level": 1,
            "champion_level": 1,
        },
        "town": {
            "town_hall": 1,
            "brick_factory": 1,
            "barracks": 1,
        },
    }

    def __init__(self, filepath: str = "savegame.json") -> None:
        self.filepath = filepath
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load save data or initialize defaults if missing or corrupted."""
        if not os.path.exists(self.filepath):
            self.data = json.loads(json.dumps(self.DEFAULT_DATA))
            self.save()
            return self.data

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge with default structure to prevent missing key errors
                self.data = json.loads(json.dumps(self.DEFAULT_DATA))
                self._deep_update(self.data, loaded)
        except Exception:
            self.data = json.loads(json.dumps(self.DEFAULT_DATA))
            self.save()

        return self.data

    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        for k, v in updates.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def reset_progress(self) -> None:
        """Reset save data back to initial default state."""
        self.data = json.loads(json.dumps(self.DEFAULT_DATA))
        self.save()

    def save(self) -> None:
        """Atomic write to disk."""
        tmp_path = self.filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            if os.path.exists(self.filepath):
                os.replace(tmp_path, self.filepath)
            else:
                os.rename(tmp_path, self.filepath)
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise e

    def add_coins(self, amount: int) -> int:
        self.data["coins"] = max(0, self.data.get("coins", 0) + amount)
        self.save()
        return self.data["coins"]

    def add_bricks(self, amount: int) -> int:
        self.data["bricks"] = max(0, self.data.get("bricks", 0) + amount)
        self.save()
        return self.data["bricks"]

    def spend_coins(self, amount: int) -> bool:
        if self.data.get("coins", 0) >= amount:
            self.data["coins"] -= amount
            self.save()
            return True
        return False

    def spend_bricks(self, amount: int) -> bool:
        if self.data.get("bricks", 0) >= amount:
            self.data["bricks"] -= amount
            self.save()
            return True
        return False

    def advance_level(self, completed_level: int) -> None:
        self.data["highest_level_beaten"] = max(
            self.data.get("highest_level_beaten", 0), completed_level
        )
        self.data["current_level"] = completed_level + 1
        self.save()
