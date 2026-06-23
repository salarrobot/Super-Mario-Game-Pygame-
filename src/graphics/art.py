"""
art.py
======

Procedural pixel-art generator.

Rather than shipping binary image files, every sprite in the game is *drawn in
code* at startup using pygame's drawing primitives. This has several upsides for
an educational project:

* The repository stays small and text-only (everything is reviewable).
* There is a single, readable source of truth for how each sprite looks.
* The same functions are reused by ``tools/export_assets.py`` to bake the art
  out to PNG files for anyone who wants traditional asset files.

Each public ``make_*`` function returns either a single ``pygame.Surface`` or a
dict of animation frames (lists of surfaces), all using per-pixel alpha so they
composite cleanly over the parallax background.
"""

from __future__ import annotations

import math
from typing import Dict, List

import pygame

from src.graphics import palette as P

# Convenience type alias
Frames = Dict[str, List[pygame.Surface]]


def _surf(w: int, h: int) -> pygame.Surface:
    """Create a transparent per-pixel-alpha surface."""
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _rrect(surf, color, rect, radius=0, width=0):
    pygame.draw.rect(surf, color, pygame.Rect(rect), border_radius=radius, width=width)


# ===========================================================================
#  THE HERO  ("Pip")
# ===========================================================================
def _draw_pip(w: int, h: int, colors: dict, leg_swing: float = 0.0,
              arm_swing: float = 0.0, bob: float = 0.0, squash: float = 0.0,
              crouch: bool = False, facing: int = 1) -> pygame.Surface:
    """
    Draw the hero in a given pose on a fresh surface.

    Parameters are normalized so a single function can produce idle, running,
    jumping, falling and crouching frames just by varying them:

    * ``leg_swing``  : -1..1, swings the legs for the run cycle.
    * ``arm_swing``  : -1..1, swings the arms (jump raises an arm).
    * ``bob``        : vertical body offset in pixels (run bounce).
    * ``squash``     : 0..1, squash-and-stretch used on landing/idle breathing.
    * ``crouch``     : compresses the character.
    """
    surf = _surf(w, h)
    cx = w // 2

    # Squash & stretch: wider+shorter as squash increases.
    sx = 1.0 + 0.12 * squash
    sy = 1.0 - 0.14 * squash
    body_h = int(h * (0.62 if not crouch else 0.42) * sy)
    head_h = int(h * (0.34 if not crouch else 0.30) * sy)
    unit = max(2, w // 12)

    top = int(h - body_h - head_h - 2 + bob)
    if crouch:
        top = int(h - body_h - head_h - 2 + bob + h * 0.18)

    # ----- shadow on the ground (soft ellipse) -----
    shadow = _surf(w, 8)
    pygame.draw.ellipse(shadow, (0, 0, 0, 70), (w * 0.18, 0, w * 0.64, 7))
    surf.blit(shadow, (0, h - 6))

    # ----- legs / shoes -----
    leg_w = int(w * 0.22 * sx)
    leg_h = int(h * 0.20)
    foot_off = int(leg_swing * w * 0.16)
    leg_y = top + head_h + body_h - leg_h + 4
    # back leg
    _rrect(surf, colors["overall_shadow"], (cx - leg_w - 1 - foot_off, leg_y, leg_w, leg_h), 3)
    _rrect(surf, P.SHOES, (cx - leg_w - 2 - foot_off, leg_y + leg_h - unit, leg_w + 3, unit + 2), 3)
    # front leg
    _rrect(surf, colors["overall"], (cx + 1 + foot_off, leg_y, leg_w, leg_h), 3)
    _rrect(surf, P.SHOES, (cx + 1 + foot_off, leg_y + leg_h - unit, leg_w + 3, unit + 2), 3)

    # ----- body / overalls -----
    body_w = int(w * 0.56 * sx)
    body_x = cx - body_w // 2
    body_y = top + head_h - 2
    _rrect(surf, colors["shirt"], (body_x, body_y, body_w, int(body_h * 0.45)), 4)
    _rrect(surf, colors["overall"], (body_x, body_y + int(body_h * 0.30), body_w, int(body_h * 0.72)), 4)
    _rrect(surf, colors["overall_shadow"], (body_x, body_y + int(body_h * 0.62), body_w, int(body_h * 0.40)), 4)
    # overall buttons
    pygame.draw.circle(surf, P.QUESTION, (cx - body_w // 4, body_y + int(body_h * 0.38)), max(1, unit // 2))
    pygame.draw.circle(surf, P.QUESTION, (cx + body_w // 4, body_y + int(body_h * 0.38)), max(1, unit // 2))

    # ----- arms -----
    arm_w = int(w * 0.16 * sx)
    arm_h = int(body_h * 0.5)
    arm_y = body_y + int(arm_swing * -h * 0.10)
    _rrect(surf, colors["shirt"], (body_x - arm_w + 2, arm_y, arm_w, arm_h), 3)
    _rrect(surf, colors["skin"], (body_x - arm_w + 2, arm_y + arm_h - unit, arm_w, unit + 1), 3)
    _rrect(surf, colors["shirt"], (body_x + body_w - 2, arm_y - int(arm_swing * h * 0.05), arm_w, arm_h), 3)
    _rrect(surf, colors["skin"], (body_x + body_w - 2, arm_y + arm_h - unit - int(arm_swing * h * 0.05), arm_w, unit + 1), 3)

    # ----- head -----
    head_w = int(w * 0.62 * sx)
    head_x = cx - head_w // 2
    head_y = top
    _rrect(surf, colors["skin"], (head_x, head_y + head_h // 3, head_w, int(head_h * 0.7)), 6)
    _rrect(surf, colors["skin_shadow"], (head_x, head_y + int(head_h * 0.7), head_w, int(head_h * 0.34)), 6)

    # cap (covers top of head + brim toward facing direction)
    _rrect(surf, colors["cap"], (head_x - 1, head_y, head_w + 2, int(head_h * 0.5)), 6)
    _rrect(surf, colors["cap_shadow"], (head_x - 1, head_y + int(head_h * 0.34), head_w + 2, int(head_h * 0.2)), 3)
    brim_w = int(head_w * 0.6)
    if facing >= 0:
        _rrect(surf, colors["cap"], (cx, head_y + int(head_h * 0.38), brim_w, unit + 1), 3)
    else:
        _rrect(surf, colors["cap"], (cx - brim_w, head_y + int(head_h * 0.38), brim_w, unit + 1), 3)

    # eye (positioned toward facing direction)
    eye_x = cx + (facing * head_w // 6) - unit // 2
    eye_y = head_y + int(head_h * 0.6)
    pygame.draw.circle(surf, P.EYE, (eye_x + (head_w // 4 if facing > 0 else -head_w // 8), eye_y), max(2, unit // 2))

    # mustache hint
    _rrect(surf, colors["skin_shadow"], (cx - head_w // 5, head_y + int(head_h * 0.82), int(head_w * 0.4), unit), 2)

    return surf


def make_player_set(big: bool = False, fire: bool = False) -> Frames:
    """Build a full animation set for one player size/state."""
    if big:
        w, h = 44, 86
    else:
        w, h = 36, 48

    colors = {
        "skin": P.SKIN, "skin_shadow": P.SKIN_SHADOW,
        "cap": P.FIRE_CAP if fire else P.CAP,
        "cap_shadow": P.CAP_SHADOW,
        "overall": P.FIRE_OVERALL if fire else P.OVERALL,
        "overall_shadow": P.FIRE_OVERALL_SHADOW if fire else P.OVERALL_SHADOW,
        "shirt": P.CAP if fire else P.SHIRT,
    }

    frames: Frames = {"idle": [], "run": [], "jump": [], "fall": [], "crouch": []}

    # Idle: subtle breathing via squash oscillation.
    for i in range(4):
        s = 0.5 + 0.5 * math.sin(i / 4 * math.tau)
        frames["idle"].append(_draw_pip(w, h, colors, squash=0.08 * s, bob=-1 * s))

    # Run: 6-frame cycle swinging legs/arms and bobbing.
    for i in range(6):
        ph = i / 6 * math.tau
        frames["run"].append(_draw_pip(
            w, h, colors,
            leg_swing=math.sin(ph), arm_swing=math.sin(ph + math.pi),
            bob=-abs(math.sin(ph)) * 3))

    # Jump (rising) and fall (descending) are single expressive poses.
    frames["jump"].append(_draw_pip(w, h, colors, leg_swing=0.4, arm_swing=1.0, bob=-2))
    frames["fall"].append(_draw_pip(w, h, colors, leg_swing=-0.3, arm_swing=0.4, squash=0.0))
    frames["crouch"].append(_draw_pip(w, h, colors, crouch=True, squash=0.4))

    return frames


def make_all_player_frames() -> Dict[str, Frames]:
    """Return frames for every player power state."""
    return {
        "small": make_player_set(big=False, fire=False),
        "big": make_player_set(big=True, fire=False),
        "fire": make_player_set(big=True, fire=True),
    }


# ===========================================================================
#  ENEMIES
# ===========================================================================
def make_goomba_frames() -> Frames:
    w, h = 44, 40
    frames: Frames = {"walk": [], "squashed": []}
    for i in range(2):
        s = _surf(w, h)
        pygame.draw.ellipse(s, (0, 0, 0, 60), (6, h - 6, w - 12, 6))
        # body (mushroom-like)
        _rrect(s, P.GOOMBA_BODY, (4, 6, w - 8, h - 16), 14)
        _rrect(s, P.GOOMBA_BODY_SHADOW, (4, h - 22, w - 8, 12), 10)
        # feet alternate
        off = 4 if i == 0 else -4
        _rrect(s, P.GOOMBA_FOOT, (6 + off, h - 10, 14, 8), 4)
        _rrect(s, P.GOOMBA_FOOT, (w - 20 - off, h - 10, 14, 8), 4)
        # eyes + angry brows
        for ex in (w // 2 - 9, w // 2 + 9):
            pygame.draw.ellipse(s, P.GOOMBA_EYE, (ex - 6, 14, 12, 14))
            pygame.draw.circle(s, P.EYE, (ex, 22), 3)
        pygame.draw.line(s, P.EYE, (w // 2 - 14, 12), (w // 2 - 4, 16), 3)
        pygame.draw.line(s, P.EYE, (w // 2 + 14, 12), (w // 2 + 4, 16), 3)
        frames["walk"].append(s)

    sq = _surf(w, h)
    _rrect(sq, P.GOOMBA_BODY_SHADOW, (4, h - 14, w - 8, 12), 8)
    _rrect(sq, P.GOOMBA_BODY, (8, h - 18, w - 16, 8), 6)
    frames["squashed"].append(sq)
    return frames


def make_koopa_frames() -> Frames:
    w, h = 42, 56
    frames: Frames = {"walk": [], "shell": []}
    for i in range(2):
        s = _surf(w, h)
        pygame.draw.ellipse(s, (0, 0, 0, 60), (6, h - 6, w - 12, 6))
        # legs
        off = 3 if i == 0 else -3
        _rrect(s, P.KOOPA_SKIN_SHADOW, (8 + off, h - 12, 10, 10), 3)
        _rrect(s, P.KOOPA_SKIN_SHADOW, (w - 18 - off, h - 12, 10, 10), 3)
        # shell
        _rrect(s, P.KOOPA_SHELL, (6, 18, w - 12, h - 26), 16)
        _rrect(s, P.KOOPA_SHELL_SHADOW, (6, h - 22, w - 12, 12), 10)
        for hx in (w // 2 - 8, w // 2 + 8):
            pygame.draw.circle(s, P.KOOPA_SHELL_SHADOW, (hx, h // 2 + 2), 4)
        # head + neck
        _rrect(s, P.KOOPA_SKIN, (w // 2 - 8, 2, 18, 22), 8)
        pygame.draw.circle(s, P.EYE, (w // 2 + 4, 12), 3)
        frames["walk"].append(s)

    # shell-only (after stomp) — two slight rotation frames for spin
    for ang in (0, 18):
        base = _surf(w, h)
        _rrect(base, P.KOOPA_SHELL, (6, 18, w - 12, h - 26), 16)
        _rrect(base, P.KOOPA_SHELL_SHADOW, (6, h - 22, w - 12, 12), 10)
        for hx in (w // 2 - 8, w // 2 + 8):
            pygame.draw.circle(base, P.KOOPA_SHELL_SHADOW, (hx, h // 2 + 2), 4)
        frames["shell"].append(pygame.transform.rotate(base, ang))
    return frames


def make_flyer_frames() -> Frames:
    w, h = 50, 44
    frames: Frames = {"fly": []}
    for i in range(2):
        s = _surf(w, h)
        # wings flap
        wy = 8 if i == 0 else 16
        pygame.draw.polygon(s, P.FLYER_WING, [(8, h // 2), (0, wy), (16, h // 2 - 2)])
        pygame.draw.polygon(s, P.FLYER_WING, [(w - 8, h // 2), (w, wy), (w - 16, h // 2 - 2)])
        # body
        _rrect(s, P.FLYER_BODY, (14, 10, w - 28, h - 18), 14)
        _rrect(s, P.FLYER_BODY_SHADOW, (14, h - 16, w - 28, 8), 8)
        for ex in (w // 2 - 6, w // 2 + 6):
            pygame.draw.circle(s, P.GOOMBA_EYE, (ex, 22), 5)
            pygame.draw.circle(s, P.EYE, (ex, 23), 2)
        frames["fly"].append(s)
    return frames


# ===========================================================================
#  TILES / WORLD BLOCKS
# ===========================================================================
def make_ground_tile(grass_top: bool = True) -> pygame.Surface:
    t = TILE = 48
    s = _surf(t, t)
    _rrect(s, P.GROUND_DIRT, (0, 0, t, t))
    # speckled dirt texture
    for (dx, dy) in [(10, 28), (30, 38), (20, 18), (38, 24), (8, 40), (28, 12)]:
        pygame.draw.circle(s, P.GROUND_DIRT_SHADOW, (dx, dy), 3)
        pygame.draw.circle(s, P.GROUND_DIRT_LIGHT, (dx - 1, dy - 1), 1)
    if grass_top:
        _rrect(s, P.GROUND_TOP, (0, 0, t, 16))
        _rrect(s, P.GROUND_TOP_SHADOW, (0, 12, t, 6))
        for gx in range(2, t, 8):
            pygame.draw.polygon(s, P.GROUND_TOP, [(gx, 0), (gx + 3, -4), (gx + 6, 0)])
    pygame.draw.rect(s, P.GROUND_DIRT_SHADOW, (0, 0, t, t), width=1)
    return s


def make_brick_tile() -> pygame.Surface:
    t = 48
    s = _surf(t, t)
    _rrect(s, P.BRICK, (0, 0, t, t), 2)
    # brick courses
    for row in range(4):
        y = row * 12
        pygame.draw.line(s, P.BRICK_LINE, (0, y), (t, y), 2)
        off = 0 if row % 2 == 0 else t // 2
        pygame.draw.line(s, P.BRICK_LINE, (off, y), (off, y + 12), 2)
        pygame.draw.line(s, P.BRICK_LINE, ((off + t // 2) % t, y), ((off + t // 2) % t, y + 12), 2)
    _rrect(s, P.BRICK_SHADOW, (0, t - 6, t, 6))
    pygame.draw.rect(s, P.BRICK_LINE, (0, 0, t, t), width=2)
    return s


def make_question_frames() -> Frames:
    t = 48
    frames: Frames = {"active": [], "used": []}
    for i in range(4):
        s = _surf(t, t)
        glow = 0.5 + 0.5 * math.sin(i / 4 * math.tau)
        base = tuple(min(255, int(c + 30 * glow)) for c in P.QUESTION)
        _rrect(s, base, (0, 0, t, t), 6)
        _rrect(s, P.QUESTION_SHADOW, (0, t - 8, t, 8), 4)
        for (cxr, cyr) in [(6, 6), (t - 6, 6), (6, t - 6), (t - 6, t - 6)]:
            pygame.draw.circle(s, P.QUESTION_RIVET, (cxr, cyr), 2)
        # "?" glyph
        fnt = pygame.font.SysFont("arialblack,impact,arial", 30, bold=True)
        q = fnt.render("?", True, P.OUTLINE)
        s.blit(q, (t // 2 - q.get_width() // 2, t // 2 - q.get_height() // 2 - 1))
        pygame.draw.rect(s, P.QUESTION_SHADOW, (0, 0, t, t), width=2, border_radius=6)
        frames["active"].append(s)

    used = _surf(t, t)
    _rrect(used, P.QUESTION_USED, (0, 0, t, t), 6)
    _rrect(used, (110, 80, 50), (0, t - 8, t, 8), 4)
    for (cxr, cyr) in [(6, 6), (t - 6, 6), (6, t - 6), (t - 6, t - 6)]:
        pygame.draw.circle(used, P.QUESTION_RIVET, (cxr, cyr), 2)
    frames["used"].append(used)
    return frames


def make_pipe_tiles() -> Dict[str, pygame.Surface]:
    t = 48
    top = _surf(t, t)
    _rrect(top, P.PIPE, (-4, 8, t + 8, t - 8), 6)
    _rrect(top, P.PIPE_LIGHT, (0, 12, 8, t - 16))
    _rrect(top, P.PIPE_SHADOW, (t - 12, 12, 10, t - 16))
    pygame.draw.rect(top, P.PIPE_SHADOW, (-4, 8, t + 8, t - 8), width=2, border_radius=6)
    body = _surf(t, t)
    _rrect(body, P.PIPE, (4, 0, t - 8, t))
    _rrect(body, P.PIPE_LIGHT, (8, 0, 8, t))
    _rrect(body, P.PIPE_SHADOW, (t - 16, 0, 10, t))
    return {"top": top, "body": body}


def make_platform_tile(metal: bool = False) -> pygame.Surface:
    t = 48
    s = _surf(t, t // 2)
    if metal:
        _rrect(s, P.METAL, (0, 0, t, t // 2), 6)
        _rrect(s, P.METAL_LIGHT, (0, 0, t, 6), 4)
        _rrect(s, P.METAL_SHADOW, (0, t // 2 - 6, t, 6), 4)
        for bx in (6, t - 12):
            pygame.draw.circle(s, P.METAL_SHADOW, (bx, t // 4), 2)
    else:
        _rrect(s, P.PLATFORM, (0, 0, t, t // 2), 6)
        _rrect(s, P.PLATFORM_TOP, (0, 0, t, 8), 4)
        pygame.draw.rect(s, P.GROUND_DIRT_SHADOW, (0, 0, t, t // 2), width=2, border_radius=6)
    return s


# ===========================================================================
#  COLLECTIBLES
# ===========================================================================
def make_coin_frames() -> List[pygame.Surface]:
    t = 32
    frames = []
    # 6 frames simulating a spinning coin by squashing horizontally.
    for i in range(6):
        s = _surf(t, t)
        ph = i / 6 * math.tau
        cw = max(4, int(abs(math.cos(ph)) * t * 0.7) + 4)
        x = t // 2 - cw // 2
        _rrect(s, P.COIN, (x, 3, cw, t - 6), cw // 2)
        if cw > 10:
            _rrect(s, P.COIN_SHINE, (x + 2, 5, max(2, cw // 4), t - 12), 3)
            _rrect(s, P.COIN_SHADOW, (x + cw - 4, 6, 3, t - 12), 2)
        frames.append(s)
    return frames


def make_mushroom() -> pygame.Surface:
    t = 40
    s = _surf(t, t)
    pygame.draw.ellipse(s, (0, 0, 0, 50), (6, t - 6, t - 12, 5))
    _rrect(s, P.MUSHROOM_STEM, (10, t // 2, t - 20, t // 2 - 4), 6)
    pygame.draw.ellipse(s, P.MUSHROOM_CAP, (2, 4, t - 4, t // 2 + 6))
    for (sx, sy, r) in [(12, 14, 5), (26, 12, 4), (20, 22, 6)]:
        pygame.draw.circle(s, P.MUSHROOM_SPOT, (sx, sy), r)
    for ex in (t // 2 - 6, t // 2 + 6):
        pygame.draw.circle(s, P.EYE, (ex, t - 12), 2)
    return s


def make_fire_flower_frames() -> List[pygame.Surface]:
    t = 40
    frames = []
    for i in range(2):
        s = _surf(t, t)
        _rrect(s, P.FLOWER_STEM, (t // 2 - 3, t // 2, 6, t // 2 - 4), 3)
        pygame.draw.ellipse(s, P.FLOWER_STEM, (6, t - 18, 14, 8))
        rot = i * 22
        for a in range(0, 360, 45):
            ang = math.radians(a + rot)
            px = t // 2 + math.cos(ang) * 11
            py = t // 3 + math.sin(ang) * 11
            pygame.draw.circle(s, P.FLOWER_PETAL, (int(px), int(py)), 6)
        pygame.draw.circle(s, P.FLOWER_CENTER, (t // 2, t // 3), 7)
        pygame.draw.circle(s, P.FIREBALL_EDGE, (t // 2, t // 3), 3)
        frames.append(s)
    return frames


def make_star_frames() -> List[pygame.Surface]:
    t = 40
    frames = []
    for i in range(4):
        s = _surf(t, t)
        glow = 0.5 + 0.5 * math.sin(i / 4 * math.tau)
        cx, cy, R, r = t // 2, t // 2, 17, 8
        pts = []
        for k in range(10):
            ang = math.pi / 2 + k * math.pi / 5
            rad = R if k % 2 == 0 else r
            pts.append((cx + math.cos(ang) * rad, cy - math.sin(ang) * rad))
        col = tuple(min(255, int(c + 25 * glow)) for c in P.STAR)
        pygame.draw.polygon(s, col, pts)
        pygame.draw.polygon(s, P.STAR_SHADOW, pts, width=2)
        pygame.draw.circle(s, P.EYE, (cx - 4, cy + 1), 2)
        pygame.draw.circle(s, P.EYE, (cx + 4, cy + 1), 2)
        frames.append(s)
    return frames


def make_fireball_frames() -> List[pygame.Surface]:
    t = 22
    frames = []
    for i in range(4):
        s = _surf(t, t)
        pygame.draw.circle(s, P.FIREBALL_EDGE, (t // 2, t // 2), 10)
        pygame.draw.circle(s, P.FIREBALL_MID, (t // 2, t // 2), 7)
        pygame.draw.circle(s, P.FIREBALL_CORE, (t // 2, t // 2), 4)
        frames.append(pygame.transform.rotate(s, i * 90))
    return frames


# ===========================================================================
#  FLAG / GOAL
# ===========================================================================
def make_flag() -> Dict[str, pygame.Surface]:
    pole = _surf(12, TILE_POLE := 48)
    _rrect(pole, P.FLAG_POLE, (4, 0, 4, TILE_POLE))
    pygame.draw.circle(pole, P.FLAG_CLOTH, (6, 4), 5)
    cloth = _surf(40, 28)
    pygame.draw.polygon(cloth, P.FLAG_CLOTH, [(0, 0), (40, 8), (0, 16)])
    pygame.draw.polygon(cloth, P.KOOPA_SHELL_SHADOW, [(0, 8), (24, 11), (0, 16)])
    return {"pole": pole, "cloth": cloth}


def make_checkpoint_frames() -> List[pygame.Surface]:
    frames = []
    for active in (False, True):
        s = _surf(24, 96)
        _rrect(s, P.METAL, (10, 0, 4, 96))
        col = (70, 190, 90) if active else (150, 156, 178)
        pygame.draw.polygon(s, col, [(14, 6), (24, 12), (14, 18)])
        frames.append(s)
    return frames


# ===========================================================================
#  SCENERY (parallax props)
# ===========================================================================
def make_cloud() -> pygame.Surface:
    s = _surf(120, 60)
    for (cx, cy, r) in [(34, 38, 22), (64, 30, 28), (92, 40, 20), (58, 44, 24)]:
        pygame.draw.circle(s, P.CLOUD_SHADOW, (cx, cy + 4), r)
    for (cx, cy, r) in [(34, 34, 22), (64, 26, 28), (92, 36, 20), (58, 40, 24)]:
        pygame.draw.circle(s, P.CLOUD, (cx, cy), r)
    return s


def make_hill(near: bool = False) -> pygame.Surface:
    w, h = (260, 150) if near else (200, 110)
    s = _surf(w, h)
    col = P.HILL_NEAR if near else P.HILL_FAR
    pygame.draw.ellipse(s, col, (0, h // 3, w, h * 2))
    pygame.draw.ellipse(s, P.GROUND_TOP_SHADOW, (0, h // 3, w, 30))
    return s


def make_bush() -> pygame.Surface:
    s = _surf(140, 60)
    for (cx, cy, r) in [(34, 42, 24), (70, 34, 28), (106, 42, 24)]:
        pygame.draw.circle(s, P.BUSH_SHADOW, (cx, cy + 3), r)
    for (cx, cy, r) in [(34, 40, 24), (70, 32, 28), (106, 40, 24)]:
        pygame.draw.circle(s, P.BUSH, (cx, cy), r)
    return s


def make_mountain() -> pygame.Surface:
    s = _surf(360, 220)
    pygame.draw.polygon(s, P.MOUNTAIN, [(0, 220), (180, 20), (360, 220)])
    pygame.draw.polygon(s, P.MOUNTAIN_SNOW, [(140, 70), (180, 20), (220, 70), (200, 60), (180, 80), (160, 60)])
    return s


# ===========================================================================
#  UI ICONS
# ===========================================================================
def make_heart(filled: bool = True) -> pygame.Surface:
    s = _surf(28, 26)
    col = P.RED if filled else (90, 70, 80)
    pygame.draw.circle(s, col, (9, 9), 8)
    pygame.draw.circle(s, col, (19, 9), 8)
    pygame.draw.polygon(s, col, [(2, 12), (26, 12), (14, 25)])
    if filled:
        pygame.draw.circle(s, P.MUSHROOM_SPOT, (7, 7), 2)
    return s


def make_coin_icon() -> pygame.Surface:
    s = _surf(28, 28)
    pygame.draw.circle(s, P.COIN, (14, 14), 12)
    pygame.draw.circle(s, P.COIN_SHADOW, (14, 14), 12, width=2)
    pygame.draw.circle(s, P.COIN_SHINE, (10, 10), 3)
    return s
