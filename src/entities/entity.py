"""
entity.py
=========

The physics foundation shared by the player, enemies and items.

:class:`PhysicsEntity` implements the classic "move-and-collide on each axis
separately" algorithm that platformers rely on:

1. Apply horizontal velocity, then push out of any solid tiles horizontally.
2. Apply gravity and vertical velocity, then push out vertically.

Resolving axes independently is what makes wall-sliding and clean landings
work. One-way platforms (and moving platforms) only stop a falling entity from
above, and a landed entity is carried along by a moving platform's per-frame
delta. Collision results are exposed via :attr:`collisions` so subclasses can
react (e.g. the player bumping a block with its head).
"""

from __future__ import annotations

import pygame

import config


class PhysicsEntity:
    def __init__(self, x: float, y: float, w: int, h: int):
        # Float position is the source of truth; the int rect is for collision.
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.on_ground = False
        self.facing = 1  # 1 right, -1 left
        self.alive = True
        self.gravity_scale = 1.0
        self.collisions = {"top": False, "bottom": False, "left": False, "right": False}
        self.carrier = None  # moving platform we're standing on

    # ------------------------------------------------------------ utilities
    def sync_rect(self) -> None:
        self.rect.x = round(self.pos.x)
        self.rect.y = round(self.pos.y)

    def apply_gravity(self) -> None:
        self.vel.y += config.GRAVITY * self.gravity_scale
        if self.vel.y > config.MAX_FALL_SPEED:
            self.vel.y = config.MAX_FALL_SPEED

    # ----------------------------------------------------- collision solver
    def move_and_collide(self, level) -> None:
        """Integrate velocity and resolve against the level geometry."""
        self.collisions = {"top": False, "bottom": False, "left": False, "right": False}
        self.carrier = None

        # ---- Horizontal ----
        self.pos.x += self.vel.x
        self.sync_rect()
        solids, one_ways = level.collision_sources(self.rect)
        for r in solids:
            if self.rect.colliderect(r):
                if self.vel.x > 0:
                    self.rect.right = r.left
                    self.collisions["right"] = True
                elif self.vel.x < 0:
                    self.rect.left = r.right
                    self.collisions["left"] = True
                self.pos.x = self.rect.x
                self.vel.x = 0

        # ---- Vertical ----
        self.apply_gravity()
        prev_bottom = self.rect.bottom
        self.pos.y += self.vel.y
        self.sync_rect()
        solids, one_ways = level.collision_sources(self.rect)

        for r in solids:
            if self.rect.colliderect(r):
                if self.vel.y > 0:
                    self.rect.bottom = r.top
                    self.collisions["bottom"] = True
                elif self.vel.y < 0:
                    self.rect.top = r.bottom
                    self.collisions["top"] = True
                self.pos.y = self.rect.y
                self.vel.y = 0

        # One-way platforms & moving platforms: block only when descending and
        # the entity's feet were above the platform top last frame.
        if self.vel.y >= 0:
            for r, mover in one_ways:
                if self.rect.colliderect(r) and prev_bottom <= r.top + 8:
                    self.rect.bottom = r.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.collisions["bottom"] = True
                    self.carrier = mover

        self.on_ground = self.collisions["bottom"]

        # Ride a moving platform horizontally (vertical handled by re-landing).
        if self.carrier is not None and self.carrier.delta.x:
            self.pos.x += self.carrier.delta.x
            self.sync_rect()
