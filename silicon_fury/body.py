"""Professional articulated fighters — solid limbs, brand armor, joint motion.

Drawn procedurally so animation never introduces black rectangles from sprite
rotation. Each roster member has a distinct silhouette, armor kit, and hair.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import pygame

from silicon_fury.characters import Character

Color = Tuple[int, int, int]

# Per-fighter visual kit (silhouette + style cues)
KITS: Dict[str, dict] = {
    "dell": {"build": 1.12, "hair": "short", "armor": "heavy", "gender": "m"},
    "hp": {"build": 0.95, "hair": "ponytail", "armor": "sleek", "gender": "f"},
    "lenovo": {"build": 1.05, "hair": "buzz", "armor": "gi", "gender": "m"},
    "asus": {"build": 1.0, "hair": "spike", "armor": "street", "gender": "m"},
    "ibm": {"build": 1.15, "hair": "slick", "armor": "heavy", "gender": "m"},
    "intel": {"build": 1.0, "hair": "short", "armor": "tech", "gender": "m"},
    "amd": {"build": 1.05, "hair": "wild", "armor": "street", "gender": "m"},
    "nvidia": {"build": 0.92, "hair": "ponytail", "armor": "neon", "gender": "f"},
}


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def _shade(c: Color, d: int) -> Color:
    return (max(0, min(255, c[0] + d)), max(0, min(255, c[1] + d)), max(0, min(255, c[2] + d)))


def _pose(state: str, t: float, on_ground: bool, walk_phase: float) -> Dict[str, float]:
    breath = math.sin(walk_phase * 0.55) * 5
    la, ra = -20 + breath, 24 - breath
    ll, rl = 10 + breath * 0.35, -10 - breath * 0.35
    lk, rk = 18, 18
    torso = breath * 0.4
    head = -breath * 0.3
    bob = math.sin(walk_phase * 0.55) * 2.5

    if state == "walk":
        swing = math.sin(walk_phase) * 40
        la, ra = -30 - swing * 0.9, 30 + swing * 0.9
        ll, rl = swing, -swing
        lk, rk = 22 + abs(swing) * 0.65, 22 + abs(swing) * 0.65
        torso = swing * 0.14
        bob = abs(math.sin(walk_phase)) * 7
    elif state == "jump" or (not on_ground and state in {"idle", "walk"}):
        la, ra = -58, 52
        ll, rl = -30, 28
        lk, rk = 75, 60
        torso = -12
        bob = -10
    elif state == "punch":
        e = _lerp(0, 1, (t - 0.08) / 0.30) if t < 0.45 else _lerp(1, 0, (t - 0.45) / 0.55)
        ra = _lerp(26, 112, e)
        la = _lerp(-18, -68, e)
        ll, rl = _lerp(10, -20, e), _lerp(-10, 32, e)
        rk = _lerp(18, 42, e)
        torso = _lerp(0, 24, e)
        head = _lerp(0, -10, e)
        bob = _lerp(0, 5, e)
    elif state in {"kick", "air_kick"}:
        e = _lerp(0, 1, (t - 0.12) / 0.28) if t < 0.5 else _lerp(1, 0, (t - 0.5) / 0.5)
        rl = _lerp(-8, 122, e)
        rk = _lerp(18, 5, e)
        ll = _lerp(10, -50, e)
        lk = _lerp(18, 70, e)
        ra, la = _lerp(20, -42, e), _lerp(-18, -55, e)
        torso = _lerp(0, -16, e)
        head = _lerp(0, 10, e)
        if state == "air_kick":
            ll = _lerp(-24, -55, e)
            rl = _lerp(20, 130, e)
            torso = _lerp(-10, -24, e)
    elif state == "special":
        pulse = math.sin(t * math.pi * 5) * 30
        ra, la = 105 + pulse, -82 - pulse * 0.4
        rl, ll = 55, -42
        rk, lk = 34, 50
        torso = 18 + pulse * 0.12
        bob = -8
    elif state == "block":
        ra, la = 85, 72
        rl, ll = 8, -8
        rk, lk = 30, 30
        torso, head = -10, 10
        bob = 8
    elif state == "hit":
        ra, la = -60, -70
        rl, ll = 45, -50
        rk, lk = 55, 60
        torso, head = -28, 22
        bob = 6
    elif state == "ko":
        ra, la = -100, -110
        rl, ll = 85, -90
        rk, lk = 24, 24
        torso, head = 78, 42
        bob = 48

    return {
        "la": la, "ra": ra, "ll": ll, "rl": rl, "lk": lk, "rk": rk,
        "torso": torso, "head": head, "bob": bob,
    }


def _end(x: float, y: float, ang: float, length: float, facing: int) -> Tuple[float, float]:
    a = math.radians(-ang * facing)
    return x + length * math.sin(a), y + length * math.cos(a)


def _capsule(surf, x0, y0, x1, y1, radius, color, outline=(18, 18, 26)) -> None:
    color = (int(color[0]), int(color[1]), int(color[2]))
    r = max(3, int(radius))
    pygame.draw.circle(surf, color, (int(x0), int(y0)), r)
    pygame.draw.circle(surf, color, (int(x1), int(y1)), r)
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length * radius, dx / length * radius
    pts = [(x0 + nx, y0 + ny), (x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny)]
    pygame.draw.polygon(surf, color, [(int(p[0]), int(p[1])) for p in pts])
    # dual highlight for volume
    pygame.draw.line(
        surf, _shade(color, 60),
        (int(x0 + nx * 0.45), int(y0 + ny * 0.45)),
        (int(x1 + nx * 0.45), int(y1 + ny * 0.45)),
        max(2, int(radius * 0.42)),
    )
    pygame.draw.line(
        surf, _shade(color, -35),
        (int(x0 - nx * 0.35), int(y0 - ny * 0.35)),
        (int(x1 - nx * 0.35), int(y1 - ny * 0.35)),
        max(2, int(radius * 0.25)),
    )
    if outline:
        pygame.draw.circle(surf, outline, (int(x0), int(y0)), r, 2)
        pygame.draw.circle(surf, outline, (int(x1), int(y1)), r, 2)


def _leg(surf, hip, thigh_ang, knee_bend, facing, primary, metal, accent, scale, armor):
    knee = _end(hip[0], hip[1], thigh_ang, 52 * scale, facing)
    thick = 14 if armor == "heavy" else 12
    _capsule(surf, hip[0], hip[1], knee[0], knee[1], thick * scale, primary)
    pygame.draw.circle(surf, metal, (int(knee[0]), int(knee[1])), int(12 * scale))
    pygame.draw.circle(surf, _shade(metal, -45), (int(knee[0]), int(knee[1])), int(12 * scale), 2)
    shin_ang = thigh_ang - knee_bend
    foot = _end(knee[0], knee[1], shin_ang, 48 * scale, facing)
    _capsule(surf, knee[0], knee[1], foot[0], foot[1], (thick - 1.5) * scale, _shade(primary, -28))
    mid = ((knee[0] + foot[0]) / 2, (knee[1] + foot[1]) / 2)
    pygame.draw.circle(surf, metal, (int(mid[0]), int(mid[1])), int(8 * scale))
    boot = pygame.Rect(int(foot[0] - 16 * scale), int(foot[1] - 8 * scale), int(34 * scale), int(18 * scale))
    pygame.draw.ellipse(surf, accent if armor == "neon" else _shade(primary, -40), boot)
    pygame.draw.ellipse(surf, metal, boot, 2)
    return foot


def _arm(surf, shoulder, arm_ang, facing, primary, metal, accent, scale, thick, armor):
    elbow = _end(shoulder[0], shoulder[1], arm_ang, 40 * scale, facing)
    _capsule(surf, shoulder[0], shoulder[1], elbow[0], elbow[1], thick * scale, primary)
    pygame.draw.circle(surf, metal, (int(shoulder[0]), int(shoulder[1])), int(15 * scale))
    pygame.draw.circle(surf, _shade(metal, -40), (int(shoulder[0]), int(shoulder[1])), int(15 * scale), 2)
    if armor in {"neon", "tech", "street"}:
        pygame.draw.arc(
            surf, accent,
            (int(shoulder[0] - 11 * scale), int(shoulder[1] - 11 * scale), int(22 * scale), int(22 * scale)),
            0.2, 2.2, 3,
        )
    hand = _end(elbow[0], elbow[1], arm_ang * 0.72, 36 * scale, facing)
    _capsule(surf, elbow[0], elbow[1], hand[0], hand[1], (thick - 1.2) * scale, _shade(primary, -22))
    glove = accent if armor in {"neon", "street"} else metal
    pygame.draw.circle(surf, glove, (int(hand[0]), int(hand[1])), int(12 * scale))
    pygame.draw.circle(surf, (24, 24, 32), (int(hand[0]), int(hand[1])), int(12 * scale), 2)
    for i in range(3):
        pygame.draw.circle(
            surf, _shade(glove, -30),
            (int(hand[0] + facing * (3 + i)), int(hand[1] - 4 + i * 3)),
            2,
        )
    return hand


def _hair(surf, hx, hy, facing, style, primary, accent, scale):
    if style == "ponytail":
        pygame.draw.circle(surf, (18, 16, 20), (int(hx), int(hy - 8 * scale)), int(20 * scale))
        pygame.draw.ellipse(
            surf, (18, 16, 20),
            (int(hx - 8 * facing * scale), int(hy - 6 * scale), int(18 * scale), int(55 * scale)),
        )
        pygame.draw.circle(surf, accent, (int(hx - 10 * facing * scale), int(hy + 40 * scale)), 4)
    elif style == "spike":
        for i, ang in enumerate((-50, -20, 10, 40)):
            tip = _end(hx, hy - 8 * scale, ang, 28 * scale, facing)
            pygame.draw.polygon(
                surf, (22, 18, 16),
                [(int(hx), int(hy - 4 * scale)), (int(tip[0]), int(tip[1])), (int(hx + 6 * facing), int(hy))],
            )
    elif style == "wild":
        for ang in (-60, -30, 0, 30, 55):
            tip = _end(hx, hy - 6 * scale, ang, 26 * scale, 1)
            pygame.draw.line(surf, (30, 20, 18), (int(hx), int(hy)), (int(tip[0]), int(tip[1])), 5)
    elif style == "slick":
        pygame.draw.ellipse(surf, (20, 20, 28), (int(hx - 20 * scale), int(hy - 22 * scale), int(40 * scale), int(28 * scale)))
        pygame.draw.line(surf, accent, (int(hx - 12 * scale), int(hy - 10 * scale)), (int(hx + 12 * scale), int(hy - 14 * scale)), 2)
    elif style == "buzz":
        pygame.draw.circle(surf, (40, 36, 34), (int(hx), int(hy - 6 * scale)), int(22 * scale))
    else:  # short
        pygame.draw.circle(surf, (22, 20, 24), (int(hx), int(hy - 10 * scale)), int(20 * scale))
        pygame.draw.rect(surf, (22, 20, 24), (int(hx - 20 * scale), int(hy - 10 * scale), int(40 * scale), int(14 * scale)))


def draw_fighter_body(
    surf: pygame.Surface,
    char: Character,
    x: float,
    y: float,
    facing: int,
    state: str,
    state_t: int,
    state_max: int,
    on_ground: bool,
    flash: int = 0,
    walk_phase: float = 0.0,
    scale: float = 1.15,
) -> None:
    kit = KITS.get(char.id, {"build": 1.0, "hair": "short", "armor": "tech", "gender": "m"})
    t = 1.0 - (state_t / max(1, state_max)) if state_max > 0 else 0.0
    ang = _pose(state, t, on_ground, walk_phase)
    s = scale * float(kit["build"])

    primary = char.primary
    secondary = char.secondary
    accent = char.accent
    metal = (200, 208, 220) if sum(primary) < 420 else (160, 168, 180)
    skin = (235, 190, 155) if kit["gender"] == "m" else (240, 198, 170)
    if flash > 0:
        primary, secondary, skin = (255, 70, 70), (160, 30, 30), (255, 210, 210)

    draw_y = y + ang["bob"]
    hip = (x, draw_y - 98 * s)
    shoulder_y = draw_y - 175 * s

    # Contact shadow
    sw = int(140 * s) if on_ground else int(95 * s)
    shadow = pygame.Surface((sw, 28), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 125 if on_ground else 55), (0, 0, sw, 28))
    surf.blit(shadow, (x - sw / 2, y - 8))

    # Legs (back then front)
    if facing > 0:
        _leg(surf, (hip[0] - 8, hip[1]), ang["ll"], ang["lk"], facing, _shade(primary, -35), metal, accent, s, kit["armor"])
        foot = _leg(surf, (hip[0] + 8, hip[1]), ang["rl"], ang["rk"], facing, primary, metal, accent, s, kit["armor"])
    else:
        _leg(surf, (hip[0] + 8, hip[1]), ang["rl"], ang["rk"], facing, _shade(primary, -35), metal, accent, s, kit["armor"])
        foot = _leg(surf, (hip[0] - 8, hip[1]), ang["ll"], ang["lk"], facing, primary, metal, accent, s, kit["armor"])

    # Torso — wider armored chest + hips
    tw, th = int(62 * s), int(88 * s)
    tx = int(x - tw // 2 + ang["torso"] * 0.45 * facing)
    ty = int(draw_y - 192 * s)
    body = pygame.Rect(tx, ty, tw, th)
    # hip block
    hips = pygame.Rect(int(x - 28 * s), int(draw_y - 115 * s), int(56 * s), int(28 * s))
    pygame.draw.rect(surf, _shade(primary, -20), hips, border_radius=12)
    pygame.draw.rect(surf, primary, body, border_radius=20)
    pygame.draw.rect(surf, secondary, body.inflate(-14, -20), border_radius=16)
    # shoulder plates
    pygame.draw.ellipse(surf, metal, (body.x - 8, body.y + 4, 28, 24))
    pygame.draw.ellipse(surf, metal, (body.right - 20, body.y + 4, 28, 24))
    pygame.draw.rect(surf, metal, (body.x + 8, body.y + 16, body.w - 16, 14), border_radius=3)
    pygame.draw.rect(surf, accent, (body.x + 14, body.centery - 4, body.w - 28, 10), border_radius=3)
    if kit["armor"] == "neon":
        for i in range(3):
            pygame.draw.line(
                surf, accent,
                (body.x + 12, body.y + 34 + i * 14),
                (body.right - 12, body.y + 38 + i * 14), 3,
            )
    pygame.draw.rect(surf, (16, 16, 24), body, 3, border_radius=20)
    pygame.draw.rect(surf, (30, 30, 38), (body.x - 6, body.bottom - 16, body.w + 12, 14), border_radius=4)
    pygame.draw.circle(surf, metal, (body.centerx, body.bottom - 9), 8)
    pygame.draw.circle(surf, accent, (body.centerx, body.bottom - 9), 5)

    font = pygame.font.SysFont("Impact", max(12, int(16 * s)))
    badge = font.render(char.name[:2], True, (12, 12, 18))
    pygame.draw.circle(surf, accent, (body.centerx, body.y + 32), int(14 * s))
    surf.blit(badge, (body.centerx - badge.get_width() // 2, body.y + 32 - badge.get_height() // 2))

    # Arms
    sh = (x + 6 * facing, shoulder_y)
    if facing > 0:
        _arm(surf, (sh[0] - 16, sh[1]), ang["la"], facing, _shade(primary, -30), metal, accent, s, 10.0, kit["armor"])
        hand = _arm(surf, (sh[0] + 14, sh[1]), ang["ra"], facing, primary, metal, accent, s, 11.0, kit["armor"])
    else:
        _arm(surf, (sh[0] + 16, sh[1]), ang["ra"], facing, _shade(primary, -30), metal, accent, s, 10.0, kit["armor"])
        hand = _arm(surf, (sh[0] - 14, sh[1]), ang["la"], facing, primary, metal, accent, s, 11.0, kit["armor"])

    # Head
    hx = x + 5 * facing + ang["head"] * 0.3 * facing
    hy = draw_y - 215 * s
    head_r = int(24 * s)
    pygame.draw.circle(surf, skin, (int(hx), int(hy)), head_r)
    pygame.draw.circle(surf, (24, 24, 32), (int(hx), int(hy)), head_r, 3)
    _hair(surf, hx, hy, facing, kit["hair"], primary, accent, s)
    # eyes
    pygame.draw.circle(surf, (20, 20, 28), (int(hx + 8 * facing), int(hy + 2)), 4)
    pygame.draw.circle(surf, (20, 20, 28), (int(hx - 6 * facing), int(hy + 2)), 4)
    pygame.draw.circle(surf, (245, 245, 255), (int(hx + 9 * facing), int(hy + 1)), 1)
    # brow
    pygame.draw.line(
        surf, (40, 30, 28),
        (int(hx - 10 * facing), int(hy - 6)),
        (int(hx + 12 * facing), int(hy - 8)), 2,
    )

    # Attack telegraph
    if state == "punch" and 0.2 < t < 0.7:
        pygame.draw.circle(surf, accent, (int(hand[0]), int(hand[1])), 16, 3)
        trail = pygame.Surface((80, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(trail, (*accent, 150), trail.get_rect())
        surf.blit(trail, (int(hand[0] - (80 if facing > 0 else 0)), int(hand[1] - 10)))
    if state in {"kick", "air_kick"} and 0.25 < t < 0.78:
        pygame.draw.circle(surf, accent, (int(foot[0]), int(foot[1])), 17, 3)
        pygame.draw.line(surf, accent, (int(hip[0]), int(hip[1])), (int(foot[0]), int(foot[1])), 5)
    if state == "special":
        pulse = 24 + int(abs(math.sin(t * math.pi * 4)) * 28)
        ring = pygame.Surface((pulse * 2, pulse * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*accent, 80), (pulse, pulse), pulse, 4)
        surf.blit(ring, (int(x - pulse), int(draw_y - 140 * s - pulse)))
