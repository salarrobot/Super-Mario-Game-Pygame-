"""
backdrop.py
===========

A shared, gently auto-scrolling scene used behind the menu screens. It reuses
the in-game :class:`ParallaxBackground` driven by a tiny fake camera that drifts
sideways on its own, and lays a scrolling strip of ground tiles along the
bottom plus an idle hero. This gives every menu a living, game-like backdrop
without each state reinventing it.
"""

from __future__ import annotations

import pygame

import config
from src.utils.animation import Animation
from src.world.parallax import ParallaxBackground

T = config.TILE_SIZE


class _FakeCamera:
    """Just enough of the Camera API for ParallaxBackground."""
    def __init__(self):
        self.offset = pygame.Vector2(0, 0)

    @property
    def total_offset(self):
        return self.offset


class MenuBackdrop:
    def __init__(self, assets):
        self.assets = assets
        self.parallax = ParallaxBackground(assets, 4000, theme="day")
        self.cam = _FakeCamera()
        self.scroll_speed = 28  # px/sec
        self.idle = Animation(assets.players["small"]["idle"], fps=5)
        self.t = 0.0

    def update(self, dt):
        self.cam.offset.x += self.scroll_speed * dt
        self.t += dt
        self.idle.update(dt)

    def draw(self, surface, with_hero=True):
        self.parallax.draw(surface, self.cam)
        # Ground strip across the bottom.
        ground_y = config.RENDER_HEIGHT - T
        start = int(self.cam.offset.x) % T
        x = -start
        while x < config.RENDER_WIDTH:
            surface.blit(self.assets.tiles["ground"], (x, ground_y))
            x += T
        if with_hero:
            frame = self.idle.current_frame
            surface.blit(frame, frame.get_rect(midbottom=(config.RENDER_WIDTH // 2, ground_y + 2)))
