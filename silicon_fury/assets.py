"""Load stage art (fighters are drawn procedurally in body.py)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "assets" / "stages"


def _load_surface(path: Path, *, alpha: bool = True) -> pygame.Surface:
    """Load an image via pygame, falling back to Pillow when SDL_image lacks PNG."""
    try:
        img = pygame.image.load(str(path))
        return img.convert_alpha() if alpha else img.convert()
    except pygame.error:
        from PIL import Image

        mode = "RGBA" if alpha else "RGB"
        pil = Image.open(path).convert(mode)
        surf = pygame.image.fromstring(pil.tobytes(), pil.size, mode)
        return surf.convert_alpha() if alpha else surf.convert()


@lru_cache(maxsize=4)
def stage_bg(size: tuple[int, int]) -> pygame.Surface:
    path = STAGES / "arena.png"
    if path.exists():
        img = _load_surface(path, alpha=False)
        if img.get_size() != size:
            img = pygame.transform.smoothscale(img, size)
        return img
    surf = pygame.Surface(size)
    surf.fill((10, 12, 24))
    return surf
