"""
export_assets.py
================

Bakes the procedurally-generated art and audio to real files on disk:

* PNG sprites + packed sprite sheets  ->  assets/images/
* WAV sound effects and music         ->  assets/sounds/

The game itself never needs these (it generates everything in memory at
startup); this tool exists so the procedural assets can be inspected, dropped
into other tools, or used as a starting point for hand-drawn replacements. It
also demonstrates the sprite-sheet packing path in
``src/utils/spritesheet.py``.

    python tools/export_assets.py
"""

import os
import sys
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import config  # noqa: E402
from src.utils.spritesheet import pack_frames  # noqa: E402


def save_image(surface, name):
    path = os.path.join(config.IMAGE_DIR, name)
    pygame.image.save(surface, path)


def export_images():
    from src.managers.assets import AssetManager
    os.makedirs(config.IMAGE_DIR, exist_ok=True)
    pygame.display.set_mode((1, 1))  # needed for convert_alpha
    assets = AssetManager()
    assets.build()

    # Single tiles & icons.
    for key, surf in assets.tiles.items():
        save_image(surf, f"tile_{key}.png")
    for key, surf in assets.icons.items():
        save_image(surf, f"icon_{key}.png")
    for key, surf in assets.scenery.items():
        save_image(surf, f"scenery_{key}.png")
    save_image(assets.powerups["mushroom"], "powerup_mushroom.png")

    # Packed sprite sheets for every animation.
    for variant, anims in assets.players.items():
        for action, frames in anims.items():
            save_image(pack_frames(frames), f"player_{variant}_{action}.png")
    for enemy, anims in assets.enemies.items():
        for action, frames in anims.items():
            save_image(pack_frames(frames), f"enemy_{enemy}_{action}.png")
    save_image(pack_frames(assets.coin_frames), "coin_spin.png")
    save_image(pack_frames(assets.fireball_frames), "fireball.png")
    save_image(pack_frames(assets.powerups["fire_flower"]), "powerup_fire_flower.png")
    save_image(pack_frames(assets.powerups["star"]), "powerup_star.png")
    save_image(pack_frames(assets.question["active"]), "block_question.png")
    print(f"Images exported to {config.IMAGE_DIR}")


def export_sounds():
    from src.audio import synth
    if not synth.HAVE_NUMPY:
        print("numpy not available; skipping audio export.")
        return
    os.makedirs(config.SOUND_DIR, exist_ok=True)

    def write_wav(name, arr):
        path = os.path.join(config.SOUND_DIR, name)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(synth.SAMPLE_RATE)
            wf.writeframes(arr.tobytes())

    for name, arr in synth.generate_sfx().items():
        write_wav(f"sfx_{name}.wav", arr)
    for name, arr in synth.generate_music().items():
        write_wav(f"music_{name}.wav", arr)
    print(f"Sounds exported to {config.SOUND_DIR}")


if __name__ == "__main__":
    pygame.init()
    export_images()
    export_sounds()
    pygame.quit()
    print("Done.")
