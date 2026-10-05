"""Generated sound code for ambient-bed-lofi (mock stub). Seed=42."""
import numpy as np
from runner.lib.audio_lib import SAMPLE_RATE, master_chain, stereo

# Prompt (truncated in stub):
# Make a 12 s ambient bed sound effect for video at 30 fps. Output: one WAV, 48 kHz / 16-bit / stereo, exactly 576000 samples. Python + numpy/scipy only. Synthesise everything (no samples, no downloads)...

def generate(seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    duration_sec = ...  # see entry timing
    # Full synthesis would be implemented here per prompt.
    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    mono = 0.2 * np.sin(2 * np.pi * 440 * t)
    return stereo(master_chain(mono))
