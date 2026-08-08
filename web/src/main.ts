import "./style.css";
import { Game } from "./game";

const canvas = document.querySelector<HTMLCanvasElement>("#game")!;
const hint = document.querySelector<HTMLElement>("#hud-hint")!;
const params = new URLSearchParams(location.search);
const demo = params.get("demo") ?? undefined;

const game = new Game(canvas, hint, demo ?? undefined);
game.start();

// Expose for capture scripts
(window as unknown as { __siliconFury: Game }).__siliconFury = game;
