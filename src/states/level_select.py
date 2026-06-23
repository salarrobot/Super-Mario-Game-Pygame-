"""
level_select.py
===============

Lets the player jump straight into any level they have unlocked. Locked levels
are shown greyed out, and each unlocked level displays its best completion time
pulled from the save file.
"""

from __future__ import annotations

import pygame

import config
from src.states.base import State
from src.ui.widgets import Button, Menu, draw_text


class LevelSelectState(State):
    def enter(self, **kwargs):
        self.backdrop = self.game.menu_backdrop
        self.title_font = self.game.assets.get_font(48)
        self.font = self.game.assets.get_font(26)
        self.small = self.game.assets.get_font(20)

        unlocked = self.game.save.data["unlocked_level"]
        cx = config.RENDER_WIDTH // 2
        buttons = []
        for i, meta in enumerate(self.game.level_meta):
            num = i + 1
            label = f"{num}.  {meta['name']}"
            btn = Button(label, (cx, 190 + i * 64), self._make_play(num), width=420)
            btn.enabled = num <= unlocked
            if not btn.enabled:
                btn.text = f"{num}.  LOCKED"
            buttons.append(btn)
        buttons.append(Button("BACK", (cx, 190 + len(self.game.level_meta) * 64 + 10),
                              self.manager.pop, width=200))
        self.menu = Menu(self.game.audio)
        self.menu.set_buttons(buttons)

    def _make_play(self, number):
        def _go():
            from src.states.play import PlayState
            self.manager.replace(PlayState(self.game), level_number=number, fresh=True)
        return _go

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.audio.play("blip")
            self.manager.pop()
            return
        self.menu.handle_event(event)

    def update(self, dt):
        self.backdrop.update(dt)

    def draw(self, surface):
        self.backdrop.draw(surface, with_hero=False)
        overlay = pygame.Surface((config.RENDER_WIDTH, config.RENDER_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 24, 120))
        surface.blit(overlay, (0, 0))

        cx = config.RENDER_WIDTH // 2
        draw_text(surface, self.title_font, "SELECT LEVEL", config.UI_ACCENT, center=(cx, 90))
        self.menu.draw(surface, self.font)

        # Best-time hint for the selected, unlocked level.
        sel = self.menu.index
        if sel < len(self.game.level_meta):
            best = self.game.save.data["best_times"].get(str(sel + 1))
            txt = f"Best time: {best:.1f}s" if best else "Not completed yet"
            draw_text(surface, self.small, txt, config.UI_MUTED,
                      center=(cx, config.RENDER_HEIGHT - 30), shadow=False)
