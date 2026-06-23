"""
coin.py
=======

The humble coin. Static in the world, it just spins (a 6-frame squash animation
that fakes 3D rotation) until the player overlaps it, at which point the play
state collects it: bumps the score and coin counter and emits a sparkle.
"""

from __future__ import annotations

import pygame

import config
from src.utils.animation import Animation

T = config.TILE_SIZE


class Coin:
    def __init__(self, col, row, assets):
        # Center the 32px coin within its tile cell.
        self.rect = pygame.Rect(col * T + (T - 32) // 2, row * T + (T - 32) // 2, 32, 32)
        self.anim = Animation(assets.coin_frames, fps=10)
        self.collected = False

    def update(self, dt):
        self.anim.update(dt)

    def draw(self, surface, camera):
        surface.blit(self.anim.current_frame, camera.apply(self.rect))
