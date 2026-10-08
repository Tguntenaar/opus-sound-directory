"""Arcade game over, take 2: two-channel chip jingle.

Creative brief
--------------
A 1.8-second arcade "game over" (86,400 samples at 48 kHz, stereo, 16-bit), cue frame 0 at 30 fps,
in the style of an early-1980s arcade sound chip with an ORIGINAL contour (not any existing game's
death or game-over melody). Band-limited oscillators (additive, every partial faded out before
19 kHz, so nothing can fold back), volume steps on a 60 Hz frame clock (16 levels, 2 dB per level,
each step smoothed over 1 ms), console-style first-order high-pass at 90 Hz and low-pass at 12 kHz.
No reverb. Silent by the end.

Take angle: an original short descending minor-mode phrase on a 50 % pulse lead -- G5, Eb5, C5, a
leaning B4 (the harmonic-minor leading tone), then a held G4 with delayed vibrato -- a 12.5 % pulse
harmony a sixth below every lead note (Bb4, G4, Eb4, D4, Bb3), a triangle bass (C3, G2, C2) and a
final noise-channel 'thud'. Everything (note on/off, volume, and even the vibrato pitch) is
quantised to 1/60 s driver frames, so the vibrato is the stepped kind a frame-rate sound driver
makes. Slightly sad, clearly "you lost". Lead sits a touch left, harmony a touch right, bass and
noise centred.

usage: python take-2.py OUT.wav
"""

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")
import sys
import wave

import numpy as np
from scipy import signal

SEED = 43
SR = 48000
N = 86400
FRAME = SR // 60                      # 800 samples per 60 Hz driver frame
NFR = N // FRAME                      # 108 frames
F_CUT, F_KNEE = 19000.0, 15000.0      # partials fade out between these: band-limited, no aliasing

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- band-limited oscillators
def _phase(f):
    return 2 * np.pi * np.cumsum(f) / SR


def bl_pulse(f, duty):
    """Additive pulse wave (Fourier series), each partial weighted to zero before F_CUT."""
    ph = _phase(f)
    out = np.zeros(N)
    kmax = int(F_CUT / max(f.min(), 20.0)) + 1
    for k in range(1, kmax + 1):
        a = 2.0 / (k * np.pi) * np.sin(np.pi * k * duty)
        if abs(a) < 1e-9:
            continue
        w = np.clip((F_CUT - k * f) / (F_CUT - F_KNEE), 0.0, 1.0)
        if not w.any():
            break
        out += a * w * np.cos(k * ph)
    return out


