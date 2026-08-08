import { CLIP_DURATION, sampleClip, type ClipName } from "./anim/clips";
import { drawSkeleton } from "./anim/skeleton";
import type { FighterKit } from "./types";
import { GROUND_Y, GRAVITY, clamp, type Pose } from "./types";
import type { EffectWorld } from "./effects";

export type FighterState =
  | "idle"
  | "walk"
  | "run"
  | "dash"
  | "jump"
  | "fall"
  | "crouch"
  | "block"
  | "punch"
  | "punch2"
  | "kick"
  | "airKick"
  | "special"
  | "hit"
  | "ko";

const ATTACKS = new Set<FighterState>(["punch", "punch2", "kick", "airKick", "special"]);

export class Fighter {
  kit: FighterKit;
  x: number;
  y: number;
  vx = 0;
  vy = 0;
  facing: 1 | -1;
  isCpu: boolean;

  maxHp: number;
  hp: number;
  meter = 0;
  maxMeter = 100;
  roundWins = 0;

  state: FighterState = "idle";
  stateT = 0;
  stateDur = 0;
  animT = 0;
  comboStep = 0;
  comboWindow = 0;
  hitstun = 0;
  attackHit = false;
  onGround = true;
  airJumps = 1;
  dashCd = 0;
  flash = 0;
  invuln = 0;

  moveSpeed: number;
  jumpPower: number;
  punchDmg: number;
  kickDmg: number;
  specialDmg: number;
  defenseFactor: number;
  reach: number;

  constructor(kit: FighterKit, x: number, facing: 1 | -1, isCpu = false) {
    this.kit = kit;
    this.x = x;
    this.y = GROUND_Y;
    this.facing = facing;
    this.isCpu = isCpu;
    this.maxHp = 1000 + kit.hp * 8;
    this.hp = this.maxHp;
    this.moveSpeed = 280 + kit.speed * 3.2;
    this.jumpPower = 780 + kit.speed * 2.2;
    this.punchDmg = 38 + kit.power * 0.28;
    this.kickDmg = 52 + kit.power * 0.34;
    this.specialDmg = 130 + kit.special * 0.7;
    this.defenseFactor = 1 - kit.defense / 230;
    this.reach = 78 + kit.power * 0.15;
  }

  get pose(): Pose {
    const clip = this.state as ClipName;
    const loop =
      this.state === "idle" ||
      this.state === "walk" ||
      this.state === "run" ||
      this.state === "fall" ||
      this.state === "crouch" ||
      this.state === "block";
    const dur = CLIP_DURATION[clip] || 0.4;
    if (loop) return sampleClip(clip, this.animT / dur, true);
    const t = this.stateDur > 0 ? 1 - this.stateT / this.stateDur : 0;
    return sampleClip(clip, t, false);
  }

  canAct(): boolean {
    return this.hp > 0 && this.hitstun <= 0 && this.state !== "ko" && this.state !== "special";
  }

  private setState(state: FighterState, dur?: number): void {
    this.state = state;
    this.stateDur = dur ?? CLIP_DURATION[state as ClipName] ?? 0.3;
    this.stateT = this.stateDur;
    this.animT = 0;
    if (ATTACKS.has(state)) this.attackHit = false;
  }

  move(dir: -1 | 1, sprint = false): void {
    if (this.hp <= 0 || this.hitstun > 0 || this.state === "ko" || this.state === "special") return;
    if (ATTACKS.has(this.state) && this.stateT > this.stateDur * 0.35) return;
    if (this.state === "block" || this.state === "crouch") return;

    const spd = (sprint ? this.moveSpeed * 1.45 : this.moveSpeed) * (this.onGround ? 1 : 0.85);
    this.vx = dir * spd;
    this.facing = dir;
    if (this.onGround && !ATTACKS.has(this.state) && this.state !== "dash") {
      this.setState(sprint ? "run" : "walk");
    }
  }

  dash(dir: -1 | 1): void {
    if (!this.canAct() || this.dashCd > 0 || !this.onGround) return;
    this.facing = dir;
    this.vx = dir * this.moveSpeed * 2.8;
    this.dashCd = 0.45;
    this.setState("dash", CLIP_DURATION.dash);
    this.invuln = 0.08;
  }

