"""
menu.py
=======

The main menu: an animated title over the shared scrolling backdrop with
keyboard/mouse-navigable buttons leading into the rest of the game.
"""

from __future__ import annotations

import math

import pygame

import config
from src.states.base import State
from src.ui.backdrop import MenuBackdrop
from src.ui.widgets import Button, Menu, draw_text


class MenuState(State):
    def enter(self, **kwargs):
        self.backdrop = self.game.menu_backdrop
        self.title_font = self.game.assets.get_font(64)
        self.font = self.game.assets.get_font(30)
        self.small = self.game.assets.get_font(20)
        self.t = 0.0

        cx = config.RENDER_WIDTH // 2
        self.menu = Menu(self.game.audio)
        self.menu.set_buttons([
            Button("PLAY", (cx, 250), self._play),
            Button("LEVEL SELECT", (cx, 318), self._levels),
            Button("SETTINGS", (cx, 386), self._settings),
            Button("QUIT", (cx, 454), self.game.quit),
        ])
        self.game.audio.play_music("menu")

    # --- button callbacks --------------------------------------------------
    def _play(self):
        from src.states.play import PlayState
        self.manager.replace(PlayState(self.game), level_number=1, fresh=True)

    def _levels(self):
        from src.states.level_select import LevelSelectState
        self.manager.push(LevelSelectState(self.game))

    def _settings(self):
        from src.states.settings import SettingsState
        self.manager.push(SettingsState(self.game))

    # --- loop --------------------------------------------------------------
    def resume(self):
        self.game.audio.play_music("menu")

    def handle_event(self, event):
        self.menu.handle_event(event)

    def update(self, dt):
        self.t += dt
        self.backdrop.update(dt)

    def draw(self, surface):
        self.backdrop.draw(surface, with_hero=True)

        cx = config.RENDER_WIDTH // 2
        bob = math.sin(self.t * 2) * 6
        draw_text(surface, self.title_font, "SUPER PIXEL", config.YELLOW,
                  center=(cx, int(110 + bob)))
        draw_text(surface, self.title_font, "QUEST", config.WHITE,
                  center=(cx, int(170 + bob)))

        self.menu.draw(surface, self.font)

        hs = self.game.save.data["high_score"]
        draw_text(surface, self.small, f"HIGH SCORE  {hs:06d}", config.UI_MUTED,
                  center=(cx, config.RENDER_HEIGHT - 24), shadow=False)
        draw_text(surface, self.small, "Arrow keys / WASD to navigate  -  Enter to select",
                  config.UI_MUTED, center=(cx, config.RENDER_HEIGHT - 48), shadow=False)
