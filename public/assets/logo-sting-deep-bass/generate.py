"""logo-sting-deep-bass: Opus Sound Directory

A 3.5-second double bass hit in E: a heavy downbeat and a softer answer, "DUM-dum".
The first hit lands on frame 0 and carries the weight: a deep sub boom whose pitch
falls from about 72 Hz to E1 (41 Hz), a soft felt-and-wood thud, and a gently
saturated low layer that puts the weight into the 80-250 Hz range, so it still feels
heavy on laptop and phone speakers. With it, a warm, wide E add9 chord (E2, B2, F#3,
G#3, B3) of filtered analog-style saws blooms open. Half a second later, on frame 15,
a lighter second hit answers a fifth higher, on B1, with its own short thud and no
new bloom. A faint glassy shimmer on E5 and B5 rises out of the chord, and both hits
ring down in a soft, dark room to silence at 3.5 s. Calm, confident and weighty,
never harsh.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 410350
DURATION_SEC = 3.5
BPM = None
KEY = "E"
FPS = 30
CUE_FRAMES = (0, 15)           # frame 0: heavy E hit, frame 15: lighter B answer
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(DURATION_SEC * SR)

rng = np.random.default_rng(SEED)
t_all = np.arange(N) / SR


def hz(note_from_a4: float) -> float:
    return 440.0 * 2 ** (note_from_a4 / 12)


E1 = hz(-41)                                            # 41.2 Hz
B1 = hz(-34)                                            # 61.7 Hz
ANSWER_T = CUE_FRAMES[1] / FPS                          # 0.5 s
CHORD = [hz(-29), hz(-22), hz(-15), hz(-13), hz(-10)]   # E2 B2 F#3 G#3 B3


# ---------------------------------------------------------------- utilities
def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def smoothstep(t: np.ndarray, a: float, b: float) -> np.ndarray:
    u = np.clip((t - a) / (b - a), 0.0, 1.0)
    return u * u * (3 - 2 * u)


def pan2(x: np.ndarray, pan) -> np.ndarray:
    th = (np.asarray(pan) + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)


def saw(freq: float, ph0: float) -> np.ndarray:
    """Band-limited additive saw (partials below 16 kHz)."""
    out = np.zeros(N)
    for k in range(1, int(16000 / freq) + 1):
        out += np.sin(k * (2 * np.pi * freq * t_all + ph0)) / k
    return out * 2 / np.pi


def tv_lowpass(x: np.ndarray, cutoff: np.ndarray) -> np.ndarray:
    """Time-varying 2-pole state-variable low-pass (TPT form)."""
    g = np.tan(np.pi * np.clip(cutoff, 20, 18000) / SR)
    k = 1.2                                  # gentle resonance
    a1 = 1 / (1 + g * (g + k))
    ic1 = ic2 = 0.0
    y = np.empty_like(x)
    for n in range(len(x)):
        v3 = x[n] - ic2
        v1 = a1[n] * ic1 + g[n] * a1[n] * v3
        v2 = ic2 + g[n] * v1
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[n] = v2
    return y


def reverb(x: np.ndarray, rt60: float = 1.8, predelay: float = 0.012) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR: a soft, dark room."""
    t = np.arange(int(rt60 * 1.15 * SR)) / SR
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [200, 5000]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


# ---------------------------------------------------------------- loudness / peak
def k_weight(x: np.ndarray) -> np.ndarray:
    """ITU-R BS.1770 K-weighting (48 kHz coefficients)."""
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def integrated_lufs(x: np.ndarray) -> float:
    """BS.1770-4 integrated loudness: 400 ms blocks, 75 % overlap, -70 LUFS abs + -10 LU rel gates."""
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    p = np.cumsum(np.concatenate([[0.0], (y ** 2).sum(axis=1)]))
    starts = np.arange(0, len(y) - blk + 1, hop)
    z = (p[starts + blk] - p[starts]) / blk
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    os = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os)) + 1e-20))


