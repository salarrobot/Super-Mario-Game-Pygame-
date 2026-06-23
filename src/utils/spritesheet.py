"""
spritesheet.py
==============

Sprite-sheet support.

Even though this game generates its art procedurally, real game projects almost
always pack frames into a single texture ("sprite sheet") for performance and
tidy asset management. This module provides both halves of that workflow:

* :class:`SpriteSheet` — slice an existing sheet surface into individual frames
  (by grid or by explicit rectangles).
* :func:`pack_frames` — combine a list of frames into one horizontal sheet,
  used by ``tools/export_assets.py`` to bake the procedural art to disk.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import pygame


class SpriteSheet:
    """Wraps a surface and slices frames out of it."""

    def __init__(self, surface: pygame.Surface):
        self.surface = surface

    @classmethod
    def from_file(cls, path: str) -> "SpriteSheet":
        return cls(pygame.image.load(path).convert_alpha())

    def frame(self, x: int, y: int, w: int, h: int) -> pygame.Surface:
        """Extract a single frame given an explicit rectangle."""
        clip = pygame.Surface((w, h), pygame.SRCALPHA)
        clip.blit(self.surface, (0, 0), pygame.Rect(x, y, w, h))
        return clip

    def grid(self, frame_w: int, frame_h: int, count: int,
             start: Tuple[int, int] = (0, 0), spacing: int = 0) -> List[pygame.Surface]:
        """Slice ``count`` evenly-spaced frames left-to-right, top-to-bottom."""
        frames: List[pygame.Surface] = []
        sheet_w = self.surface.get_width()
        cols = max(1, (sheet_w - start[0] + spacing) // (frame_w + spacing))
        for i in range(count):
            col = i % cols
            row = i // cols
            x = start[0] + col * (frame_w + spacing)
            y = start[1] + row * (frame_h + spacing)
            frames.append(self.frame(x, y, frame_w, frame_h))
        return frames

    def by_rects(self, rects: Sequence[Tuple[int, int, int, int]]) -> List[pygame.Surface]:
        return [self.frame(*r) for r in rects]


def pack_frames(frames: List[pygame.Surface], padding: int = 2) -> pygame.Surface:
    """Pack frames into a single horizontal strip surface (a sprite sheet)."""
    if not frames:
        return pygame.Surface((1, 1), pygame.SRCALPHA)
    h = max(f.get_height() for f in frames)
    w = sum(f.get_width() for f in frames) + padding * (len(frames) - 1)
    sheet = pygame.Surface((w, h), pygame.SRCALPHA)
    x = 0
    for f in frames:
        sheet.blit(f, (x, h - f.get_height()))
        x += f.get_width() + padding
    return sheet
