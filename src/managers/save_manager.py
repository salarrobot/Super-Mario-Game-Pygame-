"""
save_manager.py
===============

Persistence for two separate concerns:

* :class:`Settings` — user preferences (volumes, fullscreen, FPS counter and
  remappable controls), stored in ``settings.json``.
* :class:`SaveManager` — game progress (unlocked levels, high score, best
  per-level times), stored in ``savegame.json``.

Both are deliberately tiny JSON wrappers with defensive loading: a corrupt or
missing file simply falls back to sensible defaults instead of crashing.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Dict

import pygame

import config


class Settings:
    def __init__(self, path: str = config.SETTINGS_PATH):
        self.path = path
        self.data: Dict = copy.deepcopy(config.DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    loaded = json.load(fh)
                # Merge so newly-added default keys survive old save files.
                self.data.update({k: v for k, v in loaded.items() if k in self.data})
                if "controls" in loaded:
                    self.data["controls"] = {**config.DEFAULT_CONTROLS, **loaded["controls"]}
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2)
        except OSError:
            pass

    # Convenience accessors -------------------------------------------------
    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def key_code(self, action: str) -> int:
        """Resolve a control action ("jump") to a pygame key constant."""
        name = self.data["controls"].get(action, config.DEFAULT_CONTROLS.get(action, "space"))
        try:
            return pygame.key.key_code(name)
        except Exception:
            return pygame.key.key_code(config.DEFAULT_CONTROLS.get(action, "space"))

    def set_control(self, action: str, key_name: str) -> None:
        self.data["controls"][action] = key_name
        self.save()


class SaveManager:
    """Tracks long-term progress across play sessions."""

    DEFAULT = {
        "unlocked_level": 1,    # highest level the player may select
        "high_score": 0,
        "best_times": {},       # {"1": 142.3, ...} seconds
        "total_coins": 0,
    }

    def __init__(self, path: str = config.SAVE_PATH):
        self.path = path
        self.data: Dict = copy.deepcopy(self.DEFAULT)
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    loaded = json.load(fh)
                self.data.update({k: loaded.get(k, v) for k, v in self.DEFAULT.items()})
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2)
        except OSError:
            pass

    # --- progress updates --------------------------------------------------
    def unlock_level(self, level_number: int) -> None:
        if level_number > self.data["unlocked_level"]:
            self.data["unlocked_level"] = level_number
            self.save()

    def record_score(self, score: int) -> bool:
        """Return True if a new high score was set."""
        if score > self.data["high_score"]:
            self.data["high_score"] = score
            self.save()
            return True
        return False

    def record_time(self, level_number: int, time_taken: float) -> None:
        key = str(level_number)
        best = self.data["best_times"].get(key)
        if best is None or time_taken < best:
            self.data["best_times"][key] = round(time_taken, 2)
            self.save()

    def add_coins(self, n: int) -> None:
        self.data["total_coins"] += n
        self.save()

    def reset(self) -> None:
        self.data = copy.deepcopy(self.DEFAULT)
        self.save()