  jump(): void {
    if (this.hp <= 0 || this.hitstun > 0 || this.state === "ko" || this.state === "special") return;
    if (this.onGround) {
      this.vy = -this.jumpPower;
      this.onGround = false;
      this.airJumps = 1;
      this.setState("jump");
    } else if (this.airJumps > 0 && this.state !== "airKick") {
      this.vy = -this.jumpPower * 0.72;
      this.airJumps -= 1;
      this.setState("jump", 0.35);
    }
  }

  crouch(holding: boolean): void {
    if (this.hp <= 0 || this.hitstun > 0 || !this.onGround) return;
    if (holding && !ATTACKS.has(this.state) && this.state !== "special") {
      this.setState("crouch");
      this.vx *= 0.2;
    }
  }

  block(holding: boolean): void {
    if (this.hp <= 0 || this.hitstun > 0) return;
    if (holding && this.onGround && !ATTACKS.has(this.state) && this.state !== "special") {
      this.setState("block");
      this.vx *= 0.15;
    }
  }

  punch(): void {
    if (this.hp <= 0 || this.hitstun > 0 || this.state === "ko" || this.state === "special") return;
    if (ATTACKS.has(this.state) && this.stateT > 0.08) return;
    if (!this.onGround) {
      this.setState("punch", 0.28);
      this.vx += this.facing * 40;
      return;
    }
    if (this.comboWindow > 0 && this.comboStep === 1) {
      this.comboStep = 2;
      this.setState("punch2");
      this.vx = this.facing * 160;
      return;
    }
    this.comboStep = 1;
    this.comboWindow = 0.35;
    this.setState("punch");
    this.vx = this.facing * 140;
  }

  kick(): void {
    if (this.hp <= 0 || this.hitstun > 0 || this.state === "ko" || this.state === "special") return;
    if (ATTACKS.has(this.state) && this.stateT > 0.08) return;
    if (!this.onGround) {
      this.setState("airKick");
      this.vx = this.facing * 120;
      this.vy = Math.min(this.vy, -80);
      return;
    }
    this.setState("kick");
    this.vx = this.facing * 180;
    this.comboStep = 0;
  }

  special(fx?: EffectWorld): boolean {
    if (this.meter < 55 || this.hp <= 0 || this.hitstun > 0 || this.state === "ko") return false;
    if (this.state === "special") return false;
    this.meter -= 55;
    this.setState("special");
    this.vx = this.facing * (220 + this.kit.speed);
    if (!this.onGround) this.vy = -120;
    fx?.explosion(this.x + this.facing * 50, this.y - 120, this.kit.accent, 0.9);
    return true;
  }

  takeHit(
    dmg: number,
    knock: number,
    atkFacing: 1 | -1,
    kind: string,
    fx?: EffectWorld,
  ): void {
    const blocked = this.state === "block";
    const ix = this.x - atkFacing * 14;
    const iy = this.y - (kind === "punch" || kind === "punch2" ? 145 : 95);
    if (blocked) {
      dmg *= 0.28;
      knock *= 0.18;
      this.meter = Math.min(this.maxMeter, this.meter + 6);
      fx?.sparks(ix, iy, atkFacing, [255, 220, 120]);
    } else {
      this.hitstun = kind === "special" ? 0.35 : 0.22;
      this.setState("hit", this.hitstun);
      this.flash = 0.18;
      const power = kind === "special" ? 2 : kind.includes("kick") ? 1.35 : 1;
      fx?.blood(ix, iy, atkFacing, power);
      fx?.sparks(ix, iy, atkFacing, this.kit.accent);
      if (kind.includes("kick") || kind === "special") fx?.fire(ix, iy, kind === "special" ? 1.1 : 0.45);
      if (kind === "special") fx?.explosion(ix, iy, this.kit.accent, 1.35);
    }
    this.hp = Math.max(0, this.hp - dmg * this.defenseFactor);
    this.vx = atkFacing * knock * 60;
    this.vy = blocked ? -80 : kind === "airKick" ? -420 : -280;
    this.onGround = false;
    if (this.hp <= 0) {
      this.hp = 0;
      this.setState("ko", CLIP_DURATION.ko);
      this.hitstun = CLIP_DURATION.ko;
      fx?.blood(this.x, this.y - 100, atkFacing, 2.4);
      fx?.explosion(this.x, this.y - 80, [255, 60, 40], 1.5);
    }
  }

