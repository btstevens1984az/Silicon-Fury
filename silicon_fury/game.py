"""Silicon Fury main loop — menus, select, fight, story, demo capture."""

from __future__ import annotations

import os
import random
import sys
from typing import List, Optional, Tuple

import pygame

from silicon_fury.ai import CPUBrain
from silicon_fury.characters import CHARACTERS, Character, all_characters, by_team
from silicon_fury.config import (
    BLACK,
    CYAN,
    FPS,
    GOLD,
    GREEN,
    GROUND_Y,
    HEIGHT,
    PANEL,
    RED,
    TEAM_COMPUTER,
    TEAM_TECH,
    TITLE,
    WHITE,
    WIDTH,
)
from silicon_fury.assets import stage_bg
from silicon_fury.body import draw_fighter_body
from silicon_fury.effects import EffectWorld
from silicon_fury.fighter import Fighter


def _font(size: int, bold: bool = False) -> pygame.font.Font:
    names = ["Impact", "Arial Black", "DejaVuSans-Bold", "freesansbold"]
    for n in names:
        path = pygame.font.match_font(n, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("arial", size, bold=bold)


class SiliconFury:
    def __init__(self, *, capture_dir: Optional[str] = None, auto_demo: Optional[str] = None):
        pygame.init()
        pygame.display.set_caption(f"{TITLE} — Brand Brawl")
        flags = 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.running = True

        self.scene = "menu"  # menu|mode|select|fight|story_intro|victory
        self.mode = "1v1"  # 1v1|1vpc|story
        self.team_filter = TEAM_COMPUTER
        self.p1_char: Optional[Character] = None
        self.p2_char: Optional[Character] = None
        self.select_index = 0
        self.selecting_for = 1
        self.story_stage = 0
        self.story_roster: List[str] = []

        self.f1: Optional[Fighter] = None
        self.f2: Optional[Fighter] = None
        self.cpu: Optional[CPUBrain] = None
        self.round_time = 99.0
        self.round_num = 1
        self.ko_timer = 0
        self.msg = ""
        self.msg_t = 0
        self.shake = 0
        self.hitstops = 0
        self.fx = EffectWorld()

        self.capture_dir = capture_dir
        self.auto_demo = auto_demo
        self.capture_frames: List[pygame.Surface] = []
        self.demo_t = 0
        self.demo_phase = 0

        self.bg_stars = [
            (random.randint(0, WIDTH), random.randint(0, HEIGHT // 2), random.randint(1, 3))
            for _ in range(80)
        ]

    # ---------- Scene transitions ----------
    def start_fight(self, c1: Character, c2: Character, p2_cpu: bool) -> None:
        self.f1 = Fighter(c1, 280, facing=1, is_cpu=False)
        self.f2 = Fighter(c2, WIDTH - 280, facing=-1, is_cpu=p2_cpu)
        self.cpu = CPUBrain(0.75 if self.mode != "story" else 0.58 + self.story_stage * 0.08)
        self.round_time = 99.0
        self.round_num = 1
        self.ko_timer = 0
        self.fx.clear()
        self.scene = "fight"
        self.msg = "FIGHT!"
        self.msg_t = 90
        self.fx.fire_burst(WIDTH // 2, GROUND_Y - 20, 0.5)

    def reset_round(self, keep_wins: bool = True) -> None:
        assert self.f1 and self.f2 and self.p1_char and self.p2_char
        w1, w2 = self.f1.round_wins, self.f2.round_wins
        self.f1 = Fighter(self.p1_char, 280, facing=1, is_cpu=False)
        self.f2 = Fighter(self.p2_char, WIDTH - 280, facing=-1, is_cpu=self.f2.is_cpu if keep_wins else self.mode != "1v1")
        if keep_wins:
            self.f1.round_wins, self.f2.round_wins = w1, w2
        self.round_time = 99.0
        self.ko_timer = 0
        self.fx.clear()
        self.msg = f"ROUND {self.round_num}"
        self.msg_t = 70

    # ---------- Input ----------
    def handle_menu(self, events) -> None:
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.scene = "mode"
                elif e.key == pygame.K_ESCAPE:
                    self.running = False

    def handle_mode(self, events) -> None:
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1:
                    self.mode = "1v1"
                    self.selecting_for = 1
                    self.scene = "select"
                    self.team_filter = TEAM_COMPUTER
                    self.select_index = 0
                elif e.key == pygame.K_2:
                    self.mode = "1vpc"
                    self.selecting_for = 1
                    self.scene = "select"
                    self.team_filter = TEAM_COMPUTER
                    self.select_index = 0
                elif e.key == pygame.K_3:
                    self.mode = "story"
                    self.scene = "select"
                    self.selecting_for = 1
                    self.team_filter = TEAM_COMPUTER
                    self.select_index = 0
                    self.story_stage = 0
                elif e.key == pygame.K_ESCAPE:
                    self.scene = "menu"

    def handle_select(self, events) -> None:
        roster = by_team(self.team_filter)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.select_index = (self.select_index + 1) % len(roster)
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    self.select_index = (self.select_index - 1) % len(roster)
                elif e.key in (pygame.K_TAB, pygame.K_q):
                    self.team_filter = TEAM_TECH if self.team_filter == TEAM_COMPUTER else TEAM_COMPUTER
                    self.select_index = 0
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    chosen = roster[self.select_index]
                    if self.selecting_for == 1:
                        self.p1_char = chosen
                        if self.mode == "story":
                            # Story: climb through opposing team
                            rivals = [c.id for c in by_team(TEAM_TECH if chosen.team == TEAM_COMPUTER else TEAM_COMPUTER)]
                            random.shuffle(rivals)
                            # Ensure branded rival appears
                            if chosen.story_rival in rivals:
                                rivals.remove(chosen.story_rival)
                                rivals.append(chosen.story_rival)
                            self.story_roster = rivals
                            self.p2_char = CHARACTERS[self.story_roster[0]]
                            self.start_fight(self.p1_char, self.p2_char, p2_cpu=True)
                        elif self.mode == "1vpc":
                            # Pick random foe from other team
                            foes = by_team(TEAM_TECH if chosen.team == TEAM_COMPUTER else TEAM_COMPUTER)
                            self.p2_char = random.choice(foes)
                            self.start_fight(self.p1_char, self.p2_char, p2_cpu=True)
                        else:
                            self.selecting_for = 2
                            self.team_filter = TEAM_TECH if chosen.team == TEAM_COMPUTER else TEAM_COMPUTER
                            self.select_index = 0
                            self.msg = "PLAYER 2 SELECT"
                            self.msg_t = 60
                    else:
                        self.p2_char = chosen
                        self.start_fight(self.p1_char, self.p2_char, p2_cpu=False)
                elif e.key == pygame.K_ESCAPE:
                    self.scene = "mode"

    def handle_fight_input(self, keys) -> None:
        assert self.f1 and self.f2
        if self.ko_timer > 0:
            return
        # Player 1 — freer movement + dash (Left Shift)
        if keys[pygame.K_LSHIFT] and keys[pygame.K_a]:
            self.f1.dash(-1)
        elif keys[pygame.K_LSHIFT] and keys[pygame.K_d]:
            self.f1.dash(1)
        elif keys[pygame.K_a]:
            self.f1.move(-1)
        elif keys[pygame.K_d]:
            self.f1.move(1)
        if keys[pygame.K_w]:
            self.f1.jump()
        self.f1.block(keys[pygame.K_s])
        if keys[pygame.K_j]:
            self.f1.punch()
        if keys[pygame.K_k]:
            self.f1.kick()
        if keys[pygame.K_l]:
            if self.f1.special(self.fx):
                self.msg = self.f1.char.special_name
                self.msg_t = 40
                self.shake = 14

        if self.mode == "1v1" and not self.f2.is_cpu:
            if keys[pygame.K_RSHIFT] and keys[pygame.K_LEFT]:
                self.f2.dash(-1)
            elif keys[pygame.K_RSHIFT] and keys[pygame.K_RIGHT]:
                self.f2.dash(1)
            elif keys[pygame.K_LEFT]:
                self.f2.move(-1)
            elif keys[pygame.K_RIGHT]:
                self.f2.move(1)
            if keys[pygame.K_UP]:
                self.f2.jump()
            self.f2.block(keys[pygame.K_DOWN])
            if keys[pygame.K_n]:
                self.f2.punch()
            if keys[pygame.K_m]:
                self.f2.kick()
            if keys[pygame.K_COMMA]:
                if self.f2.special(self.fx):
                    self.msg = self.f2.char.special_name
                    self.msg_t = 40
                    self.shake = 14

    # ---------- Combat ----------
    def resolve_hits(self) -> None:
        assert self.f1 and self.f2
        for atk, dfn in ((self.f1, self.f2), (self.f2, self.f1)):
            box = atk.attack_box()
            if not box or atk.attack_hit:
                continue
            r = box.copy()
            if r.width < 0:
                r.x += r.width
                r.width = abs(r.width)
            if r.colliderect(dfn.body_box()):
                atk.attack_hit = True
                kind = atk.state
                if kind == "punch":
                    dmg, knock = atk.punch_dmg, 7.5
                elif kind in {"kick", "air_kick"}:
                    dmg, knock = atk.kick_dmg * (1.1 if kind == "air_kick" else 1.0), 9.5
                else:
                    dmg, knock = atk.special_dmg, 16
                    self.shake = 18
                dfn.take_hit(dmg, knock, atk.facing, self.fx, kind=kind)
                atk.gain_meter(14)
                atk.combo += 1
                # Short hitstop — keeps combat snappy/seamless
                self.hitstops = 2 if kind == "punch" else 3
                self.shake = max(self.shake, 8 if kind != "special" else 18)

    def update_fight(self) -> None:
        assert self.f1 and self.f2
        if self.hitstops > 0:
            self.hitstops -= 1
            self.fx.update()
            return

        if self.ko_timer == 0:
            self.round_time = max(0.0, self.round_time - 1 / FPS)
            if self.f2.is_cpu and self.cpu:
                self.cpu.step(self.f2, self.f1, self.fx)

            self.f1.update()
            self.f2.update()
            self.fx.update()
            # Face each other when idle / walking
            if self.f1.state in {"idle", "walk"}:
                self.f1.facing = 1 if self.f2.x > self.f1.x else -1
            if self.f2.state in {"idle", "walk"}:
                self.f2.facing = 1 if self.f1.x > self.f2.x else -1

            self.resolve_hits()

            if self.f1.hp <= 0 or self.f2.hp <= 0 or self.round_time <= 0:
                self.ko_timer = 1
                if self.round_time <= 0 and self.f1.hp > 0 and self.f2.hp > 0:
                    if self.f1.hp >= self.f2.hp:
                        self.f2.hp = 0
                        self.f2.set_state("ko", 120)
                        self.fx.explosion(self.f2.x, self.f2.y - 80, (255, 80, 40), 1.4)
                    else:
                        self.f1.hp = 0
                        self.f1.set_state("ko", 120)
                        self.fx.explosion(self.f1.x, self.f1.y - 80, (255, 80, 40), 1.4)
                winner = self.f1 if self.f1.hp > 0 else self.f2
                winner.round_wins += 1
                self.msg = "K.O." if min(self.f1.hp, self.f2.hp) <= 0 else "TIME!"
                self.msg_t = 80
                self.shake = 22

        else:
            self.ko_timer += 1
            self.f1.update()
            self.f2.update()
            self.fx.update()
            if self.ko_timer == 120:
                if self.f1.round_wins >= 2 or self.f2.round_wins >= 2:
                    self.scene = "victory"
                else:
                    self.round_num += 1
                    p2_cpu = self.f2.is_cpu
                    self.reset_round(True)
                    self.f2.is_cpu = p2_cpu

        if self.shake > 0:
            self.shake -= 1
        if self.msg_t > 0:
            self.msg_t -= 1

    # ---------- Draw ----------
    def draw_arena_bg(self) -> None:
        # Photoreal Tekken-style stage
        self.screen.blit(stage_bg((WIDTH, HEIGHT)), (0, 0))
        # Subtle vignette for fighter readability
        vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 50), (0, 0, WIDTH, HEIGHT))
        self.screen.blit(vignette, (0, 0))
        pygame.draw.line(self.screen, (255, 255, 255, 40), (80, GROUND_Y), (WIDTH - 80, GROUND_Y), 2)

    def draw_hud(self) -> None:
        assert self.f1 and self.f2

        def tekken_bar(x, y, w, h, frac, fill, name, wins, meter_frac, mirror=False):
            # Outer chrome frame
            frame = pygame.Rect(x - 6, y - 8, w + 12, h + 52)
            pygame.draw.rect(self.screen, (20, 20, 28), frame, border_radius=4)
            pygame.draw.rect(self.screen, (220, 200, 120), frame, 2, border_radius=4)
            # HP track
            pygame.draw.rect(self.screen, (40, 10, 10), (x, y, w, h))
            fw = int(w * max(0.0, min(1.0, frac)))
            if mirror:
                pygame.draw.rect(self.screen, fill, (x + w - fw, y, fw, h))
            else:
                pygame.draw.rect(self.screen, fill, (x, y, fw, h))
            # Gloss
            gloss = pygame.Surface((w, h // 2), pygame.SRCALPHA)
            gloss.fill((255, 255, 255, 35))
            self.screen.blit(gloss, (x, y))
            # Name + wins
            font = _font(22)
            label = font.render(name, True, WHITE)
            self.screen.blit(label, (x if not mirror else x + w - label.get_width(), y + h + 4))
            for i in range(2):
                c = (255, 210, 70) if i < wins else (55, 55, 65)
                cx = (x + w - 14 - i * 20) if not mirror else (x + 14 + i * 20)
                pygame.draw.circle(self.screen, c, (cx, y + h + 16), 6)
                pygame.draw.circle(self.screen, (30, 30, 30), (cx, y + h + 16), 6, 1)
            # Rage / special meter
            pygame.draw.rect(self.screen, (25, 25, 35), (x, y + h + 28, w, 10))
            mw = int(w * meter_frac)
            mcol = (80, 200, 255) if meter_frac >= 0.6 else (70, 90, 140)
            if mirror:
                pygame.draw.rect(self.screen, mcol, (x + w - mw, y + h + 28, mw, 10))
            else:
                pygame.draw.rect(self.screen, mcol, (x, y + h + 28, mw, 10))

        tekken_bar(36, 24, 460, 26, self.f1.hp / self.f1.max_hp, (210, 40, 55), self.f1.char.name, self.f1.round_wins, self.f1.meter / 100)
        tekken_bar(WIDTH - 496, 24, 460, 26, self.f2.hp / self.f2.max_hp, (40, 180, 90), self.f2.char.name, self.f2.round_wins, self.f2.meter / 100, mirror=True)

        # Center timer diamond
        font = _font(54)
        t = font.render(f"{int(self.round_time):02d}", True, (255, 230, 120))
        pygame.draw.rect(self.screen, (15, 15, 22), (WIDTH // 2 - 48, 16, 96, 58), border_radius=6)
        pygame.draw.rect(self.screen, (230, 200, 100), (WIDTH // 2 - 48, 16, 96, 58), 2, border_radius=6)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 18))

        tiny = _font(15)
        hint = "P1: WASD move/jump · Shift dash · J/K punch/kick (air OK) · L SPECIAL"
        if self.f2.is_cpu:
            hint = hint + "   |   CPU"
        else:
            hint = hint + "   |   P2: Arrows · RShift dash · N/M · , SPECIAL"
        self.screen.blit(tiny.render(hint, True, (200, 210, 230)), (36, HEIGHT - 26))

        if self.msg_t > 0 and self.msg:
            big = _font(78)
            label = big.render(self.msg, True, (255, 220, 80))
            shadow = big.render(self.msg, True, (0, 0, 0))
            pos = (WIDTH // 2 - label.get_width() // 2, HEIGHT // 2 - 70)
            self.screen.blit(shadow, (pos[0] + 3, pos[1] + 3))
            self.screen.blit(label, pos)

    def draw_menu(self) -> None:
        self.draw_arena_bg()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        title = _font(84).render(TITLE, True, CYAN)
        sub = _font(32).render("BRAND BRAWL", True, GOLD)
        tip = _font(24).render("PRESS ENTER — Team Computer vs Team Tech", True, WHITE)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 180))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 280))
        self.screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, 400))
        # Team pills
        for i, (name, col) in enumerate([(TEAM_COMPUTER, CYAN), (TEAM_TECH, GOLD)]):
            r = pygame.Rect(340 + i * 320, 480, 280, 56)
            pygame.draw.rect(self.screen, PANEL, r, border_radius=12)
            pygame.draw.rect(self.screen, col, r, 2, border_radius=12)
            lab = _font(26).render(name, True, col)
            self.screen.blit(lab, (r.centerx - lab.get_width() // 2, r.centery - lab.get_height() // 2))

    def draw_mode(self) -> None:
        self.draw_arena_bg()
        title = _font(48).render("SELECT MODE", True, WHITE)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        options = [
            ("1 — 1v1 VERSUS", "Two players. Same keyboard. Pure brand blood."),
            ("2 — 1v PC", "Challenge the silicon AI."),
            ("3 — STORY MODE", "Climb the rival team. Unlock the final boss fight."),
        ]
        for i, (h, d) in enumerate(options):
            y = 220 + i * 110
            pygame.draw.rect(self.screen, PANEL, (260, y, 760, 90), border_radius=14)
            pygame.draw.rect(self.screen, CYAN, (260, y, 760, 90), 2, border_radius=14)
            self.screen.blit(_font(32).render(h, True, GOLD), (290, y + 16))
            self.screen.blit(_font(20).render(d, True, WHITE), (290, y + 52))

    def draw_select(self) -> None:
        self.draw_arena_bg()
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        self.screen.blit(dim, (0, 0))
        roster = by_team(self.team_filter)
        title = _font(40).render(
            f"{'PLAYER ' + str(self.selecting_for) + ' — ' if self.mode == '1v1' else ''}{self.team_filter}",
            True,
            CYAN if self.team_filter == TEAM_COMPUTER else GOLD,
        )
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
        tip = _font(18).render("←/→ select · TAB switch team · ENTER confirm", True, WHITE)
        self.screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, 66))

        for i, ch in enumerate(roster):
            x = 40 + i * 310
            y = 100
            selected = i == self.select_index
            card = pygame.Rect(x, y, 290, 560)
            pygame.draw.rect(self.screen, (12, 14, 22), card, border_radius=10)
            pygame.draw.rect(self.screen, ch.primary if selected else (90, 90, 110), card, 3 if selected else 1, border_radius=10)
            # Live articulated preview (solid limbs)
            feet_x, feet_y = x + 145, y + 330
            phase = pygame.time.get_ticks() / 90.0 + i
            draw_fighter_body(
                self.screen,
                ch,
                feet_x,
                feet_y,
                1,
                "walk" if selected else "idle",
                8 if selected else 0,
                10 if selected else 0,
                True,
                0,
                phase,
            )
            self.screen.blit(_font(34).render(ch.name, True, WHITE), (x + 18, y + 350))
            self.screen.blit(_font(15).render(ch.tagline[:36], True, (190, 200, 220)), (x + 18, y + 390))
            self.screen.blit(_font(17).render(ch.special_name, True, ch.accent), (x + 18, y + 415))
            stats = [("HP", ch.hp), ("PWR", ch.power), ("SPD", ch.speed), ("DEF", ch.defense), ("SPC", ch.special)]
            for si, (label, val) in enumerate(stats):
                sy = y + 445 + si * 20
                self.screen.blit(_font(13).render(label, True, WHITE), (x + 18, sy))
                pygame.draw.rect(self.screen, (40, 40, 55), (x + 55, sy + 3, 200, 10), border_radius=2)
                pygame.draw.rect(self.screen, ch.primary, (x + 55, sy + 3, int(200 * val / 100), 10), border_radius=2)

    def draw_victory(self) -> None:
        self.draw_arena_bg()
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 110))
        self.screen.blit(dim, (0, 0))
        assert self.f1 and self.f2
        winner = self.f1 if self.f1.round_wins >= 2 else self.f2
        draw_fighter_body(
            self.screen,
            winner.char,
            WIDTH // 2,
            480,
            1,
            "special",
            20,
            38,
            True,
            0,
            pygame.time.get_ticks() / 80.0,
        )
        title = _font(64).render(f"{winner.char.name} WINS", True, GOLD)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 520))
        special = _font(26).render(winner.char.special_name, True, winner.char.accent)
        self.screen.blit(special, (WIDTH // 2 - special.get_width() // 2, 585))
        tip = _font(20).render("ENTER — continue   ESC — menu", True, WHITE)
        self.screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, 630))

    def draw_fight(self) -> None:
        assert self.f1 and self.f2
        ox = random.randint(-self.shake, self.shake) if self.shake else 0
        oy = random.randint(-self.shake // 2, self.shake // 2) if self.shake else 0
        if ox or oy:
            canvas = pygame.Surface((WIDTH, HEIGHT))
            old = self.screen
            self.screen = canvas
            self.draw_arena_bg()
            self.fx.draw(self.screen)
            self.f1.draw(self.screen)
            self.f2.draw(self.screen)
            self.draw_hud()
            self.screen = old
            self.screen.blit(canvas, (ox, oy))
        else:
            self.draw_arena_bg()
            self.fx.draw(self.screen)
            self.f1.draw(self.screen)
            self.f2.draw(self.screen)
            self.draw_hud()

    # ---------- Demo automation for GIFs ----------
    def run_auto_demo(self, name: str) -> None:
        """Scripted fights that produce exciting footage for GIF capture."""
        demos = {
            "01-title-teams": self._demo_title,
            "02-character-select": self._demo_select,
            "03-versus-brawl": self._demo_versus,
            "04-special-moves": self._demo_specials,
            "05-story-ko": self._demo_story_ko,
        }
        fn = demos[name]
        fn()

    def _capture(self) -> None:
        if self.capture_dir:
            self.capture_frames.append(self.screen.copy())

    def _pump_draw(self, frames: int, update=None, draw=None) -> None:
        for _ in range(frames):
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
            if update:
                update()
            if draw:
                draw()
            pygame.display.flip()
            self._capture()
            self.clock.tick(FPS)

    def _demo_title(self) -> None:
        self.scene = "menu"
        self._pump_draw(90, draw=self.draw_menu)
        self.scene = "mode"
        self._pump_draw(90, draw=self.draw_mode)

    def _demo_select(self) -> None:
        self.scene = "select"
        self.team_filter = TEAM_COMPUTER
        self.select_index = 0
        for i in range(4):
            self.select_index = i
            self._pump_draw(25, draw=self.draw_select)
        self.team_filter = TEAM_TECH
        for i in range(4):
            self.select_index = i
            self._pump_draw(25, draw=self.draw_select)

    def _scripted_brawl(self, c1: str, c2: str, seconds: float = 8.0, specials: bool = False) -> None:
        self.p1_char = CHARACTERS[c1]
        self.p2_char = CHARACTERS[c2]
        self.start_fight(self.p1_char, self.p2_char, p2_cpu=True)
        assert self.f1 and self.f2 and self.cpu
        # Start in striking range for readable fight footage
        self.f1.x, self.f2.x = 520, 760
        frames = int(seconds * FPS)
        for i in range(frames):
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
            # Keep them close for continuous exchanges + blood
            if abs(self.f2.x - self.f1.x) > 160:
                self.f1.move(1 if self.f2.x > self.f1.x else -1)
                self.f2.move(1 if self.f1.x > self.f2.x else -1)
            if i % 18 == 0:
                self.f1.punch()
            if i % 24 == 6:
                self.f1.kick()
            if i % 40 == 10:
                self.f1.jump()
            if i % 40 == 22 and not self.f1.on_ground:
                self.f1.kick()
            if i % 20 == 4:
                self.f2.punch()
            if i % 30 == 12:
                self.f2.kick()
            if i % 45 == 8:
                self.f2.jump()
            if specials and i in {70, 160, 250}:
                self.f1.meter = 100
                self.f1.special(self.fx)
                self.msg = self.f1.char.special_name
                self.msg_t = 40
                self.shake = 14
            if specials and i in {110, 210}:
                self.f2.meter = 100
                self.f2.special(self.fx)
                self.msg = self.f2.char.special_name
                self.msg_t = 40
            self.cpu.difficulty = 0.9
            self.update_fight()
            # Stay conscious for demo length (still show damage/blood)
            if self.auto_demo != "05-story-ko":
                if self.f1.hp < 120:
                    self.f1.hp = 120
                if self.f2.hp < 120:
                    self.f2.hp = 120
                self.ko_timer = 0
            self.draw_fight()
            pygame.display.flip()
            self._capture()
            self.clock.tick(FPS)

    def _demo_versus(self) -> None:
        self._scripted_brawl("asus", "nvidia", seconds=9.0, specials=False)

    def _demo_specials(self) -> None:
        self._scripted_brawl("amd", "lenovo", seconds=9.0, specials=True)

    def _demo_story_ko(self) -> None:
        self.mode = "story"
        self.p1_char = CHARACTERS["dell"]
        self.p2_char = CHARACTERS["ibm"]
        self.start_fight(self.p1_char, self.p2_char, p2_cpu=True)
        assert self.f1 and self.f2 and self.cpu
        for i in range(int(8.5 * FPS)):
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
            if i < 60:
                self.msg = "STORY BATTLE"
                self.msg_t = 40
            if i % 30 == 0:
                self.f1.move(1)
            if i % 40 == 5:
                self.f1.punch()
            if i % 50 == 15:
                self.f1.kick()
            if i == 120:
                self.f1.jump()
            if i == 135:
                self.f1.kick()
            if i == 200:
                self.f1.meter = 100
                self.f1.special(self.fx)
                self.msg = self.f1.char.special_name
                self.msg_t = 50
                self.shake = 16
            if i == 280:
                self.f2.hp = 30
            if i == 300:
                self.f1.meter = 100
                self.f1.special(self.fx)
            self.update_fight()
            self.draw_fight()
            pygame.display.flip()
            self._capture()
            self.clock.tick(FPS)
        self.scene = "victory"
        self._pump_draw(45, draw=self.draw_victory)

    # ---------- Main loop ----------
    def run(self) -> None:
        if self.auto_demo:
            self.run_auto_demo(self.auto_demo)
            self._save_capture(self.auto_demo)
            pygame.quit()
            return

        while self.running:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and self.scene == "fight":
                    self.scene = "menu"
                if e.type == pygame.KEYDOWN and self.scene == "victory":
                    if e.key == pygame.K_RETURN:
                        if self.mode == "story" and self.f1 and self.f1.round_wins >= 2:
                            self.story_stage += 1
                            if self.story_stage < len(self.story_roster):
                                self.p2_char = CHARACTERS[self.story_roster[self.story_stage]]
                                self.start_fight(self.p1_char, self.p2_char, p2_cpu=True)
                            else:
                                self.msg = "STORY COMPLETE"
                                self.scene = "menu"
                        else:
                            self.scene = "mode"
                    elif e.key == pygame.K_ESCAPE:
                        self.scene = "menu"

            if self.scene == "menu":
                self.handle_menu(events)
                self.draw_menu()
            elif self.scene == "mode":
                self.handle_mode(events)
                self.draw_mode()
            elif self.scene == "select":
                self.handle_select(events)
                self.draw_select()
            elif self.scene == "fight":
                keys = pygame.key.get_pressed()
                self.handle_fight_input(keys)
                self.update_fight()
                self.draw_fight()
            elif self.scene == "victory":
                self.draw_victory()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def _save_capture(self, name: str) -> None:
        if not self.capture_dir or not self.capture_frames:
            return
        os.makedirs(self.capture_dir, exist_ok=True)
        # Write PNG sequence
        seq = os.path.join(self.capture_dir, name)
        os.makedirs(seq, exist_ok=True)
        # Sample to ~20 fps worth for ~10s GIF (take every 3rd frame from 60fps)
        step = 3
        saved = 0
        for i, frame in enumerate(self.capture_frames[::step]):
            pygame.image.save(frame, os.path.join(seq, f"frame_{saved:04d}.png"))
            saved += 1
            if saved >= 200:  # ~10s at 20fps
                break
        print(f"Saved {saved} frames to {seq}")

