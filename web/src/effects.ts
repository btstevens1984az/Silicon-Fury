import { GROUND_Y, HEIGHT, WIDTH, type RGB } from "./types";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  max: number;
  r: number;
  color: RGB;
  kind: "blood" | "fire" | "spark" | "ember" | "debris";
  grav: number;
}

export class EffectWorld {
  particles: Particle[] = [];
  flashes: { x: number; y: number; life: number; r: number; color: RGB }[] = [];
  waves: { x: number; y: number; life: number; r: number; maxR: number; color: RGB }[] = [];

  clear(): void {
    this.particles = [];
    this.flashes = [];
    this.waves = [];
  }

  blood(x: number, y: number, facing: number, power = 1): void {
    const n = Math.floor(16 * power) + 8;
    for (let i = 0; i < n; i++) {
      const ang = -2.4 + Math.random() * 2;
      const spd = (4 + Math.random() * 10) * (0.7 + 0.5 * power);
      this.particles.push({
        x,
        y,
        vx: Math.cos(ang) * spd * facing + (Math.random() - 0.5) * 2,
        vy: Math.sin(ang) * spd - 2 - Math.random() * 6,
        life: 0.35 + Math.random() * 0.55,
        max: 0.9,
        r: 2 + Math.random() * 4,
        color: Math.random() < 0.4 ? [70, 0, 8] : [190, 12, 28],
        kind: "blood",
        grav: 900,
      });
    }
  }

  fire(x: number, y: number, power = 1): void {
    for (let i = 0; i < Math.floor(18 * power); i++) {
      const ang = Math.random() * Math.PI * 2;
      const spd = (1 + Math.random() * 6) * power;
      const palette: RGB[] = [
        [255, 220, 80],
        [255, 140, 30],
        [255, 80, 20],
        [255, 40, 10],
      ];
      this.particles.push({
        x: x + (Math.random() - 0.5) * 16,
        y: y + (Math.random() - 0.5) * 16,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd - 2,
        life: 0.25 + Math.random() * 0.35,
        max: 0.6,
        r: 3 + Math.random() * 6,
        color: palette[i % palette.length],
        kind: "fire",
        grav: -120,
      });
    }
  }

  explosion(x: number, y: number, color: RGB, power = 1): void {
    this.flashes.push({ x, y, life: 0.16 + 0.1 * power, r: 36 * power, color });
    this.waves.push({ x, y, life: 0.35 + 0.12 * power, r: 16, maxR: 110 * power, color });
    this.fire(x, y, power);
    for (let i = 0; i < Math.floor(12 * power); i++) {
      const ang = Math.random() * Math.PI * 2;
      const spd = (3 + Math.random() * 10) * power;
      this.particles.push({
        x,
        y,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd - 2,
        life: 0.2 + Math.random() * 0.3,
        max: 0.5,
        r: 2 + Math.random() * 3,
        color,
        kind: "ember",
        grav: 200,
      });
    }
  }

  sparks(x: number, y: number, facing: number, color: RGB): void {
    for (let i = 0; i < 12; i++) {
      this.particles.push({
        x,
        y,
        vx: facing * (2 + Math.random() * 9) + (Math.random() - 0.5) * 2,
        vy: -8 + Math.random() * 10,
        life: 0.12 + Math.random() * 0.18,
        max: 0.3,
        r: 2 + Math.random() * 2,
        color,
        kind: "spark",
        grav: 200,
      });
    }
  }

  update(dt: number): void {
    for (const p of this.particles) {
      p.vy += p.grav * dt;
      p.x += p.vx * dt * 60;
      p.y += p.vy * dt * 60;
      p.life -= dt;
      if (p.kind === "blood" && p.y >= GROUND_Y - 3) {
        p.y = GROUND_Y - 3;
        p.vx *= 0.5;
        p.vy = 0;
      }
      if (p.kind === "fire") {
        p.r *= 0.98;
        p.vx *= 0.96;
      }
    }
    this.particles = this.particles.filter(
      (p) => p.life > 0 && p.x > -40 && p.x < WIDTH + 40 && p.y < HEIGHT + 40,
    );
    for (const f of this.flashes) {
      f.life -= dt;
      f.r *= 1 + 4 * dt;
    }
    this.flashes = this.flashes.filter((f) => f.life > 0);
    for (const w of this.waves) {
      w.life -= dt;
      w.r += (w.maxR - w.r) * Math.min(1, 8 * dt);
    }
    this.waves = this.waves.filter((w) => w.life > 0);
  }

  draw(ctx: CanvasRenderingContext2D): void {
    for (const w of this.waves) {
      ctx.strokeStyle = `rgba(${w.color[0]},${w.color[1]},${w.color[2]},${Math.min(0.7, w.life * 3)})`;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(w.x, w.y, w.r, 0, Math.PI * 2);
      ctx.stroke();
    }
    for (const f of this.flashes) {
      const g = ctx.createRadialGradient(f.x, f.y, 2, f.x, f.y, f.r);
      g.addColorStop(0, `rgba(255,255,255,${Math.min(0.9, f.life * 6)})`);
      g.addColorStop(0.4, `rgba(${f.color[0]},${f.color[1]},${f.color[2]},${Math.min(0.55, f.life * 4)})`);
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
      ctx.fill();
    }
    for (const p of this.particles) {
      const a = Math.max(0.15, p.life / p.max);
      if (p.kind === "fire") {
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 2);
        g.addColorStop(0, `rgba(${p.color[0]},${p.color[1]},${p.color[2]},${a})`);
        g.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 2, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.fillStyle = `rgba(${p.color[0]},${p.color[1]},${p.color[2]},${a})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, Math.max(1, p.r), 0, Math.PI * 2);
        ctx.fill();
        if (p.kind === "blood" && p.y >= GROUND_Y - 5) {
          ctx.fillStyle = "rgba(100,0,12,0.7)";
          ctx.beginPath();
          ctx.ellipse(p.x, GROUND_Y - 2, p.r * 2.2, 2.5, 0, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
  }
}
