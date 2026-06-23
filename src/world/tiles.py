"""
tiles.py
========

Definitions for the world's building blocks.

* Static, non-interactive tiles (ground, dirt, pipes, one-way platforms) live in
  the level's grid as simple type codes and are drawn/collided in bulk by the
  :class:`Level`. They never change, so representing them as objects would waste
  memory and time.
* Interactive tiles (bricks you can smash, ``?`` blocks that pop out items,
  moving platforms, checkpoints, the goal flag) carry state and behaviour, so
  each is a small class instance kept in its own list.

The character -> tile mapping (the "legend") used by JSON levels is defined at
the bottom in :data:`TILE_LEGEND`.
"""

from __future__ import annotations

from typing import Optional, Tuple

import pygame

import config

T = config.TILE_SIZE

# ---------------------------------------------------------------------------
# Static tile type codes (stored in the level grid).
# Each maps to (asset_key, solid, one_way).
# ---------------------------------------------------------------------------
TILE_DEFS = {
    "ground":   ("ground",    True,  False),
    "dirt":     ("dirt",      True,  False),
    "pipe_top": ("pipe_top",  True,  False),
    "pipe_body":("pipe_body", True,  False),
    "metal":    ("metal",     True,  False),
    "platform": ("platform",  True,  True),   # one-way: only collide from above
}


class InteractiveBlock:
    """Base class for bricks and question blocks.

    Holds a grid position, a solid flag and a small "bump" animation that plays
    when the player hits the block from below.
    """

    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
        self.rect = pygame.Rect(col * T, row * T, T, T)
        self.solid = True
        self.bump_offset = 0.0   # current vertical visual offset
        self.bump_vel = 0.0
        self.active = True       # still drawable / collidable

    def bump(self) -> None:
        """Kick off the upward bump animation."""
        self.bump_vel = -6.0

    def update(self, dt: float) -> None:
        if self.bump_vel != 0 or self.bump_offset != 0:
            f = dt * 60
            self.bump_vel += 1.4 * f          # gravity pulling block back down
            self.bump_offset += self.bump_vel * f
            if self.bump_offset >= 0:
                self.bump_offset = 0.0
                self.bump_vel = 0.0

    def draw(self, surface, camera, assets) -> None:  # overridden
        pass


class BrickBlock(InteractiveBlock):
    """A brick. A *big* player smashes it from below; a small player just bumps
    it. May optionally hold coins."""

    def __init__(self, col, row, coins: int = 0):
        super().__init__(col, row)
        self.coins = coins  # >0 means it acts like a coin dispenser until empty

    def hit(self, player_is_big: bool) -> str:
        """Return the outcome of being hit from below.

        * "break"  — shattered (big player, empty brick)
        * "coin"   — dispensed a coin
        * "bump"   — just bounced (small player on solid brick)
        """
        if self.coins > 0:
            self.coins -= 1
            self.bump()
            return "coin"
        if player_is_big:
            self.active = False
            self.solid = False
            return "break"
        self.bump()
        return "bump"

    def draw(self, surface, camera, assets):
        if not self.active:
            return
        img = assets.tiles["brick"]
        r = self.rect.move(0, int(self.bump_offset))
        surface.blit(img, camera.apply(r))


class QuestionBlock(InteractiveBlock):
    """A ``?`` block. Pops a coin or a power-up the first time it is hit, then
    becomes an inert "used" block."""

    def __init__(self, col, row, content: str = "coin"):
        super().__init__(col, row)
        self.content = content    # "coin", "mushroom", "fire_flower", "star"
        self.used = False
        self.anim_index = 0.0

    def hit(self) -> Optional[str]:
        if self.used:
            return None
        self.used = True
        self.bump()
        return self.content

    def update(self, dt):
        super().update(dt)
        self.anim_index = (self.anim_index + dt * 8) % 4

    def draw(self, surface, camera, assets):
        r = self.rect.move(0, int(self.bump_offset))
        if self.used:
            img = assets.question["used"][0]
        else:
            img = assets.question["active"][int(self.anim_index)]
        surface.blit(img, camera.apply(r))


