"""
fireball.py
===========

The projectile thrown by a fire-powered player. It travels horizontally, is
pulled down by gravity and bounces off the ground a couple of times before
fizzling out. On contact with an enemy it defeats it; on contact with a wall it
pops. A short lifetime and bounce cap keep the screen from filling with stray
fireballs.
"""

from __future__ import annotations

import config
from src.entities.entity import PhysicsEntity
from src.utils.animation import Animation


class Fireball(PhysicsEntity):
    SPEED = 9.0

    def __init__(self, x, y, direction, assets, particles):
        super().__init__(x - 11, y - 11, 18, 18)
        self.assets = assets
        self.particles = particles
        self.facing = direction
        self.vel.x = self.SPEED * direction
        self.anim = Animation(assets.fireball_frames, fps=16)
        self.bounces = 0
        self.max_bounces = 3
        self.life = 2.5  # seconds

    def update(self, dt, level):
        if not self.alive:
            return
        self.life -= dt
        if self.life <= 0:
            self.pop()
            return

        self.vel.x = self.SPEED * self.facing
        self.move_and_collide(level)

        # Bounce off the floor.
        if self.collisions["bottom"]:
            self.vel.y = -7
            self.bounces += 1
            if self.bounces > self.max_bounces:
                self.pop()
        # Die against walls.
        if self.collisions["left"] or self.collisions["right"]:
            self.pop()

        self.anim.update(dt)

    def pop(self):
        if self.alive:
            self.particles.explosion(self.rect.centerx, self.rect.centery, config.FIREBALL_MID)
        self.alive = False

    def draw(self, surface, camera):
        surface.blit(self.anim.current_frame, camera.apply(self.rect))
