#!/usr/bin/env node
/**
 * Renders favicon PNGs and preview sheets for brand/concepts/.
 * Requires: @resvg/resvg-js, sharp (dev deps or npx).
 */
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Resvg } from "@resvg/resvg-js";
import sharp from "sharp";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const ARTIFACTS = "/opt/cursor/artifacts";
const BG = "#09090b";

const CONCEPTS = [
  { id: 1, slug: "1-waveform-o", name: "Waveform O" },
  { id: 2, slug: "2-pulse-ring", name: "Pulse ring" },
  { id: 3, slug: "3-eq-grid", name: "EQ grid" },
  { id: 4, slug: "4-sine-app", name: "Sine app" },
];

async function renderMarkPng(svgPath, size) {
  const svg = readFileSync(svgPath, "utf8");
  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: size },
    background: BG,
  });
  const png = resvg.render().asPng();
  return sharp(png).resize(size, size).png().toBuffer();
}

mkdirSync(ARTIFACTS, { recursive: true });

for (const c of CONCEPTS) {
  const dir = join(ROOT, "brand", "concepts", c.slug);
  const mark = join(dir, "mark.svg");
  for (const size of [16, 32, 180]) {
    const png = await renderMarkPng(mark, size);
    writeFileSync(join(dir, `favicon-${size}.png`), png);
  }
}

const sheetW = 1600;
const sheetH = 1000;
const cells = [];

for (let i = 0; i < CONCEPTS.length; i++) {
  const c = CONCEPTS[i];
  const col = i % 2;
  const row = Math.floor(i / 2);
  const ox = 80 + col * 760;
  const oy = 80 + row * 460;

  const markLarge = await renderMarkPng(join(ROOT, "brand", "concepts", c.slug, "mark.svg"), 120);
  const lockupSvg = readFileSync(join(ROOT, "brand", "concepts", c.slug, "lockup.svg"), "utf8");
  const lockupResvg = new Resvg(lockupSvg, {
    fitTo: { mode: "width", value: 340 },
    background: "transparent",
  });
  const lockupPng = lockupResvg.render().asPng();
  const fav16 = readFileSync(join(ROOT, "brand", "concepts", c.slug, "favicon-16.png"));
  const fav32 = readFileSync(join(ROOT, "brand", "concepts", c.slug, "favicon-32.png"));

  cells.push({ ox, oy, c, markLarge, lockupPng, fav16, fav32 });
}

const composites = [];
for (const cell of cells) {
  const { ox, oy, c, markLarge, lockupPng, fav16, fav32 } = cell;
  composites.push({ input: markLarge, top: oy, left: ox });
  composites.push({ input: lockupPng, top: oy + 140, left: ox });
  composites.push({ input: fav16, top: oy + 200, left: ox });
  composites.push({ input: fav32, top: oy + 196, left: ox + 28 });

  const labelSvg = Buffer.from(`<svg width="400" height="40" xmlns="http://www.w3.org/2000/svg">
    <text x="0" y="28" fill="#a1a1aa" font-family="system-ui,sans-serif" font-size="14">${c.id}. ${c.name}</text>
  </svg>`);
  composites.push({ input: labelSvg, top: oy - 28, left: ox });

  const conceptPreview = await sharp({
    create: { width: 720, height: 380, channels: 4, background: BG },
  })
    .composite([
      { input: markLarge, top: 20, left: 20 },
      { input: lockupPng, top: 160, left: 20 },
      { input: fav16, top: 220, left: 20 },
      { input: fav32, top: 216, left: 48 },
      { input: labelSvg, top: 0, left: 20 },
    ])
    .png()
    .toBuffer();
  writeFileSync(join(ARTIFACTS, `logo-${c.id}.png`), conceptPreview);
}

await sharp({
  create: { width: sheetW, height: sheetH, channels: 4, background: BG },
})
  .composite(composites)
  .png()
  .toFile(join(ARTIFACTS, "logo-concepts.png"));

console.log("Wrote logo previews to", ARTIFACTS);
