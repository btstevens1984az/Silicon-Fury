"""Articulated solid fighter body — opaque limbs with real joint motion."""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import pygame

from silicon_fury.characters import Character

Color = Tuple[int, int, int]


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def _pose_angles(state: str, t: float, on_ground: bool, walk_phase: float) -> Dict[str, float]:
    """Joint angles in degrees. 0 = straight down; positive = swing forward."""
    breath = math.sin(walk_phase * 0.5) * 4
    la, ra = -22 + breath, 26 - breath
    ll, rl = 10 + breath * 0.4, -10 - breath * 0.4
    lk, rk = 18, 18
    torso, head = breath * 0.5, -breath * 0.4

    if state == "walk":
        swing = math.sin(walk_phase) * 34
        la, ra = -24 - swing * 0.7, 24 + swing * 0.7
        ll, rl = swing, -swing
        lk, rk = 22 + abs(swing) * 0.55, 22 + abs(swing) * 0.55
        torso = swing * 0.1
    elif state == "jump" or (not on_ground and state in {"idle", "walk"}):
        la, ra = -60, 55
        ll, rl = -30, 28
        lk, rk = 70, 55
        torso = -8
    elif state == "punch":
        extend = _lerp(0, 1, (t - 0.12) / 0.35) if t < 0.5 else _lerp(1, 0, (t - 0.5) / 0.5)
        ra = _lerp(30, 100, extend)  # lead arm fires forward
        la = _lerp(-20, -70, extend)
        ll, rl = _lerp(10, -20, extend), _lerp(-10, 30, extend)
        rk = _lerp(18, 40, extend)
        torso = _lerp(0, 22, extend)
        head = _lerp(0, -10, extend)
    elif state in {"kick", "air_kick"}:
        extend = _lerp(0, 1, (t - 0.18) / 0.32) if t < 0.55 else _lerp(1, 0, (t - 0.55) / 0.45)
        rl = _lerp(-8, 115, extend)  # lead leg high kick
        rk = _lerp(20, 8, extend)
        ll = _lerp(10, -45, extend)
        lk = _lerp(18, 65, extend)
        ra, la = _lerp(20, -40, extend), _lerp(-20, -55, extend)
        torso = _lerp(0, -16, extend)
        head = _lerp(0, 8, extend)
        if state == "air_kick":
            ll = _lerp(-25, -50, extend)
            torso = _lerp(-10, -24, extend)
            rl = _lerp(20, 125, extend)
    elif state == "special":
        pulse = math.sin(t * math.pi * 4) * 25
        ra, la = 95 + pulse, -80 - pulse * 0.4
        rl, ll = 55, -40
        rk, lk = 35, 50
        torso = 14 + pulse * 0.15
    elif state == "block":
        ra, la = 78, 62
        rl, ll = 8, -8
        rk, lk = 30, 30
        torso, head = -6, 6
    elif state == "hit":
        ra, la = -55, -65
        rl, ll = 45, -50
        rk, lk = 55, 60
        torso, head = -28, 22
    elif state == "ko":
        ra, la = -100, -110
        rl, ll = 85, -90
        rk, lk = 25, 25
        torso, head = 78, 45

    return {
        "la": la,
        "ra": ra,
        "ll": ll,
        "rl": rl,
        "lk": lk,
        "rk": rk,
        "torso": torso,
        "head": head,
    }


def _end_point(x: float, y: float, ang_deg: float, length: float, facing: int) -> Tuple[float, float]:
    # ang 0 = down; positive rotates toward facing direction
    a = math.radians(-ang_deg * facing)
    # down vector (0, length) rotated
    dx = length * math.sin(a)
    dy = length * math.cos(a)
    return x + dx, y + dy


def _opaque(c: Color) -> Color:
    return (int(c[0]), int(c[1]), int(c[2]))


def _shade(c: Color, delta: int) -> Color:
    return (max(0, min(255, c[0] + delta)), max(0, min(255, c[1] + delta)), max(0, min(255, c[2] + delta)))


