"""
main.py
=======

Entry point for Super Pixel Quest.

Run from the project root:

    python main.py

This file stays intentionally tiny: it just makes sure the project root is on
the import path (so the ``src`` package resolves no matter where the game is
launched from), constructs the :class:`Game` and starts its main loop, with a
friendly message if pygame is missing.
"""

import os
import sys

# Ensure the project root (this file's directory) is importable as a package
# root, so `import config` and `from src... import ...` always work.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("PyGame is required. Install dependencies with:\n"
              "    pip install -r requirements.txt")
        sys.exit(1)

    from src.game import Game
    Game().run()


if __name__ == "__main__":
    main()
