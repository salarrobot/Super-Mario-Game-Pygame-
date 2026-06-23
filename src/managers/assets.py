"""
assets.py
=========

The :class:`AssetManager` is the single gateway every other system uses to get
images and fonts. Building it once at startup means:

* art is generated/loaded a single time (no per-frame surface creation),
* surfaces are ``convert_alpha``-ed once for fast blitting,
* and the rest of the code never touches the :mod:`art` module directly.

Although our art is procedural, the manager is written so swapping in real PNG
sprite sheets later would only require changing the ``_build`` methods.
"""

from __future__ import annotations

from typing import Dict, List

import pygame

from src.graphics import art


class AssetManager:
    def __init__(self):
        # Everything below is populated by build(). We keep them as plain dicts
        # so call-sites read naturally, e.g. assets.tiles["brick"].
        self.players: Dict[str, Dict[str, List[pygame.Surface]]] = {}
        self.enemies: Dict[str, Dict[str, List[pygame.Surface]]] = {}
        self.tiles: Dict[str, pygame.Surface] = {}
        self.question: Dict[str, List[pygame.Surface]] = {}
        self.coin_frames: List[pygame.Surface] = []
        self.powerups: Dict[str, object] = {}
        self.fireball_frames: List[pygame.Surface] = []
        self.flag: Dict[str, pygame.Surface] = {}
        self.checkpoint_frames: List[pygame.Surface] = []
        self.scenery: Dict[str, pygame.Surface] = {}
        self.icons: Dict[str, pygame.Surface] = {}
        self._fonts: Dict[int, pygame.font.Font] = {}
        self._built = False

    # ------------------------------------------------------------------ build
    def build(self) -> None:
        """Generate every sprite. Must be called after the display is set up
        so that ``convert_alpha`` has a pixel format to convert to."""
        if self._built:
            return

        self.players = art.make_all_player_frames()
        self.enemies = {
            "goomba": art.make_goomba_frames(),
            "koopa": art.make_koopa_frames(),
            "flyer": art.make_flyer_frames(),
        }
        self.tiles = {
            "ground": art.make_ground_tile(grass_top=True),
            "dirt": art.make_ground_tile(grass_top=False),
            "brick": art.make_brick_tile(),
            "platform": art.make_platform_tile(metal=False),
            "metal": art.make_platform_tile(metal=True),
        }
        pipes = art.make_pipe_tiles()
        self.tiles["pipe_top"] = pipes["top"]
        self.tiles["pipe_body"] = pipes["body"]

        self.question = art.make_question_frames()
        self.coin_frames = art.make_coin_frames()
        self.powerups = {
            "mushroom": art.make_mushroom(),
            "fire_flower": art.make_fire_flower_frames(),
            "star": art.make_star_frames(),
        }
        self.fireball_frames = art.make_fireball_frames()
        self.flag = art.make_flag()
        self.checkpoint_frames = art.make_checkpoint_frames()
        self.scenery = {
            "cloud": art.make_cloud(),
            "hill_far": art.make_hill(near=False),
            "hill_near": art.make_hill(near=True),
            "bush": art.make_bush(),
            "mountain": art.make_mountain(),
        }
        self.icons = {
            "heart": art.make_heart(True),
            "heart_empty": art.make_heart(False),
            "coin": art.make_coin_icon(),
        }

        # Convert everything for fast per-pixel-alpha blitting.
        self._convert_all()
        self._built = True

    def _convert_all(self) -> None:
        def conv(s):
            return s.convert_alpha()

        for variant in self.players.values():
            for key, frames in variant.items():
                variant[key] = [conv(f) for f in frames]
        for enemy in self.enemies.values():
            for key, frames in enemy.items():
                enemy[key] = [conv(f) for f in frames]
        self.tiles = {k: conv(v) for k, v in self.tiles.items()}
        self.question = {k: [conv(f) for f in v] for k, v in self.question.items()}
        self.coin_frames = [conv(f) for f in self.coin_frames]
        self.powerups["mushroom"] = conv(self.powerups["mushroom"])
        self.powerups["fire_flower"] = [conv(f) for f in self.powerups["fire_flower"]]
        self.powerups["star"] = [conv(f) for f in self.powerups["star"]]
        self.fireball_frames = [conv(f) for f in self.fireball_frames]
        self.flag = {k: conv(v) for k, v in self.flag.items()}
        self.checkpoint_frames = [conv(f) for f in self.checkpoint_frames]
        self.scenery = {k: conv(v) for k, v in self.scenery.items()}
        self.icons = {k: conv(v) for k, v in self.icons.items()}

    # ------------------------------------------------------------------ fonts
    def get_font(self, size: int, bold: bool = True) -> pygame.font.Font:
        """Cached font lookup. We prefer a chunky built-in font for the retro
        feel and fall back to the default font if it is unavailable."""
        key = size * 2 + (1 if bold else 0)
        if key not in self._fonts:
            try:
                font = pygame.font.SysFont("consolas,couriernew,monospace", size, bold=bold)
            except Exception:
                font = pygame.font.Font(None, size)
            self._fonts[key] = font
        return self._fonts[key]
