"""
palette.py
==========

A curated color palette used by the procedural art generator.

Centralizing colors here keeps the generated sprites visually coherent (the
same greens, browns and skin tones everywhere) and makes it trivial to retheme
the whole game by editing a single file.
"""

from __future__ import annotations

# --- Character (the hero, "Pip") ------------------------------------------
SKIN = (255, 213, 170)
SKIN_SHADOW = (224, 170, 130)
CAP = (220, 60, 60)
CAP_SHADOW = (170, 40, 40)
OVERALL = (60, 110, 210)
OVERALL_SHADOW = (40, 80, 165)
SHIRT = (70, 180, 90)
SHOES = (90, 60, 40)
EYE = (40, 44, 60)

# Fire-power variant recolors the outfit white/red.
FIRE_OVERALL = (235, 235, 240)
FIRE_OVERALL_SHADOW = (200, 200, 210)
FIRE_CAP = (210, 50, 50)

OUTLINE = (30, 26, 38)

# --- Generic accent colors (shared with the UI) ---------------------------
RED = (220, 60, 60)
GREEN = (70, 190, 90)
YELLOW = (250, 215, 70)
WHITE = (245, 245, 245)

# --- Enemies ---------------------------------------------------------------
GOOMBA_BODY = (150, 95, 55)
GOOMBA_BODY_SHADOW = (110, 68, 38)
GOOMBA_FOOT = (70, 45, 30)
GOOMBA_EYE = (250, 250, 250)

KOOPA_SHELL = (70, 180, 90)
KOOPA_SHELL_SHADOW = (45, 130, 65)
KOOPA_SKIN = (240, 210, 120)
KOOPA_SKIN_SHADOW = (205, 170, 90)

FLYER_BODY = (180, 90, 200)
FLYER_BODY_SHADOW = (140, 60, 165)
FLYER_WING = (240, 230, 250)

# --- Tiles / world ---------------------------------------------------------
GROUND_TOP = (110, 200, 95)
GROUND_TOP_SHADOW = (80, 160, 70)
GROUND_DIRT = (155, 105, 65)
GROUND_DIRT_SHADOW = (120, 80, 50)
GROUND_DIRT_LIGHT = (180, 128, 85)

BRICK = (190, 95, 60)
BRICK_SHADOW = (150, 70, 45)
BRICK_LINE = (120, 55, 35)

QUESTION = (245, 200, 70)
QUESTION_SHADOW = (210, 160, 45)
QUESTION_USED = (150, 110, 70)
QUESTION_RIVET = (255, 240, 180)

PIPE = (60, 190, 110)
PIPE_SHADOW = (40, 150, 85)
PIPE_LIGHT = (120, 225, 150)

PLATFORM = (170, 120, 80)
PLATFORM_TOP = (210, 160, 110)
METAL = (150, 158, 175)
METAL_LIGHT = (195, 202, 215)
METAL_SHADOW = (110, 118, 135)

# --- Collectibles ----------------------------------------------------------
COIN = (250, 215, 70)
COIN_SHADOW = (215, 170, 40)
COIN_SHINE = (255, 245, 200)

MUSHROOM_CAP = (225, 70, 70)
MUSHROOM_SPOT = (250, 245, 235)
MUSHROOM_STEM = (245, 225, 195)

FLOWER_PETAL = (250, 130, 60)
FLOWER_CENTER = (250, 230, 120)
FLOWER_STEM = (70, 180, 90)

STAR = (255, 225, 90)
STAR_SHADOW = (235, 185, 50)

FIREBALL_CORE = (255, 240, 170)
FIREBALL_MID = (250, 150, 50)
FIREBALL_EDGE = (220, 70, 40)

# --- Scenery / parallax ----------------------------------------------------
CLOUD = (250, 252, 255)
CLOUD_SHADOW = (215, 228, 245)
HILL_FAR = (130, 200, 150)
HILL_NEAR = (95, 180, 120)
BUSH = (80, 170, 95)
BUSH_SHADOW = (60, 140, 78)
MOUNTAIN = (150, 175, 205)
MOUNTAIN_SNOW = (235, 242, 250)

FLAG_POLE = (200, 205, 215)
FLAG_CLOTH = (70, 190, 120)
