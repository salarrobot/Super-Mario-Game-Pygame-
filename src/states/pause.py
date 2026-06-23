"""
pause.py
========

A translucent pause overlay pushed on top of (and drawn over) the frozen
gameplay. Because it is ``transparent`` the state manager keeps rendering the
play state beneath it. Music is paused on entry and resumed on exit.
"""

from __future__ import annotations

import pygame

import config
from src.states.base import State
from src.states.play import PlayState
from src.ui.widgets import Button, Menu, draw_text


class PauseState(State):
    transparent = True

    def enter(self, **kwargs):
        self.play = self.manager.stack[-2]  # the PlayState we paused
        self.font = self.game.assets.get_font(30)
        self.title_font = self.game.assets.get_font(56)
        self.game.audio.pause_music()

        cx = config.RENDER_WIDTH // 2
        self.menu = Menu(self.game.audio)
        self.menu.set_buttons([
            Button("RESUME", (cx, 250), self.manager.pop),
            Button("RESTART LEVEL", (cx, 318), self._restart),
            Button("SETTINGS", (cx, 386), self._settings),
            Button("MAIN MENU", (cx, 454), self._main_menu),
        ])

    def exit(self):
        self.game.audio.unpause_music()

    def _restart(self):
        carry = {"score": self.play.score, "coins": self.play.coins, "lives": self.play.lives}
        self.game.audio.unpause_music()
        self.manager.replace(PlayState(self.game),
                             level_number=self.play.level_number, carry=carry)

    def _settings(self):
        from src.states.settings import SettingsState
        self.manager.push(SettingsState(self.game))

    def _main_menu(self):
        from src.states.menu import MenuState
        self.game.audio.unpause_music()
        self.game.audio.stop_music()
        self.manager.replace(MenuState(self.game))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == self.game.settings.key_code("pause"):
            self.manager.pop()
            return
        self.menu.handle_event(event)

    def draw(self, surface):
        overlay = pygame.Surface((config.RENDER_WIDTH, config.RENDER_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 22, 190))
        surface.blit(overlay, (0, 0))
        cx = config.RENDER_WIDTH // 2
        draw_text(surface, self.title_font, "PAUSED", config.UI_ACCENT, center=(cx, 150))
        self.menu.draw(surface, self.font)
