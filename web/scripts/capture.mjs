/**
 * Capture demo GIFs via Playwright + ffmpeg.
 * Usage: npm run capture
 */
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { readFileSync, mkdirSync, rmSync, existsSync, readdirSync } from "node:fs";
import { join, extname } from "node:path";
import { fileURLToPath } from "node:url";
import playwright from "playwright";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const dist = join(__dirname, "..", "dist");
const root = join(__dirname, "..", "..");
const framesRoot = join(root, "media", "frames");
const gifRoot = join(root, "media", "gifs");

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
};

function serve(port) {
  const server = createServer((req, res) => {
    let path = req.url?.split("?")[0] || "/";
    if (path === "/") path = "/index.html";
    const file = join(dist, path);
    try {
      const data = readFileSync(file);
      res.writeHead(200, { "Content-Type": MIME[extname(file)] || "application/octet-stream" });
      res.end(data);
    } catch {
      res.writeHead(404);
      res.end("missing");
    }
  });
  return new Promise((resolve) => {
    server.listen(port, () => resolve({ close: () => server.close(), url: `http://127.0.0.1:${port}` }));
  });
}

function demoQuery(demo) {
  if (demo === "01-title-teams") return "title";
  if (demo === "02-character-select") return "select";
  if (demo === "04-special-moves") return "specials";
  return "versus";
}

async function capture(demo, seconds, url) {
  const out = join(framesRoot, demo);
  if (existsSync(out)) rmSync(out, { recursive: true });
  mkdirSync(out, { recursive: true });

  const browser = await playwright.chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  await page.goto(`${url}/?demo=${demoQuery(demo)}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);

  const canvas = page.locator("#game");
  const frames = Math.floor(seconds * 16);
  for (let i = 0; i < frames; i++) {
    await canvas.screenshot({ path: join(out, `frame_${String(i).padStart(4, "0")}.png`) });
    await page.waitForTimeout(1000 / 16);
  }
  await browser.close();

  mkdirSync(gifRoot, { recursive: true });
  await new Promise((resolve, reject) => {
    const ff = spawn(
      "ffmpeg",
      [
        "-y",
        "-framerate",
        "16",
        "-i",
        join(out, "frame_%04d.png"),
        "-vf",
        "scale=880:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
        "-loop",
        "0",
        join(gifRoot, `${demo}.gif`),
      ],
      { stdio: "inherit" },
    );
    ff.on("exit", (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg ${code}`))));
  });
  console.log("Wrote", demo);
}

const demos = [
  ["01-title-teams", 3.5],
  ["02-character-select", 4.5],
  ["03-versus-brawl", 7],
  ["04-special-moves", 7],
  ["05-story-ko", 7],
];

const { close, url } = await serve(4177);
try {
  for (const [d, s] of demos) await capture(d, s, url);
} finally {
  close();
}
console.log("GIFs:", readdirSync(gifRoot));
