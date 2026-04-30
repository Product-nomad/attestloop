// One-off rasteriser for site/public/og-image.png. Composes the SVG
// described in the v1 spec (charcoal background, serif wordmark, mono
// caption + version line) and uses sharp / librsvg to produce a 1200x630
// PNG. JetBrains Mono is embedded as a base64 woff2 data URI so the
// rendering doesn't depend on system-installed mono fonts; the serif
// falls through Iowan Old Style → Charter → Georgia → DejaVu Serif via
// fontconfig.
//
// Run with: node scripts/build-og-image.mjs

import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const __dirname = dirname(fileURLToPath(import.meta.url));
const fontPath = resolve(
  __dirname,
  "../node_modules/.pnpm/@fontsource+jetbrains-mono@5.2.8/node_modules/@fontsource/jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2",
);
const outPath = resolve(__dirname, "../public/og-image.png");

const fontB64 = readFileSync(fontPath).toString("base64");

const W = 1200;
const H = 630;

// Layout constants (centred + bottom-left version line, 48 px from edges)
const wordmarkY = 280;
const ruleY = 360;
const captionY = 410;
const versionX = 48;
const versionY = H - 48;

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs>
    <style>
      @font-face {
        font-family: "JetBrains Mono Embedded";
        font-style: normal;
        font-weight: 400;
        src: url(data:font/woff2;base64,${fontB64}) format("woff2");
      }
      .bg { fill: #0e1014; }
      .wordmark {
        font-family: "Iowan Old Style", "Charter", "Georgia", "DejaVu Serif", serif;
        font-weight: 400;
        font-size: 96pt;
        fill: #e6e8eb;
      }
      .rule { stroke: #363b46; stroke-width: 1; }
      .caption {
        font-family: "JetBrains Mono Embedded", "JetBrains Mono", monospace;
        font-weight: 400;
        font-size: 24pt;
        fill: #a8adb8;
        letter-spacing: 0.04em;
      }
      .version {
        font-family: "JetBrains Mono Embedded", "JetBrains Mono", monospace;
        font-weight: 400;
        font-size: 14pt;
        fill: #6b7280;
      }
    </style>
  </defs>

  <rect class="bg" x="0" y="0" width="${W}" height="${H}" />

  <text class="wordmark" x="${W / 2}" y="${wordmarkY}" text-anchor="middle">Attestloop</text>

  <line class="rule" x1="${W / 2 - 120}" y1="${ruleY}" x2="${W / 2 + 120}" y2="${ruleY}" />

  <text class="caption" x="${W / 2}" y="${captionY}" text-anchor="middle">Agentic regulatory attestation</text>

  <text class="version" x="${versionX}" y="${versionY}">v1.0.0 · attestloop.ai</text>
</svg>
`;

await sharp(Buffer.from(svg))
  .resize(W, H, { fit: "fill" })
  .png({ compressionLevel: 9 })
  .toFile(outPath);

console.log(`wrote ${outPath} (${W}x${H})`);
