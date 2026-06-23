"""
build_levels.py
===============

Generates the three level JSON files programmatically.

Hand-aligning wide ASCII maps is error-prone, so instead we build each level on
a 2D character grid by placing features at coordinates, then serialize the grid
to the same human-readable JSON the game loads. Re-run this whenever you want to
regenerate or tweak the bundled levels:

    python tools/build_levels.py

The output format is documented in ``src/world/level.py``.
"""

from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVEL_DIR = os.path.join(ROOT, "levels")

H = 15                 # rows (≈ 720px tall, taller than the viewport)
GROUND_TOP = 13        # grass row
GROUND_BOT = 14        # dirt row


class Grid:
    def __init__(self, width):
        self.w = width
        self.g = [[" "] * width for _ in range(H)]

    def set(self, c, r, ch):
        if 0 <= r < H and 0 <= c < self.w:
            self.g[r][c] = ch

    def ground(self, x0, x1):
        for x in range(x0, x1 + 1):
            self.set(x, GROUND_TOP, "X")
            self.set(x, GROUND_BOT, "D")

    def hline(self, ch, x0, x1, y):
        for x in range(x0, x1 + 1):
            self.set(x, y, ch)

    def coins_row(self, x0, x1, y):
        for x in range(x0, x1 + 1):
            self.set(x, y, "o")

    def stairs(self, x0, height, y_base, ch="U", step=1, down=False):
        """Build a Mario-style staircase of solid blocks."""
        for i in range(height):
            col = x0 + i * step
            h = (height - i) if down else (i + 1)
            for j in range(h):
                self.set(col, y_base - j, ch)

    def to_map(self):
        return ["".join(row) for row in self.g]


