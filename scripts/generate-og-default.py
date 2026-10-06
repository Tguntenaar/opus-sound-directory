#!/usr/bin/env python3
"""Build public/og-default.png (1200×630) for social sharing."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "og-default.png"
MARK = ROOT / "public" / "brand" / "og-mark-200.png"
W, H = 1200, 630
BG = "#09090b"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        p = Path(path)
        if p.is_file():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    if MARK.is_file():
        mark = Image.open(MARK).convert("RGBA")
        mark = mark.resize((180, 180), Image.Resampling.LANCZOS)
        img.paste(mark, (80, 225), mark)

    title_font = load_font(52, bold=True)
    sub_font = load_font(22)
    draw.multiline_text(
        (520, 180),
        "Opus Sounds\nDirectory",
        fill="#fafafa",
        font=title_font,
        spacing=8,
    )
    draw.multiline_text(
        (520, 340),
        "Royalty-free SFX & music beds for AI video\nPrompt · Python code · loudness metrics",
        fill="#a78bfa",
        font=sub_font,
        spacing=6,
    )

    px, py = 520.0, 520.0
    first = True
    for x in np.linspace(520, 900, 400):
        t = (x - 520) / 380
        y = 520 + 20 * np.sin(2 * np.pi * 6 * t) * np.exp(-((t - 0.5) ** 2) * 8)
        if first:
            px, py = x, y
            first = False
        else:
            draw.line([(px, py), (x, y)], fill="#7c3aed", width=3)
            px, py = x, y

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
