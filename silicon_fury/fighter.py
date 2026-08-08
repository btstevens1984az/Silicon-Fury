"""Fighter entity — movement, attacks, specials, rendering."""

from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

import pygame

from silicon_fury.characters import Character
from silicon_fury.config import GROUND_Y, GRAVITY, WIDTH


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
        self.particles: List[dict] = []

        self.move_speed = 3.2 + char.speed * 0.035
        self.jump_power = 14.5 + char.speed * 0.02
        self.punch_dmg = 28 + char.power * 0.22
        self.kick_dmg = 38 + char.power * 0.28
        self.special_dmg = 95 + char.special * 0.55
        self.defense_factor = 1.0 - (char.defense / 220.0)
        self.reach_px = 58 + char.reach * 0.5

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
            self.set_state("jump", 20)

    def block(self, holding: bool) -> None:
        if self.hp <= 0 or self.hitstun > 0:
            return
        if holding and self.on_ground and self.state not in {"punch", "kick", "special"}:
            self.set_state("block", 4)
            self.vx *= 0.3

    def punch(self) -> None:
        if self.can_act() and self.state not in {"punch", "kick"}:
            self.set_state("punch", 16)
            self.vx = self.facing * 1.5

    def kick(self) -> None:
        if self.can_act() and self.state not in {"punch", "kick"}:
            self.set_state("kick", 20)
            self.vx = self.facing * 2.0

    def special(self) -> bool:
        if self.meter < 60 or not self.can_act():
            return False
        self.meter -= 60
        self.set_state("special", 40)
        self.vx = self.facing * (3.0 + self.char.speed * 0.02)
        self._burst(self.char.accent, 18)
        return True

    def take_hit(self, dmg: float, knock: float, attacker_facing: int) -> None:
        if self.state == "block":
            dmg *= 0.35
            knock *= 0.25
            self.meter = min(self.max_meter, self.meter + 4)
        else:
            self.hitstun = 14
            self.set_state("hit", 14)
            self.flash = 8
            self.combo = 0
        dmg *= self.defense_factor
        self.hp = max(0, self.hp - dmg)
        self.vx = attacker_facing * knock
        self.vy = -3.5 if self.state != "block" else -1.0
        self.on_ground = False
        self._burst(self.char.accent, 12)
        if self.hp <= 0:
            self.hp = 0
            self.set_state("ko", 120)
            self.hitstun = 120

    def gain_meter(self, amount: float) -> None:
        self.meter = min(self.max_meter, self.meter + amount)

    def attack_box(self) -> Optional[pygame.Rect]:
        def box(x_off: float, y: float, w: int, h: int) -> pygame.Rect:
            x = int(self.x + self.facing * x_off)
            if self.facing < 0:
                x -= w
            return pygame.Rect(x, int(y), w, h)

        elapsed_punch = 16 - self.state_t
        elapsed_kick = 20 - self.state_t
        elapsed_special = 40 - min(self.state_t, 40)
        if self.state == "punch" and 4 <= elapsed_punch <= 10:
            return box(36, self.y - 100, int(self.reach_px), 40)
        if self.state == "kick" and 6 <= elapsed_kick <= 14:
            return box(28, self.y - 70, int(self.reach_px + 22), 44)
        if self.state == "special" and 8 <= elapsed_special <= 32:
            return box(16, self.y - 130, int(self.reach_px + 70 + self.char.special * 0.35), 90)
        return None

    def body_box(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - 34), int(self.y - 150), 68, 150)

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
        self.vx *= 0.85

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        self.x = max(70, min(WIDTH - 70, self.x))
        if self.state == "idle":
            self.gain_meter(0.08)

        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _burst(self, color: Tuple[int, int, int], n: int = 8) -> None:
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(2.0, 6.5)
            self.particles.append(
                {
                    "x": self.x,
                    "y": self.y - 90,
                    "vx": math.cos(ang) * spd,
                    "vy": math.sin(ang) * spd - 1,
                    "life": random.randint(12, 26),
                    "color": color,
                    "r": random.randint(2, 5),
                }
            )

    def draw(self, surf: pygame.Surface) -> None:
        for p in self.particles:
            pygame.draw.circle(surf, p["color"], (int(p["x"]), int(p["y"])), p.get("r", 3))

        # Soft shadow
        shadow = pygame.Surface((120, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 110), (0, 0, 120, 28))
        surf.blit(shadow, (self.x - 60, GROUND_Y - 10))

        c = self.char
        flash = self.flash > 0
        skin = (255, 224, 196) if not flash else (255, 255, 255)
        primary = (255, 255, 255) if flash else c.primary
        secondary = c.secondary
        accent = c.accent
        f = self.facing

        bob = math.sin(pygame.time.get_ticks() / 160.0 + self.x * 0.01) * (3 if self.state == "idle" else 0)
        lean = 0
        arm_l = arm_r = 0
        leg_l = leg_r = 0
        crouch = 0

        if self.state == "walk":
            phase = math.sin(pygame.time.get_ticks() / 70.0)
            leg_l, leg_r = phase * 14, -phase * 14
        elif self.state == "punch":
            arm_r = f * 46
            lean = f * 12
        elif self.state == "kick":
            leg_r = f * 52
            lean = f * 10
            arm_l = -f * 16
        elif self.state == "special":
            arm_r = f * 58
            lean = f * 16
            # Expanding energy ring
            pulse = 40 - min(self.state_t, 40)
            radius = 55 + pulse * 3
            aura = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*accent, 40), (radius, radius), radius)
            pygame.draw.circle(aura, (*primary, 70), (radius, radius), int(radius * 0.55), 4)
            surf.blit(aura, (self.x - radius, self.y - 100 - radius // 2))
            # Beam / shockwave
            beam = pygame.Surface((160, 36), pygame.SRCALPHA)
            pygame.draw.ellipse(beam, (*accent, 120), (0, 0, 160, 36))
            bx = self.x + (20 if f > 0 else -180)
            surf.blit(beam, (bx, self.y - 95))
        elif self.state == "block":
            arm_l = arm_r = -f * 8
            lean = -f * 6
            crouch = 8
        elif self.state == "hit":
            lean = -f * 18
        elif self.state == "ko":
            body = pygame.Rect(self.x - 70, self.y - 40, 140, 36)
            pygame.draw.ellipse(surf, secondary, body)
            pygame.draw.ellipse(surf, primary, (self.x - 70, self.y - 40, 140, 36), 3)
            hx = self.x - f * 50
            pygame.draw.circle(surf, primary, (int(hx), int(self.y - 48)), 22)
            pygame.draw.circle(surf, skin, (int(hx), int(self.y - 48)), 17)
            pygame.draw.rect(surf, accent, (hx - 12, self.y - 54, 24, 8), border_radius=3)
            return
        elif self.state == "jump":
            leg_l, leg_r = -8, 8

        cx = self.x + lean
        cy = self.y - 78 + bob + crouch

        # Legs (thigh + shin)
        hip_l = (cx - 12, cy + 28)
        hip_r = (cx + 12, cy + 28)
        foot_l = (cx - 18 + leg_l, cy + 78)
        foot_r = (cx + 18 + leg_r, cy + 78)
        pygame.draw.line(surf, secondary, hip_l, foot_l, 14)
        pygame.draw.line(surf, secondary, hip_r, foot_r, 14)
        pygame.draw.circle(surf, primary, (int(foot_l[0]), int(foot_l[1])), 9)
        pygame.draw.circle(surf, primary, (int(foot_r[0]), int(foot_r[1])), 9)

        # Torso armor
        torso = pygame.Rect(cx - 28, cy - 36, 56, 70)
        pygame.draw.rect(surf, primary, torso, border_radius=14)
        pygame.draw.rect(surf, secondary, (cx - 22, cy - 28, 44, 54), border_radius=10)
        # Brand chest plate
        pygame.draw.polygon(
            surf,
            accent,
            [(cx, cy - 18), (cx + f * 18, cy + 4), (cx, cy + 16), (cx - f * 10, cy + 4)],
        )
        pygame.draw.rect(surf, accent, (cx - 20, cy + 22, 40, 6), border_radius=2)

        # Shoulders / arms
        shoulder_l = (cx - 28, cy - 22)
        shoulder_r = (cx + 28, cy - 22)
        hand_l = (cx - 48 - arm_l * 0.15, cy + 8 + abs(arm_l) * 0.05)
        hand_r = (cx + 48 + arm_r, cy + 2)
        pygame.draw.line(surf, skin, shoulder_l, hand_l, 11)
        pygame.draw.line(surf, skin, shoulder_r, hand_r, 12)
        pygame.draw.circle(surf, secondary, (int(shoulder_l[0]), int(shoulder_l[1])), 11)
        pygame.draw.circle(surf, secondary, (int(shoulder_r[0]), int(shoulder_r[1])), 11)
        pygame.draw.circle(surf, accent, (int(hand_l[0]), int(hand_l[1])), 10)
        glove_r = 14 if self.state in {"punch", "special"} else 11
        pygame.draw.circle(surf, accent, (int(hand_r[0]), int(hand_r[1])), glove_r)
        if self.state in {"punch", "special"}:
            pygame.draw.circle(surf, (255, 255, 255), (int(hand_r[0]), int(hand_r[1])), glove_r, 2)

        # Head + helm
        pygame.draw.circle(surf, skin, (int(cx), int(cy - 58)), 20)
        pygame.draw.rect(surf, secondary, (cx - 18, cy - 70, 36, 18), border_radius=6)
        pygame.draw.rect(surf, primary, (cx - 16, cy - 68, 32, 12), border_radius=4)
        pygame.draw.rect(surf, accent, (cx - 12, cy - 65, 24, 7), border_radius=3)
        # Eye glow toward facing side
        pygame.draw.circle(surf, accent, (int(cx + f * 7), int(cy - 58)), 4)
        pygame.draw.circle(surf, (255, 255, 255), (int(cx + f * 7), int(cy - 58)), 2)

        # Special callout
        if self.state == "special":
            font = pygame.font.SysFont("Impact", 26)
            label = font.render(self.char.special_name, True, accent)
            outline = font.render(self.char.special_name, True, (0, 0, 0))
            lx = self.x - label.get_width() / 2
            ly = self.y - 200
            surf.blit(outline, (lx + 2, ly + 2))
            surf.blit(label, (lx, ly))
