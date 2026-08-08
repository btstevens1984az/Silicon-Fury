import type { EffectWorld } from "./effects";
import type { Fighter } from "./fighter";

export class CPUBrain {
  difficulty: number;
  cooldown = 0;

  constructor(difficulty = 0.72) {
    this.difficulty = difficulty;
  }

  step(me: Fighter, foe: Fighter, fx: EffectWorld, dt: number): void {
    if (me.hp <= 0) return;
    this.cooldown = Math.max(0, this.cooldown - dt);
    const dist = foe.x - me.x;
    const ad = Math.abs(dist);
    me.facing = dist > 0 ? 1 : -1;

    if (this.cooldown > 0) {
      if (ad > 170 && me.onGround) me.move(dist > 0 ? 1 : -1, ad > 280);
      return;
    }

    if (
      ["punch", "punch2", "kick", "airKick", "special"].includes(foe.state) &&
      ad < 140 &&
      Math.random() < 0.42 * this.difficulty
    ) {
      me.block(true);
      this.cooldown = 0.12;
      return;
    }

    if (ad > 240) {
      if (Math.random() < 0.4 * this.difficulty) {
        me.dash(dist > 0 ? 1 : -1);
        this.cooldown = 0.2;
      } else {
        me.move(dist > 0 ? 1 : -1, true);
      }
      return;
    }

    if (ad > 110) {
      me.move(dist > 0 ? 1 : -1);
      const r = Math.random();
      if (r < 0.1 * this.difficulty) {
        me.jump();
        this.cooldown = 0.12;
      } else if (r < 0.28 * this.difficulty) {
        me.kick();
        this.cooldown = 0.2;
      } else if (r < 0.4 * this.difficulty) {
        me.punch();
        this.cooldown = 0.14;
      }
      return;
    }

    if (!me.onGround) {
      if (Math.random() < 0.55 * this.difficulty) {
        me.kick();
        this.cooldown = 0.18;
      } else if (Math.random() < 0.35) {
        me.punch();
        this.cooldown = 0.14;
      }
      return;
    }

    const roll = Math.random();
    if (me.meter >= 55 && roll < 0.22 * this.difficulty) {
      me.special(fx);
      this.cooldown = 0.4;
    } else if (roll < 0.32) {
      me.punch();
      this.cooldown = 0.12;
    } else if (roll < 0.55) {
      me.kick();
      this.cooldown = 0.2;
    } else if (roll < 0.7) {
      me.jump();
      this.cooldown = 0.12;
    } else if (roll < 0.82) {
      me.dash(dist > 0 ? 1 : -1);
      this.cooldown = 0.2;
    } else {
      me.move(dist > 0 ? -1 : 1);
      this.cooldown = 0.1;
    }
  }
}
