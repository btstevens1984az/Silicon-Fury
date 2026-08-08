#!/usr/bin/env python3
"""Silicon Fury — launch the Brand Brawl."""

from __future__ import annotations

import argparse
import os

# Allow headless / CI capture via SDL dummy when needed
if os.environ.get("SILICON_FURY_HEADLESS") == "1":
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def main() -> None:
    parser = argparse.ArgumentParser(description="Silicon Fury — Tekken-style brand brawler")
    parser.add_argument(
        "--demo",
        choices=[
            "01-title-teams",
            "02-character-select",
            "03-versus-brawl",
            "04-special-moves",
            "05-story-ko",
        ],
        help="Record a scripted demo sequence for GIF export",
    )
    parser.add_argument(
        "--capture-dir",
        default="media/frames",
        help="Directory for demo frame sequences",
    )
    args = parser.parse_args()

    from silicon_fury.game import SiliconFury

    game = SiliconFury(
        capture_dir=args.capture_dir if args.demo else None,
        auto_demo=args.demo,
    )
    game.run()


if __name__ == "__main__":
    main()
