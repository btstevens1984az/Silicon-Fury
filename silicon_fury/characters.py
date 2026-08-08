"""Fighter roster — Tekken-like attributes + unique specials."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Character:
    id: str
    name: str
    team: str
    tagline: str
    # Tekken-style attributes (1-100)
    hp: int
    power: int
    speed: int
    defense: int
    reach: int
    special: int
    # Visual identity
    primary: tuple
    secondary: tuple
    accent: tuple
    special_name: str
    special_desc: str
    story_rival: str  # id of story-mode rival


CHARACTERS: Dict[str, Character] = {
    # Team Computer (4)
    "dell": Character(
        id="dell",
        name="DELL",
        team="Team Computer",
        tagline="Enterprise iron. Home to hyperscale.",
        hp=100,
        power=78,
        speed=62,
        defense=80,
        reach=70,
        special=72,
        primary=(0, 120, 215),
        secondary=(20, 40, 80),
        accent=(180, 220, 255),
        special_name="POWEREDGE SLAM",
        special_desc="Server-rack overhead crush that stuns.",
        story_rival="ibm",
    ),
    "hp": Character(
        id="hp",
        name="HP",
        team="Team Computer",
        tagline="Laptops, lasers, and relentless print pressure.",
        hp=92,
        power=74,
        speed=70,
        defense=72,
        reach=68,
        special=76,
        primary=(0, 150, 100),
        secondary=(10, 50, 40),
        accent=(120, 255, 200),
        special_name="LASERJET BARRAGE",
        special_desc="Rapid ink-beam volley from mid range.",
        story_rival="intel",
    ),
    "lenovo": Character(
        id="lenovo",
        name="LENOVO",
        team="Team Computer",
        tagline="ThinkPad toughness. Yoga flexibility.",
        hp=96,
        power=76,
        speed=68,
        defense=84,
        reach=66,
        special=70,
        primary=(220, 40, 40),
        secondary=(60, 15, 20),
        accent=(255, 160, 160),
        special_name="THINKPAD STRIKE",
        special_desc="Armor-piercing keyboard combo finisher.",
        story_rival="amd",
    ),
    "asus": Character(
        id="asus",
        name="ASUS",
        team="Team Computer",
        tagline="ROG energy. Motherboard mastery.",
        hp=88,
        power=82,
        speed=84,
        defense=64,
        reach=72,
        special=86,
        primary=(255, 60, 40),
        secondary=(40, 10, 20),
        accent=(255, 200, 80),
        special_name="ROG RAMPAGE",
        special_desc="RGB-charged dash assault with Aura burst.",
        story_rival="nvidia",
    ),
    # Team Tech (4)
    "ibm": Character(
        id="ibm",
        name="IBM",
        team="Team Tech",
        tagline="Mainframes. Cloud. Watson mind games.",
        hp=104,
        power=80,
        speed=58,
        defense=86,
        reach=74,
        special=82,
        primary=(30, 90, 200),
        secondary=(15, 30, 70),
        accent=(160, 190, 255),
        special_name="WATSON WAVE",
        special_desc="AI prediction blast that reads your next move.",
        story_rival="dell",
    ),
    "intel": Character(
        id="intel",
        name="INTEL",
        team="Team Tech",
        tagline="Cores that cook. Tick-tock tempo.",
        hp=90,
        power=84,
        speed=78,
        defense=68,
        reach=70,
        special=80,
        primary=(0, 113, 197),
        secondary=(20, 40, 90),
        accent=(0, 200, 255),
        special_name="CORE MELTDOWN",
        special_desc="Overclocked flurry ending in thermal spike.",
        story_rival="hp",
    ),
    "amd": Character(
        id="amd",
        name="AMD",
        team="Team Tech",
        tagline="Ryzen rush. Radeon rage.",
        hp=94,
        power=86,
        speed=80,
        defense=66,
        reach=72,
        special=84,
        primary=(237, 28, 36),
        secondary=(60, 10, 20),
        accent=(255, 120, 80),
        special_name="RYZEN RUSH",
        special_desc="Multi-core chain punches into chipset smash.",
        story_rival="lenovo",
    ),
    "nvidia": Character(
        id="nvidia",
        name="NVIDIA",
        team="Team Tech",
        tagline="RTX rays. CUDA chaos. AI apex.",
        hp=86,
        power=90,
        speed=82,
        defense=60,
        reach=78,
        special=92,
        primary=(118, 185, 0),
        secondary=(20, 40, 10),
        accent=(180, 255, 80),
        special_name="CUDA CANNON",
        special_desc="Ray-traced beam that shreds defense frames.",
        story_rival="asus",
    ),
}


def by_team(team: str) -> List[Character]:
    return [c for c in CHARACTERS.values() if c.team == team]


def all_characters() -> List[Character]:
    return list(CHARACTERS.values())
