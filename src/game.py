"""
game.py
=======

The application shell. :class:`Game` wires the subsystems together and runs the
main loop:

    init pygame -> build assets/audio -> load settings & progress ->
    discover levels -> push the menu state -> loop (events / update / draw).

Rendering uses a fixed-resolution off-screen surface that is scaled to the
window every frame. This keeps the pixel-art crisp and the game logic resolution
independent of the actual window size or fullscreen resolution, and it is the
reason mouse coordinates are mapped back into render space before reaching the
UI.
"""

from __future__ import annotations

import glob
import json
import os

import pygame

import config
from src.managers.assets import AssetManager
from src.managers.audio import AudioManager
from src.managers.save_manager import SaveManager, Settings
from src.states.base import StateManager
from src.ui.backdrop import MenuBackdrop


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(config.GAME_TITLE)

        # Persisted preferences & progress (loaded before the display so the
        # fullscreen preference is honoured from the first frame).
        self.settings = Settings()
        self.save = SaveManager()

        # Display: an off-screen render target scaled to the window.
        self.render_surface = pygame.Surface((config.RENDER_WIDTH, config.RENDER_HEIGHT))
        self.window = None
        self.viewport = pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        self.scale = 1.0
        self.set_fullscreen(self.settings["fullscreen"])

        self.clock = pygame.time.Clock()
        self.running = True

        # Assets & audio (need a display to convert/format against).
        self.assets = AssetManager()
        self.assets.build()
        self.audio = AudioManager(self.settings["music_volume"], self.settings["sfx_volume"])
        self.audio.build()

        self.vignette = self._build_vignette()
        self.level_meta = self._discover_levels()
        self.menu_backdrop = MenuBackdrop(self.assets)

        # State machine: start at the main menu.
        self.states = StateManager()
        from src.states.menu import MenuState
        self.states.push(MenuState(self))

    # ------------------------------------------------------------ display
    def set_fullscreen(self, enabled: bool):
        if enabled:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self._compute_viewport()

    def _compute_viewport(self):
        """Letterbox the fixed-resolution render onto the actual window."""
        ww, wh = self.window.get_size()
        self.scale = min(ww / config.RENDER_WIDTH, wh / config.RENDER_HEIGHT)
        vw = int(config.RENDER_WIDTH * self.scale)
        vh = int(config.RENDER_HEIGHT * self.scale)
        self.viewport = pygame.Rect((ww - vw) // 2, (wh - vh) // 2, vw, vh)

    def _map_mouse(self, pos):
        """Convert a window-space mouse position into render space."""
        x = (pos[0] - self.viewport.x) / self.scale
        y = (pos[1] - self.viewport.y) / self.scale
        return (x, y)

    def _build_vignette(self):
        """A soft darkening toward the screen edges, built once at low res and
        smooth-scaled up (cheap and good enough for a subtle lighting effect)."""
        sw, sh = 192, 108
        small = pygame.Surface((sw, sh), pygame.SRCALPHA)
        cx, cy = sw / 2, sh / 2
        maxd = (cx ** 2 + cy ** 2) ** 0.5
        for y in range(sh):
            for x in range(sw):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / maxd
                a = int(max(0, (d - 0.55)) * 230)
                if a:
                    small.set_at((x, y), (0, 0, 0, min(150, a)))
        return pygame.transform.smoothscale(small, (config.RENDER_WIDTH, config.RENDER_HEIGHT))

    def _discover_levels(self):
        files = sorted(glob.glob(os.path.join(config.LEVEL_DIR, "level*.json")))
        meta = []
        for f in files:
            name = os.path.basename(f)
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    name = json.load(fh).get("name", name)
            except (OSError, json.JSONDecodeError):
                pass
            meta.append({"file": f, "name": name})
        return meta

    # --------------------------------------------------------------- loop
    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self._process_events()
            self.states.update(dt)
            self._render()
        self.settings.save()
        pygame.quit()

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.settings["fullscreen"] = not self.settings["fullscreen"]
                self.settings.save()
                self.set_fullscreen(self.settings["fullscreen"])
                continue
            # Remap mouse coordinates into render space before dispatching.
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP):
                mapped = self._map_mouse(event.pos)
                data = dict(event.dict)
                data["pos"] = mapped
                event = pygame.event.Event(event.type, data)
            self.states.handle_event(event)

    def _render(self):
        self.states.draw(self.render_surface)
        self.window.fill((0, 0, 0))
        scaled = pygame.transform.scale(self.render_surface, self.viewport.size)
        self.window.blit(scaled, self.viewport.topleft)
        pygame.display.flip()
