// Rasterises site/public/og-image.svg to site/public/og-image.png
// at 1200x630. The authored SVG references "JetBrains Mono" by name; this
// script substitutes a base64-embedded copy of the woff2 file before
// passing the SVG to sharp / librsvg, so the rendered PNG renders the
// caption exactly even when fontconfig on the host machine doesn't have
// JetBrains Mono installed. The serif wordmark is left to the
// fontconfig fallback chain.
//
// Run with: pnpm og:build

import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = resolve(__dirname, "..");

const svgPath = resolve(SITE_ROOT, "public", "og-image.svg");
const pngPath = resolve(SITE_ROOT, "public", "og-image.png");
const fontPath = resolve(
  SITE_ROOT,
  "node_modules/.pnpm/@fontsource+jetbrains-mono@5.2.8/node_modules/@fontsource/jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2",
);

const WIDTH = 1200;
const HEIGHT = 630;

const fontB64 = readFileSync(fontPath).toString("base64");
const svgSource = readFileSync(svgPath, "utf-8");

const fontFaceBlock = `
    @font-face {
      font-family: "JetBrains Mono";
      font-style: normal;
      font-weight: 400;
      src: url(data:font/woff2;base64,${fontB64}) format("woff2");
    }`;

// Inject the @font-face directive at the top of the existing <style> block.
const svgForRender = svgSource.replace("<style>", `<style>${fontFaceBlock}`);

await sharp(Buffer.from(svgForRender))
  .resize(WIDTH, HEIGHT, { fit: "fill" })
  .png({ compressionLevel: 9 })
  .toFile(pngPath);

console.log(`wrote ${pngPath} (${WIDTH}x${HEIGHT})`);
