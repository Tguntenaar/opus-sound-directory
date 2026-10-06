#!/usr/bin/env python3
"""Rasterise public/favicon.svg into PNG sizes for browsers and PWA."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

BG = "#09090b"
BARS = [
    (6, 14, 3, 8, "#7c3aed"),
    (11, 10, 3, 12, "#a78bfa"),
    (16, 12, 3, 10, "#7c3aed"),
    (21, 8, 3, 14, "#c4b5fd"),
    (26, 13, 3, 9, "#6d28d9"),
]


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)
    scale = size / 32
    radius = max(1, int(6 * scale))
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=BG)
    for x, y, w, h, color in BARS:
        x0 = int(x * scale)
        y0 = int(y * scale)
        x1 = int((x + w) * scale)
        y1 = int((y + h) * scale)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=max(1, int(scale)), fill=color)
    return img


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name, size in [
        ("favicon-16.png", 16),
        ("favicon-32.png", 32),
        ("apple-touch-icon.png", 180),
        ("icon-192.png", 192),
        ("icon-512.png", 512),
    ]:
        out = PUBLIC / name
        draw_icon(size).save(out, format="PNG", optimize=True)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