def write(name, data):
    os.makedirs(LEVEL_DIR, exist_ok=True)
    path = os.path.join(LEVEL_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print(f"wrote {path}  ({len(data['map'][0])}x{len(data['map'])})")


# ===========================================================================
#  LEVEL 1 — Green Hills (gentle introduction)
# ===========================================================================
def level1():
    W = 110
    g = Grid(W)
    # Ground with two small, jumpable pits.
    g.ground(0, 26)
    g.ground(30, 58)
    g.ground(62, W - 1)

    g.set(3, 12, "@")                       # player start

    g.coins_row(6, 9, 11)                   # welcome coins
    g.set(10, 9, "M")                       # mushroom block
    g.set(12, 9, "?")
    g.set(13, 9, "?")
    g.set(16, 12, "g")                      # first goomba
    g.coins_row(28, 29, 9)                  # coins over pit 1

    g.set(20, 12, "g")
    g.hline("C", 24, 24, 9)                 # coin brick
    g.hline("B", 25, 26, 9)

    # Pipe obstacle (2 tall, stands on the ground).
    g.set(36, 12, "T")
    g.set(36, 13, "I")  # overwrites ground cell with pipe body (still solid)
    g.set(40, 12, "k")                      # koopa

    # Bonus climb: platform stairs up to a coin shelf.
    g.set(44, 11, "=")
    g.set(46, 10, "=")
    g.set(48, 9, "=")
    g.hline("=", 50, 55, 7)
    g.coins_row(50, 55, 6)
    g.set(52, 6, "L")                       # fire flower up high (overwrites a coin)

    g.set(56, 12, "p")                      # checkpoint
    g.coins_row(60, 61, 9)                  # coins over pit 2
    g.set(66, 9, "S")                       # star block
    g.set(68, 12, "g")
    g.set(72, 12, "g")
    g.set(78, 8, "f")                       # a flyer

    # Closing staircase up to the goal.
    g.stairs(88, 4, 12, ch="U")
    g.set(104, 12, "F")                     # goal flag

    return {
        "name": "Green Hills",
        "theme": "day",
        "music": "level1",
        "time_limit": 300,
        "map": g.to_map(),
        "moving_platforms": [
            {"col": 31, "row": 11, "axis": "h", "span": 3, "speed": 1.4},
        ],
    }


# ===========================================================================
#  LEVEL 2 — Cliffside Caves (more enemies, more verticality)
# ===========================================================================
def level2():
    W = 130
    g = Grid(W)
    g.ground(0, 18)
    g.ground(23, 40)
    g.ground(46, 72)
    g.ground(78, 100)
    g.ground(106, W - 1)

    g.set(2, 12, "@")
    g.set(6, 9, "M")
    g.coins_row(8, 12, 10)
    g.set(10, 12, "g")
    g.set(14, 12, "k")

    # Floating brick path with a flyer guarding it.
    g.hline("B", 20, 22, 10)
    g.set(21, 7, "f")
    g.coins_row(20, 22, 9)

    g.set(28, 12, "g")
    g.set(30, 9, "?")
    g.set(32, 9, "L")
    g.hline("B", 30, 33, 9)                 # bricks around the ? blocks
    g.set(36, 12, "k")
    g.set(38, 12, "g")

    g.set(43, 11, "=")                      # stepping stones over a gap
    g.set(44, 10, "=")

    g.set(50, 12, "p")                      # checkpoint
    g.set(52, 12, "g")
    g.set(55, 8, "f")
    g.set(58, 9, "S")                       # star

    # High bonus shelf reachable by a moving platform.
    g.hline("=", 60, 66, 6)
    g.coins_row(60, 66, 5)
    g.set(63, 5, "L")

    g.set(70, 12, "k")
    g.hline("C", 84, 86, 9)
    g.set(88, 12, "g")
    g.set(90, 12, "g")
    g.set(92, 8, "f")
    g.set(95, 9, "?")

    g.stairs(108, 5, 12, ch="U")
    g.stairs(116, 5, 12, ch="U", down=True)
    g.set(124, 12, "F")

    return {
        "name": "Cliffside Caves",
        "theme": "dusk",
        "music": "level2",
        "time_limit": 320,
        "map": g.to_map(),
        "moving_platforms": [
            {"col": 41, "row": 12, "axis": "h", "span": 4, "speed": 2.0},
            {"col": 74, "row": 11, "axis": "v", "span": 4, "speed": 1.6},
            {"col": 102, "row": 11, "axis": "h", "span": 3, "speed": 2.2},
        ],
    }


# ===========================================================================
#  LEVEL 3 — Sky Fortress (the gauntlet)
# ===========================================================================
def level3():
    W = 150
    g = Grid(W)
    g.ground(0, 14)
    g.ground(20, 30)
    g.ground(36, 50)
    g.ground(56, 70)
    g.ground(76, 92)
    g.ground(98, 116)
    g.ground(122, W - 1)

    g.set(2, 12, "@")
    g.set(5, 9, "M")
    g.set(8, 12, "g")
    g.set(11, 12, "k")
    g.coins_row(6, 10, 10)

    # Brick maze with a fire flower in the middle (break in as big Pip).
    g.hline("B", 16, 19, 10)
    g.hline("B", 16, 19, 8)
    g.set(17, 9, "o")
    g.set(18, 9, "L")
    g.set(22, 12, "g")
    g.set(24, 12, "g")
    g.set(26, 8, "f")

    g.set(31, 11, "=")
    g.set(33, 10, "=")
    g.coins_row(31, 34, 9)

    g.set(40, 12, "k")
    g.set(43, 12, "g")
    g.set(45, 9, "S")
    g.set(47, 8, "f")
    g.set(40, 12, "p")                      # checkpoint near the midpoint

    # Sky bridge of one-way platforms with flyers.
    g.hline("=", 52, 58, 7)
    g.coins_row(52, 58, 6)
    g.set(54, 5, "f")
    g.set(57, 5, "f")

    g.set(62, 12, "g")
    g.set(64, 12, "k")
    g.set(66, 12, "g")
    g.hline("C", 60, 62, 9)

    # Stacked bricks & ? blocks.
    g.hline("B", 78, 84, 9)
    g.set(80, 9, "?")
    g.set(82, 9, "L")
    g.hline("o", 78, 84, 8)
    g.set(86, 12, "k")
    g.set(88, 8, "f")
    g.set(90, 8, "f")

    g.set(100, 12, "g")
    g.set(103, 12, "g")
    g.set(106, 12, "k")
    g.set(108, 9, "S")
    g.coins_row(110, 114, 10)

    # Final ascent to the fortress flag.
    g.stairs(124, 6, 12, ch="U")
    g.set(140, 12, "F")

    return {
        "name": "Sky Fortress",
        "theme": "dusk",
        "music": "level3",
        "time_limit": 360,
        "map": g.to_map(),
        "moving_platforms": [
            {"col": 15, "row": 12, "axis": "h", "span": 4, "speed": 2.4},
            {"col": 51, "row": 11, "axis": "v", "span": 3, "speed": 1.8},
            {"col": 72, "row": 11, "axis": "h", "span": 4, "speed": 2.6},
            {"col": 94, "row": 11, "axis": "h", "span": 3, "speed": 2.4},
            {"col": 118, "row": 11, "axis": "v", "span": 4, "speed": 2.0},
        ],
    }


if __name__ == "__main__":
    write("level1.json", level1())
    write("level2.json", level2())
    write("level3.json", level3())
    print("Done. Levels written to", LEVEL_DIR)
