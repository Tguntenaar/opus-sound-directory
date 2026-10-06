#!/usr/bin/env node
/** Rasterise public/brand/*.svg into favicons, PWA icons, ICO, and preview sheet. */
import { readFileSync, writeFileSync, copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Resvg } from "@resvg/resvg-js";
import sharp from "sharp";
import toIco from "to-ico";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const PUBLIC = join(ROOT, "public");
const BRAND = join(PUBLIC, "brand");
const ARTIFACTS = "/opt/cursor/artifacts";
const BG = "#09090b";

async function svgToPng(svgPath, size, background = BG) {
  const svg = readFileSync(svgPath, "utf8");
  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: size },
    background,
  });
  const png = resvg.render().asPng();
  return sharp(png).resize(size, size).png({ compressionLevel: 9 }).toBuffer();
}

async function maskableFromTile(tilePng, size) {
  const inner = Math.round(size * 0.62);
  const scaled = await sharp(tilePng).resize(inner, inner).png().toBuffer();
  return sharp({
    create: { width: size, height: size, channels: 4, background: BG },
  })
    .composite([{ input: scaled, gravity: "center" }])
    .png({ compressionLevel: 9 })
    .toBuffer();
}

async function buildPreviewSheet(tileSvg) {
  mkdirSync(ARTIFACTS, { recursive: true });
  const sizes = [16, 32, 48, 180];
  const backgrounds = [
    { name: "light", color: "#ffffff" },
    { name: "dark", color: "#202124" },
  ];

  const cell = 96;
  const pad = 24;
  const cols = sizes.length;
  const rows = backgrounds.length;
  const labelH = 28;
  const sheetW = pad * 2 + cols * cell;
  const sheetH = pad * 2 + labelH + rows * cell + 72;

  const composites = [];

  const titleSvg = Buffer.from(
    `<svg width="${sheetW}" height="32" xmlns="http://www.w3.org/2000/svg">
      <text x="${pad}" y="24" fill="#e4e4e7" font-family="system-ui,sans-serif" font-size="18" font-weight="600">Opus Sounds — favicon preview</text>
    </svg>`,
  );
  composites.push({ input: titleSvg, top: 8, left: 0 });

  for (let r = 0; r < backgrounds.length; r++) {
    const bg = backgrounds[r];
    const rowY = pad + labelH + r * cell;

    const rowLabel = Buffer.from(
      `<svg width="200" height="24" xmlns="http://www.w3.org/2000/svg">
        <text x="0" y="18" fill="#a1a1aa" font-family="system-ui,sans-serif" font-size="13">${bg.name} (${bg.color})</text>
      </svg>`,
    );
    composites.push({ input: rowLabel, top: rowY - 20, left: pad });

    for (let c = 0; c < sizes.length; c++) {
      const size = sizes[c];
      const colX = pad + c * cell;
      const iconFull = await svgToPng(tileSvg, size, bg.color);
      const display = Math.min(size, cell - 24);
      const icon =
        size === display
          ? iconFull
          : await sharp(iconFull).resize(display, display).png().toBuffer();
      const swatchSize = cell - 8;
      const offset = Math.floor((swatchSize - display) / 2);

      const swatch = await sharp({
        create: { width: swatchSize, height: swatchSize, channels: 3, background: bg.color },
      })
        .composite([
          {
            input: icon,
            left: offset,
            top: offset,
          },
        ])
        .png()
        .toBuffer();

      composites.push({ input: swatch, top: rowY, left: colX });

      const sizeLabel = Buffer.from(
        `<svg width="${cell}" height="20" xmlns="http://www.w3.org/2000/svg">
          <text x="${Math.floor(cell / 2)}" y="14" text-anchor="middle" fill="#71717a" font-family="system-ui,sans-serif" font-size="11">${size}px</text>
        </svg>`,
      );
      composites.push({ input: sizeLabel, top: rowY + cell - 28, left: colX });
    }
  }

  const tabY = pad + labelH + rows * cell + 8;
  const tabW = 280;
  const tabH = 40;
  const tab16 = await svgToPng(tileSvg, 16);
  const tabMock = await sharp({
    create: { width: tabW, height: tabH, channels: 4, background: { r: 32, g: 33, b: 36, alpha: 1 } },
  })
    .composite([
      { input: tab16, left: 12, top: Math.floor((tabH - 16) / 2) },
      {
        input: Buffer.from(
          `<svg width="200" height="20" xmlns="http://www.w3.org/2000/svg">
            <text x="0" y="15" fill="#e8eaed" font-family="system-ui,sans-serif" font-size="13">Opus Sounds Directory</text>
          </svg>`,
        ),
        left: 36,
        top: 12,
      },
    ])
    .png()
    .toBuffer();

  composites.push({ input: tabMock, top: tabY, left: pad });

  const tabCaption = Buffer.from(
    `<svg width="320" height="20" xmlns="http://www.w3.org/2000/svg">
      <text x="0" y="15" fill="#71717a" font-family="system-ui,sans-serif" font-size="11">Mock browser tab (dark chrome)</text>
    </svg>`,
  );
  composites.push({ input: tabCaption, top: tabY - 18, left: pad });

  await sharp({
    create: { width: sheetW, height: sheetH, channels: 3, background: "#18181b" },
  })
    .composite(composites)
    .png()
    .toFile(join(ARTIFACTS, "favicon-preview.png"));

  console.log("Wrote /opt/cursor/artifacts/favicon-preview.png");
}

const faviconSvg = join(BRAND, "mark-favicon.svg");
const markTileSvg = join(BRAND, "mark-tile.svg");

if (!readFileSync(join(BRAND, "mark.svg"), "utf8")) {
  throw new Error("missing public/brand/mark.svg");
}

copyFileSync(faviconSvg, join(PUBLIC, "favicon.svg"));

const rasterTargets = [
  ["favicon-16.png", 16, markTileSvg],
  ["favicon-32.png", 32, markTileSvg],
  ["favicon-48.png", 48, markTileSvg],
  ["apple-touch-icon.png", 180, markTileSvg],
  ["icon-192.png", 192, markTileSvg],
  ["icon-512.png", 512, markTileSvg],
];

for (const [name, size, src] of rasterTargets) {
  writeFileSync(join(PUBLIC, name), await svgToPng(src, size));
  console.log(`Wrote public/${name}`);
}

const tile192 = await svgToPng(markTileSvg, 192);
const tile512 = await svgToPng(markTileSvg, 512);
writeFileSync(join(PUBLIC, "icon-192-maskable.png"), await maskableFromTile(tile192, 192));
writeFileSync(join(PUBLIC, "icon-512-maskable.png"), await maskableFromTile(tile512, 512));
console.log("Wrote public/icon-192-maskable.png");
console.log("Wrote public/icon-512-maskable.png");

const icoSizes = [16, 32, 48];
const icoBuffers = await Promise.all(icoSizes.map((s) => svgToPng(markTileSvg, s)));
writeFileSync(join(PUBLIC, "favicon.ico"), await toIco(icoBuffers));
console.log("Wrote public/favicon.ico");

writeFileSync(join(BRAND, "og-mark-200.png"), await svgToPng(markTileSvg, 200));
console.log("Wrote public/brand/og-mark-200.png");

await buildPreviewSheet(markTileSvg);
