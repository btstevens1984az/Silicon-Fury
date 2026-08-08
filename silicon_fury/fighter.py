"""Fighter entity — articulated limbs, aerial combat, explosive hits."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, List, Optional

import pygame

from silicon_fury.body import draw_fighter_body
from silicon_fury.characters import Character
from silicon_fury.config import GRAVITY, GROUND_Y, WIDTH

if TYPE_CHECKING:
    from silicon_fury.effects import EffectWorld


class Fighter:
    def __init__(self, char: Character, x: float, facing: int = 1, is_cpu: bool = False):
        self.char = char
        self.x = x
        self.y = float(GROUND_Y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = facing
        self.is_cpu = is_cpu

        self.max_hp = 1000 + char.hp * 8
        self.hp = float(self.max_hp)
        self.meter = 0.0
        self.max_meter = 100.0

        self.state = "idle"
        self.state_t = 0
        self.state_max = 0
        self.hitstun = 0
        self.attack_hit = False
        self.on_ground = True
        self.combo = 0
        self.round_wins = 0
        self.flash = 0
        self.walk_phase = random.random() * 10
        self.air_jumps = 0
        self.dash_t = 0

        self.move_speed = 4.6 + char.speed * 0.05
        self.jump_power = 16.5 + char.speed * 0.03
        self.punch_dmg = 34 + char.power * 0.26
        self.kick_dmg = 48 + char.power * 0.32
        self.special_dmg = 125 + char.special * 0.65
        self.defense_factor = 1.0 - (char.defense / 220.0)
        self.reach_px = 78 + char.reach * 0.6

        # local sparks (also mirrored into EffectWorld on hits)
        self.sparks: List[dict] = []

    def set_state(self, state: str, frames: int = 12) -> None:
        self.state = state
        self.state_t = frames
        self.state_max = frames
        if state in {"punch", "kick", "air_kick", "special"}:
            self.attack_hit = False

    def can_act(self) -> bool:
        return self.hp > 0 and self.hitstun <= 0 and self.state not in {"ko", "special"}

    def _attacking(self) -> bool:
        return self.state in {"punch", "kick", "air_kick", "special"}

    def move(self, direction: int) -> None:
        if self.hp <= 0 or self.hitstun > 0 or self.state in {"ko", "special", "block"}:
            return
        # Seamless: allow movement during late attack recovery / air
        if self._attacking() and self.state_t > self.state_max * 0.35:
            return
        speed = self.move_speed if self.on_ground else self.move_speed * 0.85
        self.vx = direction * speed
        self.facing = 1 if direction > 0 else -1
        if self.on_ground and not self._attacking():
            self.set_state("walk", 10)
            self.walk_phase += 0.35

    def dash(self, direction: int) -> None:
        if not self.can_act() or self.dash_t > 0:
            return
        self.facing = 1 if direction > 0 else -1
        self.vx = self.facing * (self.move_speed * 2.4)
        self.dash_t = 14
        if self.on_ground:
            self.set_state("walk", 10)

    def jump(self) -> None:
        if self.hp <= 0 or self.hitstun > 0 or self.state in {"ko", "special"}:
            return
        if self.on_ground:
            self.vy = -self.jump_power
            self.on_ground = False
            self.air_jumps = 1
            self.set_state("jump", 28)
        elif self.air_jumps > 0 and self.state not in {"air_kick"}:
            # short double-hop for aerial freedom
            self.vy = -self.jump_power * 0.72
            self.air_jumps -= 1
            self.set_state("jump", 20)

    def block(self, holding: bool) -> None:
        if self.hp <= 0 or self.hitstun > 0:
            return
        if holding and self.on_ground and self.state not in {"punch", "kick", "air_kick", "special"}:
            self.set_state("block", 4)
            self.vx *= 0.2

    def punch(self) -> None:
        if self.hp <= 0 or self.hitstun > 0 or self.state in {"ko", "special"}:
            return
        if self.state in {"punch", "kick", "air_kick"} and self.state_t > 6:
            return
        if not self.on_ground:
            # air punch / jab
            self.set_state("punch", 14)
            self.vx += self.facing * 1.5
            return
        self.set_state("punch", 14)
        self.vx = self.facing * 3.2

    def kick(self) -> None:
        if self.hp <= 0 or self.hitstun > 0 or self.state in {"ko", "special"}:
            return
        if self.state in {"punch", "kick", "air_kick"} and self.state_t > 6:
            return
        if not self.on_ground:
            self.set_state("air_kick", 18)
            self.vx = self.facing * 3.5
            self.vy = min(self.vy, -2.5)  # hang for the kick
            return
        self.set_state("kick", 18)
        self.vx = self.facing * 3.8

    def special(self, fx: Optional["EffectWorld"] = None) -> bool:
        if self.meter < 55 or self.hp <= 0 or self.hitstun > 0 or self.state == "ko":
            return False
        if self.state == "special":
            return False
        self.meter -= 55
        self.set_state("special", 38)
        self.vx = self.facing * (4.2 + self.char.speed * 0.025)
        if not self.on_ground:
            self.vy = -3
        if fx:
            fx.explosion(self.x + self.facing * 40, self.y - 110, self.char.accent, 0.85)
            fx.fire_burst(self.x, self.y - 40, 0.7)
        for _ in range(14):
            self.sparks.append(
                {
                    "x": self.x,
                    "y": self.y - 120,
                    "vx": self.facing * random.uniform(2, 9),
                    "vy": random.uniform(-5, 2),
                    "life": random.randint(12, 26),
                    "color": self.char.accent,
                }
            )
        return True

    def take_hit(
        self,
        dmg: float,
        knock: float,
        attacker_facing: int,
        fx: Optional["EffectWorld"] = None,
        kind: str = "punch",
    ) -> None:
        blocked = self.state == "block"
        impact_x = self.x - attacker_facing * 12
        impact_y = self.y - (140 if kind == "punch" else 90)
        if blocked:
            dmg *= 0.28
            knock *= 0.18
            self.meter = min(self.max_meter, self.meter + 6)
            if fx:
                fx.hit_sparks(impact_x, impact_y, attacker_facing, (255, 220, 120))
        else:
            self.hitstun = 10 if kind != "special" else 16
            self.set_state("hit", self.hitstun)
            self.flash = 8
            self.combo = 0
            if fx:
                power = 1.0 if kind == "punch" else (1.35 if kind == "kick" or kind == "air_kick" else 2.0)
                fx.blood_burst(impact_x, impact_y, attacker_facing, power)
                fx.hit_sparks(impact_x, impact_y, attacker_facing, self.char.accent)
                if kind in {"kick", "air_kick"}:
                    fx.fire_burst(impact_x, impact_y, 0.45)
                if kind == "special":
                    fx.explosion(impact_x, impact_y, self.char.accent, 1.3)
                    fx.blood_burst(impact_x, impact_y - 20, attacker_facing, 1.8)
        dmg *= self.defense_factor
        self.hp = max(0, self.hp - dmg)
        self.vx = attacker_facing * knock
        self.vy = -5.5 if not blocked else -1.5
        if kind == "air_kick":
            self.vy = -7.5
        self.on_ground = False
        if self.hp <= 0:
            self.hp = 0
            self.set_state("ko", 140)
            self.hitstun = 140
            if fx:
                fx.blood_burst(self.x, self.y - 100, attacker_facing, 2.4)
                fx.explosion(self.x, self.y - 80, (255, 60, 40), 1.6)
                fx.fire_burst(self.x, self.y - 20, 1.2)

    def gain_meter(self, amount: float) -> None:
        self.meter = min(self.max_meter, self.meter + amount)

    def attack_box(self) -> Optional[pygame.Rect]:
        def box(x_off: float, y: float, w: int, h: int) -> pygame.Rect:
            x = int(self.x + self.facing * x_off)
            if self.facing < 0:
                x -= w
            return pygame.Rect(x, int(y), w, h)

        prog = 1.0 - (self.state_t / max(1, self.state_max))
        if self.state == "punch" and 0.22 <= prog <= 0.72:
            return box(48, self.y - 145, int(self.reach_px), 50)
        if self.state == "kick" and 0.28 <= prog <= 0.78:
            return box(42, self.y - 100, int(self.reach_px + 36), 56)
        if self.state == "air_kick" and 0.25 <= prog <= 0.8:
            return box(40, self.y - 120, int(self.reach_px + 40), 60)
        if self.state == "special" and 0.18 <= prog <= 0.85:
            return box(24, self.y - 170, int(self.reach_px + 100 + self.char.special * 0.4), 120)
        return None

    def body_box(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - 36), int(self.y - 200), 72, 200)

    def update(self) -> None:
        if self.hitstun > 0:
            self.hitstun -= 1
        if self.dash_t > 0:
            self.dash_t -= 1
        if self.state_t > 0:
            self.state_t -= 1
            if self.state_t <= 0 and self.state != "ko":
                if not self.on_ground:
                    self.state = "jump"
                    self.state_t = 8
                    self.state_max = 8
                else:
                    self.state = "idle"
                    self.state_max = 0

        if self.flash > 0:
            self.flash -= 1

        if self.state == "walk":
            self.walk_phase += 0.42
        elif self.state == "idle" and self.on_ground:
            self.walk_phase += 0.08

        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        # less sticky friction so movement feels free
        self.vx *= 0.90 if self.on_ground else 0.96

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            if not self.on_ground and self.state not in {"ko", "hit"}:
                if self.state in {"jump", "air_kick"}:
                    self.state = "idle"
            self.on_ground = True
            self.air_jumps = 1
        else:
            self.on_ground = False

        self.x = max(70, min(WIDTH - 70, self.x))
        if self.state == "idle":
            self.gain_meter(0.12)

        for s in self.sparks:
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["life"] -= 1
        self.sparks = [s for s in self.sparks if s["life"] > 0]

    def draw(self, surf: pygame.Surface) -> None:
        for s in self.sparks:
            pygame.draw.circle(surf, s["color"], (int(s["x"]), int(s["y"])), 3)

        # Special aura — ring only (no filled blob that reads as a dark box)
        if self.state == "special":
            pulse = self.state_max - self.state_t
            radius = 70 + pulse * 4
            aura = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*self.char.accent, 110), (radius, radius), radius, 6)
            pygame.draw.circle(aura, (*self.char.primary, 70), (radius, radius), int(radius * 0.72), 3)
            surf.blit(aura, (self.x - radius, self.y - 130 - radius // 2))

        draw_fighter_body(
            surf,
            self.char,
            self.x,
            self.y,
            self.facing,
            self.state,
            self.state_t,
            self.state_max,
            self.on_ground,
            self.flash,
            self.walk_phase,
        )

        if self.state == "special":
            font = pygame.font.SysFont("Impact", 30)
            label = font.render(self.char.special_name, True, self.char.accent)
            outline = font.render(self.char.special_name, True, (0, 0, 0))
            lx = self.x - label.get_width() / 2
            ly = self.y - 290
            surf.blit(outline, (lx + 2, ly + 2))
            surf.blit(label, (lx, ly))
