import { IDLE_POSE, easeInOut, easeOutCubic, lerpPose, type Pose } from "../types";

/** Named combat / locomotion clips with human weight and follow-through. */
export type ClipName =
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

type Key = { t: number; pose: Pose; ease?: (t: number) => number };

function p(partial: Partial<Pose>): Pose {
  return { ...IDLE_POSE, ...partial };
}

const WALK_A = p({
  torso: 8,
  head: -4,
  lShoulder: 42,
  rShoulder: -38,
  lElbow: 55,
  rElbow: 50,
  lHip: -38,
  rHip: 40,
  lKnee: 55,
  rKnee: 22,
  hipY: -4,
  leanX: 6,
});
const WALK_B = p({
  torso: 6,
  head: -2,
  lShoulder: -38,
  rShoulder: 42,
  lElbow: 50,
  rElbow: 55,
  lHip: 40,
  rHip: -38,
  lKnee: 22,
  rKnee: 55,
  hipY: -4,
  leanX: 6,
});

const CLIPS: Record<ClipName, Key[]> = {
  idle: [
    { t: 0, pose: p({ lShoulder: -26, rShoulder: 30, lHip: 10, rHip: -8, hipY: 0 }) },
    { t: 0.5, pose: p({ lShoulder: -30, rShoulder: 34, lHip: 14, rHip: -12, hipY: -3, torso: 6 }) },
    { t: 1, pose: p({ lShoulder: -26, rShoulder: 30, lHip: 10, rHip: -8, hipY: 0 }) },
  ],
  walk: [
    { t: 0, pose: WALK_A },
    { t: 0.5, pose: WALK_B },
    { t: 1, pose: WALK_A },
  ],
  run: [
    { t: 0, pose: p({ torso: 18, head: -8, lShoulder: 55, rShoulder: -50, lElbow: 70, rElbow: 65, lHip: -55, rHip: 58, lKnee: 75, rKnee: 28, hipY: -8, leanX: 14 }) },
    { t: 0.5, pose: p({ torso: 16, head: -6, lShoulder: -50, rShoulder: 55, lElbow: 65, rElbow: 70, lHip: 58, rHip: -55, lKnee: 28, rKnee: 75, hipY: -8, leanX: 14 }) },
    { t: 1, pose: p({ torso: 18, head: -8, lShoulder: 55, rShoulder: -50, lElbow: 70, rElbow: 65, lHip: -55, rHip: 58, lKnee: 75, rKnee: 28, hipY: -8, leanX: 14 }) },
  ],
  dash: [
    { t: 0, pose: p({ torso: 10, leanX: 0 }), ease: easeOutCubic },
    { t: 0.25, pose: p({ torso: 28, head: -12, lShoulder: -70, rShoulder: 90, lElbow: 40, rElbow: 20, lHip: -20, rHip: 50, leanX: 28, hipY: -10 }) },
    { t: 1, pose: p({ torso: 8, leanX: 8, lShoulder: -30, rShoulder: 40 }) },
  ],
  jump: [
    { t: 0, pose: p({ hipY: 8, lKnee: 40, rKnee: 40, torso: 8 }), ease: easeOutCubic },
    { t: 0.15, pose: p({ hipY: 18, lKnee: 70, rKnee: 70, torso: 12, lShoulder: -20, rShoulder: 20 }) },
    { t: 0.45, pose: p({ hipY: -6, lHip: -25, rHip: 20, lKnee: 55, rKnee: 40, lShoulder: -55, rShoulder: 50, torso: -6 }) },
    { t: 1, pose: p({ hipY: -4, lHip: -20, rHip: 18, lKnee: 50, rKnee: 45, lShoulder: -45, rShoulder: 45 }) },
  ],
  fall: [
    { t: 0, pose: p({ lShoulder: -40, rShoulder: 45, lHip: -15, rHip: 18, lKnee: 35, rKnee: 40, torso: -4 }) },
    { t: 1, pose: p({ lShoulder: -50, rShoulder: 55, lHip: -25, rHip: 28, lKnee: 55, rKnee: 50, torso: -8 }) },
  ],
  crouch: [
    { t: 0, pose: IDLE_POSE, ease: easeOutCubic },
    { t: 1, pose: p({ hipY: 42, torso: 12, head: 6, lHip: 55, rHip: 50, lKnee: 95, rKnee: 92, lShoulder: 50, rShoulder: 55, lElbow: 80, rElbow: 80, leanX: -4 }) },
  ],
  block: [
    { t: 0, pose: IDLE_POSE, ease: easeOutCubic },
    { t: 1, pose: p({ torso: -6, head: 8, lShoulder: 75, rShoulder: 85, lElbow: 95, rElbow: 100, lHip: 18, rHip: 10, lKnee: 35, rKnee: 32, leanX: -10, hipY: 10 }) },
  ],
  punch: [
    { t: 0, pose: IDLE_POSE, ease: easeInOut },
    // anticipation
    { t: 0.12, pose: p({ torso: -8, leanX: -12, rShoulder: -20, lShoulder: -40, rElbow: 90, hipY: 4 }) },
    // strike
    { t: 0.38, pose: p({ torso: 22, head: -10, leanX: 34, rShoulder: 110, rElbow: 8, lShoulder: -70, lElbow: 70, rHip: 35, lHip: -25, rKnee: 30, hipY: -2 }), ease: easeOutCubic },
    // recover
    { t: 0.7, pose: p({ torso: 10, leanX: 12, rShoulder: 50, rElbow: 45, lShoulder: -35 }) },
    { t: 1, pose: IDLE_POSE },
  ],
  punch2: [
    { t: 0, pose: p({ torso: 10, leanX: 10, rShoulder: 40 }), ease: easeInOut },
    { t: 0.15, pose: p({ torso: -6, leanX: -8, lShoulder: -10, rShoulder: 30, lElbow: 85 }) },
    { t: 0.4, pose: p({ torso: 24, leanX: 36, lShoulder: 105, lElbow: 10, rShoulder: -55, rHip: -20, lHip: 30 }), ease: easeOutCubic },
    { t: 0.75, pose: p({ torso: 8, leanX: 8, lShoulder: 20 }) },
    { t: 1, pose: IDLE_POSE },
  ],
  kick: [
    { t: 0, pose: IDLE_POSE, ease: easeInOut },
    { t: 0.14, pose: p({ torso: -12, leanX: -8, rHip: -30, rKnee: 80, lShoulder: -40, rShoulder: -20, hipY: 6 }) },
    { t: 0.42, pose: p({ torso: -18, head: 8, leanX: 22, rHip: 118, rKnee: 8, lHip: -45, lKnee: 70, lShoulder: -50, rShoulder: -35, hipY: -4 }), ease: easeOutCubic },
    { t: 0.72, pose: p({ torso: -8, leanX: 8, rHip: 40, rKnee: 40 }) },
    { t: 1, pose: IDLE_POSE },
  ],
  airKick: [
    { t: 0, pose: p({ lShoulder: -45, rShoulder: 45, lHip: -20, rHip: 20 }), ease: easeOutCubic },
    { t: 0.35, pose: p({ torso: -22, leanX: 18, rHip: 125, rKnee: 5, lHip: -50, lKnee: 60, lShoulder: -55, rShoulder: -40 }) },
    { t: 1, pose: p({ torso: -10, rHip: 40, lHip: -25, lShoulder: -40, rShoulder: 40 }) },
  ],
  special: [
    { t: 0, pose: IDLE_POSE, ease: easeInOut },
    { t: 0.18, pose: p({ torso: -15, leanX: -16, lShoulder: -90, rShoulder: -40, hipY: 8, lKnee: 40, rKnee: 40 }) },
    { t: 0.45, pose: p({ torso: 28, leanX: 42, rShoulder: 125, rElbow: 5, lShoulder: -85, rHip: 55, lHip: -35, hipY: -6 }), ease: easeOutCubic },
    { t: 0.7, pose: p({ torso: 18, leanX: 28, rShoulder: 100, lShoulder: -70 }) },
    { t: 1, pose: p({ torso: 8, leanX: 10, rShoulder: 40 }) },
  ],
  hit: [
    { t: 0, pose: IDLE_POSE, ease: easeOutCubic },
    { t: 0.3, pose: p({ torso: -32, head: 24, leanX: -28, lShoulder: -70, rShoulder: -60, lHip: 45, rHip: -40, lKnee: 55, rKnee: 50, hipY: 4 }) },
    { t: 1, pose: p({ torso: -18, leanX: -16, lShoulder: -50, rShoulder: -40 }) },
  ],
  ko: [
    { t: 0, pose: p({ torso: -20, leanX: -20 }), ease: easeInOut },
    { t: 0.45, pose: p({ torso: 55, head: 35, leanX: -50, lShoulder: -100, rShoulder: -95, lHip: 70, rHip: -75, hipY: 20 }) },
    { t: 1, pose: p({ torso: 88, head: 40, leanX: -70, lShoulder: -110, rShoulder: -105, lHip: 85, rHip: -90, hipY: 55 }) },
  ],
};

export function sampleClip(name: ClipName, time01: number, loop = false): Pose {
  const keys = CLIPS[name];
  let t = time01;
  if (loop) t = ((t % 1) + 1) % 1;
  else t = Math.max(0, Math.min(1, t));

  if (t <= keys[0].t) return keys[0].pose;
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (t <= b.t) {
      let u = (t - a.t) / Math.max(1e-6, b.t - a.t);
      const ease = b.ease ?? a.ease ?? easeInOut;
      u = ease(u);
      return lerpPose(a.pose, b.pose, u);
    }
  }
  return keys[keys.length - 1].pose;
}

export const CLIP_DURATION: Record<ClipName, number> = {
  idle: 1.6,
  walk: 0.55,
  run: 0.38,
  dash: 0.22,
  jump: 0.45,
  fall: 0.4,
  crouch: 0.12,
  block: 0.1,
  punch: 0.32,
  punch2: 0.34,
  kick: 0.42,
  airKick: 0.36,
  special: 0.7,
  hit: 0.28,
  ko: 1.1,
};