def _capsule(surf: pygame.Surface, x0: float, y0: float, x1: float, y1: float, radius: float, color: Color) -> None:
    """Fully opaque capsule (no alpha / no see-through)."""
    color = _opaque(color)
    pygame.draw.circle(surf, color, (int(x0), int(y0)), int(radius))
    pygame.draw.circle(surf, color, (int(x1), int(y1)), int(radius))
    # thick polygon between circles
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length * radius, dx / length * radius
    pts = [
        (x0 + nx, y0 + ny),
        (x0 - nx, y0 - ny),
        (x1 - nx, y1 - ny),
        (x1 + nx, y1 + ny),
    ]
    pygame.draw.polygon(surf, color, [(int(p[0]), int(p[1])) for p in pts])
    # solid highlight streak (still opaque, lighter color)
    hi = _shade(color, 45)
    pygame.draw.line(
        surf,
        hi,
        (int(x0 + nx * 0.35), int(y0 + ny * 0.35)),
        (int(x1 + nx * 0.35), int(y1 + ny * 0.35)),
        max(2, int(radius * 0.35)),
    )


def _draw_leg(
    surf: pygame.Surface,
    hip: Tuple[float, float],
    thigh_ang: float,
    knee_bend: float,
    facing: int,
    color: Color,
    scale: float,
    boot: Color,
) -> None:
    knee = _end_point(hip[0], hip[1], thigh_ang, 50 * scale, facing)
    _capsule(surf, hip[0], hip[1], knee[0], knee[1], 9 * scale, color)
    shin_ang = thigh_ang - knee_bend
    foot = _end_point(knee[0], knee[1], shin_ang, 46 * scale, facing)
    _capsule(surf, knee[0], knee[1], foot[0], foot[1], 8 * scale, _shade(color, -30))
    # opaque boot
    pygame.draw.ellipse(
        surf,
        _opaque(boot),
        (int(foot[0] - 12 * scale), int(foot[1] - 5 * scale), int(26 * scale), int(14 * scale)),
    )
    pygame.draw.ellipse(
        surf,
        _shade(boot, -40),
        (int(foot[0] - 12 * scale), int(foot[1] - 5 * scale), int(26 * scale), int(14 * scale)),
        2,
    )


