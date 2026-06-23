"""
player.py
=========

The hero, "Pip".

This class is where the game *feels* good or bad, so it implements the small
quality-of-life mechanics players expect from a modern platformer:

* **Acceleration / friction** instead of instant velocity for weighty control.
* **Variable jump height** — tapping jumps low, holding jumps high.
* **Coyote time** — a few frames of jump grace after walking off a ledge.
* **Jump buffering** — a jump pressed just before landing still fires.
* **Optional double jump.**
* Three power states (small / big / fire), damage with invincibility frames,
  and a star "invincible" mode.

The player delegates spawning fireballs and reacting to block hits back to the
owning play state via :attr:`controller`, keeping this class focused on the
character itself.
"""

from __future__ import annotations

import pygame

import config
from src.entities.entity import PhysicsEntity
from src.utils.animation import Animation

# Collision-box sizes per power state. The drawn sprite is larger than the box
# and is bottom-aligned so the character's feet always match the ground.
SIZES = {
    "small": (30, 42),
    "big": (38, 78),
    "fire": (38, 78),
}


class Player(PhysicsEntity):
    def __init__(self, x, y, assets, audio, particles, settings):
        self.state = "small"
        w, h = SIZES[self.state]
        # Spawn so the player's feet rest on the start tile.
        super().__init__(x, y, w, h)
        self.assets = assets
        self.audio = audio
        self.particles = particles
        self.settings = settings
        self.controller = None  # set by the play state for callbacks

        # Movement / jump bookkeeping
        self.jump_buffer = 0
        self.coyote = 0
        self.jumps_used = 0
        self.jump_held = False
        self.jump_hold_frames = 0
        self.crouching = False
        self.allow_double_jump = True

        # Status timers (in frames)
        self.invincible = 0
        self.star_timer = 0
        self.fireball_cooldown = 0
        self.dead = False
        self.victory = False

        # Flag the play state inspects to resolve block head-bumps.
        self.head_bump = False

        self._build_animations()

    # ------------------------------------------------------------ animation
    def _build_animations(self):
        frames = self.assets.players[self.state]
        self.anims = {
            "idle": Animation(frames["idle"], fps=5),
            "run": Animation(frames["run"], fps=12),
            "jump": Animation(frames["jump"], fps=1, loop=False),
            "fall": Animation(frames["fall"], fps=1, loop=False),
            "crouch": Animation(frames["crouch"], fps=1, loop=False),
        }
        self.current_anim = "idle"

    def _resize(self, new_state):
        """Change power state while keeping the feet planted."""
        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        self.state = new_state
        w, h = SIZES[new_state]
        self.rect.width, self.rect.height = w, h
        self.rect.bottom = old_bottom
        self.rect.centerx = old_centerx
        self.pos.update(self.rect.x, self.rect.y)
        self._build_animations()

    # --------------------------------------------------------------- events
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == self.settings.key_code("jump"):
                self.jump_buffer = config.JUMP_BUFFER
            elif event.key == self.settings.key_code("shoot"):
                self.try_shoot()

    # ----------------------------------------------------------- power-ups
    def apply_powerup(self, kind: str):
        if kind == "mushroom":
            if self.state == "small":
                self._resize("big")
            self.audio.play("powerup")
        elif kind == "fire_flower":
            self._resize("fire")
            self.audio.play("powerup")
        elif kind == "star":
            self.star_timer = config.STAR_TIME
            self.audio.play("powerup")
        if self.controller:
            self.controller.add_score(config.POWERUP_SCORE)

    def take_damage(self):
        """Returns True if the hit was lethal."""
        if self.invincible > 0 or self.star_timer > 0 or self.dead:
            return False
        if self.state == "fire":
            self._resize("big")
            self.invincible = config.INVINCIBLE_TIME
            self.audio.play("powerdown")
        elif self.state == "big":
            self._resize("small")
            self.invincible = config.INVINCIBLE_TIME
            self.audio.play("powerdown")
        else:
            self.die()
            return True
        return False

    def die(self):
        if self.dead:
            return
        self.dead = True
        self.alive = False
        self.vel.update(0, -14)  # classic little death hop
        self.audio.play("death")

    def bounce(self, strength=-12):
        """Bounce after stomping an enemy."""
        self.vel.y = strength
        self.on_ground = False

    # ---------------------------------------------------------------- shoot
    def try_shoot(self):
        if self.state != "fire" or self.fireball_cooldown > 0 or self.dead:
            return
        if self.controller is None:
            return
        self.fireball_cooldown = 18
        spawn_x = self.rect.centerx + self.facing * 18
        self.controller.spawn_fireball(spawn_x, self.rect.centery, self.facing)
        self.audio.play("fireball")

    # --------------------------------------------------------------- update
    def update(self, dt, level, keys):
        if self.dead:
            # Death animation: arc upward then fall straight through the world.
            self.pos.y += self.vel.y
            self.vel.y += config.GRAVITY
            self.sync_rect()
            return

        self._handle_input(keys)
        self._handle_jump()

        # Integrate physics & resolve collisions.
        self.move_and_collide(level)
        self.head_bump = self.collisions["top"] and not self.on_ground

        # Coyote time refreshes while grounded.
        if self.on_ground:
            self.coyote = config.COYOTE_TIME
            self.jumps_used = 0
        elif self.coyote > 0:
            self.coyote -= 1

        # Decay timers.
        if self.jump_buffer > 0:
            self.jump_buffer -= 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.star_timer > 0:
            self.star_timer -= 1
            self.particles.star_trail(self.rect.centerx, self.rect.centery)
        if self.fireball_cooldown > 0:
            self.fireball_cooldown -= 1

        self._update_animation(dt)

    def _handle_input(self, keys):
        left = keys[self.settings.key_code("left")]
        right = keys[self.settings.key_code("right")]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN]
        run = keys[self.settings.key_code("run")]
        self.jump_held = keys[self.settings.key_code("jump")]

        self.crouching = down and self.on_ground and self.state != "small"

        max_speed = config.PLAYER_MAX_SPEED * (1.4 if run else 1.0)
        if self.crouching:
            # Slide to a stop while crouching.
            self.vel.x += self.vel.x * config.PLAYER_FRICTION
        else:
            if left and not right:
                self.vel.x -= config.PLAYER_ACCEL
                self.facing = -1
            elif right and not left:
                self.vel.x += config.PLAYER_ACCEL
                self.facing = 1
            else:
                # Apply friction proportional to velocity for a smooth stop.
                self.vel.x += self.vel.x * config.PLAYER_FRICTION

        self.vel.x = max(-max_speed, min(max_speed, self.vel.x))
        if abs(self.vel.x) < 0.1:
            self.vel.x = 0

    def _handle_jump(self):
        want_jump = self.jump_buffer > 0
        can_ground_jump = self.on_ground or self.coyote > 0

        if want_jump and can_ground_jump:
            self.vel.y = config.PLAYER_JUMP_SPEED
            self.jumps_used = 1
            self.coyote = 0
            self.jump_buffer = 0
            self.jump_hold_frames = config.PLAYER_MAX_JUMP_HOLD
            self.audio.play("jump")
            self.particles.jump_dust(self.rect.centerx, self.rect.bottom)
        elif want_jump and self.allow_double_jump and self.jumps_used == 1 and not self.on_ground:
            self.vel.y = config.PLAYER_DOUBLE_JUMP_SPEED
            self.jumps_used = 2
            self.jump_buffer = 0
            self.jump_hold_frames = config.PLAYER_MAX_JUMP_HOLD
            self.audio.play("double_jump")
            self.particles.jump_dust(self.rect.centerx, self.rect.bottom)

        # Variable jump height: keep accelerating up a little while held,
        # and cut the jump short when released early.
        if self.jump_held and self.jump_hold_frames > 0 and self.vel.y < 0:
            self.jump_hold_frames -= 1
        elif not self.jump_held and self.vel.y < 0:
            self.vel.y *= 0.55
            self.jump_hold_frames = 0

    def _update_animation(self, dt):
        if not self.on_ground:
            self.current_anim = "jump" if self.vel.y < 0 else "fall"
        elif self.crouching:
            self.current_anim = "crouch"
        elif abs(self.vel.x) > 0.5:
            self.current_anim = "run"
        else:
            self.current_anim = "idle"
        anim = self.anims[self.current_anim]
        # Speed the run cycle up with horizontal speed for a lively gait.
        if self.current_anim == "run":
            anim.frame_duration = 1.0 / max(6.0, abs(self.vel.x) * 2.2)
        anim.update(dt)

    # ---------------------------------------------------------------- draw
    def draw(self, surface, camera):
        # Flicker while invincible (skip drawing on alternate frames).
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            return
        frame = self.anims[self.current_anim].get_frame(flip_x=(self.facing < 0))
        # Bottom-align the (taller) sprite on the collision box.
        draw_rect = frame.get_rect()
        draw_rect.midbottom = (self.rect.centerx, self.rect.bottom + 2)
        screen_rect = camera.apply(draw_rect)

        if self.star_timer > 0:
            # Cycle a bright tint while the star is active.
            tinted = frame.copy()
            hue = (pygame.time.get_ticks() // 60) % 3
            tint = [config.YELLOW, config.WHITE, config.RED][hue]
            tinted.fill((*tint, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(tinted, screen_rect)
        else:
            surface.blit(frame, screen_rect)
