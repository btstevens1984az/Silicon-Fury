"""Aggressive CPU — dashes, jumps, air kicks, specials."""

from __future__ import annotations

import random

from typing import TYPE_CHECKING, Optional

from silicon_fury.fighter import Fighter

if TYPE_CHECKING:
    from silicon_fury.effects import EffectWorld


class CPUBrain:
    def __init__(self, difficulty: float = 0.7):
        self.difficulty = difficulty
        self.cooldown = 0

    def step(self, me: Fighter, foe: Fighter, fx: Optional["EffectWorld"] = None) -> None:
        if me.hp <= 0:
            return
        if self.cooldown > 0:
            self.cooldown -= 1
            # still chase while cooling down
            dist = foe.x - me.x
            if abs(dist) > 160 and me.on_ground and me.state in {"idle", "walk"}:
                me.move(1 if dist > 0 else -1)
            return

        dist = foe.x - me.x
        ad = abs(dist)
        me.facing = 1 if dist > 0 else -1

        # Block under fire
        if foe.state in {"punch", "kick", "air_kick", "special"} and ad < 130 and random.random() < 0.4 * self.difficulty:
            me.block(True)
            self.cooldown = 5
            return

        # Approach / dash in
        if ad > 200:
            if random.random() < 0.35 * self.difficulty:
                me.dash(1 if dist > 0 else -1)
                self.cooldown = 8
            else:
                me.move(1 if dist > 0 else -1)
            if random.random() < 0.05:
                me.jump()
            return

        if ad > 100:
            me.move(1 if dist > 0 else -1)
            roll = random.random()
            if roll < 0.1 * self.difficulty:
                me.jump()
                self.cooldown = 4
            elif roll < 0.22 * self.difficulty:
                me.kick()
                self.cooldown = 9
            elif roll < 0.32 * self.difficulty:
                me.punch()
                self.cooldown = 7
            return

        # Close range / aerial pressure
        if not me.on_ground:
            if random.random() < 0.55 * self.difficulty:
                me.kick()  # air kick
                self.cooldown = 10
            elif random.random() < 0.35:
                me.punch()
                self.cooldown = 8
            return

        roll = random.random()
        if me.meter >= 55 and roll < 0.2 * self.difficulty:
            me.special(fx)
            self.cooldown = 18
        elif roll < 0.28:
            me.punch()
            self.cooldown = 7
        elif roll < 0.52:
            me.kick()
            self.cooldown = 10
        elif roll < 0.68:
            me.jump()
            self.cooldown = 5
        elif roll < 0.8:
            me.dash(1 if dist > 0 else -1)
            self.cooldown = 8
        else:
            me.move(-1 if dist > 0 else 1)
            self.cooldown = 4
