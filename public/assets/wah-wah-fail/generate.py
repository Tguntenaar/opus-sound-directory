#!/usr/bin/env python3
"""Wah-wah fail, take 1: "three-step droop".

Creative brief
--------------
A 2.8-second comedic "wah-wah" fail for the plan-goes-wrong beat: 134,400 samples at 48 kHz stereo,
30 fps, first note on frame 0 (sample 0). Muted-brass feel: band-limited additive saw with a slight
pitch scoop into each note, a breathy noise onset, and a plunger-mute "wah" (a resonant band-pass
sweeping ~500 -> 1,400 -> 500 Hz on each note). Small dry room, no reverb wash. Mono-ish, low end
centred. Fades to true silence by ~2.6 s. Loudness about -14 LUFS, true peak <= -1 dBTP.

Take angle (three-step droop), an ORIGINAL contour (not the stock four falling semitones):
  E4 (frame 0, short)  ->  C#4 (frame 12, short)  ->  C4 (frame 26) held.
  The held C4 bends down about a minor third (to ~A3) over its last second, with a widening vibrato,
  while the plunger opens and closes twice on it ("waaah ... waaaoww").

Usage: python take-1.py OUT.wav
"""

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")
import sys
import wave

import numpy as np
from scipy import ndimage, signal

SR = 48000
N = 134400                      # 2.8 s exactly
SEED = 42
TARGET_LUFS = -14.0
rng = np.random.default_rng(SEED)

E4, CS4, C4 = 329.628, 277.183, 261.626
FRAME = SR / 30.0


# ----------------------------------------------------------------------------- helpers
def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def slow_noise(n, hz):
    """Unit-variance smooth random curve (for drift / wobble)."""
    w = rng.standard_normal(n + SR)
    y = signal.sosfilt(signal.butter(2, hz, fs=SR, output="sos"), w)[SR:]
    return y / (np.std(y) + 1e-12)


def brass(f_hz, openness, bright_hz, *, fcut=9000.0, q=4.0, floor=0.12, floor_lp=420.0,
          formants=()):
    """Band-limited additive saw shaped per harmonic by a plunger-mute model.

    The mute is a resonant band-pass whose centre follows `openness` (0 -> 500 Hz, 1 -> 1,400 Hz)
    plus a low-passed leak that is small and muffled when closed and broader when open. Applying the filter magnitude to each harmonic keeps everything
    vectorised and alias-free (harmonics fade out smoothly above `fcut`).
    """
    phase = 2.0 * np.pi * np.cumsum(f_hz) / SR
    fc = 500.0 * (1400.0 / 500.0) ** openness
    out = np.zeros(len(f_hz))
    kmax = int(fcut * 1.4 / f_hz.min()) + 1
    for k in range(1, kmax + 1):
        fk = k * f_hz
        aa = 0.5 * (1.0 - np.tanh((fk - fcut) / (0.08 * fcut)))
        tilt = 1.0 / (1.0 + (fk / bright_hz) ** 2)
        bp = 1.0 / np.sqrt(1.0 + (q * (fk / fc - fc / fk)) ** 2)
        # leak through the plunger: small and muffled when closed, broad and louder when open
        leak_lp = floor_lp * (1.0 + 3.0 * openness)
        g = (floor + 0.55 * openness) / np.sqrt(1.0 + (fk / leak_lp) ** 4) + bp
        for ff, fq, fgain in formants:
            g = g + fgain / np.sqrt(1.0 + (fq * (fk / ff - ff / fk)) ** 2)
        # near-coherent phases keep the buzzy brass edge
        out += (aa * tilt * g / k) * np.sin(k * phase + rng.uniform(-0.35, 0.35))
    return out


def note_env(n, att_s, hold_s, rel_s, bump=0.15, bump_tau=0.06):
    t = np.arange(n) / SR
    e = np.ones(n)
    a = t < att_s
    e[a] = 0.5 - 0.5 * np.cos(np.pi * t[a] / att_s)
    e *= 1.0 + bump * np.exp(-t / bump_tau)
    e *= 0.5 + 0.5 * np.cos(np.pi * np.clip((t - hold_s) / rel_s, 0.0, 1.0))
    return e


def breath(n, onset_lvl, sustain, env):
    t = np.arange(n) / SR
    nz = signal.sosfilt(signal.butter(2, [1100, 5000], btype="bandpass", fs=SR, output="sos"),
                        rng.standard_normal(n))
    nz /= np.std(nz) + 1e-12
    onset = (1.0 - np.exp(-t / 0.002)) * np.exp(-t / 0.035)
    return nz * (onset_lvl * onset + sustain * env)


def scoop(t, cents=-70.0, tau=0.028):
    return cents * np.exp(-t / tau)


def wah_bump(t, t0, t1, p=1.3):
    """One plunger opening: 0 (closed) -> 1 (open) -> 0 between t0 and t1."""
    u = np.clip((t - t0) / (t1 - t0), 0.0, 1.0)
    return np.sin(np.pi * u) ** p


def place(out, start_s, sig):
    s = int(round(start_s * SR))
    m = min(len(sig), len(out) - s)
    out[s:s + m] += sig[:m]


def render_note(f0, dur_s, cents, openness, amp, onset_lvl=0.35, breath_sus=0.02):
    n = len(amp)
    f = f0 * 2.0 ** (cents / 1200.0)
    bright = 900.0 + 2600.0 * np.clip(amp, 0, 1.3)          # louder = brighter, like real brass
    tone = brass(f, openness, bright)
    tone /= np.sqrt(np.mean(tone[: int(0.1 * SR)] ** 2)) + 1e-12
    level = amp * (0.45 + 0.55 * openness)                    # a closed plunger is also quieter
    return tone * level + breath(n, onset_lvl, breath_sus, amp)


