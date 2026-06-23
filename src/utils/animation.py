"""
animation.py
============

A tiny, reusable frame-animation player.

The :class:`Animation` class is intentionally engine-agnostic: it just holds an
ordered list of surfaces and advances an internal timer. Every animated entity
(player, enemies, coins, power-ups) owns one or more ``Animation`` objects and
asks for ``current_frame`` each draw. This keeps timing logic in one place
instead of scattering frame counters across the codebase.
"""

from __future__ import annotations

from typing import List, Optional

import pygame


class Animation:
    def __init__(self, frames: List[pygame.Surface], fps: float = 10.0,
                 loop: bool = True):
        assert frames, "Animation needs at least one frame"
        self.frames = frames
        self.frame_duration = 1.0 / fps if fps > 0 else 0.0
        self.loop = loop
        self.index = 0
        self.timer = 0.0
        self.finished = False

    def reset(self) -> None:
        self.index = 0
        self.timer = 0.0
        self.finished = False

    def update(self, dt: float) -> None:
        """Advance the animation by ``dt`` seconds."""
        if self.finished or self.frame_duration <= 0 or len(self.frames) == 1:
            return
        self.timer += dt
        while self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.index += 1
            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.finished = True
                    break

    @property
    def current_frame(self) -> pygame.Surface:
        return self.frames[self.index]

    def get_frame(self, flip_x: bool = False) -> pygame.Surface:
        """Return the current frame, optionally horizontally mirrored."""
        frame = self.frames[self.index]
        if flip_x:
            return pygame.transform.flip(frame, True, False)
        return frame
