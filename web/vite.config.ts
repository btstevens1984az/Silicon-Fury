import { defineConfig } from "vite";

export default defineConfig({
  // Relative base so GitHub Pages + local preview both resolve assets.
  base: "./",
  server: { port: 5173, open: false },
  build: {
    outDir: "dist",
    assetsDir: "assets",
  },
});
