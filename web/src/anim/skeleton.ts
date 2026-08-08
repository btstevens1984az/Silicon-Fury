import type { FighterKit, Pose, RGB } from "../types";

function shade(c: RGB, d: number): RGB {
  return [
    Math.max(0, Math.min(255, c[0] + d)),
    Math.max(0, Math.min(255, c[1] + d)),
    Math.max(0, Math.min(255, c[2] + d)),
  ];
}

function rgb(c: RGB, a = 1): string {
  return a < 1 ? `rgba(${c[0]},${c[1]},${c[2]},${a})` : `rgb(${c[0]},${c[1]},${c[2]})`;
}

function end(
  x: number,
  y: number,
  angDeg: number,
  len: number,
  facing: number,
): [number, number] {
  // 0° = down; positive swings toward facing
  const a = ((-angDeg * facing) * Math.PI) / 180;
  return [x + Math.sin(a) * len, y + Math.cos(a) * len];
}

/** Soft capsule — drawn as path directly on ctx (never an offscreen black rect). */
function capsule(
  ctx: CanvasRenderingContext2D,
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  r0: number,
  r1: number,
  color: RGB,
  outline: RGB = [18, 18, 26],
): void {
  const dx = x1 - x0;
  const dy = y1 - y0;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  const nx = -uy;
  const ny = ux;

  ctx.beginPath();
  ctx.moveTo(x0 + nx * r0, y0 + ny * r0);
  ctx.lineTo(x1 + nx * r1, y1 + ny * r1);
  ctx.arc(x1, y1, r1, Math.atan2(ny, nx), Math.atan2(-ny, -nx));
  ctx.lineTo(x0 - nx * r0, y0 - ny * r0);
  ctx.arc(x0, y0, r0, Math.atan2(-ny, -nx), Math.atan2(ny, nx));
  ctx.closePath();
  ctx.fillStyle = rgb(color);
  ctx.fill();

  ctx.strokeStyle = rgb(shade(color, 50), 0.9);
  ctx.lineWidth = Math.max(2, (r0 + r1) * 0.18);
  ctx.beginPath();
  ctx.moveTo(x0 + nx * r0 * 0.4, y0 + ny * r0 * 0.4);
  ctx.lineTo(x1 + nx * r1 * 0.4, y1 + ny * r1 * 0.4);
  ctx.stroke();

  ctx.strokeStyle = rgb(outline, 0.85);
  ctx.lineWidth = 1.5;
  ctx.stroke();
}

