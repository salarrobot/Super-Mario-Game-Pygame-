"""
widgets.py
==========

Small reusable UI primitives used by every menu: a text helper, a clickable/
selectable :class:`Button`, and a :class:`Slider` for volume controls. They are
deliberately framework-light — each just knows how to draw itself and whether a
point is inside it; navigation and selection state live in the menu states.
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import pygame

import config


def draw_text(surface, font, text, color, center=None, topleft=None,
              shadow=True, shadow_color=(0, 0, 0)):
    """Render text with an optional drop shadow and return its rect."""
    if shadow:
        sh = font.render(text, True, shadow_color)
        if center:
            surface.blit(sh, sh.get_rect(center=(center[0] + 2, center[1] + 2)))
        elif topleft:
            surface.blit(sh, (topleft[0] + 2, topleft[1] + 2))
    img = font.render(text, True, color)
    if center:
        rect = img.get_rect(center=center)
    else:
        rect = img.get_rect(topleft=topleft or (0, 0))
    surface.blit(img, rect)
    return rect


class Button:
    def __init__(self, text: str, center: Tuple[int, int],
                 callback: Optional[Callable] = None, width=320, height=56):
        self.text = text
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center
        self.callback = callback
        self.selected = False
        self.enabled = True

    def hit(self, pos) -> bool:
        return self.enabled and self.rect.collidepoint(pos)

    def activate(self):
        if self.enabled and self.callback:
            self.callback()

    def draw(self, surface, font):
        # Panel with a highlighted border when selected.
        base = config.UI_PANEL if self.enabled else (40, 40, 52)
        col = base if not self.selected else (60, 64, 92)
        pygame.draw.rect(surface, (0, 0, 0), self.rect.move(3, 4), border_radius=12)
        pygame.draw.rect(surface, col, self.rect, border_radius=12)
        border = config.UI_ACCENT if self.selected else (70, 74, 100)
        pygame.draw.rect(surface, border, self.rect, width=3, border_radius=12)
        text_col = config.UI_TEXT if self.enabled else config.UI_MUTED
        draw_text(surface, font, self.text, text_col, center=self.rect.center, shadow=False)
        if self.selected:
            # Little selection arrow.
            ax = self.rect.left - 18
            ay = self.rect.centery
            pygame.draw.polygon(surface, config.UI_ACCENT,
                                [(ax, ay - 9), (ax + 12, ay), (ax, ay + 9)])


class Menu:
    """Manages keyboard/mouse navigation across a list of :class:`Button`.

    Centralizing this means every menu screen shares identical, predictable
    navigation (arrows/W-S to move, Enter/Space/click to confirm) and the same
    audio feedback, instead of each state re-implementing it.
    """

    def __init__(self, audio=None):
        self.audio = audio
        self.buttons = []
        self.index = 0

    def set_buttons(self, buttons):
        self.buttons = buttons
        self.index = 0
        self._first_enabled()
        self._sync()

    def _first_enabled(self):
        for i, b in enumerate(self.buttons):
            if b.enabled:
                self.index = i
                return

    def _sync(self):
        for i, b in enumerate(self.buttons):
            b.selected = (i == self.index)

    def _blip(self):
        if self.audio:
            self.audio.play("blip")

    def move(self, step):
        n = len(self.buttons)
        for _ in range(n):
            self.index = (self.index + step) % n
            if self.buttons[self.index].enabled:
                break
        self._sync()
        self._blip()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.move(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self._confirm()
        elif event.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.hit(event.pos):
                    if i != self.index:
                        self.index = i
                        self._sync()
                        self._blip()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for b in self.buttons:
                if b.hit(event.pos):
                    if self.audio:
                        self.audio.play("confirm")
                    b.activate()

    def _confirm(self):
        if self.buttons:
            if self.audio:
                self.audio.play("confirm")
            self.buttons[self.index].activate()

    def draw(self, surface, font):
        for b in self.buttons:
            b.draw(surface, font)


class Slider:
    def __init__(self, label: str, center: Tuple[int, int], value: float,
                 width=320):
        self.label = label
        self.value = value
        self.rect = pygame.Rect(0, 0, width, 18)
        self.rect.center = center
        self.selected = False

    @property
    def knob_x(self):
        return int(self.rect.left + self.value * self.rect.width)

    def adjust(self, delta: float):
        self.value = max(0.0, min(1.0, self.value + delta))

    def set_from_pos(self, x):
        self.value = max(0.0, min(1.0, (x - self.rect.left) / self.rect.width))

    def draw(self, surface, font):
        draw_text(surface, font, f"{self.label}: {int(self.value * 100)}%",
                  config.UI_ACCENT if self.selected else config.UI_TEXT,
                  center=(self.rect.centerx, self.rect.top - 22), shadow=False)
        pygame.draw.rect(surface, (20, 20, 30), self.rect, border_radius=9)
        fill = self.rect.copy()
        fill.width = int(self.value * self.rect.width)
        pygame.draw.rect(surface, config.UI_ACCENT, fill, border_radius=9)
        knob = pygame.Rect(0, 0, 22, 30)
        knob.center = (self.knob_x, self.rect.centery)
        pygame.draw.rect(surface, config.UI_TEXT, knob, border_radius=7)
        if self.selected:
            pygame.draw.rect(surface, config.UI_ACCENT, knob, width=3, border_radius=7)
