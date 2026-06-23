"""
level.py
========

Loads a level from JSON and owns all of its world content: the static tile grid,
interactive blocks, moving platforms, enemies, coins, checkpoints and the goal
flag. It is also the authority on collision: entities ask it for the solid and
one-way surfaces near a rectangle.

Level format (see ``levels/*.json``)
------------------------------------
A level is an ASCII map plus a little metadata::

    {
      "name": "Green Hills",
      "theme": "day",
      "music": "level1",
      "time_limit": 300,
      "map": ["  ?  ", "XXXXX"],
      "moving_platforms": [{"col": 10, "row": 8, "axis": "h", "span": 4}]
    }

Each character in ``map`` is looked up in :data:`src.world.tiles.TILE_LEGEND`.
This keeps levels human-readable and editable in any text editor, while the
``moving_platforms`` list carries the few objects that need parameters.
"""

from __future__ import annotations

import json
from typing import List, Optional, Tuple

import pygame

import config
from src.entities.coin import Coin
from src.entities.enemies import Flyer, Goomba, Koopa
from src.entities.powerup import PowerUp
from src.world import tiles
from src.world.parallax import ParallaxBackground

T = config.TILE_SIZE


class Level:
    def __init__(self, data: dict, assets, audio, particles):
        self.assets = assets
        self.audio = audio
        self.particles = particles

        self.name = data.get("name", "Level")
        self.theme = data.get("theme", "day")
        self.music = data.get("music", "level1")
        self.time_limit = data.get("time_limit", config.DEFAULT_TIME_LIMIT)

        rows = data["map"]
        self.row_count = len(rows)
        self.col_count = max(len(r) for r in rows)
        self.pixel_width = self.col_count * T
        self.pixel_height = self.row_count * T

        # Static tile grid: grid[row][col] -> tile-def key or None.
        self.grid: List[List[Optional[str]]] = [
            [None] * self.col_count for _ in range(self.row_count)
        ]
        self.blocks: List[tiles.InteractiveBlock] = []
        self.block_map = {}                     # (col, row) -> block
        self.coins: List[Coin] = []
        self.enemies: list = []
        self.powerups: List[PowerUp] = []       # dynamically spawned items
        self.checkpoints: List[tiles.Checkpoint] = []
        self.goal: Optional[tiles.Goal] = None
        self.player_start: Tuple[int, int] = (2, self.row_count - 3)

        self._parse_map(rows)

        for mp in data.get("moving_platforms", []):
            self.blocks_platform(mp)
        self.moving_platforms = getattr(self, "moving_platforms", [])

        self.background = ParallaxBackground(assets, self.pixel_width, self.theme)

    # ----------------------------------------------------------- factory
    @classmethod
    def from_file(cls, path: str, assets, audio, particles) -> "Level":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(data, assets, audio, particles)

    # ----------------------------------------------------------- parsing
    def blocks_platform(self, mp: dict):
        if not hasattr(self, "moving_platforms"):
            self.moving_platforms = []
        self.moving_platforms.append(tiles.MovingPlatform(
            mp["col"], mp["row"], mp.get("axis", "h"),
            mp.get("span", 3), mp.get("speed", 1.5)))

    def _spawn_enemy(self, kind: str, col: int, row: int):
        cls_map = {"goomba": Goomba, "koopa": Koopa, "flyer": Flyer}
        enemy = cls_map[kind](col * T, row * T, self.assets, self.audio, self.particles)
        # Align feet to the bottom of the marker cell.
        enemy.rect.bottom = (row + 1) * T
        enemy.rect.centerx = col * T + T // 2
        enemy.pos.update(enemy.rect.x, enemy.rect.y)
        if isinstance(enemy, Flyer):
            enemy.base_y = float(enemy.rect.y)
            enemy.start_x = float(enemy.rect.x)
        self.enemies.append(enemy)

    def _parse_map(self, rows: List[str]):
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch == " ":
                    continue
                kind, param = tiles.TILE_LEGEND.get(ch, (None, None))
                if kind == "static":
                    self.grid[r][c] = param
                elif kind == "brick":
                    self._add_block(tiles.BrickBlock(c, r))
                elif kind == "brick_coins":
                    self._add_block(tiles.BrickBlock(c, r, coins=param))
                elif kind == "question":
                    self._add_block(tiles.QuestionBlock(c, r, content=param))
                elif kind == "coin":
                    self.coins.append(Coin(c, r, self.assets))
                elif kind == "enemy":
                    self._spawn_enemy(param, c, r)
                elif kind == "checkpoint":
                    self.checkpoints.append(tiles.Checkpoint(c, r))
                elif kind == "goal":
                    self.goal = tiles.Goal(c, r)
                elif kind == "player_start":
                    self.player_start = (c, r)

    def _add_block(self, block):
        self.blocks.append(block)
        self.block_map[(block.col, block.row)] = block

    # --------------------------------------------------------- collision
    def is_solid_pixel(self, x: float, y: float) -> bool:
        """Used by enemy ledge detection: is there ground at this pixel?"""
        col, row = int(x // T), int(y // T)
        if 0 <= row < self.row_count and 0 <= col < self.col_count:
            if self.grid[row][col] is not None:
                return True
            block = self.block_map.get((col, row))
            if block and block.active and block.solid:
                return True
        for mp in self.moving_platforms:
            if mp.rect.collidepoint(x, y):
                return True
        return False

    def collision_sources(self, rect: pygame.Rect):
        """Return (solids, one_ways) rectangles near ``rect``.

        ``solids`` block movement on every side. ``one_ways`` is a list of
        ``(rect, mover)`` tuples blocking only a downward landing; ``mover`` is
        the owning :class:`MovingPlatform` (or ``None``) so riders can be
        carried along.
        """
        solids = []
        one_ways = []
        c0 = max(0, rect.left // T - 1)
        c1 = min(self.col_count - 1, rect.right // T + 1)
        r0 = max(0, rect.top // T - 1)
        r1 = min(self.row_count - 1, rect.bottom // T + 1)
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                key = self.grid[row][col]
                if key is not None:
                    _, solid, one_way = tiles.TILE_DEFS[key]
                    tile_rect = pygame.Rect(col * T, row * T, T, T)
                    if one_way:
                        one_ways.append((tile_rect, None))
                    elif solid:
                        solids.append(tile_rect)
                block = self.block_map.get((col, row))
                if block and block.active and block.solid:
                    solids.append(pygame.Rect(col * T, row * T, T, T))
        # Moving platforms act as one-way carriers.
        for mp in self.moving_platforms:
            if mp.rect.right >= rect.left - T and mp.rect.left <= rect.right + T:
                one_ways.append((mp.rect, mp))
        return solids, one_ways

    def block_at(self, col: int, row: int):
        return self.block_map.get((col, row))

    def spawn_powerup(self, kind: str, col: int, row: int):
        x = col * T + (T - 36) // 2
        y = row * T
        self.powerups.append(PowerUp(x, y, kind, self.assets, self.audio, self.particles))

    # ------------------------------------------------------------ update
    def update(self, dt: float):
        for block in self.blocks:
            block.update(dt)
        for mp in self.moving_platforms:
            mp.update(dt)
        for coin in self.coins:
            coin.update(dt)
        if self.goal:
            self.goal.update(dt)

    # -------------------------------------------------------------- draw
    def draw_background(self, surface, camera):
        self.background.draw(surface, camera)

    def draw_world(self, surface, camera):
        """Draw static tiles in view plus all world objects."""
        o = camera.total_offset
        c0 = max(0, int(o.x // T))
        c1 = min(self.col_count - 1, int((o.x + config.RENDER_WIDTH) // T) + 1)
        r0 = max(0, int(o.y // T))
        r1 = min(self.row_count - 1, int((o.y + config.RENDER_HEIGHT) // T) + 1)
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                key = self.grid[row][col]
                if key is not None:
                    img = self.assets.tiles[tiles.TILE_DEFS[key][0]]
                    surface.blit(img, camera.apply(pygame.Rect(col * T, row * T, T, T)))

        for mp in self.moving_platforms:
            mp.draw(surface, camera, self.assets)
        for block in self.blocks:
            block.draw(surface, camera, self.assets)
        for cp in self.checkpoints:
            cp.draw(surface, camera, self.assets)
        if self.goal:
            self.goal.draw(surface, camera, self.assets)
        for coin in self.coins:
            coin.draw(surface, camera)