def bl_triangle(f):
    ph = _phase(f)
    out = np.zeros(N)
    kmax = int(F_CUT / max(f.min(), 20.0)) + 1
    for k in range(1, kmax + 1, 2):
        w = np.clip((F_CUT - k * f) / (F_CUT - F_KNEE), 0.0, 1.0)
        if not w.any():
            break
        out += (8 / np.pi ** 2) * ((-1) ** ((k - 1) // 2)) / k ** 2 * w * np.sin(k * ph)
    return out


def noise_channel(periods):
    """Chip noise: random bits held for an integer number of samples (period register, per frame).
    Every edge lies on the sample grid, so the held steps cannot alias."""
    out = np.zeros(N)
    for fr, n in enumerate(periods):
        if n <= 0:
            continue
        k = -(-FRAME // n)
        bits = rng.integers(0, 2, k) * 2.0 - 1.0
        out[fr * FRAME:(fr + 1) * FRAME] = np.repeat(bits, n)[:FRAME]
    return out


# ---------------------------------------------------------------- 60 Hz volume register
def _ma(x, n):
    """causal n-sample moving average with zero history (env[0] == 0)."""
    c = np.concatenate([[0.0], np.cumsum(np.concatenate([np.zeros(n), x]))])
    return (c[n:n + len(x)] - c[:len(x)]) / n


def level_env(levels):
    """levels: int array (0..15) per frame -> per-sample amplitude, 2 dB/step, 1 ms smoothed steps."""
    lv = np.asarray(levels)
    amp = np.where(lv > 0, 10 ** (-2.0 * (15 - lv) / 20), 0.0)
    return _ma(np.repeat(amp, FRAME)[:N], 48)


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def frames_to_samples(fhz):
    """per-frame frequency (Hz) -> per-sample frequency, held for the whole frame (phase continuous)."""
    return np.repeat(np.asarray(fhz, dtype=float), FRAME)[:N]


# ---------------------------------------------------------------- score (all in frames)
G5, Eb5, C5, B4, G4 = 79, 75, 72, 71, 67
# (lead midi, harmony midi a sixth below, start frame, length in frames)
phrase = [(G5, 70, 0, 6), (Eb5, 67, 6, 6), (C5, 63, 12, 6), (B4, 62, 18, 15), (G4, 58, 36, 50)]
bass = [(48, 0, 12), (43, 12, 23), (36, 36, 46)]          # C3, G2, C2

lead_hz = np.full(NFR, midi_hz(G4))
harm_hz = np.full(NFR, midi_hz(58))
bass_hz = np.full(NFR, midi_hz(36))
lead_lv = np.zeros(NFR, dtype=int)
harm_lv = np.zeros(NFR, dtype=int)
bass_lv = np.zeros(NFR, dtype=int)

for i, (m, h, s, n) in enumerate(phrase):
    gate = n - 1                                          # one key-off frame for chip articulation
    lead_hz[s:s + n] = midi_hz(m)
    harm_hz[s:s + n] = midi_hz(h)
    if i < len(phrase) - 1:
        env = np.maximum(np.array([14, 13] + [12] * (gate - 2)) - np.arange(gate) // 5, 8)
    else:                                                 # held G4: sustain then stepped fade
        sus = 26
        env = np.concatenate([[14, 13, 12], np.full(sus, 11), np.repeat(np.arange(10, 0, -1), 2)])[:gate]
        k = np.arange(n)
        cents = np.where(k >= 12, 32 * np.minimum((k - 12) / 10, 1) * np.sin(2 * np.pi * 6 * (k - 12) / 60), 0.0)
        cents -= np.clip(k - 38, 0, None) * 4.0           # tiny sag as it dies
        lead_hz[s:s + n] = midi_hz(m) * 2 ** (cents / 1200)
        harm_hz[s:s + n] = midi_hz(h) * 2 ** (cents / 1200)
    lead_lv[s:s + gate] = env
    harm_lv[s:s + gate] = np.maximum(env - 2, 0)

for m, s, n in bass:
    gate = n - 1
    bass_hz[s:s + n] = midi_hz(m)
    env = np.full(gate, 13)
    if m == 36:
        env = np.concatenate([np.full(gate - 18, 13), np.repeat(np.arange(12, 3, -1), 2)])
    bass_lv[s:s + gate] = env

# noise 'thud': long period (dull, low-clock noise) getting longer each frame, fast stepped decay
noise_period = np.zeros(NFR, dtype=int)
noise_lv = np.zeros(NFR, dtype=int)
th = 88
noise_period[th:th + 7] = [56, 72, 88, 104, 120, 140, 160]
noise_lv[th:th + 7] = [13, 12, 10, 8, 6, 3, 1]

lead = bl_pulse(frames_to_samples(lead_hz), 0.5) * level_env(lead_lv)
harm = bl_pulse(frames_to_samples(harm_hz), 0.125) * level_env(harm_lv)
tri = bl_triangle(frames_to_samples(bass_hz)) * level_env(bass_lv)
nz = noise_channel(noise_period) * level_env(noise_lv)

L = 0.50 * lead + 0.36 * harm + 0.62 * tri + 0.42 * nz
R = 0.40 * lead + 0.45 * harm + 0.62 * tri + 0.42 * nz
x = np.stack([L, R], axis=1)

# ---------------------------------------------------------------- console + mastering
for order, fc, kind in ((1, 90, "highpass"), (1, 12000, "lowpass"), (2, 25, "highpass")):
    b, a = signal.butter(order, fc, kind, fs=SR)
    x = signal.lfilter(b, a, x, axis=0)


def lufs(x):
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    z1 = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return -0.691 + 10 * np.log10(z2.mean())


def true_peak_db(x):
    return 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)


x *= 10 ** ((-14.0 - lufs(x)) / 20)
tp = true_peak_db(x)
if tp > -1.3:
    x *= 10 ** ((-1.3 - tp) / 20)
assert np.all(np.isfinite(x))
pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")

out = sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote {out}: {lufs(x):.2f} LUFS, {true_peak_db(x):.2f} dBTP")
