#!/usr/bin/env python3
"""Build public/og-default.png (1200×630) for social sharing."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "og-default.png"

fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor="#09090b")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor("#09090b")
ax.axis("off")

# Decorative bar waveform (no matplotlib axis labels from spectrograms)
bar_x = np.array([0.12, 0.18, 0.24, 0.30, 0.36, 0.42, 0.48])
bar_h = np.array([0.22, 0.38, 0.55, 0.42, 0.62, 0.35, 0.28])
for x, h in zip(bar_x, bar_h):
    ax.add_patch(
        plt.Rectangle(
            (x, 0.5 - h / 2),
            0.04,
            h,
            facecolor="#7c3aed",
            alpha=0.85,
            linewidth=0,
        )
    )

ax.text(
    0.58,
    0.62,
    "Opus Sound\nDirectory",
    color="#fafafa",
    fontsize=42,
    fontweight="bold",
    va="top",
    ha="left",
    family="sans-serif",
)
ax.text(
    0.58,
    0.38,
    "Synthesised beds & SFX\nPrompts · code · spectrograms",
    color="#a78bfa",
    fontsize=18,
    va="top",
    ha="left",
    family="sans-serif",
)

t = np.linspace(0, 1, 800)
wave = 0.03 * np.sin(2 * np.pi * 6 * t) * np.exp(-((t - 0.5) ** 2) * 8)
ax.plot(0.58 + t * 0.32, 0.18 + wave, color="#7c3aed", linewidth=2, alpha=0.8)

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, facecolor="#09090b", bbox_inches="tight", pad_inches=0, pil_kwargs={"optimize": True})
plt.close(fig)
print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
