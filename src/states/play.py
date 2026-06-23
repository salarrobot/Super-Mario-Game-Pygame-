"""
play.py
=======

The gameplay state — the conductor that owns a live level and drives every
system each frame: input, physics updates for the player/enemies/items, all the
inter-entity collision rules (stomps, shells, fireballs, coins, power-ups, block
bumps, checkpoints and the goal), the score/lives/time bookkeeping, the camera,
particles and HUD, plus the death and level-complete sequences.

It also acts as the *controller* the player calls back into (``spawn_fireball``,
``add_score``), which keeps the entity classes ignorant of game-wide concerns.
"""

from __future__ import annotations

import os

import pygame

import config
from src.core.camera import Camera
from src.core.particles import ParticleSystem
from src.entities.enemies import Koopa
from src.entities.fireball import Fireball
from src.entities.player import Player
from src.states.base import State
from src.ui.hud import HUD
from src.ui.widgets import draw_text
from src.world.level import Level

T = config.TILE_SIZE


class PlayState(State):
    def enter(self, level_number=1, fresh=True, carry=None, **kwargs):
        self.level_number = level_number
        self.assets = self.game.assets
        self.audio = self.game.audio

        # Run-wide stats carry across levels and lives.
        carry = carry or {}
        self.score = carry.get("score", 0)
        self.coins = carry.get("coins", 0)
        self.lives = carry.get("lives", config.START_LIVES)

        self.hud = HUD(self.assets)
        self.checkpoint_pos = None
        self._load_level()

    # ------------------------------------------------------------ loading
    def _load_level(self):
        meta = self.game.level_meta[self.level_number - 1]
        self.particles = ParticleSystem()
        self.level = Level.from_file(meta["file"], self.assets, self.audio, self.particles)
        self.camera = Camera(self.level.pixel_width, self.level.pixel_height)
        self.fireballs = []

        # Spawn the player at the active checkpoint, else the level start.
        if self.checkpoint_pos:
            cx, bottom = self.checkpoint_pos
        else:
            col, row = self.level.player_start
            cx, bottom = col * T + T // 2, (row + 1) * T
        self.player = Player(0, 0, self.assets, self.audio, self.particles, self.game.settings)
        self.player.rect.midbottom = (cx, bottom)
        self.player.pos.update(self.player.rect.x, self.player.rect.y)
        self.player.controller = self

        self.time_left = float(self.level.time_limit)
        self.completing = False
        self.complete_timer = 0.0
        self.dying = False
        self.death_timer = 0.0
        self.camera.snap_to(self.player.rect)
        self.audio.play_music(self.level.music)

    # -------------------------------------------------- controller callbacks
    def add_score(self, amount):
        self.score = max(0, self.score + amount)

    def spawn_fireball(self, x, y, direction):
        if len(self.fireballs) < 2:
            self.fireballs.append(Fireball(x, y, direction, self.assets, self.particles))

    def _gain_coin(self, n=1):
        self.coins += n
        self.add_score(config.COIN_SCORE * n)
        if self.coins >= 100:
            self.coins -= 100
            self.lives += 1
            self.audio.play("oneup")

    # ------------------------------------------------------------- events
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == self.game.settings.key_code("pause"):
            if not self.dying and not self.completing:
                from src.states.pause import PauseState
                self.manager.push(PauseState(self.game))
            return
        if not self.dying and not self.completing:
            self.player.handle_event(event)

    def resume(self):
        # Returning from the pause menu: make sure music is playing again.
        self.audio.play_music(self.level.music)

    # ------------------------------------------------------------- update
    def update(self, dt):
        # Cap dt so a hitch (e.g. window drag) can't fling entities through walls.
        dt = min(dt, 1 / 30)

        if self.completing:
            self._update_completing(dt)
            return
        if self.dying:
            self._update_dying(dt)
            return

        keys = pygame.key.get_pressed()

        # Countdown timer.
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.player.die()

        self.level.update(dt)
        self.player.update(dt, self.level, keys)
        for e in self.level.enemies:
            e.update(dt, self.level)
        for p in self.level.powerups:
            p.update(dt, self.level)
        for f in self.fireballs:
            f.update(dt, self.level)
        self.particles.update(dt)

        self._resolve_collisions()
        self._cleanup()

        # Keep the player inside the world horizontally.
        if self.player.pos.x < 0:
            self.player.pos.x = 0
            self.player.sync_rect()

        # Falling into a pit is fatal.
        if not self.player.dead and self.player.rect.top > self.level.pixel_height:
            self.player.die()

        if self.player.dead:
            self._begin_dying()

        self.camera.update(dt, self.player.rect, self.player.facing)

    # ---------------------------------------------------- collision rules
    def _resolve_collisions(self):
        self._bump_blocks()
        self._coins_and_items()
        self._enemy_interactions()
        self._fireball_hits()
        self._shell_hits()
        self._checkpoints_and_goal()

    def _bump_blocks(self):
        """When the player's head hits a block, trigger its effect."""
        if not self.player.head_bump:
            return
        row = (self.player.rect.top - 1) // T
        for col in range(self.player.rect.left // T, self.player.rect.right // T + 1):
            block = self.level.block_at(col, row)
            if not block or not block.active:
                continue
            from src.world.tiles import BrickBlock, QuestionBlock
            if isinstance(block, QuestionBlock):
                content = block.hit()
                if content == "coin":
                    self._gain_coin()
                    self.audio.play("coin")
                    self.particles.coin_sparkle(block.rect.centerx, block.rect.top)
                elif content:
                    self.level.spawn_powerup(content, block.col, block.row - 1)
                break
            elif isinstance(block, BrickBlock):
                result = block.hit(self.player.state != "small")
                if result == "break":
                    self.audio.play("break")
                    self.particles.brick_debris(block.rect.centerx, block.rect.centery)
                    self.camera.shake(6, 0.2)
                    self.add_score(50)
                elif result == "coin":
                    self._gain_coin()
                    self.audio.play("coin")
                    self.particles.coin_sparkle(block.rect.centerx, block.rect.top)
                else:
                    self.audio.play("bump")
                break

    def _coins_and_items(self):
        for coin in self.level.coins:
            if not coin.collected and self.player.rect.colliderect(coin.rect):
                coin.collected = True
                self._gain_coin()
                self.audio.play("coin")
                self.particles.coin_sparkle(coin.rect.centerx, coin.rect.centery)
        for item in self.level.powerups:
            if item.alive and not item.emerging and self.player.rect.colliderect(item.rect):
                item.alive = False
                self.player.apply_powerup(item.kind)

    def _enemy_interactions(self):
        for e in self.level.enemies:
            if not e.alive or not self.player.rect.colliderect(e.rect):
                continue
            # Star mode obliterates anything on contact.
            if self.player.star_timer > 0:
                e.defeat()
                self.add_score(e.score)
                self.audio.play("stomp")
                continue
            stomped = (self.player.vel.y > 0 and
                       self.player.rect.bottom <= e.rect.centery + 8)
            if stomped and e.stompable:
                gained = e.stomp(self.player)
                self.add_score(gained)
                self.player.bounce()
            else:
                self._player_hit_enemy(e)

    def _player_hit_enemy(self, e):
        if isinstance(e, Koopa):
            result = e.side_contact(self.player)
            if result == "damage":
                self.player.take_damage()
                self.camera.shake(8, 0.25)
        else:
            if e.dangerous:
                self.player.take_damage()
                self.camera.shake(8, 0.25)

    def _fireball_hits(self):
        for f in self.fireballs:
            if not f.alive:
                continue
            for e in self.level.enemies:
                if e.alive and e.dangerous and f.rect.colliderect(e.rect):
                    e.defeat()
                    self.add_score(e.score)
                    self.audio.play("stomp")
                    f.pop()
                    break

    def _shell_hits(self):
        """A sliding Koopa shell knocks out anything it touches."""
        for shell in self.level.enemies:
            if not (isinstance(shell, Koopa) and shell.state == "shell_move"):
                continue
            for other in self.level.enemies:
                if other is shell or not other.alive:
                    continue
                if shell.rect.colliderect(other.rect):
                    other.defeat()
                    self.add_score(other.score)
                    self.audio.play("stomp")

    def _checkpoints_and_goal(self):
        for cp in self.level.checkpoints:
            if not cp.activated and self.player.rect.colliderect(cp.rect):
                cp.activated = True
                self.checkpoint_pos = (cp.rect.centerx, cp.rect.bottom)
                self.audio.play("checkpoint")
                self.particles.coin_sparkle(cp.rect.centerx, cp.rect.top)
        if self.level.goal and not self.completing and \
                self.player.rect.colliderect(self.level.goal.rect):
            self._begin_completing()

    def _cleanup(self):
        self.level.enemies = [e for e in self.level.enemies if e.alive]
        self.level.powerups = [p for p in self.level.powerups if p.alive]
        self.level.coins = [c for c in self.level.coins if not c.collected]
        self.fireballs = [f for f in self.fireballs if f.alive]

    # ------------------------------------------------ sequences: death/win
    def _begin_dying(self):
        if self.dying:
            return
        self.dying = True
        self.death_timer = 2.0
        self.audio.stop_music()

    def _update_dying(self, dt):
        self.player.update(dt, self.level, pygame.key.get_pressed())
        self.particles.update(dt)
        self.death_timer -= dt
        if self.death_timer <= 0:
            self.lives -= 1
            if self.lives < 0:
                self.game.save.record_score(self.score)
                from src.states.gameover import GameOverState
                self.manager.replace(GameOverState(self.game), score=self.score)
            else:
                self._load_level()  # respawn at checkpoint, stats retained

    def _begin_completing(self):
        self.completing = True
        self.complete_timer = 3.0
        self.level.goal.lower_flag()
        self.add_score(config.FLAG_SCORE)
        self.audio.stop_music()
        self.audio.play_jingle("victory")

    def _update_completing(self, dt):
        self.level.update(dt)
        self.particles.update(dt)
        # Convert remaining time into bonus points over the sequence.
        if self.time_left > 0:
            drain = min(self.time_left, 120 * dt)
            self.time_left -= drain
            self.add_score(int(drain * 50))
            if int(self.time_left * 10) % 2 == 0:
                self.audio.play("coin")
        # Stroll the hero forward for flourish.
        self.player.facing = 1
        self.player.vel.x = 3
        self.player.move_and_collide(self.level)
        self.player._update_animation(dt)
        self.camera.update(dt, self.player.rect, 1)

        self.complete_timer -= dt
        if self.complete_timer <= 0:
            self._finish_level()

    def _finish_level(self):
        time_taken = self.level.time_limit - self.time_left
        self.game.save.record_time(self.level_number, time_taken)
        self.game.save.record_score(self.score)
        self.game.save.add_coins(0)
        next_number = self.level_number + 1
        carry = {"score": self.score, "coins": self.coins, "lives": self.lives}
        if next_number <= len(self.game.level_meta):
            self.game.save.unlock_level(next_number)
            self.checkpoint_pos = None
            self.manager.replace(PlayState(self.game),
                                 level_number=next_number, carry=carry)
        else:
            from src.states.victory import VictoryState
            self.manager.replace(VictoryState(self.game),
                                 score=self.score, lives=self.lives)

    # --------------------------------------------------------------- draw
    def draw(self, surface):
        self.level.draw_background(surface, self.camera)
        self.level.draw_world(surface, self.camera)
        for item in self.level.powerups:
            item.draw(surface, self.camera)
        for e in self.level.enemies:
            e.draw(surface, self.camera)
        for f in self.fireballs:
            f.draw(surface, self.camera)
        self.player.draw(surface, self.camera)
        self.particles.draw(surface, self.camera)

        # Soft vignette for a touch of lighting depth.
        if self.game.vignette is not None:
            surface.blit(self.game.vignette, (0, 0))

        self.hud.draw(surface, score=self.score, coins=self.coins,
                      lives=self.lives, time_left=self.time_left,
                      fps=self.game.clock.get_fps(),
                      show_fps=self.game.settings["show_fps"],
                      power=self.player.state)

        if self.completing:
            cx = config.RENDER_WIDTH // 2
            draw_text(surface, self.assets.get_font(54), "LEVEL CLEAR!",
                      config.YELLOW, center=(cx, 160))
