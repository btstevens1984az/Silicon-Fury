/** Shared types and constants */

export type RGB = [number, number, number];

export const WIDTH = 1280;
export const HEIGHT = 720;
export const GROUND_Y = 580;
export const GRAVITY = 2200;
export const FPS = 60;

export type Team = "computer" | "tech";

export interface FighterKit {
  id: string;
  name: string;
  team: Team;
  tagline: string;
  specialName: string;
  primary: RGB;
  secondary: RGB;
  accent: RGB;
  skin: RGB;
  hair: RGB;
  gender: "m" | "f";
  hairStyle: "short" | "spike" | "ponytail" | "slick" | "buzz" | "wild";
  build: number; // width scale
  hp: number;
  power: number;
  speed: number;
  defense: number;
  special: number;
  rival: string;
}

/** Full-body pose in degrees (0 = straight down for limbs; torso 0 = upright). */
export interface Pose {
  hipTilt: number;
  torso: number;
  head: number;
  /** left / right arm swing (positive = forward) */
  lShoulder: number;
  rShoulder: number;
  lElbow: number;
  rElbow: number;
  lHip: number;
  rHip: number;
  lKnee: number;
  rKnee: number;
  lAnkle: number;
  rAnkle: number;
  /** body offsets in px relative to feet */
  hipY: number;
  leanX: number;
}

export const IDLE_POSE: Pose = {
  hipTilt: 0,
  torso: 4,
  head: -2,
  lShoulder: -28,
  rShoulder: 32,
  lElbow: 35,
  rElbow: 40,
  lHip: 12,
  rHip: -10,
  lKnee: 18,
  rKnee: 16,
  lAnkle: 0,
  rAnkle: 0,
  hipY: 0,
  leanX: 0,
};

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

export function easeInOut(t: number): number {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

export function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export function easeInCubic(t: number): number {
  return t * t * t;
}

export function lerpPose(a: Pose, b: Pose, t: number): Pose {
  const k = clamp(t, 0, 1);
  const out = {} as Pose;
  (Object.keys(a) as (keyof Pose)[]).forEach((key) => {
    out[key] = lerp(a[key], b[key], k);
  });
  return out;
}

export function blendPoses(poses: { pose: Pose; w: number }[]): Pose {
  const total = poses.reduce((s, p) => s + p.w, 0) || 1;
  const acc = { ...IDLE_POSE };
  (Object.keys(IDLE_POSE) as (keyof Pose)[]).forEach((key) => {
    acc[key] = poses.reduce((s, p) => s + p.pose[key] * p.w, 0) / total;
  });
  return acc;
}
