import { CHARACTERS, byTeam } from "./characters";
import type { FighterKit } from "./types";
import { CPUBrain } from "./ai";
import { EffectWorld } from "./effects";
import { Fighter } from "./fighter";
import { Input } from "./input";
import { FPS, GROUND_Y, HEIGHT, WIDTH } from "./types";

type Scene = "menu" | "mode" | "select" | "fight" | "victory";
type Mode = "1v1" | "1vpc" | "story";

function aabb(
  a: { x: number; y: number; w: number; h: number },
  b: { x: number; y: number; w: number; h: number },
): boolean {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

export class Game {
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  input = new Input();
  fx = new EffectWorld();

  scene: Scene = "menu";
  mode: Mode = "1v1";
  team: "computer" | "tech" = "computer";
  selectIndex = 0;
  selectingFor = 1;
  p1?: FighterKit;
  p2?: FighterKit;
  f1?: Fighter;
  f2?: Fighter;
  cpu?: CPUBrain;
  storyRoster: string[] = [];
  storyStage = 0;

  roundTime = 99;
  roundNum = 1;
  koTimer = 0;
  msg = "";
  msgT = 0;
  shake = 0;
  hitstop = 0;

  arena?: HTMLImageElement;
  last = 0;
  hint: HTMLElement;
  demo?: string;
  demoT = 0;
  running = true;

  constructor(canvas: HTMLCanvasElement, hint: HTMLElement, demo?: string) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d")!;
    this.hint = hint;
    this.demo = demo;
    const img = new Image();
    img.src = `${import.meta.env.BASE_URL}arena.png`;
    img.onload = () => {
      this.arena = img;
    };
  }

  start(): void {
    this.last = performance.now();
    const loop = (now: number) => {
      if (!this.running) return;
      const dt = Math.min(0.033, (now - this.last) / 1000);
      this.last = now;
      this.update(dt);
      this.draw();
      this.input.endFrame();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  private startFight(c1: FighterKit, c2: FighterKit, p2cpu: boolean): void {
    this.f1 = new Fighter(c1, 300, 1, false);
    this.f2 = new Fighter(c2, WIDTH - 300, -1, p2cpu);
    this.cpu = new CPUBrain(this.mode === "story" ? 0.55 + this.storyStage * 0.08 : 0.75);
    this.roundTime = 99;
    this.roundNum = 1;
    this.koTimer = 0;
    this.fx.clear();
    this.scene = "fight";
    this.msg = "FIGHT!";
    this.msgT = 1.2;
    this.fx.fire(WIDTH / 2, GROUND_Y - 20, 0.5);
  }

  private resetRound(): void {
    if (!this.f1 || !this.f2 || !this.p1 || !this.p2) return;
    const w1 = this.f1.roundWins;
    const w2 = this.f2.roundWins;
    const cpu = this.f2.isCpu;
    this.f1 = new Fighter(this.p1, 300, 1, false);
    this.f2 = new Fighter(this.p2, WIDTH - 300, -1, cpu);
    this.f1.roundWins = w1;
    this.f2.roundWins = w2;
    this.roundTime = 99;
    this.koTimer = 0;
    this.fx.clear();
    this.msg = `ROUND ${this.roundNum}`;
    this.msgT = 1;
  }

  private update(dt: number): void {
    if (this.demo) {
      this.runDemo(dt);
      return;
    }
    if (this.scene === "menu") {
      this.hint.textContent = "ENTER — start   ·   ESC — quit hint";
      if (this.input.press("Enter") || this.input.press("Space")) this.scene = "mode";
    } else if (this.scene === "mode") {
      this.hint.textContent = "1 1v1   ·   2 vs CPU   ·   3 Story   ·   ESC back";
      if (this.input.press("Digit1") || this.input.press("Numpad1")) {
        this.mode = "1v1";
        this.selectingFor = 1;
        this.team = "computer";
        this.selectIndex = 0;
        this.scene = "select";
      } else if (this.input.press("Digit2") || this.input.press("Numpad2")) {
        this.mode = "1vpc";
        this.selectingFor = 1;
        this.team = "computer";
        this.selectIndex = 0;
        this.scene = "select";
      } else if (this.input.press("Digit3") || this.input.press("Numpad3")) {
        this.mode = "story";
        this.selectingFor = 1;
        this.team = "computer";
        this.selectIndex = 0;
        this.storyStage = 0;
        this.scene = "select";
      } else if (this.input.press("Escape")) this.scene = "menu";
    } else if (this.scene === "select") {
      this.handleSelect();
    } else if (this.scene === "fight") {
      this.handleFight(dt);
    } else if (this.scene === "victory") {
      this.hint.textContent = "ENTER continue   ·   ESC menu";
      if (this.input.press("Enter")) {
        if (this.mode === "story" && this.f1 && this.f1.roundWins >= 2) {
          this.storyStage += 1;
          if (this.storyStage < this.storyRoster.length && this.p1) {
            this.p2 = CHARACTERS[this.storyRoster[this.storyStage]];
            this.startFight(this.p1, this.p2, true);
          } else {
            this.scene = "menu";
            this.msg = "STORY COMPLETE";
          }
        } else this.scene = "mode";
      } else if (this.input.press("Escape")) this.scene = "menu";
    }
  }

  private handleSelect(): void {
    const roster = byTeam(this.team);
    this.hint.textContent = "←/→ select · TAB team · ENTER confirm · ESC back";
    if (this.input.press("ArrowRight") || this.input.press("KeyD")) {
      this.selectIndex = (this.selectIndex + 1) % roster.length;
    }
    if (this.input.press("ArrowLeft") || this.input.press("KeyA")) {
      this.selectIndex = (this.selectIndex - 1 + roster.length) % roster.length;
    }
    if (this.input.press("Tab") || this.input.press("KeyQ")) {
      this.team = this.team === "computer" ? "tech" : "computer";
      this.selectIndex = 0;
    }
    if (this.input.press("Enter") || this.input.press("Space")) {
      const chosen = roster[this.selectIndex];
      if (this.selectingFor === 1) {
        this.p1 = chosen;
        if (this.mode === "story") {
          const rivals = byTeam(chosen.team === "computer" ? "tech" : "computer").map((c) => c.id);
          rivals.sort(() => Math.random() - 0.5);
          if (rivals.includes(chosen.rival)) {
            const i = rivals.indexOf(chosen.rival);
            rivals.splice(i, 1);
            rivals.push(chosen.rival);
          }
          this.storyRoster = rivals;
          this.p2 = CHARACTERS[rivals[0]];
          this.startFight(this.p1, this.p2, true);
        } else if (this.mode === "1vpc") {
          const foes = byTeam(chosen.team === "computer" ? "tech" : "computer");
          this.p2 = foes[Math.floor(Math.random() * foes.length)];
          this.startFight(this.p1, this.p2, true);
        } else {
          this.selectingFor = 2;
          this.team = chosen.team === "computer" ? "tech" : "computer";
          this.selectIndex = 0;
        }
      } else {
        this.p2 = chosen;
        this.startFight(this.p1!, this.p2, false);
      }
    }
    if (this.input.press("Escape")) this.scene = "mode";
  }

  private handleFight(dt: number): void {
    if (!this.f1 || !this.f2) return;
    this.hint.textContent =
      "P1 WASD · Shift dash · J/K punch/kick · L special   |   P2 arrows · RShift · N/M · , special";

    if (this.input.press("Escape")) {
      this.scene = "menu";
      return;
    }

    if (this.koTimer === 0) {
      // P1
      let p1Moved = false;
      if (this.input.hold("ShiftLeft") && this.input.hold("KeyA")) {
        this.f1.dash(-1);
        p1Moved = true;
      } else if (this.input.hold("ShiftLeft") && this.input.hold("KeyD")) {
        this.f1.dash(1);
        p1Moved = true;
      } else if (this.input.hold("KeyA")) {
        this.f1.move(-1, this.input.hold("ShiftLeft"));
        p1Moved = true;
      } else if (this.input.hold("KeyD")) {
        this.f1.move(1, this.input.hold("ShiftLeft"));
        p1Moved = true;
      }
      if (this.input.press("KeyW")) this.f1.jump();
      this.f1.block(this.input.hold("KeyS"));
      if (this.input.press("KeyJ")) this.f1.punch();
      if (this.input.press("KeyK")) this.f1.kick();
      if (this.input.press("KeyL") && this.f1.special(this.fx)) {
        this.msg = this.f1.kit.specialName;
        this.msgT = 0.7;
        this.shake = 0.25;
      }
      if (
        !this.demo &&
        !p1Moved &&
        this.f1.onGround &&
        (this.f1.state === "walk" || this.f1.state === "run") &&
        !this.input.hold("KeyS")
      ) {
        this.f1.state = "idle";
        this.f1.animT = 0;
      }

      if (this.mode === "1v1" && !this.f2.isCpu && !this.demo) {
        if (this.input.hold("ShiftRight") && this.input.hold("ArrowLeft")) this.f2.dash(-1);
        else if (this.input.hold("ShiftRight") && this.input.hold("ArrowRight")) this.f2.dash(1);
        else if (this.input.hold("ArrowLeft")) this.f2.move(-1);
        else if (this.input.hold("ArrowRight")) this.f2.move(1);
        if (this.input.press("ArrowUp")) this.f2.jump();
        this.f2.block(this.input.hold("ArrowDown"));
        if (this.input.press("KeyN")) this.f2.punch();
        if (this.input.press("KeyM")) this.f2.kick();
        if (this.input.press("Comma") && this.f2.special(this.fx)) {
          this.msg = this.f2.kit.specialName;
          this.msgT = 0.7;
          this.shake = 0.25;
        }
      }
    }

    if (this.hitstop > 0) {
      this.hitstop -= dt;
      this.fx.update(dt);
      return;
    }

    if (this.koTimer === 0) {
      this.roundTime = Math.max(0, this.roundTime - dt);
      if (this.f2.isCpu && this.cpu) this.cpu.step(this.f2, this.f1, this.fx, dt);
      this.f1.update(dt);
      this.f2.update(dt);
      this.fx.update(dt);

      if (this.f1.state === "idle" || this.f1.state === "walk" || this.f1.state === "run") {
        this.f1.facing = this.f2.x > this.f1.x ? 1 : -1;
      }
      if (this.f2.state === "idle" || this.f2.state === "walk" || this.f2.state === "run") {
        this.f2.facing = this.f1.x > this.f2.x ? 1 : -1;
      }

      this.resolveHits();

      if (this.f1.hp <= 0 || this.f2.hp <= 0 || this.roundTime <= 0) {
        this.koTimer = 0.01;
        if (this.roundTime <= 0 && this.f1.hp > 0 && this.f2.hp > 0) {
          if (this.f1.hp >= this.f2.hp) {
            this.f2.hp = 0;
            this.f2.takeHit(0, 0, 1, "special", this.fx);
          } else {
            this.f1.hp = 0;
            this.f1.takeHit(0, 0, -1, "special", this.fx);
          }
        }
        const winner = this.f1.hp > 0 ? this.f1 : this.f2;
        winner.roundWins += 1;
        this.msg = Math.min(this.f1.hp, this.f2.hp) <= 0 ? "K.O." : "TIME!";
        this.msgT = 1.2;
        this.shake = 0.4;
      }
    } else {
      this.koTimer += dt;
      this.f1.update(dt);
      this.f2.update(dt);
      this.fx.update(dt);
      if (this.koTimer > 2) {
        if (this.f1.roundWins >= 2 || this.f2.roundWins >= 2) this.scene = "victory";
        else {
          this.roundNum += 1;
          this.resetRound();
        }
      }
    }

    if (this.shake > 0) this.shake -= dt;
    if (this.msgT > 0) this.msgT -= dt;
  }

  private resolveHits(): void {
    if (!this.f1 || !this.f2) return;
    for (const [atk, dfn] of [
      [this.f1, this.f2],
      [this.f2, this.f1],
    ] as const) {
      const box = atk.attackBox();
      if (!box || atk.attackHit || dfn.invuln > 0) continue;
      if (aabb(box, dfn.bodyBox())) {
        atk.attackHit = true;
        const kind = atk.state;
        let dmg = atk.punchDmg;
        let knock = 7.5;
        if (kind === "punch2") {
          dmg = atk.punchDmg * 1.15;
          knock = 8.5;
        } else if (kind === "kick" || kind === "airKick") {
          dmg = atk.kickDmg * (kind === "airKick" ? 1.1 : 1);
          knock = 10;
        } else if (kind === "special") {
          dmg = atk.specialDmg;
          knock = 16;
          this.shake = 0.35;
        }
        dfn.takeHit(dmg, knock, atk.facing, kind, this.fx);
        atk.meter = Math.min(100, atk.meter + 14);
        this.hitstop = kind === "punch" || kind === "punch2" ? 0.04 : 0.06;
        this.shake = Math.max(this.shake, kind === "special" ? 0.35 : 0.15);
      }
    }
  }

  private draw(): void {
    const ctx = this.ctx;
    // Full clear every frame — prevents black edge artifacts during shake
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, WIDTH, HEIGHT);

    const ox = this.shake > 0 ? (Math.random() - 0.5) * 14 * this.shake * 4 : 0;
    const oy = this.shake > 0 ? (Math.random() - 0.5) * 8 * this.shake * 4 : 0;
    ctx.save();
    ctx.translate(ox, oy);

    if (this.arena) ctx.drawImage(this.arena, 0, 0, WIDTH, HEIGHT);
    else {
      ctx.fillStyle = "#0a0c18";
      ctx.fillRect(0, 0, WIDTH, HEIGHT);
    }
    // vignette
    const g = ctx.createRadialGradient(WIDTH / 2, HEIGHT / 2, 200, WIDTH / 2, HEIGHT / 2, 700);
    g.addColorStop(0, "rgba(0,0,0,0)");
    g.addColorStop(1, "rgba(0,0,0,0.45)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    if (this.scene === "menu") this.drawMenu();
    else if (this.scene === "mode") this.drawMode();
    else if (this.scene === "select") this.drawSelect();
    else if (this.scene === "fight" || this.scene === "victory") {
      this.fx.draw(ctx);
      this.f1?.draw(ctx);
      this.f2?.draw(ctx);
      if (this.scene === "fight") this.drawHud();
      else this.drawVictory();
    }

    ctx.restore();
  }

  private drawMenu(): void {
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.45)";
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    // Showcase walkers — live skeletal idle/walk, no sprite boxes
    const t = performance.now() / 1000;
    const a = new Fighter(CHARACTERS.asus, 240, 1);
    const b = new Fighter(CHARACTERS.nvidia, WIDTH - 240, -1);
    a.state = "walk";
    a.animT = t;
    a.y = 520;
    b.state = "walk";
    b.animT = t + 0.4;
    b.y = 520;
    a.draw(ctx);
    b.draw(ctx);

    ctx.textAlign = "center";
    ctx.fillStyle = "#3de0ff";
    ctx.font = "92px Bebas Neue, Impact, sans-serif";
    ctx.fillText("SILICON FURY", WIDTH / 2, 160);
    ctx.fillStyle = "#f0c36a";
    ctx.font = "36px Bebas Neue, Impact, sans-serif";
    ctx.fillText("BRAND BRAWL", WIDTH / 2, 220);
    ctx.fillStyle = "#e8eefc";
    ctx.font = "24px Rajdhani, sans-serif";
    ctx.fillText("PRESS ENTER — Team Computer vs Team Tech", WIDTH / 2, 360);
  }

  private drawMode(): void {
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.5)";
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    ctx.textAlign = "center";
    ctx.fillStyle = "#fff";
    ctx.font = "48px Bebas Neue, Impact, sans-serif";
    ctx.fillText("SELECT MODE", WIDTH / 2, 120);
    const opts = [
      ["1 — 1v1 VERSUS", "Two players. One keyboard. Brand blood."],
      ["2 — 1v CPU", "Challenge the silicon AI."],
      ["3 — STORY MODE", "Climb the rival roster to the final boss."],
    ];
    opts.forEach(([h, d], i) => {
      const y = 220 + i * 110;
      ctx.fillStyle = "rgba(12,18,36,0.92)";
      roundRect(ctx, 260, y, 760, 90, 14);
      ctx.strokeStyle = "#3de0ff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#f0c36a";
      ctx.font = "32px Bebas Neue, Impact, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(h, 290, y + 40);
      ctx.fillStyle = "#e8eefc";
      ctx.font = "20px Rajdhani, sans-serif";
      ctx.fillText(d, 290, y + 70);
    });
  }

  private drawSelect(): void {
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    const roster = byTeam(this.team);
    ctx.textAlign = "center";
    ctx.fillStyle = this.team === "computer" ? "#3de0ff" : "#f0c36a";
    ctx.font = "40px Bebas Neue, Impact, sans-serif";
    const who = this.mode === "1v1" ? `PLAYER ${this.selectingFor} — ` : "";
    ctx.fillText(`${who}Team ${this.team === "computer" ? "Computer" : "Tech"}`, WIDTH / 2, 48);

    roster.forEach((ch, i) => {
      const x = 36 + i * 312;
      const y = 80;
      const selected = i === this.selectIndex;
      ctx.fillStyle = "rgba(10,12,20,0.95)";
      roundRect(ctx, x, y, 296, 580, 12);
      ctx.strokeStyle = selected ? `rgb(${ch.accent.join(",")})` : "#4a5060";
      ctx.lineWidth = selected ? 3 : 1;
      ctx.stroke();

      const f = new Fighter(ch, x + 148, 1);
      f.state = selected ? "walk" : "idle";
      f.animT = performance.now() / 1000 + i;
      f.y = y + 360;
      f.draw(ctx);

      ctx.textAlign = "left";
      ctx.fillStyle = "#fff";
      ctx.font = "32px Bebas Neue, Impact, sans-serif";
      ctx.fillText(ch.name, x + 16, y + 400);
      ctx.fillStyle = "#bec8dc";
      ctx.font = "15px Rajdhani, sans-serif";
      ctx.fillText(ch.tagline.slice(0, 34), x + 16, y + 428);
      ctx.fillStyle = `rgb(${ch.accent.join(",")})`;
      ctx.font = "18px Bebas Neue, Impact, sans-serif";
      ctx.fillText(ch.specialName, x + 16, y + 454);
      const stats: [string, number][] = [
        ["HP", ch.hp],
        ["PWR", ch.power],
        ["SPD", ch.speed],
        ["DEF", ch.defense],
        ["SPC", ch.special],
      ];
      stats.forEach(([label, val], si) => {
        const sy = y + 480 + si * 18;
        ctx.fillStyle = "#fff";
        ctx.font = "13px Rajdhani, sans-serif";
        ctx.fillText(label, x + 16, sy);
        ctx.fillStyle = "#282832";
        ctx.fillRect(x + 55, sy - 10, 200, 10);
        ctx.fillStyle = `rgb(${ch.primary.join(",")})`;
        ctx.fillRect(x + 55, sy - 10, 200 * (val / 100), 10);
      });
    });
  }

  private drawHud(): void {
    if (!this.f1 || !this.f2) return;
    const ctx = this.ctx;
    const bar = (
      x: number,
      y: number,
      w: number,
      frac: number,
      fill: string,
      name: string,
      wins: number,
      meter: number,
      mirror: boolean,
    ) => {
      ctx.fillStyle = "#14141c";
      roundRect(ctx, x - 6, y - 8, w + 12, 78, 4);
      ctx.strokeStyle = "#dcc878";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#280a0a";
      ctx.fillRect(x, y, w, 26);
      const fw = Math.max(0, Math.min(w, w * frac));
      ctx.fillStyle = fill;
      if (mirror) ctx.fillRect(x + w - fw, y, fw, 26);
      else ctx.fillRect(x, y, fw, 26);
      ctx.fillStyle = "rgba(255,255,255,0.15)";
      ctx.fillRect(x, y, w, 12);
      ctx.fillStyle = "#fff";
      ctx.font = "22px Bebas Neue, Impact, sans-serif";
      ctx.textAlign = mirror ? "right" : "left";
      ctx.fillText(name, mirror ? x + w : x, y + 48);
      for (let i = 0; i < 2; i++) {
        ctx.fillStyle = i < wins ? "#ffd246" : "#373741";
        const cx = mirror ? x + 14 + i * 20 : x + w - 14 - i * 20;
        ctx.beginPath();
        ctx.arc(cx, y + 44, 6, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.fillStyle = "#191923";
      ctx.fillRect(x, y + 56, w, 10);
      const mw = w * meter;
      ctx.fillStyle = meter >= 0.55 ? "#50c8ff" : "#465a8c";
      if (mirror) ctx.fillRect(x + w - mw, y + 56, mw, 10);
      else ctx.fillRect(x, y + 56, mw, 10);
    };

    bar(36, 24, 460, this.f1.hp / this.f1.maxHp, "#d22837", this.f1.kit.name, this.f1.roundWins, this.f1.meter / 100, false);
    bar(WIDTH - 496, 24, 460, this.f2.hp / this.f2.maxHp, "#28b45a", this.f2.kit.name, this.f2.roundWins, this.f2.meter / 100, true);

    ctx.fillStyle = "#0f0f16";
    roundRect(ctx, WIDTH / 2 - 48, 16, 96, 58, 6);
    ctx.strokeStyle = "#e6c864";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = "#ffe678";
    ctx.font = "54px Bebas Neue, Impact, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(String(Math.floor(this.roundTime)).padStart(2, "0"), WIDTH / 2, 62);

    if (this.msgT > 0 && this.msg) {
      ctx.font = "78px Bebas Neue, Impact, sans-serif";
      ctx.fillStyle = "#000";
      ctx.fillText(this.msg, WIDTH / 2 + 3, HEIGHT / 2 - 50);
      ctx.fillStyle = "#ffdc50";
      ctx.fillText(this.msg, WIDTH / 2, HEIGHT / 2 - 52);
    }
  }

  private drawVictory(): void {
    if (!this.f1 || !this.f2) return;
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(0,0,0,0.4)";
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    const winner = this.f1.roundWins >= 2 ? this.f1 : this.f2;
    winner.state = "special";
    winner.animT = performance.now() / 1000;
    winner.x = WIDTH / 2;
    winner.y = 470;
    winner.facing = 1;
    winner.draw(ctx);
    ctx.textAlign = "center";
    ctx.fillStyle = "#f0c36a";
    ctx.font = "64px Bebas Neue, Impact, sans-serif";
    ctx.fillText(`${winner.kit.name} WINS`, WIDTH / 2, 540);
    ctx.fillStyle = `rgb(${winner.kit.accent.join(",")})`;
    ctx.font = "28px Bebas Neue, Impact, sans-serif";
    ctx.fillText(winner.kit.specialName, WIDTH / 2, 590);
  }

  /** Scripted demo for GIF capture via ?demo=versus */
  private runDemo(dt: number): void {
    this.demoT += dt;
    const name = this.demo!;
    if (name === "title") {
      this.scene = this.demoT < 2 ? "menu" : "mode";
      if (this.demoT > 4) this.running = false;
    } else if (name === "select") {
      this.scene = "select";
      this.team = this.demoT < 2.5 ? "computer" : "tech";
      this.selectIndex = Math.floor(this.demoT * 1.2) % 4;
      if (this.demoT > 5) this.running = false;
    } else {
      if (!this.f1) {
        this.p1 = CHARACTERS.asus;
        this.p2 = CHARACTERS.nvidia;
        this.startFight(this.p1, this.p2, true);
        this.f1!.x = 520;
        this.f2!.x = 760;
      }
      // Keep them mobile so walk cycles read in GIFs
      if (Math.abs(this.f2!.x - this.f1!.x) > 150) {
        this.f1!.move(this.f2!.x > this.f1!.x ? 1 : -1, true);
        this.f2!.move(this.f1!.x > this.f2!.x ? 1 : -1);
      } else if (Math.floor(this.demoT * 2) % 2 === 0) {
        this.f1!.move(1);
      } else {
        this.f1!.move(-1);
      }
      const i = Math.floor(this.demoT * FPS);
      if (i % 16 === 0) this.f1!.punch();
      if (i % 22 === 6) this.f1!.kick();
      if (i % 36 === 10) this.f1!.jump();
      if (i % 36 === 20 && !this.f1!.onGround) this.f1!.kick();
      if (i % 18 === 4) this.f2!.punch();
      if (i % 26 === 12) this.f2!.kick();
      if (i % 50 === 8) this.f2!.jump();
      if (name === "specials" && [1.2, 2.8, 4.2].some((t) => Math.abs(this.demoT - t) < dt)) {
        this.f1!.meter = 100;
        this.f1!.special(this.fx);
        this.msg = this.f1!.kit.specialName;
        this.msgT = 0.7;
        this.shake = 0.25;
      }
      if (name === "specials" && Math.abs(this.demoT - 5.2) < dt) {
        this.f2!.meter = 100;
        this.f2!.special(this.fx);
        this.msg = this.f2!.kit.specialName;
        this.msgT = 0.7;
        this.shake = 0.25;
      }
      this.koTimer = 0;
      if (this.f1!.hp < 180) this.f1!.hp = 180;
      if (this.f2!.hp < 180) this.f2!.hp = 180;
      // Simulate fight without keyboard clearing walk state
      if (this.hitstop > 0) {
        this.hitstop -= dt;
        this.fx.update(dt);
      } else {
        this.f1!.update(dt);
        this.f2!.update(dt);
        this.fx.update(dt);
        this.resolveHits();
      }
      if (this.shake > 0) this.shake -= dt;
      if (this.msgT > 0) this.msgT -= dt;
      if (this.demoT > 8) this.running = false;
    }
  }
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
): void {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
  ctx.fill();
}
