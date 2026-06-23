"""
parallax.py
===========

A multi-layer parallax background.

Depth is faked by scrolling each layer at a different fraction of the camera's
horizontal movement: distant mountains barely move, near bushes move almost as
fast as the foreground. A vertical gradient sky is drawn first, then each prop
layer back-to-front. Props are laid out once at construction (seeded by the
level width) so the scene is stable frame to frame.
"""

from __future__ import annotations

import random
from typing import List, Tuple

import pygame

import config


class _Layer:
    def __init__(self, factor: float, props: List[Tuple[pygame.Surface, float, float]]):
        self.factor = factor               # 0 = static, 1 = moves with camera
        self.props = props                 # (image, world_x, y)


class ParallaxBackground:
    def __init__(self, assets, level_pixel_width: int, theme: str = "day"):
        self.assets = assets
        self.width = level_pixel_width
        self.theme = theme
        self.sky = self._make_sky(theme)
        self.layers: List[_Layer] = []
        self._build_layers()

    # ------------------------------------------------------------------ sky
    def _make_sky(self, theme: str) -> pygame.Surface:
        top, bottom = config.SKY_TOP, config.SKY_BOTTOM
        if theme == "dusk":
            top, bottom = (70, 80, 140), (250, 180, 120)
        elif theme == "cave":
            top, bottom = (30, 28, 48), (60, 55, 85)
        surf = pygame.Surface((config.RENDER_WIDTH, config.RENDER_HEIGHT))
        for y in range(config.RENDER_HEIGHT):
            t = y / config.RENDER_HEIGHT
            col = [int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)]
            pygame.draw.line(surf, col, (0, y), (config.RENDER_WIDTH, y))
        return surf

    # --------------------------------------------------------------- layers
    def _scatter(self, image, factor, count, y_range, jitter=True):
        rng = random.Random(int(self.width * factor * 13 + count))
        props = []
        # Spread props across an extended width so wrapping looks continuous.
        span = max(self.width, config.RENDER_WIDTH) + image.get_width()
        step = span / count
        for i in range(count):
            x = i * step + (rng.uniform(-step * 0.3, step * 0.3) if jitter else 0)
            y = rng.uniform(*y_range)
            props.append((image, x, y))
        return props

    def _build_layers(self):
        a = self.assets.scenery
        ground_y = config.RENDER_HEIGHT
        # Furthest: mountains
        self.layers.append(_Layer(0.20, self._scatter(
            a["mountain"], 0.20, max(3, self.width // 700),
            (ground_y - 260, ground_y - 220))))
        # Far hills
        self.layers.append(_Layer(0.40, self._scatter(
            a["hill_far"], 0.40, max(4, self.width // 480),
            (ground_y - 150, ground_y - 120))))
        # Clouds (high up, gentle drift)
        self.layers.append(_Layer(0.30, self._scatter(
            a["cloud"], 0.30, max(4, self.width // 420),
            (40, config.RENDER_HEIGHT * 0.45))))
        # Near hills
        self.layers.append(_Layer(0.60, self._scatter(
            a["hill_near"], 0.60, max(4, self.width // 520),
            (ground_y - 180, ground_y - 150))))
        # Foreground bushes
        self.layers.append(_Layer(0.80, self._scatter(
            a["bush"], 0.80, max(5, self.width // 360),
            (ground_y - 70, ground_y - 55))))

    # ----------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface, camera) -> None:
        surface.blit(self.sky, (0, 0))
        cam_x = camera.offset.x
        sw = config.RENDER_WIDTH
        for layer in self.layers:
            shift = cam_x * layer.factor
            for img, wx, y in layer.props:
                # Wrap the prop across the visible region for endless scrolling.
                span = max(self.width, sw) + img.get_width()
                x = (wx - shift) % span
                if x > sw:
                    x -= span
                if -img.get_width() <= x <= sw:
                    surface.blit(img, (int(x), int(y)))