  attackBox(): { x: number; y: number; w: number; h: number } | null {
    if (!ATTACKS.has(this.state) || this.attackHit) return null;
    const prog = 1 - this.stateT / Math.max(1e-3, this.stateDur);
    const box = (xOff: number, y: number, w: number, h: number) => {
      let x = this.x + this.facing * xOff;
      if (this.facing < 0) x -= w;
      return { x, y, w, h };
    };
    if (this.state === "punch" && prog > 0.2 && prog < 0.55) return box(48, this.y - 150, this.reach, 48);
    if (this.state === "punch2" && prog > 0.22 && prog < 0.58) return box(52, this.y - 148, this.reach + 8, 50);
    if (this.state === "kick" && prog > 0.25 && prog < 0.62) return box(46, this.y - 105, this.reach + 36, 54);
    if (this.state === "airKick" && prog > 0.2 && prog < 0.7) return box(44, this.y - 120, this.reach + 40, 56);
    if (this.state === "special" && prog > 0.28 && prog < 0.75)
      return box(30, this.y - 170, this.reach + 110 + this.kit.special * 0.35, 120);
    return null;
  }

  bodyBox(): { x: number; y: number; w: number; h: number } {
    const crouch = this.state === "crouch" || this.state === "block";
    const h = crouch ? 140 : 200;
    return { x: this.x - 34, y: this.y - h, w: 68, h };
  }

  update(dt: number): void {
    if (this.hitstun > 0) this.hitstun -= dt;
    if (this.dashCd > 0) this.dashCd -= dt;
    if (this.flash > 0) this.flash -= dt;
    if (this.invuln > 0) this.invuln -= dt;
    if (this.comboWindow > 0) {
      this.comboWindow -= dt;
      if (this.comboWindow <= 0) this.comboStep = 0;
    }

    this.animT += dt;
    const looping =
      this.state === "idle" ||
      this.state === "walk" ||
      this.state === "run" ||
      this.state === "fall" ||
      this.state === "crouch" ||
      this.state === "block";

    if (!looping && this.stateT > 0) {
      this.stateT -= dt;
      if (this.stateT <= 0 && this.state !== "ko") {
        if (!this.onGround) this.setState("fall");
        else this.setState("idle");
      }
    } else if (looping) {
      // Keep locomotion / hold poses looping — never snap mid-stride.
      this.stateT = this.stateDur;
    }

    this.vy += GRAVITY * dt;
    this.x += this.vx * dt;
    this.y += this.vy * dt;
    this.vx *= this.onGround ? 0.82 : 0.96;

    if (this.y >= GROUND_Y) {
      this.y = GROUND_Y;
      this.vy = 0;
      if (!this.onGround && this.state !== "ko" && this.state !== "hit") {
        if (this.state === "jump" || this.state === "fall" || this.state === "airKick") this.setState("idle");
      }
      this.onGround = true;
      this.airJumps = 1;
    } else {
      this.onGround = false;
      if (this.state === "idle" || this.state === "walk" || this.state === "run") this.setState("fall");
    }

    this.x = clamp(this.x, 70, 1210);
    if (this.state === "idle") this.meter = Math.min(this.maxMeter, this.meter + 8 * dt);

    // Stop walk/run when nearly still
    if (
      this.onGround &&
      (this.state === "walk" || this.state === "run") &&
      Math.abs(this.vx) < 25
    ) {
      this.setState("idle");
    }
  }

  draw(ctx: CanvasRenderingContext2D): void {
    const attackFlash =
      ATTACKS.has(this.state) && this.stateT / this.stateDur < 0.65 && this.stateT / this.stateDur > 0.2
        ? 0.7
        : 0;
    drawSkeleton(ctx, this.kit, this.x, this.y, this.facing, this.pose, {
      flash: this.flash,
      airborne: !this.onGround,
      attackFlash,
    });

    if (this.state === "special") {
      ctx.save();
      ctx.font = "bold 28px Bebas Neue, Impact, sans-serif";
      ctx.textAlign = "center";
      ctx.fillStyle = "#000";
      ctx.fillText(this.kit.specialName, this.x + 2, this.y - 268);
      ctx.fillStyle = `rgb(${this.kit.accent.join(",")})`;
      ctx.fillText(this.kit.specialName, this.x, this.y - 270);
      ctx.restore();
    }
  }
}
