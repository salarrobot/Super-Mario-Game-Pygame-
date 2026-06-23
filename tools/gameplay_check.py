"""
gameplay_check.py
=================

Asserts that the core mechanics actually *work* (not just that they don't
crash): ground collision, coin collection, enemy stomping, power-ups and
reaching the goal. Complements smoketest.py. Run from the project root.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import config  # noqa: E402

DT = 1 / 60.0
failures = []


def check(name, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    if not cond:
        failures.append(name)


def main():
    from src.game import Game
    from src.states.play import PlayState

    g = Game()
    g.states.replace(PlayState(g), level_number=1)
    play = g.states.current
    p = play.player

    # 1) Gravity + ground collision: drop the player and let it settle.
    for _ in range(60):
        play.update(DT)
    check("player lands on ground", p.on_ground and not p.dead)
    ground_y = p.rect.bottom
    print(f"      settled bottom={p.rect.bottom}, on_ground={p.on_ground}")

    # 2) Coin collection.
    before = play.coins
    coin = play.level.coins[0]
    p.rect.center = coin.rect.center
    p.pos.update(p.rect.x, p.rect.y)
    play.update(DT)
    check("coin collected increments counter", play.coins == before + 1)
    check("coin collection adds score", play.score >= config.COIN_SCORE)

    # 3) Power-up changes state small -> big.
    check("starts small", p.state == "small")
    p.apply_powerup("mushroom")
    check("mushroom grows player", p.state == "big")
    p.apply_powerup("fire_flower")
    check("fire flower upgrades to fire", p.state == "fire")

    # 4) Enemy stomp defeats enemy and scores.
    enemy = play.level.enemies[0]
    score_before = play.score
    p.rect.midbottom = (enemy.rect.centerx, enemy.rect.top - 2)
    p.pos.update(p.rect.x, p.rect.y)
    p.vel.y = 6
    p.invincible = 0
    play.update(DT)
    check("stomp scores points", play.score > score_before)
    # The enemy is removed (goomba) or retracted (koopa) within a moment.
    for _ in range(40):
        play.update(DT)

    # 5) Fireball spawns when fire-powered.
    play.spawn_fireball(p.rect.centerx, p.rect.centery, 1)
    check("fireball spawned", len(play.fireballs) == 1)

    # 6) Reaching the goal starts the completion sequence.
    goal = play.level.goal
    p.rect.midbottom = goal.rect.midbottom
    p.pos.update(p.rect.x, p.rect.y)
    play.update(DT)
    check("touching goal triggers completion", play.completing)

    print("\nRESULT:", "ALL GAMEPLAY CHECKS PASSED" if not failures
          else f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
