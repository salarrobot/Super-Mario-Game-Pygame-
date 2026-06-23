"""
particles.py
============

A lightweight particle system for "juice": dust when you jump or land, sparkles
when you grab a coin, debris when a brick shatters, and a star trail during
invincibility.

Particles are plain lightweight objects updated and drawn in bulk. The system
caps the live particle count so a busy scene can never tank the frame rate.
"""

from __future__ import annotations

import math
import random
from typing import List, Tuple

import pygame

import config


class Particle:
    __slots__ = ("pos", "vel", "color", "life", "max_life", "size",
                 "gravity", "shrink", "glow")

    def __init__(self, x, y, vx, vy, color, life, size, gravity=0.2,
                 shrink=True, glow=False):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(vx, vy)
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
        self.shrink = shrink
        self.glow = glow

    def update(self, dt: float) -> None:
        # dt is normalized to 60fps units for tuning convenience.
        f = dt * 60
        self.vel.y += self.gravity * f
        self.pos += self.vel * f
        self.life -= dt

    @property
    def alive(self) -> bool:
        return self.life > 0


class ParticleSystem:
    MAX_PARTICLES = 600

    def __init__(self):
        self.particles: List[Particle] = []

    def clear(self) -> None:
        self.particles.clear()

    def _add(self, p: Particle) -> None:
        if len(self.particles) < self.MAX_PARTICLES:
            self.particles.append(p)

    # ------------------------------------------------------------ emitters
    def burst(self, x, y, color, count=10, speed=4.0, life=0.5, size=4,
              gravity=0.2, spread=math.tau, direction=-math.pi / 2):
        for _ in range(count):
            ang = direction + random.uniform(-spread / 2, spread / 2)
            spd = random.uniform(speed * 0.4, speed)
            self._add(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                               color, life * random.uniform(0.7, 1.2),
                               size * random.uniform(0.6, 1.2), gravity))

    def jump_dust(self, x, y):
        self.burst(x, y, (220, 220, 230), count=8, speed=3, life=0.35,
                   size=5, gravity=0.1, spread=math.pi, direction=math.pi / 2)

    def land_dust(self, x, y):
        self.burst(x, y, (210, 205, 215), count=10, speed=3.5, life=0.4,
                   size=5, gravity=0.05, spread=math.pi * 0.8, direction=0)
        self.burst(x, y, (210, 205, 215), count=6, speed=3.5, life=0.4,
                   size=5, gravity=0.05, spread=math.pi * 0.8, direction=math.pi)

    def coin_sparkle(self, x, y):
        for _ in range(10):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(1.5, 4.5)
            self._add(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                               config.COIN_SHINE if random.random() > 0.4 else config.YELLOW,
                               random.uniform(0.3, 0.6), random.uniform(2, 4),
                               gravity=0.08, glow=True))

    def enemy_poof(self, x, y, color=(150, 95, 55)):
        self.burst(x, y, color, count=14, speed=5, life=0.5, size=5, gravity=0.25,
                   spread=math.tau, direction=0)

    def brick_debris(self, x, y, color=(190, 95, 60)):
        for _ in range(12):
            self._add(Particle(x, y,
                               random.uniform(-4, 4), random.uniform(-8, -2),
                               color, random.uniform(0.5, 0.9),
                               random.uniform(4, 8), gravity=0.5, shrink=False))

    def star_trail(self, x, y):
        self._add(Particle(x + random.uniform(-6, 6), y + random.uniform(-6, 6),
                           random.uniform(-1, 1), random.uniform(-1, 1),
                           random.choice([config.STAR, config.WHITE, config.YELLOW]),
                           0.4, random.uniform(2, 5), gravity=0.0, glow=True))

    def explosion(self, x, y, color):
        self.burst(x, y, color, count=18, speed=6, life=0.5, size=5,
                   gravity=0.15, spread=math.tau, direction=0)

    # ----------------------------------------------------------- lifecycle
    def update(self, dt: float) -> None:
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface: pygame.Surface, camera) -> None:
        for p in self.particles:
            t = max(0.0, p.life / p.max_life)
            size = p.size * (t if p.shrink else 1.0)
            if size < 1:
                continue
            sx, sy = camera.apply_point(p.pos.x, p.pos.y)
            if p.glow:
                # Soft additive glow for sparkles/star trail.
                glow = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*p.color, int(80 * t)),
                                   (int(size * 2), int(size * 2)), int(size * 2))
                pygame.draw.circle(glow, (*p.color, int(220 * t)),
                                   (int(size * 2), int(size * 2)), max(1, int(size)))
                surface.blit(glow, (sx - size * 2, sy - size * 2),
                             special_flags=pygame.BLEND_RGBA_ADD)
            else:
                pygame.draw.rect(surface, p.color,
                                 (int(sx - size / 2), int(sy - size / 2),
                                  int(size), int(size)))