def _draw_arm(
    surf: pygame.Surface,
    shoulder: Tuple[float, float],
    arm_ang: float,
    facing: int,
    color: Color,
    scale: float,
    glove: Color,
    thick: float,
) -> Tuple[float, float]:
    elbow = _end_point(shoulder[0], shoulder[1], arm_ang, 38 * scale, facing)
    _capsule(surf, shoulder[0], shoulder[1], elbow[0], elbow[1], thick * scale, color)
    hand_ang = arm_ang * 0.7
    hand = _end_point(elbow[0], elbow[1], hand_ang, 34 * scale, facing)
    _capsule(surf, elbow[0], elbow[1], hand[0], hand[1], (thick - 1.5) * scale, _shade(color, -25))
    pygame.draw.circle(surf, _opaque(glove), (int(hand[0]), int(hand[1])), int(10 * scale))
    pygame.draw.circle(surf, _shade(glove, -50), (int(hand[0]), int(hand[1])), int(10 * scale), 2)
    return hand


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
) -> None:
    t = 1.0 - (state_t / max(1, state_max)) if state_max > 0 else 0.0
    ang = _pose_angles(state, t, on_ground, walk_phase)

    primary = _opaque(char.primary)
    secondary = _opaque(char.secondary)
    accent = _opaque(char.accent)
    skin = (232, 188, 148)
    if flash > 0:
        primary = (255, 70, 70)
        secondary = (160, 30, 30)
        skin = (255, 210, 210)

    s = 1.2
    hip = (x, y - 100 * s)
    # Legs — back then front
    back_ll = facing > 0
    if back_ll:
        _draw_leg(surf, hip, ang["ll"], ang["lk"], facing, _shade(primary, -40), s, accent)
        _draw_leg(surf, hip, ang["rl"], ang["rk"], facing, primary, s, accent)
    else:
        _draw_leg(surf, hip, ang["rl"], ang["rk"], facing, _shade(primary, -40), s, accent)
        _draw_leg(surf, hip, ang["ll"], ang["lk"], facing, primary, s, accent)

    # Torso — draw as opaque rect (no SRCALPHA surface)
    torso_h, torso_w = int(78 * s), int(50 * s)
    tx = int(x - torso_w // 2 + ang["torso"] * 0.4 * facing)
    ty = int(y - 178 * s)
    body = pygame.Rect(tx, ty, torso_w, torso_h)
    pygame.draw.rect(surf, primary, body, border_radius=16)
    inner = body.inflate(-14, -20)
    pygame.draw.rect(surf, secondary, inner, border_radius=12)
    # brand chest bar
    pygame.draw.rect(surf, accent, (body.x + 10, body.centery - 5, body.w - 20, 10), border_radius=3)
    pygame.draw.rect(surf, (15, 15, 22), body, 3, border_radius=16)
    # initials badge
    font = pygame.font.SysFont("Impact", 16)
    badge = font.render(char.name[:2], True, (12, 12, 18))
    bx = body.centerx - badge.get_width() // 2
    by = body.centery - badge.get_height() // 2 - 14
    pygame.draw.circle(surf, accent, (body.centerx, body.centery - 14), 14)
    pygame.draw.circle(surf, (20, 20, 28), (body.centerx, body.centery - 14), 14, 2)
    surf.blit(badge, (bx, by))

    # Shoulders / arms
    sh = (x + 4 * facing, y - 168 * s)
    if facing > 0:
        _draw_arm(surf, (sh[0] - 10, sh[1]), ang["la"], facing, _shade(primary, -35), s, accent, 8)
        hand = _draw_arm(surf, (sh[0] + 8, sh[1]), ang["ra"], facing, primary, s, accent, 9)
    else:
        _draw_arm(surf, (sh[0] + 10, sh[1]), ang["ra"], facing, _shade(primary, -35), s, accent, 8)
        hand = _draw_arm(surf, (sh[0] - 8, sh[1]), ang["la"], facing, primary, s, accent, 9)

    # Head — solid
    hx = x + 6 * facing + ang["head"] * 0.25 * facing
    hy = y - 208 * s
    pygame.draw.circle(surf, skin, (int(hx), int(hy)), int(24 * s))
    pygame.draw.circle(surf, (25, 25, 35), (int(hx), int(hy)), int(24 * s), 3)
    # hair / helm cap
    pygame.draw.circle(surf, primary, (int(hx), int(hy - 10 * s)), int(18 * s))
    pygame.draw.rect(surf, primary, (int(hx - 18 * s), int(hy - 10 * s), int(36 * s), int(14 * s)))
    # eyes
    pygame.draw.circle(surf, (20, 20, 28), (int(hx + 7 * facing), int(hy + 2)), 4)
    pygame.draw.circle(surf, (20, 20, 28), (int(hx - 5 * facing), int(hy + 2)), 4)
    pygame.draw.circle(surf, (240, 240, 255), (int(hx + 8 * facing), int(hy + 1)), 1)

    # Attack trails (opaque-ish bright strokes)
    if state == "punch" and 0.25 < t < 0.7:
        pygame.draw.circle(surf, accent, (int(hand[0]), int(hand[1])), 16, 3)
        pygame.draw.line(
            surf,
            accent,
            (int(hand[0] - facing * 40), int(hand[1])),
            (int(hand[0]), int(hand[1])),
            6,
        )
    if state in {"kick", "air_kick"} and 0.28 < t < 0.78:
        kx, ky = _end_point(hip[0], hip[1], ang["rl"], 96 * s, facing)
        pygame.draw.circle(surf, accent, (int(kx), int(ky)), 18, 3)
        pygame.draw.line(surf, accent, (int(hip[0]), int(hip[1])), (int(kx), int(ky)), 5)