function drawHair(
  ctx: CanvasRenderingContext2D,
  hx: number,
  hy: number,
  facing: number,
  kit: FighterKit,
  s: number,
): void {
  ctx.fillStyle = rgb(kit.hair);
  const style = kit.hairStyle;
  if (style === "ponytail") {
    ctx.beginPath();
    ctx.arc(hx, hy - 8 * s, 19 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(hx - 10 * facing * s, hy + 18 * s, 9 * s, 28 * s, 0.15 * facing, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = rgb(kit.accent);
    ctx.beginPath();
    ctx.arc(hx - 10 * facing * s, hy + 42 * s, 4 * s, 0, Math.PI * 2);
    ctx.fill();
  } else if (style === "spike") {
    for (const ang of [-55, -25, 5, 35, 60]) {
      const [tx, ty] = end(hx, hy - 6 * s, ang, 26 * s, facing);
      ctx.beginPath();
      ctx.moveTo(hx - 4 * facing, hy);
      ctx.lineTo(tx, ty);
      ctx.lineTo(hx + 6 * facing, hy - 2);
      ctx.closePath();
      ctx.fill();
    }
  } else if (style === "wild") {
    for (const ang of [-65, -35, -5, 25, 50]) {
      const [tx, ty] = end(hx, hy - 4 * s, ang, 24 * s, 1);
      ctx.strokeStyle = rgb(kit.hair);
      ctx.lineWidth = 5 * s;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(hx, hy);
      ctx.lineTo(tx, ty);
      ctx.stroke();
    }
  } else if (style === "slick") {
    ctx.beginPath();
    ctx.ellipse(hx, hy - 10 * s, 20 * s, 14 * s, -0.2 * facing, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = rgb(kit.accent);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(hx - 12 * s, hy - 10 * s);
    ctx.lineTo(hx + 12 * s, hy - 14 * s);
    ctx.stroke();
  } else if (style === "buzz") {
    ctx.beginPath();
    ctx.arc(hx, hy - 6 * s, 21 * s, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.beginPath();
    ctx.arc(hx, hy - 10 * s, 19 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(hx - 19 * s, hy - 10 * s, 38 * s, 12 * s);
  }
}

export interface DrawOpts {
  flash?: number;
  airborne?: boolean;
  attackFlash?: number;
}

/**
 * Draw a humanoid fighter with articulated limbs.
 * Everything is path-drawn on the live canvas — no offscreen sprite rects.
 */
export function drawSkeleton(
  ctx: CanvasRenderingContext2D,
  kit: FighterKit,
  x: number,
  footY: number,
  facing: number,
  pose: Pose,
  opts: DrawOpts = {},
): { hand: [number, number]; foot: [number, number]; head: [number, number] } {
  const s = 1.18 * kit.build;
  const flash = opts.flash ?? 0;
  let primary = kit.primary;
  let secondary = kit.secondary;
  let skin = kit.skin;
  if (flash > 0) {
    primary = [255, 70, 70];
    secondary = [160, 30, 30];
    skin = [255, 210, 210];
  }
  const metal: RGB = [190, 198, 210];
  const accent = kit.accent;

  const hipX = x + pose.leanX * facing;
  const hipY = footY - 100 * s + pose.hipY;

  // Soft elliptical contact shadow (path only — never a filled Surface rect)
  ctx.save();
  ctx.fillStyle = `rgba(0,0,0,${opts.airborne ? 0.18 : 0.38})`;
  ctx.beginPath();
  ctx.ellipse(x, footY - 4, opts.airborne ? 36 : 52, 10, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  const drawLeg = (side: 1 | -1, hipAng: number, kneeBend: number, back: boolean) => {
    const color = back ? shade(primary, -35) : primary;
    const hx = hipX + side * 8 * facing;
    const [kx, ky] = end(hx, hipY, hipAng, 50 * s, facing);
    capsule(ctx, hx, hipY, kx, ky, (back ? 12 : 14) * s, (back ? 10 : 11.5) * s, color);
    // knee plate
    ctx.fillStyle = rgb(metal);
    ctx.beginPath();
    ctx.arc(kx, ky, 11 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = rgb(shade(metal, -40));
    ctx.lineWidth = 2;
    ctx.stroke();
    const shinAng = hipAng - kneeBend;
    const [fx, fy] = end(kx, ky, shinAng, 46 * s, facing);
    capsule(ctx, kx, ky, fx, fy, 11 * s, 8.5 * s, shade(color, -25));
    // boot
    ctx.fillStyle = rgb(kit.hairStyle === "ponytail" && kit.id === "nvidia" ? accent : shade(primary, -45));
    ctx.beginPath();
    ctx.ellipse(fx + 4 * facing, fy + 2, 16 * s, 8 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = rgb(metal);
    ctx.lineWidth = 2;
    ctx.stroke();
    return [fx, fy] as [number, number];
  };

  // Legs: far then near
  if (facing > 0) {
    drawLeg(-1, pose.lHip, pose.lKnee, true);
  } else {
    drawLeg(1, pose.rHip, pose.rKnee, true);
  }
  const frontFoot =
    facing > 0
      ? drawLeg(1, pose.rHip, pose.rKnee, false)
      : drawLeg(-1, pose.lHip, pose.lKnee, false);

  // Hips / pelvis
  ctx.fillStyle = rgb(shade(primary, -15));
  roundRect(ctx, hipX - 26 * s, hipY - 8 * s, 52 * s, 26 * s, 10 * s);

  // Torso
  const torsoAng = (pose.torso * facing * Math.PI) / 180;
  const shoulderY = hipY - 78 * s;
  const shoulderX = hipX + Math.sin(torsoAng) * 20;
  ctx.save();
  ctx.translate(hipX, hipY - 8 * s);
  ctx.rotate(torsoAng);
  roundRect(ctx, -30 * s, -78 * s, 60 * s, 86 * s, 16 * s, primary);
  roundRect(ctx, -22 * s, -68 * s, 44 * s, 66 * s, 12 * s, secondary);
  // chest plate
  roundRect(ctx, -20 * s, -60 * s, 40 * s, 12 * s, 3 * s, metal);
  roundRect(ctx, -16 * s, -30 * s, 32 * s, 8 * s, 3 * s, accent);
  // belt
  roundRect(ctx, -28 * s, -4 * s, 56 * s, 12 * s, 3 * s, [28, 28, 36]);
  ctx.fillStyle = rgb(metal);
  ctx.beginPath();
  ctx.arc(0, 2 * s, 7 * s, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = rgb(accent);
  ctx.beginPath();
  ctx.arc(0, 2 * s, 4 * s, 0, Math.PI * 2);
  ctx.fill();
  // badge
  ctx.fillStyle = rgb(accent);
  ctx.beginPath();
  ctx.arc(0, -48 * s, 13 * s, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#0c0c12";
  ctx.font = `bold ${Math.max(11, 14 * s)}px Bebas Neue, Impact, sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(kit.name.slice(0, 2), 0, -48 * s);
  ctx.restore();

  const drawArm = (side: 1 | -1, shAng: number, elBend: number, back: boolean) => {
    const color = back ? shade(primary, -30) : primary;
    const sx = shoulderX + side * 16 * facing;
    const sy = shoulderY;
    // pauldron
    ctx.fillStyle = rgb(metal);
    ctx.beginPath();
    ctx.arc(sx, sy, 14 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = rgb(shade(metal, -40));
    ctx.lineWidth = 2;
    ctx.stroke();
    const [ex, ey] = end(sx, sy, shAng, 38 * s, facing);
    capsule(ctx, sx, sy, ex, ey, (back ? 10 : 11.5) * s, 9 * s, color);
    const handAng = shAng - elBend * 0.35;
    const [hx, hy] = end(ex, ey, handAng, 34 * s, facing);
    capsule(ctx, ex, ey, hx, hy, 9 * s, 7.5 * s, shade(color, -20));
    // glove
    ctx.fillStyle = rgb(accent);
    ctx.beginPath();
    ctx.arc(hx, hy, 11 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = rgb([24, 24, 32]);
    ctx.lineWidth = 2;
    ctx.stroke();
    return [hx, hy] as [number, number];
  };

  if (facing > 0) {
    drawArm(-1, pose.lShoulder, pose.lElbow, true);
  } else {
    drawArm(1, pose.rShoulder, pose.rElbow, true);
  }
  const hand =
    facing > 0
      ? drawArm(1, pose.rShoulder, pose.rElbow, false)
      : drawArm(-1, pose.lShoulder, pose.lElbow, false);

  // Head
  const headAng = ((pose.head + pose.torso * 0.4) * facing * Math.PI) / 180;
  const hx = shoulderX + Math.sin(headAng) * 8 * facing + 4 * facing;
  const hy = shoulderY - 32 * s;
  drawHair(ctx, hx, hy, facing, kit, s);
  ctx.fillStyle = rgb(skin);
  ctx.beginPath();
  ctx.arc(hx, hy, 23 * s, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = rgb([24, 24, 32]);
  ctx.lineWidth = 3;
  ctx.stroke();
  // eyes + mouth for readable human face
  ctx.fillStyle = rgb([20, 20, 28]);
  ctx.beginPath();
  ctx.arc(hx + 8 * facing, hy + 1, 3.8, 0, Math.PI * 2);
  ctx.arc(hx - 6 * facing, hy + 1, 3.8, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#fff";
  ctx.beginPath();
  ctx.arc(hx + 9 * facing, hy, 1.3, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = rgb(shade(kit.hair, 20));
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(hx - 10 * facing, hy - 7);
  ctx.lineTo(hx + 12 * facing, hy - 9);
  ctx.stroke();
  ctx.strokeStyle = rgb([120, 70, 70]);
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(hx + 2 * facing, hy + 10, 6, 0.15, Math.PI - 0.15);
  ctx.stroke();

  // Attack whoosh (additive-looking stroke, still path-based)
  if ((opts.attackFlash ?? 0) > 0) {
    ctx.save();
    ctx.globalAlpha = Math.min(1, opts.attackFlash!);
    ctx.strokeStyle = rgb(accent);
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.arc(hand[0], hand[1], 18, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  return { hand, foot: frontFoot, head: [hx, hy] };
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
  fill?: RGB,
): void {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
  if (fill) {
    ctx.fillStyle = rgb(fill);
    ctx.fill();
    ctx.strokeStyle = "rgba(16,16,24,0.9)";
    ctx.lineWidth = 2;
    ctx.stroke();
  } else {
    ctx.fill();
  }
}
