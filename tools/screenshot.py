"""Render a few frames headlessly and save PNGs so the visuals can be reviewed."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa
import config  # noqa

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".preview")
os.makedirs(OUT, exist_ok=True)
DT = 1 / 60.0


def save(surface, name):
    pygame.image.save(surface, os.path.join(OUT, name))
    print("saved", name)


def main():
    from src.game import Game
    from src.states.play import PlayState

    class Keys:
        def __init__(self, a): self.a = set(a)
        def __getitem__(self, k): return k in self.a

    g = Game()

    for _ in range(20):
        g.states.update(DT)
    g.states.draw(g.render_surface)
    save(g.render_surface, "menu.png")

    held = {pygame.K_d, pygame.K_RIGHT, pygame.K_LSHIFT}
    pygame.key.get_pressed = lambda: Keys(held)

    for n, frames in [(1, 80), (2, 140), (3, 200)]:
        g.states.replace(PlayState(g), level_number=n)
        play = g.states.current
        # Give the hero a power-up so screenshots show the bigger sprite.
        play.player.apply_powerup("mushroom")
        for i in range(frames):
            if i % 40 == 0 and not play.dying and not play.completing:
                play.player.jump_buffer = config.JUMP_BUFFER
            g.states.update(DT)
        g.states.draw(g.render_surface)
        save(g.render_surface, f"level{n}.png")


if __name__ == "__main__":
    main()
