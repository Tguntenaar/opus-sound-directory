"""Shock boom (heavy-boom-meme), take 1: faithful.

Creative brief:
A 1.5-second heavy "shock" boom for reaction cuts and zoom-ins: exactly 72,000 samples at 48 kHz
stereo, 30 fps, and the hit lands on sample 0 (frame 0) with no pre-roll. Layers:
  (1) a mono sub thump, a sine falling from ~110 Hz to ~42 Hz in 120 ms, soft tanh drive and an
      84 Hz second harmonic so it still reads on phone speakers;
  (2) a dull metallic body of six inharmonic modes (~95 Hz x 1, 1.59, 2.14, 2.65, 3.17, 3.89)
      decaying in 0.3-0.6 s;
  (3) a 4 ms noise click on the attack;
  (4) a wide, dark hall tail (~1.1 s, low-passed at 3 kHz) that gives the "boom... oom" echo.
Loudest in the first 80 ms; true silence by 1.45 s. Only the sub sits below 120 Hz, mono.
Original sound, not modelled on any specific recording.

Take angle 1 (faithful): implement the brief exactly as written; polish the balance between sub,
metal body and hall. The body's 95 Hz fundamental mode is kept mono and quiet so that the sub owns
everything under 120 Hz; the hall and the side channel are high-passed at 120 Hz.

usage: python take-1.py OUT.wav
"""

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")
import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d

SR = 48000
N = 72000
SEED = 42
TARGET_LUFS = -14.0
rng = np.random.default_rng(SEED)
t = np.arange(N) / SR


