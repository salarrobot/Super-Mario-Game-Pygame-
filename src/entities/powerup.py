"""
powerup.py
==========

Collectible power-ups that pop out of ``?`` blocks:

* **Mushroom** — slides along the ground like an enemy (gravity + wall turns).
* **Fire Flower** — stays put on top of the block, gently animating.
* **Star** — bounces continuously and drifts, granting temporary invincibility.

Each item first *emerges* from its source block (rising one tile over a short
time, ignoring collision) before becoming active and collectible.
"""

from __future__ import annotations

import config
from src.entities.entity import PhysicsEntity
from src.utils.animation import Animation

T = config.TILE_SIZE


class PowerUp(PhysicsEntity):
    def __init__(self, x, y, kind, assets, audio, particles):
        size = 36
        super().__init__(x, y, size, size)
        self.kind = kind
        self.assets = assets
        self.audio = audio
        self.particles = particles
        self.speed = 2.0
        self.facing = 1

        # Emerge animation: rise one tile out of the block.
        self.emerging = True
        self.emerge_target = y - T
        self.gravity_scale = 0.0

        if kind == "fire_flower":
            self.anim = Animation(assets.powerups["fire_flower"], fps=4)
        elif kind == "star":
            self.anim = Animation(assets.powerups["star"], fps=8)
        else:
            self.anim = None  # mushroom is a single static sprite

        self.audio.play("powerup_appear")

    def update(self, dt, level):
        if not self.alive:
            return

        if self.emerging:
            self.pos.y -= 60 * dt
            if self.pos.y <= self.emerge_target:
                self.pos.y = self.emerge_target
                self.emerging = False
                self.gravity_scale = 0.0 if self.kind == "fire_flower" else 1.0
            self.sync_rect()
            return

        if self.kind == "mushroom":
            self.vel.x = self.speed * self.facing
            self.move_and_collide(level)
            if self.collisions["left"]:
                self.facing = 1
            elif self.collisions["right"]:
                self.facing = -1
        elif self.kind == "star":
            self.vel.x = self.speed * self.facing
            self.move_and_collide(level)
            if self.collisions["left"]:
                self.facing = 1
            elif self.collisions["right"]:
                self.facing = -1
            if self.on_ground:
                self.vel.y = -11  # perpetual bounce
        # fire_flower just sits and animates.

        if self.anim:
            self.anim.update(dt)

    def draw(self, surface, camera):
        if self.kind == "mushroom":
            frame = self.assets.powerups["mushroom"]
        else:
            frame = self.anim.current_frame
        draw_rect = frame.get_rect(center=self.rect.center)
        surface.blit(frame, camera.apply(draw_rect))
