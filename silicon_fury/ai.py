"""Simple but lively CPU opponent."""

from __future__ import annotations

import random

from silicon_fury.fighter import Fighter


class CPUBrain:
    def __init__(self, difficulty: float = 0.65):
        self.difficulty = difficulty
        self.cooldown = 0

    def step(self, me: Fighter, foe: Fighter) -> None:
        if me.hp <= 0:
            return
        if self.cooldown > 0:
            self.cooldown -= 1
            return

        dist = foe.x - me.x
        ad = abs(dist)
        me.facing = 1 if dist > 0 else -1

        # Block sometimes when foe attacks
        if foe.state in {"punch", "kick", "special"} and ad < 120 and random.random() < 0.45 * self.difficulty:
            me.block(True)
            self.cooldown = 6
            return

        if ad > 140:
            me.move(1 if dist > 0 else -1)
            if random.random() < 0.03:
                me.jump()
        elif ad > 70:
            if random.random() < 0.55:
                me.move(1 if dist > 0 else -1)
            if random.random() < 0.12 * self.difficulty:
                me.kick()
                self.cooldown = 10
            elif random.random() < 0.1 * self.difficulty:
                me.punch()
                self.cooldown = 8
        else:
            roll = random.random()
            if me.meter >= 60 and roll < 0.18 * self.difficulty:
                me.special()
                self.cooldown = 20
            elif roll < 0.4:
                me.punch()
                self.cooldown = 8
            elif roll < 0.7:
                me.kick()
                self.cooldown = 12
            elif roll < 0.82:
                me.jump()
                self.cooldown = 6
            else:
                me.move(-1 if dist > 0 else 1)
                self.cooldown = 5