# ---------------------------------------------------------------- helpers
def sos_filt(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def lufs(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    z1 = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return -0.691 + 10 * np.log10(z2.mean())


def true_peak_per_sample(x):
    up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    return up[: len(x) * 4].reshape(len(x), 4).max(axis=1)


def limit(x, ceiling_db=-1.4, look=480):
    """Vectorised look-ahead peak limiter on the 4x-oversampled peak."""
    ceil = 10 ** (ceiling_db / 20)
    g = np.minimum(1.0, ceil / (true_peak_per_sample(x) + 1e-12))
    g = minimum_filter1d(g, 2 * look + 1)
    k = np.ones(look + 1) / (look + 1)
    g = np.convolve(np.pad(g, look, mode="edge"), k, mode="same")[look:-look]
    return x * g[:, None]


def master(x, fade_start, fade_end):
    env = np.ones(N)
    a, b = int(fade_start * SR), int(fade_end * SR)
    env[a:b] = 0.5 * (1 + np.cos(np.pi * np.arange(b - a) / (b - a)))
    env[b:] = 0.0
    for _ in range(4):
        x = x * 10 ** ((TARGET_LUFS - lufs(x)) / 20)
        x = limit(x)
        x = x * env[:, None]
    tp = true_peak_per_sample(x).max()
    if tp > 10 ** (-1.2 / 20):
        x *= 10 ** (-1.2 / 20) / tp
    return x


def write_wav(path, x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- (1) sub thump
f_sub = 42.0 + (110.0 - 42.0) * np.exp(-t / 0.034)          # ~110 -> ~42 Hz within 120 ms
ph = 2 * np.pi * np.cumsum(f_sub) / SR
ph -= ph[0]                                                   # start exactly at phase 0
sub_env = (0.72 * np.exp(-t / 0.085) + 0.28 * np.exp(-t / 0.33)) * (1 - np.exp(-t / 0.0006))
drive = 1.8
sub = np.tanh(drive * np.sin(ph)) / np.tanh(drive)
sub = 0.80 * sub + 0.32 * np.sin(2 * ph) * np.exp(-t / 0.22)   # 2nd harmonic -> 84 Hz once settled
sub *= sub_env

# ---------------------------------------------------------------- (2) dull metallic body
f0 = 95.0
ratios = np.array([1.0, 1.59, 2.14, 2.65, 3.17, 3.89])
decays = np.array([0.60, 0.55, 0.48, 0.42, 0.36, 0.30])        # time to -40 dB, seconds
amps = np.array([0.18, 0.55, 0.50, 0.38, 0.30, 0.22])          # fundamental kept low (sub owns <120 Hz)
body = np.zeros(N)
for r, d, a in zip(ratios, decays, amps):
    f = f0 * r * (1 + 0.012 * np.exp(-t / 0.05))               # tiny strike-pitch sag
    phm = 2 * np.pi * np.cumsum(f) / SR
    body += a * np.sin(phm - phm[0]) * np.exp(-4.6 * t / d)
body *= 1 - np.exp(-t / 0.0015)
body = sos_filt(body, "lowpass", 1800, 2)                      # dull, not ringing
body = 0.9 * body

# ---------------------------------------------------------------- (3) 4 ms noise click
nc = int(0.004 * SR)
cw = np.zeros(N)
u = np.arange(nc) / nc
cw[:nc] = np.sin(np.pi * np.minimum(u / 0.08, 1) / 2) ** 2 * (1 - u) ** 2
click = rng.standard_normal(N) * cw
click = sos_filt(click, "bandpass", [900, 7000], 2) * 0.9

# ---------------------------------------------------------------- (4) wide dark hall
def hall_ir(seed_rng, rt60=1.1, length=1.2):
    n = int(length * SR)
    ti = np.arange(n) / SR
    ir = seed_rng.standard_normal(n) * np.exp(-6.91 * ti / rt60)
    ir *= 1 - np.exp(-ti / 0.035)                              # diffuse build-up -> "oom" bloom
    for d, g in [(0.019, 0.5), (0.031, 0.42), (0.047, 0.35), (0.071, 0.3), (0.13, 0.22)]:
        k = int(d * SR * (1 + 0.04 * seed_rng.standard_normal()))
        ir[k] += g * 6
    # late reflection cluster around 0.24 s: the "... oom" answer of the hall
    late = np.exp(-0.5 * ((ti - 0.24) / 0.04) ** 2)
    ir += 0.7 * seed_rng.standard_normal(n) * late * np.exp(-6.91 * 0.24 / rt60)
    ir = sos_filt(ir, "lowpass", 3000, 4)
    ir = sos_filt(ir, "highpass", 120, 2)
    return ir / np.sqrt(np.sum(ir ** 2))

hall_in = body + 0.2 * click + 0.8 * sos_filt(sos_filt(sub, "highpass", 120, 4), "lowpass", 700, 2)
dry = sub + body + click
# A random hall reacting to a few tonal modes can lean hard to one side; draw a handful of (seeded)
# IR candidates and keep the most balanced, most decorrelated one.
wins = [(int(a * SR), int(b * SR)) for a, b in [(0.0, 0.08), (0.08, 0.2), (0.2, 0.35), (0.35, 0.6), (0.6, 1.0)]]
cands = [hall_ir(rng) for _ in range(16)]
wets = [signal.fftconvolve(hall_in, ir)[:N] for ir in cands]
best, score = None, np.inf
for i in range(0, 16, 2):
    for j in range(1, 16, 2):
        h = 0.6 * np.stack([wets[i], wets[j]], axis=1)
        y = dry[:, None] + h
        imb = max(abs(10 * np.log10(np.mean(y[a:b, 0] ** 2) / np.mean(y[a:b, 1] ** 2))) for a, b in wins)
        if imb < score:
            best, score = h, imb
hall = best

# ---------------------------------------------------------------- mix
x = dry[:, None] + hall
mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
side = sos_filt(side, "highpass", 120, 8)                      # mono below 120 Hz
x = np.stack([mid + side, mid - side], axis=1)
x = sos_filt(x, "highpass", 25, 2)                             # DC removal
x = master(x, 1.25, 1.44)
assert np.all(np.isfinite(x))

if __name__ == "__main__":
    write_wav(sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT, x)
