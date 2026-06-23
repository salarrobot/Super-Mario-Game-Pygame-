"""
victory.py
==========

The end-of-game celebration shown after the final level is cleared: a confetti
shower over the score summary, with options to play again or return to the menu.
"""

from __future__ import annotations

import random

import pygame

import config
from src.core.particles import ParticleSystem
from src.states.base import State
from src.ui.widgets import Button, Menu, draw_text


class _StaticCam:
    """Particles are drawn in world space; victory confetti is in screen space,
    so a zero-offset camera makes ``apply_point`` an identity transform."""
    @property
    def total_offset(self):
        return pygame.Vector2(0, 0)

    def apply_point(self, x, y):
        return x, y


class VictoryState(State):
    def enter(self, score=0, lives=0, **kwargs):
        self.score = score
        self.lives = lives
        self.font = self.game.assets.get_font(30)
        self.title_font = self.game.assets.get_font(64)
        self.small = self.game.assets.get_font(22)
        self.particles = ParticleSystem()
        self.cam = _StaticCam()
        self.spawn_timer = 0.0

        self.game.save.record_score(score)
        self.game.audio.stop_music()
        self.game.audio.play_jingle("victory")

        cx = config.RENDER_WIDTH // 2
        self.menu = Menu(self.game.audio)
        self.menu.set_buttons([
            Button("PLAY AGAIN", (cx, 360), self._again),
            Button("MAIN MENU", (cx, 428), self._menu),
        ])

    def _again(self):
        from src.states.play import PlayState
        self.manager.replace(PlayState(self.game), level_number=1, fresh=True)

    def _menu(self):
        from src.states.menu import MenuState
        self.manager.replace(MenuState(self.game))

    def handle_event(self, event):
        self.menu.handle_event(event)

    def update(self, dt):
        # Rain confetti from the top of the screen.
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = 0.04
            for _ in range(6):
                x = random.uniform(0, config.RENDER_WIDTH)
                color = random.choice([config.RED, config.YELLOW, config.GREEN,
                                       config.BLUE, config.WHITE])
                self.particles.burst(x, -10, color, count=1, speed=2, life=2.2,
                                     size=7, gravity=0.12, spread=0.6,
                                     direction=1.57)
        self.particles.update(dt)

    def draw(self, surface):
        surface.fill((20, 24, 48))
        self.particles.draw(surface, self.cam)
        cx = config.RENDER_WIDTH // 2
        draw_text(surface, self.title_font, "YOU WIN!", config.YELLOW, center=(cx, 130))
        draw_text(surface, self.small, "Thanks for playing Super Pixel Quest!",
                  config.UI_TEXT, center=(cx, 200))
        draw_text(surface, self.font, f"FINAL SCORE   {self.score:06d}",
                  config.UI_TEXT, center=(cx, 260))
        draw_text(surface, self.small, f"Lives remaining: {self.lives}",
                  config.UI_MUTED, center=(cx, 300))
        self.menu.draw(surface, self.font)
