"""Fighter entity — Tekken-style sprite combat with blood FX."""

from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

import pygame

from silicon_fury.assets import fighter_sprite, tint_surface
from silicon_fury.characters import Character
from silicon_fury.config import GRAVITY, GROUND_Y, WIDTH


class BloodDrop:
    __slots__ = ("x", "y", "vx", "vy", "life", "r", "dark")

    def __init__(self, x: float, y: float):
        ang = random.uniform(-2.4, -0.7)
        spd = random.uniform(3.5, 11)
        self.x = x
        self.y = y
        self.vx = math.cos(ang) * spd * random.choice([-1, 1])
        self.vy = math.sin(ang) * spd - random.uniform(2, 6)
        self.life = random.randint(18, 40)
        self.r = random.randint(2, 5)
        self.dark = random.random() < 0.35


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
        self.hitstun = 0
        self.attack_hit = False
        self.on_ground = True
        self.combo = 0
        self.round_wins = 0
        self.flash = 0
        self.blood: List[BloodDrop] = []
        self.sparks: List[dict] = []
        self.base_sprite = fighter_sprite(char.id)

        self.move_speed = 3.4 + char.speed * 0.038
        self.jump_power = 15.0 + char.speed * 0.02
        self.punch_dmg = 32 + char.power * 0.24
        self.kick_dmg = 44 + char.power * 0.3
        self.special_dmg = 110 + char.special * 0.6
        self.defense_factor = 1.0 - (char.defense / 220.0)
        self.reach_px = 70 + char.reach * 0.55

    def set_state(self, state: str, frames: int = 12) -> None:
        self.state = state
        self.state_t = frames
        if state in {"punch", "kick", "special"}:
            self.attack_hit = False

    def can_act(self) -> bool:
        return self.hp > 0 and self.hitstun <= 0 and self.state not in {"ko", "special"}

    def move(self, direction: int) -> None:
        if not self.can_act() or self.state in {"punch", "kick", "block"}:
            return
        self.vx = direction * self.move_speed
        self.facing = 1 if direction > 0 else -1
        if self.on_ground:
            self.set_state("walk", 8)

    def jump(self) -> None:
        if self.can_act() and self.on_ground:
            self.vy = -self.jump_power
            self.on_ground = False
            self.set_state("jump", 22)

    def block(self, holding: bool) -> None:
        if self.hp <= 0 or self.hitstun > 0:
            return
        if holding and self.on_ground and self.state not in {"punch", "kick", "special"}:
            self.set_state("block", 4)
            self.vx *= 0.25

    def punch(self) -> None:
        if self.can_act() and self.state not in {"punch", "kick"}:
            self.set_state("punch", 16)
            self.vx = self.facing * 2.2

    def kick(self) -> None:
        if self.can_act() and self.state not in {"punch", "kick"}:
            self.set_state("kick", 20)
            self.vx = self.facing * 2.8

    def special(self) -> bool:
        if self.meter < 60 or not self.can_act():
            return False
        self.meter -= 60
        self.set_state("special", 42)
        self.vx = self.facing * (3.4 + self.char.speed * 0.02)
        for _ in range(10):
            self.sparks.append(
                {
                    "x": self.x,
                    "y": self.y - 120,
                    "vx": self.facing * random.uniform(2, 8),
                    "vy": random.uniform(-4, 2),
                    "life": random.randint(12, 24),
                    "color": self.char.accent,
                }
            )
        return True

    def _spawn_blood(self, amount: int, facing: int) -> None:
        for _ in range(amount):
            d = BloodDrop(self.x + facing * 20, self.y - random.uniform(70, 140))
            d.vx = abs(d.vx) * facing + random.uniform(-1, 1)
            self.blood.append(d)

    def take_hit(self, dmg: float, knock: float, attacker_facing: int) -> None:
        blocked = self.state == "block"
        if blocked:
            dmg *= 0.32
            knock *= 0.2
            self.meter = min(self.max_meter, self.meter + 5)
            # sparks instead of heavy blood when blocked
            for _ in range(6):
                self.sparks.append(
                    {
                        "x": self.x - attacker_facing * 10,
                        "y": self.y - 100,
                        "vx": random.uniform(-4, 4),
                        "vy": random.uniform(-3, 1),
                        "life": 12,
                        "color": (255, 220, 120),
                    }
                )
        else:
            self.hitstun = 16
            self.set_state("hit", 16)
            self.flash = 10
            self.combo = 0
            blood_n = 10 + int(min(28, dmg / 6))
            self._spawn_blood(blood_n, attacker_facing)
        dmg *= self.defense_factor
        self.hp = max(0, self.hp - dmg)
        self.vx = attacker_facing * knock
        self.vy = -4.2 if not blocked else -1.2
        self.on_ground = False
        if self.hp <= 0:
            self.hp = 0
            self.set_state("ko", 140)
            self.hitstun = 140
            self._spawn_blood(40, attacker_facing)

    def gain_meter(self, amount: float) -> None:
        self.meter = min(self.max_meter, self.meter + amount)

    def attack_box(self) -> Optional[pygame.Rect]:
        def box(x_off: float, y: float, w: int, h: int) -> pygame.Rect:
            x = int(self.x + self.facing * x_off)
            if self.facing < 0:
                x -= w
            return pygame.Rect(x, int(y), w, h)

        ep = 16 - self.state_t
        ek = 20 - self.state_t
        es = 42 - min(self.state_t, 42)
        if self.state == "punch" and 4 <= ep <= 11:
            return box(40, self.y - 130, int(self.reach_px), 48)
        if self.state == "kick" and 6 <= ek <= 15:
            return box(36, self.y - 90, int(self.reach_px + 28), 52)
        if self.state == "special" and 8 <= es <= 34:
            return box(20, self.y - 160, int(self.reach_px + 90 + self.char.special * 0.4), 110)
        return None

    def body_box(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - 40), int(self.y - 200), 80, 200)

    def update(self) -> None:
        if self.hitstun > 0:
            self.hitstun -= 1
        if self.state_t > 0:
            self.state_t -= 1
            if self.state_t <= 0 and self.state != "ko":
                self.state = "idle"
        if self.flash > 0:
            self.flash -= 1

        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.86

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        self.x = max(90, min(WIDTH - 90, self.x))
        if self.state == "idle":
            self.gain_meter(0.09)

        for b in self.blood:
            b.vy += 0.55
            b.x += b.vx
            b.y += b.vy
            b.life -= 1
            if b.y > GROUND_Y - 4:
                b.y = GROUND_Y - 4
                b.vx *= 0.4
                b.vy = 0
        self.blood = [b for b in self.blood if b.life > 0]

        for s in self.sparks:
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["life"] -= 1
        self.sparks = [s for s in self.sparks if s["life"] > 0]

    def _posed_sprite(self) -> pygame.Surface:
        spr = self.base_sprite
        # Pose transforms to sell attacks (Tekken-like motion readability)
        angle = 0
        scale_x, scale_y = 1.0, 1.0
        if self.state == "punch":
            angle = -12 * self.facing
            scale_x = 1.08
        elif self.state == "kick":
            angle = 16 * self.facing
            scale_x = 1.1
            scale_y = 0.96
        elif self.state == "special":
            pulse = 1.0 + (42 - min(self.state_t, 42)) * 0.004
            scale_x = scale_y = pulse
            angle = -6 * self.facing
        elif self.state == "block":
            scale_y = 0.94
            angle = 4 * self.facing
        elif self.state == "hit":
            angle = 18 * (-self.facing)
            scale_x = 0.95
        elif self.state == "ko":
            angle = 80 * (-self.facing)
            scale_y = 0.7
        elif self.state == "walk":
            bob = math.sin(pygame.time.get_ticks() / 70.0) * 2
            angle = bob * self.facing
        elif self.state == "jump":
            angle = -8 * self.facing

        w, h = spr.get_width(), spr.get_height()
        spr = pygame.transform.smoothscale(spr, (max(1, int(w * scale_x)), max(1, int(h * scale_y))))
        if self.facing < 0:
            spr = pygame.transform.flip(spr, True, False)
        if abs(angle) > 0.1:
            spr = pygame.transform.rotate(spr, angle)
        if self.flash > 0:
            spr = tint_surface(spr, (255, 80, 80), 0.55)
        elif self.state == "special":
            spr = tint_surface(spr, self.char.accent, 0.25)
        return spr

    def draw(self, surf: pygame.Surface) -> None:
        # Blood first (under/around character)
        for b in self.blood:
            col = (90, 0, 0) if b.dark else (170, 10, 20)
            pygame.draw.circle(surf, col, (int(b.x), int(b.y)), b.r)
            if b.y >= GROUND_Y - 6:
                pygame.draw.ellipse(surf, (110, 0, 10), (int(b.x - b.r), int(GROUND_Y - 5), b.r * 3, 6))

        for s in self.sparks:
            pygame.draw.circle(surf, s["color"], (int(s["x"]), int(s["y"])), 3)

        # Contact shadow
        shadow = pygame.Surface((160, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 130), (0, 0, 160, 36))
        surf.blit(shadow, (self.x - 80, GROUND_Y - 12))

        spr = self._posed_sprite()
        rect = spr.get_rect()
        if self.state == "ko":
            rect.midbottom = (int(self.x), int(self.y - 10))
        else:
            # Bob idle
            bob = math.sin(pygame.time.get_ticks() / 180.0 + self.x * 0.01) * (3 if self.state == "idle" else 0)
            lunge = 0
            if self.state == "punch":
                lunge = self.facing * 28
            elif self.state == "kick":
                lunge = self.facing * 36
            elif self.state == "special":
                lunge = self.facing * 48
            elif self.state == "hit":
                lunge = -self.facing * 22
            rect.midbottom = (int(self.x + lunge), int(self.y + bob))

        # Special aura ring
        if self.state == "special":
            pulse = 42 - min(self.state_t, 42)
            radius = 70 + pulse * 3
            aura = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*self.char.accent, 50), (radius, radius), radius, 6)
            pygame.draw.circle(aura, (*self.char.primary, 35), (radius, radius), int(radius * 0.7))
            surf.blit(aura, (rect.centerx - radius, rect.centery - radius))
            # Energy slash
            slash = pygame.Surface((220, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(slash, (*self.char.accent, 140), (0, 0, 220, 50))
            sx = rect.centerx if self.facing > 0 else rect.centerx - 220
            surf.blit(slash, (sx, rect.centery - 20))

        surf.blit(spr, rect)

        if self.state == "special":
            font = pygame.font.SysFont("Impact", 30)
            label = font.render(self.char.special_name, True, self.char.accent)
            outline = font.render(self.char.special_name, True, (0, 0, 0))
            lx = self.x - label.get_width() / 2
            ly = self.y - 250
            surf.blit(outline, (lx + 2, ly + 2))
            surf.blit(label, (lx, ly))
