"""
camera.py
=========

A smooth side-scrolling camera.

The camera stores a world-space offset that everything is drawn relative to.
Each frame it eases toward the player (linear interpolation) with a small
look-ahead in the direction the player faces, then clamps itself to the level
bounds so we never show empty space past the edges. A decaying screen-shake
offset is layered on top for impact feedback (landing, taking damage, breaking
blocks).
"""

from __future__ import annotations

import random

import pygame

import config


class Camera:
    def __init__(self, level_pixel_width: int, level_pixel_height: int):
        self.offset = pygame.Vector2(0, 0)
        self.level_width = level_pixel_width
        self.level_height = level_pixel_height
        self.view_w = config.RENDER_WIDTH
        self.view_h = config.RENDER_HEIGHT
        self._shake_time = 0.0
        self._shake_mag = 0.0
        self._shake_offset = pygame.Vector2(0, 0)

    def set_level_size(self, w: int, h: int) -> None:
        self.level_width = w
        self.level_height = h

    def shake(self, magnitude: float = 8.0, duration: float = 0.3) -> None:
        """Trigger a screen shake; stronger requests win over weaker ones."""
        self._shake_mag = max(self._shake_mag, magnitude)
        self._shake_time = max(self._shake_time, duration)

    def snap_to(self, target_rect: pygame.Rect) -> None:
        """Instantly center on a target (used on level start / respawn)."""
        self._desired(target_rect, 0)
        self.offset.update(self._target_x, self._target_y)

    def _desired(self, target_rect: pygame.Rect, facing: int) -> None:
        look = config.CAMERA_LOOKAHEAD * facing
        self._target_x = target_rect.centerx - self.view_w / 2 + look
        self._target_y = target_rect.centery - self.view_h / 2
        # Clamp so we don't scroll past the level edges.
        self._target_x = max(0, min(self._target_x, self.level_width - self.view_w))
        self._target_y = max(0, min(self._target_y, self.level_height - self.view_h))

    def update(self, dt: float, target_rect: pygame.Rect, facing: int = 1) -> None:
        self._desired(target_rect, facing)
        # Frame-rate independent smoothing.
        t = 1 - pow(1 - config.CAMERA_SMOOTHING, dt * 60)
        self.offset.x += (self._target_x - self.offset.x) * t
        self.offset.y += (self._target_y - self.offset.y) * t

        # Screen shake (decays over its duration).
        if self._shake_time > 0:
            self._shake_time -= dt
            mag = self._shake_mag * max(0.0, self._shake_time)
            self._shake_offset.update(random.uniform(-mag, mag), random.uniform(-mag, mag))
            if self._shake_time <= 0:
                self._shake_mag = 0.0
                self._shake_offset.update(0, 0)
        else:
            self._shake_offset.update(0, 0)

    # --- coordinate transforms --------------------------------------------
    @property
    def total_offset(self) -> pygame.Vector2:
        return self.offset + self._shake_offset

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Convert a world-space rect to screen space."""
        o = self.total_offset
        return rect.move(-int(o.x), -int(o.y))

    def apply_point(self, x: float, y: float):
        o = self.total_offset
        return x - o.x, y - o.y
