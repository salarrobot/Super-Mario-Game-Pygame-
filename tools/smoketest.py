"""
smoketest.py
============

Headless integration test. Runs the whole game with the SDL "dummy" video and
audio drivers (no window, no sound device) and drives it through every major
code path to make sure nothing raises:

* builds assets + synthesized audio,
* loads and simulates each level with the hero auto-running and jumping,
* forces power-ups, fireballs, an enemy stomp and a block bump,
* and renders a frame of every menu/overlay state.

Run from the project root:  python tools/smoketest.py
"""

import os
import sys
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import config  # noqa: E402


class FakeKeys:
    """Stand-in for pygame.key.get_pressed() returning True for held actions."""
    def __init__(self, active):
        self.active = set(active)

    def __getitem__(self, k):
        return k in self.active


def main():
    from src.game import Game
    from src.states.play import PlayState

    g = Game()
    print(f"[ok] Game built. Levels discovered: {[m['name'] for m in g.level_meta]}")

    # Hold "run right".
    held = {pygame.K_d, pygame.K_RIGHT, pygame.K_LSHIFT}
    pygame.key.get_pressed = lambda: FakeKeys(held)

    DT = 1 / 60.0

    for n in range(1, len(g.level_meta) + 1):
        g.states.replace(PlayState(g), level_number=n)
        play = g.states.current
        print(f"[..] Simulating level {n}: {play.level.name} "
              f"({play.level.col_count}x{play.level.row_count}, "
              f"{len(play.level.enemies)} enemies, {len(play.level.coins)} coins)")
        for i in range(420):
            cur = g.states.current
            if isinstance(cur, PlayState) and not cur.dying and not cur.completing:
                if i % 45 == 0:
                    cur.player.jump_buffer = config.JUMP_BUFFER
            g.states.update(DT)
            g.states.draw(g.render_surface)
        print(f"[ok] Level {n} simulated. Score now {getattr(g.states.current, 'score', 'n/a')}")

    # --- Targeted interaction checks on a fresh level 1 ---
    g.states.replace(PlayState(g), level_number=1)
    play = g.states.current
    for kind in ("mushroom", "fire_flower", "star"):
        play.player.apply_powerup(kind)
    play.spawn_fireball(play.player.rect.centerx, play.player.rect.centery, 1)
    # Force an enemy stomp.
    if play.level.enemies:
        e = play.level.enemies[0]
        play.player.rect.midbottom = (e.rect.centerx, e.rect.top - 2)
        play.player.pos.update(play.player.rect.x, play.player.rect.y)
        play.player.vel.y = 5
        play.update(DT)
    # Bump a block from below.
    if play.level.blocks:
        b = play.level.blocks[0]
        play.player.rect.midtop = (b.rect.centerx, b.rect.bottom + 1)
        play.player.pos.update(play.player.rect.x, play.player.rect.y)
        play.player.vel.y = -5
        play.player.head_bump = True
        play._bump_blocks()
    play.player.take_damage()
    for _ in range(30):
        play.update(DT)
        play.draw(g.render_surface)
    print("[ok] Power-ups, fireball, stomp, block bump and damage exercised.")

    # --- Render one frame of every other state ---
    from src.states.menu import MenuState
    from src.states.level_select import LevelSelectState
    from src.states.settings import SettingsState
    from src.states.pause import PauseState
    from src.states.gameover import GameOverState
    from src.states.victory import VictoryState

    g.states.replace(MenuState(g))
    for _ in range(3):
        g.states.update(DT); g.states.draw(g.render_surface)

    for cls, kwargs in [(LevelSelectState, {}), (SettingsState, {})]:
        g.states.push(cls(g), **kwargs)
        g.states.update(DT); g.states.draw(g.render_surface)
        g.states.pop()
    print("[ok] Menu, level-select and settings rendered.")

    # Pause requires a play state beneath it.
    g.states.replace(PlayState(g), level_number=1)
    g.states.push(PauseState(g))
    g.states.update(DT); g.states.draw(g.render_surface)
    g.states.pop()

    g.states.replace(GameOverState(g), score=12345)
    g.states.update(DT); g.states.draw(g.render_surface)
    g.states.replace(VictoryState(g), score=54321, lives=3)
    for _ in range(5):
        g.states.update(DT); g.states.draw(g.render_surface)
    print("[ok] Pause, game-over and victory rendered.")

    print("\nSMOKE TEST PASSED — no exceptions across all systems.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
