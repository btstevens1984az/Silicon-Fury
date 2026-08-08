"""Load Tekken-style fighter sprites and stage art."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[1]
FIGHTERS = ROOT / "assets" / "fighters"
STAGES = ROOT / "assets" / "stages"


@lru_cache(maxsize=32)
def fighter_sprite(char_id: str) -> pygame.Surface:
    path = FIGHTERS / f"{char_id}.png"
    if not path.exists():
        # fallback placeholder
        surf = pygame.Surface((200, 420), pygame.SRCALPHA)
        pygame.draw.rect(surf, (80, 80, 100), (40, 40, 120, 340), border_radius=20)
        return surf
    img = pygame.image.load(str(path)).convert_alpha()
    return img


@lru_cache(maxsize=4)
def stage_bg(size: tuple[int, int]) -> pygame.Surface:
    path = STAGES / "arena.png"
    if path.exists():
        img = pygame.image.load(str(path)).convert()
        if img.get_size() != size:
            img = pygame.transform.smoothscale(img, size)
        return img
    surf = pygame.Surface(size)
    surf.fill((10, 12, 24))
    return surf


def tint_surface(surf: pygame.Surface, color: tuple[int, int, int], strength: float = 0.45) -> pygame.Surface:
    out = surf.copy()
    overlay = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, int(255 * strength)))
    out.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out
