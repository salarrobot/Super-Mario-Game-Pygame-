"""
config.py
=========

Central configuration module for the whole game.

Keeping every tunable constant in one place is a deliberate design decision:
it makes the game easy to balance (physics, difficulty, visuals) without having
to hunt through the codebase, and it gives every other module a single, trusted
source of truth.

Nothing in here imports from the rest of the project, so this module can be
imported from anywhere without creating circular-import problems.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# We resolve everything relative to this file so the game works no matter what
# directory it is launched from.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(ROOT_DIR, "assets")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
SOUND_DIR = os.path.join(ASSET_DIR, "sounds")
LEVEL_DIR = os.path.join(ROOT_DIR, "levels")
SAVE_PATH = os.path.join(ROOT_DIR, "savegame.json")
SETTINGS_PATH = os.path.join(ROOT_DIR, "settings.json")

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
GAME_TITLE = "Super Pixel Quest"
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60

# The game world is rendered to a fixed-size surface and then scaled up to the
# window. This keeps the pixel-art crisp and the physics resolution constant
# regardless of the actual window size or fullscreen resolution.
RENDER_WIDTH = SCREEN_WIDTH
RENDER_HEIGHT = SCREEN_HEIGHT

# ---------------------------------------------------------------------------
# Tiles / world units
# ---------------------------------------------------------------------------
TILE_SIZE = 48  # pixels per tile; the entire level grid is built on this unit
GRAVITY = 0.85  # downward acceleration applied every frame
MAX_FALL_SPEED = 22  # terminal velocity so the player never tunnels through floors

# ---------------------------------------------------------------------------
# Player physics (tuned for a snappy, Mario-like feel)
# ---------------------------------------------------------------------------
PLAYER_ACCEL = 0.9          # horizontal acceleration while a run key is held
PLAYER_FRICTION = -0.16     # multiplied by velocity for smooth deceleration
PLAYER_MAX_SPEED = 7.0      # horizontal speed cap
PLAYER_JUMP_SPEED = -16.5   # initial upward velocity of a jump
PLAYER_DOUBLE_JUMP_SPEED = -13.5
PLAYER_MAX_JUMP_HOLD = 12   # frames a jump can be "held" for variable height
COYOTE_TIME = 6             # frames after leaving a ledge you can still jump
JUMP_BUFFER = 6             # frames a jump press is remembered before landing
INVINCIBLE_TIME = 90        # frames of i-frames after taking damage
STAR_TIME = 600             # frames a star power-up lasts (~10s at 60fps)

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_SMOOTHING = 0.12     # 0 = locked to target, 1 = instant snap (lerp factor)
CAMERA_LOOKAHEAD = 60       # how far ahead of the player (in facing dir) to look

# ---------------------------------------------------------------------------
# Gameplay
# ---------------------------------------------------------------------------
START_LIVES = 3
DEFAULT_TIME_LIMIT = 300    # seconds per level if a level doesn't specify one
COIN_SCORE = 100
ENEMY_SCORE = 200
POWERUP_SCORE = 1000
FLAG_SCORE = 2000

# ---------------------------------------------------------------------------
# Colors (R, G, B). A small named palette keeps rendering consistent.
# ---------------------------------------------------------------------------
WHITE = (245, 245, 245)
BLACK = (18, 18, 24)
RED = (220, 60, 60)
GREEN = (70, 190, 90)
BLUE = (70, 130, 220)
YELLOW = (250, 215, 70)
ORANGE = (240, 150, 50)
SKY_TOP = (96, 168, 240)
SKY_BOTTOM = (180, 222, 255)
UI_PANEL = (28, 30, 46)
UI_ACCENT = (250, 215, 70)
UI_TEXT = (235, 238, 245)
UI_MUTED = (150, 156, 178)

# A few gameplay tint colors referenced by particle/entity effects. They mirror
# the values in :mod:`src.graphics.palette` so effect code can stay palette-free.
COIN_SHINE = (255, 245, 200)
STAR = (255, 225, 90)
FIREBALL_MID = (250, 150, 50)
GOOMBA_BODY = (150, 95, 55)
KOOPA_SHELL = (70, 180, 90)
FLYER_BODY = (180, 90, 200)

# ---------------------------------------------------------------------------
# Default key bindings. These can be remapped at runtime from the settings
# menu and are persisted to settings.json. Values are pygame key constants,
# stored here as their integer codes via pygame after import elsewhere; we keep
# them as string names so the file has no pygame dependency.
# ---------------------------------------------------------------------------
DEFAULT_CONTROLS = {
    "left": "a",
    "right": "d",
    "jump": "space",
    "run": "left shift",
    "shoot": "j",
    "pause": "escape",
}

# Default user-tunable settings (mirrored/overridden by settings.json).
DEFAULT_SETTINGS = {
    "music_volume": 0.5,
    "sfx_volume": 0.7,
    "fullscreen": False,
    "show_fps": True,
    "controls": DEFAULT_CONTROLS,
}

# Depth/Z ordering helpers used by particle and entity drawing.
LAYER_BACKGROUND = 0
LAYER_WORLD = 1
LAYER_ENTITIES = 2
LAYER_PARTICLES = 3
LAYER_UI = 4
