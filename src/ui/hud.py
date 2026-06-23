"""
hud.py
======

The heads-up display drawn over the gameplay each frame: score, coin counter,
remaining lives (as heart icons), the level timer, an FPS readout and the
current power state. It draws in screen space (never offset by the camera) and
reads plain values passed in by the play state, so it stays decoupled from game
logic.
"""

from __future__ import annotations

import pygame

import config
from src.ui.widgets import draw_text


class HUD:
    def __init__(self, assets):
        self.assets = assets
        self.font = assets.get_font(26)
        self.small = assets.get_font(20)

    def _panel(self, surface, rect):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((*config.UI_PANEL, 170))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, (*config.UI_ACCENT, 90), rect, width=2, border_radius=8)

    def draw(self, surface, *, score, coins, lives, time_left, fps,
             show_fps, power):
        w = config.RENDER_WIDTH

        # Top-left: score & coins.
        self._panel(surface, pygame.Rect(12, 12, 240, 76))
        draw_text(surface, self.font, f"SCORE", config.UI_MUTED, topleft=(24, 18), shadow=False)
        draw_text(surface, self.font, f"{score:06d}", config.UI_TEXT, topleft=(24, 44), shadow=False)
        surface.blit(self.assets.icons["coin"], (150, 20))
        draw_text(surface, self.font, f"x{coins:02d}", config.UI_ACCENT, topleft=(182, 20), shadow=False)
        draw_text(surface, self.small, power.upper(), config.GREEN, topleft=(150, 54), shadow=False)

        # Top-center: timer.
        self._panel(surface, pygame.Rect(w // 2 - 80, 12, 160, 50))
        tcol = config.RED if time_left <= 30 else config.UI_TEXT
        draw_text(surface, self.font, f"TIME {int(time_left):03d}", tcol,
                  center=(w // 2, 37), shadow=False)

        # Top-right: lives.
        panel = pygame.Rect(w - 12 - 200, 12, 200, 50)
        self._panel(surface, panel)
        draw_text(surface, self.font, "LIVES", config.UI_MUTED, topleft=(panel.x + 12, 24), shadow=False)
        for i in range(max(0, lives)):
            surface.blit(self.assets.icons["heart"], (panel.x + 92 + i * 32, 22))

        # FPS counter (optional).
        if show_fps:
            draw_text(surface, self.small, f"{int(fps)} FPS", config.UI_MUTED,
                      topleft=(12, config.RENDER_HEIGHT - 28), shadow=False)
