"""
settings.py
===========

The settings screen. Exposes everything persisted in ``settings.json``:

* music / SFX volume sliders,
* fullscreen and FPS-counter toggles,
* fully remappable controls (select a binding, press a key),
* and a "reset progress" action that wipes the save file.

Rows are a simple list of typed dicts; navigation moves between them and the
behaviour of Left/Right/Enter depends on the focused row's type. Changes are
applied live and saved immediately.
"""

from __future__ import annotations

import pygame

import config
from src.states.base import State
from src.ui.widgets import Slider, draw_text


class SettingsState(State):
    ACTIONS = ["left", "right", "jump", "run", "shoot", "pause"]

    def enter(self, **kwargs):
        self.backdrop = self.game.menu_backdrop
        self.title_font = self.game.assets.get_font(46)
        self.font = self.game.assets.get_font(24)
        self.small = self.game.assets.get_font(18)
        self.settings = self.game.settings

        cx = config.RENDER_WIDTH // 2
        self.music_slider = Slider("Music Volume", (cx, 0), self.settings["music_volume"])
        self.sfx_slider = Slider("SFX Volume", (cx, 0), self.settings["sfx_volume"])

        # Build the navigable rows.
        self.rows = [
            {"type": "slider", "slider": self.music_slider, "key": "music_volume"},
            {"type": "slider", "slider": self.sfx_slider, "key": "sfx_volume"},
            {"type": "toggle", "label": "Fullscreen", "key": "fullscreen"},
            {"type": "toggle", "label": "Show FPS", "key": "show_fps"},
        ]
        for action in self.ACTIONS:
            self.rows.append({"type": "keybind", "action": action})
        self.rows.append({"type": "action", "label": "RESET PROGRESS", "fn": self._reset})
        self.rows.append({"type": "action", "label": "BACK", "fn": self._back})

        self.index = 0
        self.listening = False  # capturing a key for a rebind

    # --- actions -----------------------------------------------------------
    def _reset(self):
        self.game.save.reset()
        self.game.audio.play("confirm")

    def _back(self):
        self.settings.save()
        self.game.audio.play("blip")
        self.manager.pop()

    def _apply_volumes(self):
        self.settings["music_volume"] = self.music_slider.value
        self.settings["sfx_volume"] = self.sfx_slider.value
        self.game.audio.set_music_volume(self.music_slider.value)
        self.game.audio.set_sfx_volume(self.sfx_slider.value)
        self.settings.save()

    # --- input -------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        # Rebind capture mode swallows the next key press.
        if self.listening:
            if event.key != pygame.K_ESCAPE:
                action = self.rows[self.index]["action"]
                self.settings.set_control(action, pygame.key.name(event.key))
                self.game.audio.play("confirm")
            self.listening = False
            return

        if event.key == pygame.K_ESCAPE:
            self._back()
            return

        row = self.rows[self.index]
        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(self.rows)
            self.game.audio.play("blip")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(self.rows)
            self.game.audio.play("blip")
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._adjust(row, -1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust(row, +1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            self._activate(row)

    def _adjust(self, row, direction):
        if row["type"] == "slider":
            row["slider"].adjust(0.05 * direction)
            self._apply_volumes()
        elif row["type"] == "toggle":
            self._toggle(row)

    def _activate(self, row):
        if row["type"] == "action":
            row["fn"]()
        elif row["type"] == "toggle":
            self._toggle(row)
        elif row["type"] == "keybind":
            self.listening = True
            self.game.audio.play("blip")

    def _toggle(self, row):
        key = row["key"]
        self.settings[key] = not self.settings[key]
        self.settings.save()
        if key == "fullscreen":
            self.game.set_fullscreen(self.settings[key])
        self.game.audio.play("blip")

    def update(self, dt):
        self.backdrop.update(dt)

    # --- draw --------------------------------------------------------------
    def draw(self, surface):
        self.backdrop.draw(surface, with_hero=False)
        overlay = pygame.Surface((config.RENDER_WIDTH, config.RENDER_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 24, 150))
        surface.blit(overlay, (0, 0))

        cx = config.RENDER_WIDTH // 2
        draw_text(surface, self.title_font, "SETTINGS", config.UI_ACCENT, center=(cx, 50))

        y = 110
        for i, row in enumerate(self.rows):
            focused = (i == self.index)
            color = config.UI_ACCENT if focused else config.UI_TEXT
            if row["type"] == "slider":
                row["slider"].rect.center = (cx, y + 8)
                row["slider"].selected = focused
                row["slider"].draw(surface, self.small)
                y += 44
            elif row["type"] == "toggle":
                state = "ON" if self.settings[row["key"]] else "OFF"
                self._row_text(surface, f"{row['label']}", f"< {state} >", y, color, focused)
                y += 32
            elif row["type"] == "keybind":
                action = row["action"]
                name = self.settings["controls"][action].upper()
                value = "PRESS A KEY..." if (focused and self.listening) else name
                self._row_text(surface, action.capitalize(), value, y, color, focused)
                y += 32
            elif row["type"] == "action":
                draw_text(surface, self.font, row["label"], color, center=(cx, y + 6), shadow=False)
                if focused:
                    pygame.draw.polygon(surface, config.UI_ACCENT,
                                        [(cx - 130, y + 6 - 8), (cx - 118, y + 6), (cx - 130, y + 6 + 8)])
                y += 34

        draw_text(surface, self.small,
                  "Up/Down move  -  Left/Right adjust  -  Enter select/rebind  -  Esc back",
                  config.UI_MUTED, center=(cx, config.RENDER_HEIGHT - 20), shadow=False)

    def _row_text(self, surface, label, value, y, color, focused):
        cx = config.RENDER_WIDTH // 2
        draw_text(surface, self.font, label, color, topleft=(cx - 230, y), shadow=False)
        draw_text(surface, self.font, value, color, topleft=(cx + 60, y), shadow=False)
        if focused:
            pygame.draw.polygon(surface, config.UI_ACCENT,
                                [(cx - 255, y + 12 - 7), (cx - 244, y + 12), (cx - 255, y + 12 + 7)])
