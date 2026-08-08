"""World FX — blood, fire, explosions, sparks for explosive combat."""

from __future__ import annotations

import math
import random
from typing import List, Tuple

import pygame

from silicon_fury.config import GROUND_Y, HEIGHT, WIDTH


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "r", "color", "kind", "gravity")

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        life: int,
        r: float,
        color: Tuple[int, int, int],
        kind: str = "spark",
        gravity: float = 0.35,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.r = r
        self.color = color
        self.kind = kind
        self.gravity = gravity


class EffectWorld:
    def __init__(self) -> None:
        self.particles: List[Particle] = []
        self.flashes: List[dict] = []
        self.shockwaves: List[dict] = []
        self.fire_patches: List[dict] = []

    def clear(self) -> None:
        self.particles.clear()
        self.flashes.clear()
        self.shockwaves.clear()
        self.fire_patches.clear()

    def blood_burst(self, x: float, y: float, facing: int, power: float = 1.0) -> None:
        n = int(18 * power) + random.randint(8, 16)
        for _ in range(n):
            ang = random.uniform(-2.6, -0.4)
            spd = random.uniform(4, 14) * (0.7 + 0.5 * power)
            vx = math.cos(ang) * spd * facing + random.uniform(-2, 2)
            vy = math.sin(ang) * spd - random.uniform(2, 8)
            dark = random.random() < 0.4
            col = (70, 0, 8) if dark else (190, 12, 28)
            self.particles.append(
                Particle(x, y, vx, vy, random.randint(22, 55), random.uniform(2, 6), col, "blood", 0.6)
            )
        # arterial streak
        for _ in range(int(6 * power)):
            self.particles.append(
                Particle(
                    x,
                    y - random.uniform(0, 20),
                    facing * random.uniform(8, 16),
                    random.uniform(-6, -1),
                    random.randint(14, 28),
                    random.uniform(2, 4),
                    (160, 0, 20),
                    "blood",
                    0.5,
                )
            )

    def fire_burst(self, x: float, y: float, power: float = 1.0) -> None:
        for _ in range(int(22 * power)):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(1, 7) * power
            col = random.choice(
                [(255, 220, 80), (255, 140, 30), (255, 80, 20), (255, 40, 10), (255, 250, 200)]
            )
            self.particles.append(
                Particle(
                    x + random.uniform(-10, 10),
                    y + random.uniform(-10, 10),
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - random.uniform(1, 4),
                    random.randint(16, 36),
                    random.uniform(3, 9),
                    col,
                    "fire",
                    -0.08,  # fire rises
                )
            )
        self.fire_patches.append(
            {"x": x, "y": min(y + 20, GROUND_Y - 8), "life": int(40 * power), "r": 28 * power}
        )

    def explosion(self, x: float, y: float, color: Tuple[int, int, int], power: float = 1.0) -> None:
        self.flashes.append({"x": x, "y": y, "life": int(10 + 6 * power), "r": 40 * power, "color": color})
        self.shockwaves.append({"x": x, "y": y, "life": int(18 + 8 * power), "r": 20.0, "max_r": 120 * power, "color": color})
        self.fire_burst(x, y, power)
        for _ in range(int(16 * power)):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(3, 12) * power
            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - 2,
                    random.randint(12, 30),
                    random.uniform(2, 5),
                    color,
                    "ember",
                    0.2,
                )
            )
        # debris
        for _ in range(int(10 * power)):
            self.particles.append(
                Particle(
                    x,
                    y,
                    random.uniform(-10, 10),
                    random.uniform(-12, -2),
                    random.randint(20, 40),
                    random.uniform(2, 4),
                    (40, 40, 50),
                    "debris",
                    0.55,
                )
            )

    def hit_sparks(self, x: float, y: float, facing: int, color: Tuple[int, int, int]) -> None:
        for _ in range(14):
            self.particles.append(
                Particle(
                    x,
                    y,
                    facing * random.uniform(2, 10) + random.uniform(-2, 2),
                    random.uniform(-8, 2),
                    random.randint(8, 18),
                    random.uniform(2, 4),
                    color,
                    "spark",
                    0.25,
                )
            )

    def update(self) -> None:
        for p in self.particles:
            p.vy += p.gravity
            p.x += p.vx
            p.y += p.vy
            p.life -= 1
            if p.kind == "blood" and p.y >= GROUND_Y - 3:
                p.y = GROUND_Y - 3
                p.vx *= 0.45
                p.vy = 0
                p.r = max(1.5, p.r * 0.98)
            if p.kind == "fire":
                p.r *= 0.97
                p.vx *= 0.96
        self.particles = [p for p in self.particles if p.life > 0 and  -40 < p.x < WIDTH + 40 and p.y < HEIGHT + 40]

        for f in self.flashes:
            f["life"] -= 1
            f["r"] *= 1.08
        self.flashes = [f for f in self.flashes if f["life"] > 0]

        for s in self.shockwaves:
            s["life"] -= 1
            t = 1.0 - s["life"] / max(1, s.get("max_life", 26))
            s["r"] = s["r"] + (s["max_r"] - s["r"]) * 0.18
        self.shockwaves = [s for s in self.shockwaves if s["life"] > 0]

        for fp in self.fire_patches:
            fp["life"] -= 1
            # keep feeding flame particles
            if fp["life"] % 3 == 0:
                self.particles.append(
                    Particle(
                        fp["x"] + random.uniform(-fp["r"], fp["r"]),
                        fp["y"],
                        random.uniform(-1, 1),
                        random.uniform(-4, -1),
                        random.randint(10, 22),
                        random.uniform(3, 7),
                        random.choice([(255, 160, 40), (255, 90, 20), (255, 220, 90)]),
                        "fire",
                        -0.1,
                    )
                )
        self.fire_patches = [fp for fp in self.fire_patches if fp["life"] > 0]

    def draw(self, surf: pygame.Surface) -> None:
        # Ground fire patches
        for fp in self.fire_patches:
            alpha = max(30, min(180, fp["life"] * 4))
            r = int(fp["r"])
            blob = pygame.Surface((r * 4, r * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(blob, (255, 120, 20, alpha), (0, 0, r * 4, r * 2))
            pygame.draw.ellipse(blob, (255, 220, 80, alpha // 2), (r, 0, r * 2, r))
            surf.blit(blob, (int(fp["x"] - r * 2), int(fp["y"] - r)))

        for s in self.shockwaves:
            rr = int(s["r"])
            if rr < 2:
                continue
            ring = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            a = max(20, min(160, s["life"] * 8))
            pygame.draw.circle(ring, (*s["color"], a), (rr + 2, rr + 2), rr, 3)
            surf.blit(ring, (int(s["x"] - rr - 2), int(s["y"] - rr - 2)))

        for f in self.flashes:
            rr = int(f["r"])
            flash = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            a = max(40, min(200, f["life"] * 18))
            pygame.draw.circle(flash, (*f["color"], a), (rr, rr), rr)
            pygame.draw.circle(flash, (255, 255, 255, a), (rr, rr), max(4, rr // 3))
            surf.blit(flash, (int(f["x"] - rr), int(f["y"] - rr)), special_flags=pygame.BLEND_ADD)

        for p in self.particles:
            t = p.life / max(1, p.max_life)
            if p.kind == "blood":
                col = p.color
                pygame.draw.circle(surf, col, (int(p.x), int(p.y)), max(1, int(p.r)))
                if p.y >= GROUND_Y - 5:
                    pygame.draw.ellipse(
                        surf,
                        (100, 0, 12),
                        (int(p.x - p.r * 1.5), int(GROUND_Y - 4), int(p.r * 4), 5),
                    )
            elif p.kind == "fire":
                a = int(220 * t)
                glow = pygame.Surface((int(p.r * 4), int(p.r * 4)), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*p.color, a), (int(p.r * 2), int(p.r * 2)), int(p.r * 2))
                surf.blit(glow, (int(p.x - p.r * 2), int(p.y - p.r * 2)), special_flags=pygame.BLEND_ADD)
            else:
                pygame.draw.circle(surf, p.color, (int(p.x), int(p.y)), max(1, int(p.r * t + 1)))