# ----------------------------------------------------------------------------- score
dry = np.zeros(N)

# note 1: E4 on frame 0, short
d1 = 0.33
n1 = int((d1 + 0.04) * SR)
t = np.arange(n1) / SR
env = note_env(n1, 0.006, d1, 0.04)
cents = scoop(t) + 3.0 * slow_noise(n1, 3.0)
place(dry, 0.0, render_note(E4, d1, cents, wah_bump(t, 0.0, d1 + 0.02), env))

# note 2: C#4 on frame 12, short
d2 = 0.36
n2 = int((d2 + 0.04) * SR)
t = np.arange(n2) / SR
env = note_env(n2, 0.007, d2, 0.04)
cents = scoop(t) + 3.0 * slow_noise(n2, 3.0)
place(dry, 12 / 30, render_note(CS4, d2, cents, wah_bump(t, 0.0, d2 + 0.02), env))

# note 3: C4 on frame 26, held; plunger opens twice; bends down a minor third over its last second
t3 = 26 / 30
end3 = 2.56
n3 = int((end3 - t3) * SR)
t = np.arange(n3) / SR
ta = t + t3                                               # absolute time
env = note_env(n3, 0.008, 10.0, 0.1)
env *= 1.0 - 0.15 * smoothstep((ta - 1.2) / 0.4)          # settle after the first wah
env *= np.cos(0.5 * np.pi * smoothstep((ta - 1.85) / (end3 - 1.85))) ** 1.5   # fade to silence
bend = -300.0 * smoothstep((ta - 1.50) / 0.95)             # C4 -> ~A3 across the last second
vib_depth = 30.0 * smoothstep((ta - 1.25) / 1.15)          # widening vibrato
vib_rate = 5.0 + 0.6 * smoothstep((ta - 1.25) / 1.2)
vib = vib_depth * np.sin(2 * np.pi * np.cumsum(vib_rate) / SR)
cents = scoop(t, -80.0, 0.035) + bend + vib + 3.0 * slow_noise(n3, 2.5)
openness = np.maximum(wah_bump(ta, t3 - 0.02, 1.58, 1.2), wah_bump(ta, 1.56, 2.52, 1.1))
place(dry, t3, render_note(C4, end3 - t3, cents, openness, env, onset_lvl=0.4))


# ----------------------------------------------------------------------------- room + master
def room(x):
    """Small, dry room: a few early reflections plus a ~0.2 s diffuse tail, decorrelated L/R."""
    L = int(0.16 * SR)
    tt = np.arange(L) / SR
    lp = signal.butter(2, 4500, fs=SR, output="sos")
    wet = []
    for ch in range(2):
        ir = np.zeros(L)
        for ms, g in zip(rng.uniform(2.5, 18.0, 7), rng.uniform(0.04, 0.14, 7)):
            ir[int(ms * SR / 1000)] += g * rng.choice([-1, 1])
        tail = signal.sosfilt(lp, rng.standard_normal(L)) * np.exp(-tt / 0.03) * (tt > 0.008)
        ir += 0.5 * tail / (np.abs(tail).max() + 1e-12) * 0.25
        wet.append(signal.fftconvolve(x, ir)[: len(x)])
    wet = np.stack(wet, axis=1) * 0.22
    out = x[:, None] + wet
    m, s = out.mean(axis=1), 0.5 * (out[:, 0] - out[:, 1])
    s = 0.6 * signal.sosfilt(signal.butter(2, 400, btype="highpass", fs=SR, output="sos"), s)
    return np.stack([m + s, m - s], axis=1)


def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x):
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    idx = np.arange(0, len(y) - blk + 1, hop)
    c = np.concatenate([np.zeros((1, 2)), np.cumsum(y ** 2, axis=0)])
    z = ((c[idx + blk] - c[idx]) / blk).sum(axis=1)
    z1 = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return -0.691 + 10 * np.log10(z2.mean())


def true_peak_db(x):
    return 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)


def tp_limit(x, ceil_db):
    """Look-ahead true-peak limiter, fully vectorised (min-filter + smoothing window)."""
    c = 10 ** (ceil_db / 20)
    pk = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)[: 4 * len(x)]
    pk = pk.reshape(len(x), 4).max(axis=1)
    g = np.minimum(1.0, c / np.maximum(pk, 1e-12))
    h = 96
    g = ndimage.minimum_filter1d(g, 2 * h + 1)
    w = np.hanning(2 * h + 1)
    g = np.convolve(g, w / w.sum(), mode="same")
    return x * g[:, None]


def master(x):
    x = room(x)
    x = signal.sosfilt(signal.butter(2, 25, btype="highpass", fs=SR, output="sos"), x, axis=0)
    for _ in range(6):
        x *= 10 ** ((TARGET_LUFS - lufs(x)) / 20)
        x = tp_limit(x, -1.3)
    tt = np.arange(N) / SR
    x *= (0.5 + 0.5 * np.cos(np.pi * np.clip((tt - 2.58) / 0.06, 0, 1)))[:, None]   # true silence
    tp = true_peak_db(x)
    if tp > -1.05:
        x *= 10 ** ((-1.05 - tp) / 20)
    assert np.all(np.isfinite(x))
    return x


def write_wav(path, x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT
    y = master(dry)
    assert y.shape == (N, 2)
    write_wav(out_path, y)
    print(f"{out_path}: {lufs(y):.2f} LUFS, {true_peak_db(y):.2f} dBTP")
