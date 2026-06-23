"""
synth.py
========

Procedural audio synthesizer.

Just like the artwork, all sound is generated in code so the project ships with
zero binary assets. We synthesize short 8-bit-style waveforms (square / triangle
/ noise) with simple amplitude envelopes for sound effects, and stitch notes
together into looping chiptune melodies for music.

Everything here depends on :mod:`numpy`. If numpy is unavailable the public
``generate_*`` functions return empty dicts and the :class:`AudioManager`
degrades gracefully to silence.
"""

from __future__ import annotations

from typing import Dict

try:
    import numpy as np
    HAVE_NUMPY = True
except Exception:  # pragma: no cover - numpy is optional
    HAVE_NUMPY = False

SAMPLE_RATE = 44100


# ---------------------------------------------------------------------------
# Low level oscillators & helpers (all operate on numpy float arrays in -1..1)
# ---------------------------------------------------------------------------
def _t(duration: float) -> "np.ndarray":
    return np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)


def _square(freq: float, dur: float, duty: float = 0.5) -> "np.ndarray":
    t = _t(dur)
    phase = (t * freq) % 1.0
    return np.where(phase < duty, 1.0, -1.0)


def _triangle(freq: float, dur: float) -> "np.ndarray":
    t = _t(dur)
    phase = (t * freq) % 1.0
    return 2.0 * np.abs(2.0 * phase - 1.0) - 1.0


def _sine(freq: float, dur: float) -> "np.ndarray":
    return np.sin(2 * np.pi * freq * _t(dur))


def _noise(dur: float) -> "np.ndarray":
    return np.random.uniform(-1, 1, int(SAMPLE_RATE * dur))