def limiter_gain(x: np.ndarray, ceiling_db: float, look_ms: float = 3.0, rel_ms: float = 150.0) -> np.ndarray:
    """Gain curve of a look-ahead limiter driven by the 4x-oversampled (true) peak.
    Held over the look-ahead window, one-pole release, edge-safe box smoothing."""
    ceil = 10 ** (ceiling_db / 20)
    os = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = os[: len(x) * 4].reshape(len(x), 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    L = int(look_ms * 1e-3 * SR)
    held = minimum_filter1d(need, size=2 * L + 1, mode="nearest")
    rc = np.exp(-1.0 / (rel_ms * 1e-3 * SR))
    g = np.empty_like(held)
    prev = 1.0
    for n, h in enumerate(held.tolist()):
        prev = min(h, prev * rc + (1 - rc))
        g[n] = prev
    return uniform_filter1d(g, size=L + 1, mode="nearest")


def master(mix: np.ndarray) -> np.ndarray:
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3
    for _ in range(12):
        z = mix * 10 ** (gain_db / 20)
        y = z * limiter_gain(z, ceiling)[:, None]
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    t = t_all

    # --- each hit: pitch-falling sub, saturated 80-250 Hz weight, felt thud, soft knock (mono)
    def hit(t0: float, f_end: float, f_start: float, decay: float, gain: float,
            choke: float = 99.0) -> tuple[np.ndarray, np.ndarray]:
        u = np.maximum(t - t0, 0.0)
        on = (t >= t0).astype(float)
        f = f_end + (f_start - f_end) * np.exp(-u / 0.09)
        env = on * np.minimum(1, u / 0.0015) * np.exp(-u / decay) * (1 - smoothstep(t, 2.6, 3.4))
        env *= 1 - smoothstep(t, choke - 0.07, choke - 0.003)      # re-struck drum: the old ring stops
        sub = np.cos(2 * np.pi * np.cumsum(f * on) / SR) * env      # starts at peak phase: instant weight
        heavy = np.tanh(2.8 * sub) - 0.55 * sub
        heavy = sos_filter(sos_filter(heavy, "highpass", 75, order=2), "lowpass", 260, order=4)
        thud_env = on * np.minimum(1, u / 0.0008) * np.exp(-u / 0.055)
        thud = sos_filter(rng.standard_normal(N), "bandpass", [70, 420], order=2) * thud_env
        knock = sos_filter(rng.standard_normal(N), "bandpass", [900, 2600], order=2) * on * np.minimum(1, u / 0.0005) * np.exp(-u / 0.008)
        return (sub * 0.85 + heavy * 1.1 + thud * 0.75) * gain, knock * gain

    low1, knock1 = hit(0.0, E1, 72.0, 0.45, 1.0, choke=ANSWER_T)               # heavy downbeat
    low2, knock2 = hit(ANSWER_T, B1, 96.0, 0.50, 0.50)          # lighter, shorter answer a fifth up
    low = low1 + low2
    knock = knock1 + knock2

    # --- E add9 chord: detuned saws through a blooming low-pass, wide
    bloom_cut = 260 + 1500 * (smoothstep(t, 0.0, 0.32) * np.exp(-np.maximum(t - 0.32, 0) / 0.7))
    chord_env = np.minimum(1, t / 0.006) * (0.35 + 0.65 * smoothstep(t, 0.0, 0.18)) * np.exp(-t / 1.1)
    chord_env *= 1 - 0.65 * (smoothstep(t, ANSWER_T - 0.08, ANSWER_T - 0.01) - smoothstep(t, ANSWER_T + 0.03, ANSWER_T + 0.3))
    chord = np.zeros((N, 2))
    pans = (-0.15, 0.2, -0.45, 0.45, 0.0)
    for j, f0 in enumerate(CHORD):
        for d, side in ((-0.06, -1), (0.06, 1)):
            v = saw(f0 * 2 ** (d / 12), rng.uniform(0, 2 * np.pi))
            chord += pan2(v, np.clip(pans[j] + 0.3 * side, -0.85, 0.85))
    chord = np.stack([tv_lowpass(chord[:, 0], bloom_cut), tv_lowpass(chord[:, 1], bloom_cut)], axis=1)
    chord = sos_filter(chord, "highpass", 130, order=4) * chord_env[:, None]

    # --- glassy shimmer on E5 / B5, rising out of the chord
    shim_env = smoothstep(t, 0.15, 0.7) * np.exp(-np.maximum(t - 0.7, 0) / 0.8)
    shim = np.zeros((N, 2))
    for f0, p in ((hz(7), -0.5), (hz(14), 0.5), (hz(19), 0.0)):
        shim += pan2(np.sin(2 * np.pi * f0 * t + rng.uniform(0, 6.28)) * (1 + 0.004 * np.sin(2 * np.pi * 5.1 * t)), p)
    shim *= shim_env[:, None]

    top = chord * 0.13 + shim * 0.035 + pan2(knock, 0.0) * 0.05
    top = top + reverb(top, rt60=1.8) * 0.35
    mix = top + low[:, None] * 0.9

    mix = sos_filter(mix, "highpass", 22, order=2)
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=10)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "lowpass", 15000, order=4)
    return mix * (1 - smoothstep(t, 3.1, 3.45))[:, None]


def main() -> None:
    mix = render()
    y = master(mix)
    y = y - y.mean(axis=0, keepdims=True)                 # constant per-channel DC trim
    y = y * (1 - smoothstep(t_all, 3.42, 3.49))[:, None]
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    pcm[0] = 0
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
