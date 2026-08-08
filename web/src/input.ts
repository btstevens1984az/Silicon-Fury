export class Input {
  private down = new Set<string>();
  private pressed = new Set<string>();

  constructor() {
    window.addEventListener("keydown", (e) => {
      if (!this.down.has(e.code)) this.pressed.add(e.code);
      this.down.add(e.code);
      if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code)) {
        e.preventDefault();
      }
    });
    window.addEventListener("keyup", (e) => this.down.delete(e.code));
  }

  hold(code: string): boolean {
    return this.down.has(code);
  }

  press(code: string): boolean {
    if (this.pressed.has(code)) {
      this.pressed.delete(code);
      return true;
    }
    return false;
  }

  endFrame(): void {
    this.pressed.clear();
  }
}
