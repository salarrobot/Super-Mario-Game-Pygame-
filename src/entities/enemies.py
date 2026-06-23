"""
enemies.py
==========

Three enemy archetypes, each a small state machine:

* :class:`Goomba` — walks, turns at walls and ledges, is defeated by a stomp
  (squashes flat) and hurts the player on side contact.
* :class:`Koopa` — walks; a stomp retracts it into a shell; touching a still
  shell kicks it into a fast slide that mows down other enemies; a moving shell
  is dangerous until stomped again.
* :class:`Flyer` — hovers along a horizontal patrol bobbing on a sine wave,
  ignoring gravity. A stomp pops it.

All inherit movement/collision from :class:`PhysicsEntity` and share the
patrol/turn logic in :class:`EnemyBase`.
"""

from __future__ import annotations

import math

import pygame

import config
from src.entities.entity import PhysicsEntity
from src.utils.animation import Animation

T = config.TILE_SIZE


class EnemyBase(PhysicsEntity):
    score = config.ENEMY_SCORE

    def __init__(self, x, y, w, h, assets, audio, particles):
        super().__init__(x, y, w, h)
        self.assets = assets
        self.audio = audio
        self.particles = particles
        self.speed = 1.4
        self.facing = -1
        self.state = "walk"
        self.dangerous = True   # hurts player on side contact
        self.stompable = True
        self.remove_timer = 0.0
        self.poof_color = (150, 95, 55)

    def _patrol(self, level):
        """Walk back and forth, turning at walls and avoiding ledges."""
        self.vel.x = self.speed * self.facing
        # Turn at walls.
        if self.collisions["left"]:
            self.facing = 1
        elif self.collisions["right"]:
            self.facing = -1
        # Avoid walking off ledges: probe the tile just ahead of the feet.
        if self.on_ground:
            probe_x = self.rect.centerx + self.facing * (self.rect.width // 2 + 2)
            probe_y = self.rect.bottom + 4
            if not level.is_solid_pixel(probe_x, probe_y):
                self.facing *= -1

    def defeat(self, by="stomp"):
        """Remove this enemy with a poof of particles."""
        self.particles.enemy_poof(self.rect.centerx, self.rect.centery, self.poof_color)
        self.alive = False

    def update(self, dt, level):
        if not self.alive:
            return
        if self.remove_timer > 0:
            self.remove_timer -= dt
            if self.remove_timer <= 0:
                self.alive = False
            return
        self._behaviour(dt, level)

    def _behaviour(self, dt, level):
        self._patrol(level)
        self.move_and_collide(level)

    def draw(self, surface, camera):
        frame = self._frame()
        draw_rect = frame.get_rect()
        draw_rect.midbottom = (self.rect.centerx, self.rect.bottom + 2)
        surface.blit(frame, camera.apply(draw_rect))

    def _frame(self):  # overridden
        raise NotImplementedError


class Goomba(EnemyBase):
    def __init__(self, x, y, assets, audio, particles):
        super().__init__(x, y, 40, 38, assets, audio, particles)
        frames = assets.enemies["goomba"]
        self.anim = Animation(frames["walk"], fps=6)
        self.squashed_frame = frames["squashed"][0]
        self.speed = 1.3
        self.poof_color = config.GOOMBA_BODY

    def _behaviour(self, dt, level):
        super()._behaviour(dt, level)
        self.anim.update(dt)

    def stomp(self, player):
        """Player landed on top: squash flat and award score."""
        self.state = "squashed"
        self.dangerous = False
        self.stompable = False
        self.vel.x = 0
        self.remove_timer = 0.4
        self.audio.play("stomp")
        return self.score

    def _frame(self):
        if self.state == "squashed":
            return self.squashed_frame
        return self.anim.get_frame(flip_x=(self.facing > 0))


class Koopa(EnemyBase):
    SHELL_SPEED = 8.0

    def __init__(self, x, y, assets, audio, particles):
        super().__init__(x, y, 36, 52, assets, audio, particles)
        frames = assets.enemies["koopa"]
        self.walk_anim = Animation(frames["walk"], fps=5)
        self.shell_anim = Animation(frames["shell"], fps=14)
        self.speed = 1.1
        self.poof_color = config.KOOPA_SHELL

    def _behaviour(self, dt, level):
        if self.state == "walk":
            self._patrol(level)
            self.move_and_collide(level)
            self.walk_anim.update(dt)
        elif self.state == "shell":
            # Stationary shell still obeys gravity.
            self.vel.x = 0
            self.move_and_collide(level)
        elif self.state == "shell_move":
            self.vel.x = self.SHELL_SPEED * self.facing
            self.move_and_collide(level)
            if self.collisions["left"]:
                self.facing = 1
            elif self.collisions["right"]:
                self.facing = -1
            self.shell_anim.update(dt)

    def _enter_shell(self):
        old_bottom = self.rect.bottom
        self.rect.height = 36
        self.rect.bottom = old_bottom
        self.pos.update(self.rect.x, self.rect.y)
        self.state = "shell"
        self.dangerous = False

    def stomp(self, player):
        if self.state == "walk":
            self._enter_shell()
            self.audio.play("stomp")
            return self.score
        if self.state == "shell_move":
            # Stop a moving shell.
            self.state = "shell"
            self.dangerous = False
            self.vel.x = 0
            self.audio.play("stomp")
            return 0
        # Stomping a still shell kicks it.
        return self.kick(player.rect.centerx)

    def kick(self, from_x):
        """Send a still shell sliding away from ``from_x``."""
        if self.state != "shell":
            return 0
        self.facing = 1 if self.rect.centerx >= from_x else -1
        self.state = "shell_move"
        self.dangerous = True
        self.audio.play("stomp")
        return 0

    def side_contact(self, player):
        """Resolve a non-stomp collision. Returns "kick", "damage" or None."""
        if self.state == "shell":
            self.kick(player.rect.centerx)
            return "kick"
        if self.state == "shell_move":
            return "damage"
        return "damage"

    def _frame(self):
        if self.state == "walk":
            return self.walk_anim.get_frame(flip_x=(self.facing > 0))
        return self.shell_anim.current_frame


class Flyer(EnemyBase):
    def __init__(self, x, y, assets, audio, particles, span_tiles=4):
        super().__init__(x, y, 44, 34, assets, audio, particles)
        self.anim = Animation(assets.enemies["flyer"]["fly"], fps=8)
        self.gravity_scale = 0.0  # flyers ignore gravity
        self.base_y = float(y)
        self.span = span_tiles * T
        self.start_x = float(x)
        self.speed = 1.8
        self.phase = 0.0
        self.poof_color = config.FLYER_BODY

    def _behaviour(self, dt, level):
        self.phase += dt
        # Horizontal patrol within span.
        self.pos.x += self.speed * self.facing
        if self.pos.x > self.start_x + self.span:
            self.facing = -1
        elif self.pos.x < self.start_x - self.span:
            self.facing = 1
        # Sine-wave bob.
        self.pos.y = self.base_y + math.sin(self.phase * 3.0) * 26
        self.sync_rect()
        self.anim.update(dt)

    def stomp(self, player):
        self.audio.play("stomp")
        self.defeat()
        return self.score

    def _frame(self):
        return self.anim.get_frame(flip_x=(self.facing > 0))
