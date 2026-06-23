"""
gameover.py
===========

Shown when the player runs out of lives. Displays the final score (flagging a
new high score) and offers a fresh run or a trip back to the main menu.
"""

from __future__ import annotations

import pygame

import config
from src.states.base import State
from src.ui.widgets import Button, Menu, draw_text


class GameOverState(State):
    def enter(self, score=0, **kwargs):
        self.score = score
        self.new_high = (score >= self.game.save.data["high_score"])
        self.font = self.game.assets.get_font(30)
        self.title_font = self.game.assets.get_font(64)
        self.small = self.game.assets.get_font(22)
        self.t = 0.0

        self.game.audio.stop_music()
        self.game.audio.play_jingle("gameover")

        cx = config.RENDER_WIDTH // 2
        self.menu = Menu(self.game.audio)
        self.menu.set_buttons([
            Button("TRY AGAIN", (cx, 340), self._retry),
            Button("MAIN MENU", (cx, 408), self._menu),
        ])

    def _retry(self):
        from src.states.play import PlayState
        self.manager.replace(PlayState(self.game), level_number=1, fresh=True)

    def _menu(self):
        from src.states.menu import MenuState
        self.manager.replace(MenuState(self.game))

    def handle_event(self, event):
        self.menu.handle_event(event)

    def update(self, dt):
        self.t += dt

    def draw(self, surface):
        surface.fill((14, 12, 24))
        cx = config.RENDER_WIDTH // 2
        draw_text(surface, self.title_font, "GAME OVER", config.RED, center=(cx, 150))
        draw_text(surface, self.font, f"FINAL SCORE   {self.score:06d}",
                  config.UI_TEXT, center=(cx, 240))
        if self.new_high:
            # Blink a "new record" banner.
            if int(self.t * 2) % 2 == 0:
                draw_text(surface, self.small, "NEW HIGH SCORE!", config.YELLOW,
                          center=(cx, 282))
        self.menu.draw(surface, self.font)