def _env(signal: "np.ndarray", attack=0.005, release=0.05) -> "np.ndarray":
    """Apply a simple linear attack/release envelope to avoid clicks."""
    n = len(signal)
    a = min(int(SAMPLE_RATE * attack), n // 2)
    r = min(int(SAMPLE_RATE * release), n // 2)
    env = np.ones(n)
    if a:
        env[:a] = np.linspace(0, 1, a)
    if r:
        env[-r:] = np.linspace(1, 0, r)
    return signal * env


def _sweep(f0: float, f1: float, dur: float, kind="square") -> "np.ndarray":
    """Frequency glide from f0 to f1 (great for jumps / power-ups)."""
    t = _t(dur)
    freqs = np.linspace(f0, f1, len(t))
    phase = np.cumsum(2 * np.pi * freqs / SAMPLE_RATE)
    if kind == "square":
        return np.sign(np.sin(phase))
    return np.sin(phase)


def _to_int16_stereo(mono: "np.ndarray", volume: float = 0.4) -> "np.ndarray":
    """Normalize, apply headroom and duplicate into a stereo int16 array."""
    if mono.size == 0:
        return np.zeros((1, 2), dtype=np.int16)
    peak = np.max(np.abs(mono)) or 1.0
    mono = (mono / peak) * volume
    data = np.clip(mono, -1, 1)
    ints = (data * 32767).astype(np.int16)
    return np.column_stack((ints, ints))


def _midi(n: int) -> float:
    """MIDI note number -> frequency in Hz."""
    return 440.0 * (2 ** ((n - 69) / 12.0))


# ---------------------------------------------------------------------------
# Sound effects
# ---------------------------------------------------------------------------
def _sfx() -> Dict[str, "np.ndarray"]:
    out: Dict[str, np.ndarray] = {}

    # Jump: quick upward square sweep.
    out["jump"] = _to_int16_stereo(_env(_sweep(380, 760, 0.18), 0.005, 0.08), 0.35)

    # Double jump: a touch higher / shorter.
    out["double_jump"] = _to_int16_stereo(_env(_sweep(520, 980, 0.14), 0.005, 0.07), 0.32)

    # Coin: two-note "ting".
    coin = np.concatenate([_env(_square(_midi(95), 0.05), 0.002, 0.02),
                           _env(_square(_midi(100), 0.12), 0.002, 0.06)])
    out["coin"] = _to_int16_stereo(coin, 0.3)

    # Stomp / enemy defeat: downward noisy thud.
    stomp = _env(_sweep(300, 90, 0.16) * 0.6 + _noise(0.16) * 0.4, 0.002, 0.08)
    out["stomp"] = _to_int16_stereo(stomp, 0.4)

    # Block break: bright noise burst.
    out["break"] = _to_int16_stereo(_env(_noise(0.18) * (np.linspace(1, 0, int(SAMPLE_RATE * 0.18)) ** 2), 0.001, 0.05), 0.4)

    # Bump (hitting a solid block from below).
    out["bump"] = _to_int16_stereo(_env(_square(180, 0.08), 0.002, 0.04), 0.3)

    # Power-up appear / collect: rising arpeggio.
    arp = np.concatenate([_env(_square(_midi(n), 0.06), 0.002, 0.02)
                          for n in (72, 76, 79, 84, 88)])
    out["powerup"] = _to_int16_stereo(arp, 0.3)
    out["powerup_appear"] = _to_int16_stereo(_env(_sweep(200, 600, 0.3, "sine"), 0.01, 0.1), 0.25)

    # Power down / take damage: descending warble.
    out["powerdown"] = _to_int16_stereo(_env(_sweep(500, 160, 0.4), 0.005, 0.1), 0.3)

    # Death.
    death = np.concatenate([_env(_square(_midi(72), 0.12)), _env(_sweep(400, 80, 0.5, "square"), 0.005, 0.2)])
    out["death"] = _to_int16_stereo(death, 0.35)

    # Fireball shoot.
    out["fireball"] = _to_int16_stereo(_env(_sweep(700, 300, 0.12), 0.002, 0.05), 0.28)

    # 1-Up.
    oneup = np.concatenate([_env(_square(_midi(n), 0.08), 0.002, 0.03) for n in (76, 81, 84, 88)])
    out["oneup"] = _to_int16_stereo(oneup, 0.3)

    # Checkpoint.
    out["checkpoint"] = _to_int16_stereo(np.concatenate(
        [_env(_triangle(_midi(n), 0.1), 0.005, 0.04) for n in (72, 79)]), 0.3)

    # Menu blip + confirm.
    out["blip"] = _to_int16_stereo(_env(_square(_midi(84), 0.05), 0.002, 0.02), 0.25)
    out["confirm"] = _to_int16_stereo(np.concatenate(
        [_env(_square(_midi(79), 0.05)), _env(_square(_midi(86), 0.09))]), 0.3)

    return out


# ---------------------------------------------------------------------------
# Music — short loopable chiptune sequences
# ---------------------------------------------------------------------------
def _melody(notes, bpm=120, wave="square", duty=0.5, vol=0.5) -> "np.ndarray":
    """Render a list of (midi|None, beats) into a waveform."""
    beat = 60.0 / bpm
    chunks = []
    for note, beats in notes:
        dur = beat * beats
        if note is None:
            chunks.append(np.zeros(int(SAMPLE_RATE * dur)))
        else:
            if wave == "triangle":
                sig = _triangle(_midi(note), dur)
            else:
                sig = _square(_midi(note), dur, duty)
            chunks.append(_env(sig, 0.005, min(0.08, dur * 0.4)) * vol)
    return np.concatenate(chunks) if chunks else np.zeros(1)


def _mix(*tracks) -> "np.ndarray":
    """Sum several equal-length-ish tracks, padding to the longest."""
    n = max(len(t) for t in tracks)
    acc = np.zeros(n)
    for t in tracks:
        acc[:len(t)] += t
    return acc


def _music() -> Dict[str, "np.ndarray"]:
    out: Dict[str, np.ndarray] = {}

    # ----- Menu theme: gentle, looping -----
    lead = _melody([(76, 1), (79, 1), (84, 2), (81, 1), (79, 1), (76, 2),
                    (74, 1), (77, 1), (81, 2), (79, 2)], bpm=104, vol=0.4)
    bass = _melody([(48, 2), (55, 2), (53, 2), (50, 2), (48, 4)], bpm=104, wave="triangle", vol=0.5)
    out["menu"] = _to_int16_stereo(_mix(lead, np.tile(bass, 1)[:len(lead)]), 0.32)

    # ----- Level 1: bright & bouncy -----
    l1 = _melody([(72, .5), (76, .5), (79, .5), (84, .5), (83, 1), (79, .5), (76, .5),
                  (77, .5), (81, .5), (84, .5), (88, .5), (86, 1), (81, 1)], bpm=132, vol=0.4)
    b1 = _melody([(48, 1), (48, .5), (55, .5), (53, 1), (50, 1)] * 2, bpm=132, wave="triangle", vol=0.55)
    out["level1"] = _to_int16_stereo(_mix(l1, np.resize(b1, len(l1))), 0.3)

    # ----- Level 2: slightly darker / faster -----
    l2 = _melody([(69, .5), (72, .5), (74, .5), (77, .5), (76, 1), (72, .5), (69, .5),
                  (71, .5), (74, .5), (77, .5), (79, .5), (77, 1), (74, 1)], bpm=144, duty=0.35, vol=0.38)
    b2 = _melody([(45, .5), (45, .5), (52, .5), (50, .5)] * 4, bpm=144, wave="triangle", vol=0.55)
    out["level2"] = _to_int16_stereo(_mix(l2, np.resize(b2, len(l2))), 0.3)

    # ----- Level 3: heroic / driving -----
    l3 = _melody([(81, .5), (79, .5), (76, .5), (79, .5), (84, 1), (83, .5), (81, .5),
                  (79, .5), (76, .5), (74, .5), (76, .5), (79, 2)], bpm=150, vol=0.4)
    b3 = _melody([(40, .5), (47, .5), (45, .5), (43, .5)] * 4, bpm=150, wave="triangle", vol=0.55)
    out["level3"] = _to_int16_stereo(_mix(l3, np.resize(b3, len(l3))), 0.3)

    # ----- Game over: short somber phrase -----
    out["gameover"] = _to_int16_stereo(_melody(
        [(72, 1), (68, 1), (65, 1), (60, 2), (None, 1)], bpm=100, wave="triangle", vol=0.5), 0.3)

    # ----- Victory: triumphant fanfare -----
    out["victory"] = _to_int16_stereo(_melody(
        [(72, .5), (76, .5), (79, .5), (84, 1), (79, .5), (84, 2)], bpm=140, vol=0.45), 0.32)

    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_sfx() -> Dict[str, "np.ndarray"]:
    if not HAVE_NUMPY:
        return {}
    return _sfx()


def generate_music() -> Dict[str, "np.ndarray"]:
    if not HAVE_NUMPY:
        return {}
    return _music()
