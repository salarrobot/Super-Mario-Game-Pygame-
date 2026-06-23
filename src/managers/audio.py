"""
audio.py
========

The :class:`AudioManager` owns the mixer. It synthesizes every sound effect and
music track once at startup (see :mod:`src.audio.synth`) and exposes a tiny API
the rest of the game uses:

    audio.play("jump")
    audio.play_music("level1")
    audio.set_music_volume(0.5)

Channel 0 is *reserved* for looping background music so that adjusting music
volume never touches sound effects, and SFX automatically grab any of the other
channels. If numpy (and therefore synthesis) is unavailable, every method
becomes a safe no-op so the game still runs silently.
"""

from __future__ import annotations

from typing import Dict, Optional

import pygame

from src.audio import synth


class AudioManager:
    def __init__(self, music_volume: float = 0.5, sfx_volume: float = 0.7):
        self.enabled = False
        self.sfx: Dict[str, pygame.mixer.Sound] = {}
        self.music: Dict[str, pygame.mixer.Sound] = {}
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        self.current_music: Optional[str] = None
        self._music_channel: Optional[pygame.mixer.Channel] = None

    def build(self) -> None:
        """Initialize the mixer and bake all sounds. Safe to call once."""
        if not synth.HAVE_NUMPY:
            print("[audio] numpy not available — running without sound.")
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=synth.SAMPLE_RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)  # reserve channel 0 for music
            self._music_channel = pygame.mixer.Channel(0)
            self.enabled = True
        except Exception as exc:  # pragma: no cover
            print(f"[audio] mixer init failed ({exc}); continuing silently.")
            return

        import pygame.sndarray as sndarray

        for name, arr in synth.generate_sfx().items():
            try:
                self.sfx[name] = sndarray.make_sound(arr)
            except Exception:
                pass
        for name, arr in synth.generate_music().items():
            try:
                self.music[name] = sndarray.make_sound(arr)
            except Exception:
                pass

        self._apply_sfx_volume()

    # ------------------------------------------------------------------ sfx
    def play(self, name: str) -> None:
        if not self.enabled:
            return
        snd = self.sfx.get(name)
        if snd is not None:
            snd.play()

    def _apply_sfx_volume(self) -> None:
        for snd in self.sfx.values():
            snd.set_volume(self.sfx_volume)

    # ---------------------------------------------------------------- music
    def play_music(self, name: str, restart: bool = False) -> None:
        if not self.enabled or self._music_channel is None:
            return
        if name == self.current_music and not restart and self._music_channel.get_busy():
            return
        snd = self.music.get(name)
        if snd is None:
            return
        self.current_music = name
        snd.set_volume(self.music_volume)
        self._music_channel.play(snd, loops=-1)

    def stop_music(self) -> None:
        if self._music_channel is not None:
            self._music_channel.stop()
        self.current_music = None

    def pause_music(self) -> None:
        if self._music_channel is not None:
            self._music_channel.pause()

    def unpause_music(self) -> None:
        if self._music_channel is not None:
            self._music_channel.unpause()

    def play_jingle(self, name: str) -> None:
        """Play a non-looping music cue (victory/game over) on the music channel."""
        if not self.enabled or self._music_channel is None:
            return
        snd = self.music.get(name)
        if snd is None:
            return
        self.current_music = None
        snd.set_volume(self.music_volume)
        self._music_channel.play(snd, loops=0)

    # ------------------------------------------------------------- volumes
    def set_music_volume(self, vol: float) -> None:
        self.music_volume = max(0.0, min(1.0, vol))
        if self._music_channel is not None:
            self._music_channel.set_volume(self.music_volume)

    def set_sfx_volume(self, vol: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, vol))
        self._apply_sfx_volume()
