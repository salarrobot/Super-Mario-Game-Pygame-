"""
base.py
=======

The state-machine foundation.

Each screen of the game (menu, level select, settings, gameplay, pause, game
over, victory) is a :class:`State`. The :class:`StateManager` keeps them on a
stack so transient screens can be layered over persistent ones — e.g. pushing
the pause menu over the still-visible (but frozen) gameplay. States marked
``transparent`` let the state beneath them keep drawing.
"""

from __future__ import annotations

from typing import List

import pygame


class State:
    transparent = False  # if True, the state below is still drawn

    def __init__(self, game):
        self.game = game
        self.manager: "StateManager" = game.states

    # Lifecycle hooks --------------------------------------------------------
    def enter(self, **kwargs):
        """Called when this state becomes active (pushed or revealed)."""

    def exit(self):
        """Called when this state is removed from the stack."""

    def pause(self):
        """Called when another state is pushed on top of this one."""

    def resume(self):
        """Called when the state on top of this one is popped."""

    # Per-frame hooks --------------------------------------------------------
    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        pass


class StateManager:
    def __init__(self):
        self.stack: List[State] = []

    @property
    def current(self):
        return self.stack[-1] if self.stack else None

    def push(self, state: State, **kwargs):
        if self.stack:
            self.stack[-1].pause()
        self.stack.append(state)
        state.enter(**kwargs)

    def pop(self):
        if self.stack:
            state = self.stack.pop()
            state.exit()
        if self.stack:
            self.stack[-1].resume()

    def replace(self, state: State, **kwargs):
        while self.stack:
            self.stack.pop().exit()
        self.stack.append(state)
        state.enter(**kwargs)

    def clear(self):
        while self.stack:
            self.stack.pop().exit()

    # Delegation -------------------------------------------------------------
    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def draw(self, surface):
        # Draw the deepest non-transparent state first, then transparent ones
        # layered on top (so a pause overlay shows the frozen game beneath it).
        start = len(self.stack) - 1
        while start > 0 and self.stack[start].transparent:
            start -= 1
        for state in self.stack[start:]:
            state.draw(surface)