class MovingPlatform:
    """A solid platform that oscillates between two points and carries the
    player. ``axis`` is 'h' or 'v'; ``span`` is travel distance in tiles."""

    def __init__(self, col, row, axis="h", span=3, speed=1.5):
        self.start = pygame.Vector2(col * T, row * T)
        self.rect = pygame.Rect(col * T, row * T, T, T // 2)
        self.axis = axis
        self.span = span * T
        self.speed = speed
        self.dir = 1
        self.delta = pygame.Vector2(0, 0)  # movement applied this frame
        self.solid = True
        self.one_way = True  # ride on top

    def update(self, dt: float) -> None:
        f = dt * 60
        move = self.speed * self.dir * f
        prev = self.rect.topleft
        if self.axis == "h":
            self.rect.x += move
            if self.rect.x > self.start.x + self.span:
                self.rect.x = int(self.start.x + self.span)
                self.dir = -1
            elif self.rect.x < self.start.x:
                self.rect.x = int(self.start.x)
                self.dir = 1
        else:
            self.rect.y += move
            if self.rect.y > self.start.y + self.span:
                self.rect.y = int(self.start.y + self.span)
                self.dir = -1
            elif self.rect.y < self.start.y:
                self.rect.y = int(self.start.y)
                self.dir = 1
        self.delta.update(self.rect.x - prev[0], self.rect.y - prev[1])

    def draw(self, surface, camera, assets):
        surface.blit(assets.tiles["metal"], camera.apply(self.rect))


class Checkpoint:
    """A flag that, once touched, becomes the player's respawn point."""

    def __init__(self, col, row):
        self.rect = pygame.Rect(col * T + T // 2 - 12, row * T - T, 24, 96)
        self.activated = False

    def draw(self, surface, camera, assets):
        frame = assets.checkpoint_frames[1 if self.activated else 0]
        surface.blit(frame, camera.apply(self.rect))


class Goal:
    """The level-completion flag at the end of a level."""

    def __init__(self, col, row, height_tiles=6):
        self.height = height_tiles * T
        # Base sits on top of the ground cell below the marker (row + 1).
        top = (row + 1) * T - self.height
        self.rect = pygame.Rect(col * T + T // 2 - 6, top, 12, self.height)
        self.cloth_y = self.rect.top + 6  # animated slide-down on completion
        self.lowered = False

    def lower_flag(self):
        self.lowered = True

    def update(self, dt):
        if self.lowered and self.cloth_y < self.rect.bottom - 40:
            self.cloth_y += 180 * dt

    def draw(self, surface, camera, assets):
        # pole
        pole = pygame.transform.scale(assets.flag["pole"], (12, self.height))
        surface.blit(pole, camera.apply(self.rect))
        # cloth
        cloth = assets.flag["cloth"]
        cx, cy = camera.apply_point(self.rect.right, self.cloth_y)
        surface.blit(cloth, (cx - 2, cy))


# ---------------------------------------------------------------------------
# JSON map legend: maps single characters in a level's "map" array to either a
# static tile type code, or a marker handled specially by the Level loader.
# ---------------------------------------------------------------------------
TILE_LEGEND = {
    "X": ("static", "ground"),
    "D": ("static", "dirt"),
    "T": ("static", "pipe_top"),
    "I": ("static", "pipe_body"),
    "=": ("static", "platform"),   # one-way platform
    "U": ("static", "metal"),
    "B": ("brick", 0),
    "C": ("brick_coins", 3),       # brick that dispenses coins
    "?": ("question", "coin"),
    "M": ("question", "mushroom"),
    "L": ("question", "fire_flower"),
    "S": ("question", "star"),
    "o": ("coin", None),
    "g": ("enemy", "goomba"),
    "k": ("enemy", "koopa"),
    "f": ("enemy", "flyer"),
    "p": ("checkpoint", None),
    "F": ("goal", None),
    "@": ("player_start", None),
}
