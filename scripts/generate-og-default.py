#!/usr/bin/env python3
"""Build public/og-default.png (1200×630) for social sharing."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "og-default.png"
SPEC = ROOT / "public" / "assets" / "ad-bed-15-upbeat" / "spectrogram.png"

fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor="#09090b")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor("#09090b")
ax.axis("off")

if SPEC.exists():
    spec = plt.imread(SPEC)
    ax.imshow(spec, aspect="auto", extent=[0.05, 0.62, 0.12, 0.88], alpha=0.85)

ax.text(
    0.66,
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
    0.66,
    0.38,
    "Synthesised beds & SFX\nPrompts · code · spectrograms",
    color="#a78bfa",
    fontsize=18,
    va="top",
    ha="left",
    family="sans-serif",
)

# subtle waveform decoration
t = np.linspace(0, 1, 800)
wave = 0.03 * np.sin(2 * np.pi * 6 * t) * np.exp(-((t - 0.5) ** 2) * 8)
ax.plot(0.66 + t * 0.3, 0.18 + wave, color="#7c3aed", linewidth=2, alpha=0.8)

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, facecolor="#09090b", bbox_inches="tight", pad_inches=0)
plt.close(fig)
print(f"Wrote {OUT}")
