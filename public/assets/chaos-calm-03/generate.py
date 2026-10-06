"""chaos-calm-03: Opus Sound Directory

A 10-second notification storm that dissolves into one long breath in D. Frame 0
fires an alert stack: five different notifications at once over a tense pulse.
For four seconds, UI sounds pile up faster and faster at 100 BPM. There are
two-tone FM chimes, quick tri-tone alerts, bubble "message" pops, rattling phone
vibrations and rapid keyboard ticks, all in clashing keys and scattered across
the stereo field, over a low throb that speeds from eighths to sixteenths. At
frame 120 (4.0 s) every notification mutes within 3 ms. What follows is a single
slow swell, like a long inhale and exhale: shaped noise through resonators tuned
to D (D, A, D, F#, A, plus a soft mono D sine). A broad filter opens as the
breath fills, peaks near 7 s, then closes and sighs to silence by 10 s.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 120903
DURATION_SEC = 10
BPM = 100
KEY = "chaos -> D"
FPS = 30
CUE_FRAMES = (0, 120)          # frame 0: alert stack, frame 120: notifications mute, breath begins
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.6 s
CALM_T = CUE_FRAMES[1] / FPS   # 4.0 s
CALM_S = int(round(CALM_T * SR))

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Short raised-cosine attack/release so nothing starts or stops with a click."""
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na)))[(...,) + (None,) * (x.ndim - 1)]
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr)))[(...,) + (None,) * (x.ndim - 1)]
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a mono (L,) or stereo (L,2) snippet into a stereo bus at time t (equal-power pan)."""
    s = int(round(t * SR))
    if s >= len(bus):
        return
    if x.ndim == 1:
        th = (pan + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)
    e = min(len(bus), s + len(x))
    bus[s:e] += gain * x[: e - s]


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


def svf_bandpass(x: np.ndarray, fc: np.ndarray, q: float) -> np.ndarray:
    """Zavalishin TPT state-variable band-pass with per-sample cutoff (for sweeps)."""
    g = np.tan(np.pi * np.clip(fc, 20, 0.45 * SR) / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    y = np.empty(len(x))
    ic1 = ic2 = 0.0
    for n, (xn, b1, b2, b3) in enumerate(zip(x.tolist(), a1.tolist(), a2.tolist(), a3.tolist())):
        v3 = xn - ic2
        v1 = b1 * ic1 + b2 * v3
        v2 = ic2 + b2 * ic1 + b3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[n] = v1
    return y


def reverb(x: np.ndarray, rt60: float = 1.4, predelay: float = 0.018, band=(250, 7500)) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", list(band)) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


# ---------------------------------------------------------------- storm voices
def chime_note(f: float, dur: float) -> np.ndarray:
    """Glassy notification chime: near-harmonic additive partials (1, 2, 3.01, 4.2),
    upper ones dying faster. All partials < 15 kHz."""
    t = tt(dur)
    y = np.zeros_like(t)
    for ratio, amp, dec in ((1.0, 1.0, 0.22), (2.0, 0.35, 0.12), (3.01, 0.18, 0.07), (4.2, 0.08, 0.04)):
        if ratio * f < 15000:
            y += amp * np.exp(-t / dec) * np.sin(2 * np.pi * ratio * f * t + rng.uniform(0, 2 * np.pi))
    return fade(y, a=0.0012, r=0.02)


def two_tone(m1: float, m2: float) -> np.ndarray:
    """'Ding-dong': two chime notes 110 ms apart."""
    a = chime_note(hz(m1), 0.45)
    b = chime_note(hz(m2), 0.55)
    y = np.zeros(int(0.11 * SR) + len(b))
    y[: len(a)] += a
    y[int(0.11 * SR):] += b
    return y * 0.35


def tri_alert(base: float, intervals=(0, 4, 7)) -> np.ndarray:
    """Three quick rising triangle-ish beeps (odd partials 1/k^2 up to 12 kHz)."""
    gap = 0.075
    y = np.zeros(int((gap * 2 + 0.09) * SR))
    for i, iv in enumerate(intervals):
        f = hz(base + iv)
        t = tt(0.07)
        v = np.zeros_like(t)
        for k in range(1, int(12000 // f) + 1, 2):
            v += ((-1) ** ((k - 1) // 2)) * np.sin(2 * np.pi * k * f * t) / k ** 2
        v = fade(v * np.exp(-t / 0.05), a=0.0015, r=0.01)
        s = int(i * gap * SR)
        y[s:s + len(v)] += v
    return y * 0.3


def bubble_pop() -> np.ndarray:
    """Message pop: sine sweeping 300 -> 1300 Hz in ~35 ms under a sine-bump envelope."""
    t = tt(0.07)
    f = 300 * (1300 / 300) ** np.minimum(t / 0.035, 1.0)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.minimum(t / 0.07, 1.0)) ** 1.5
    return fade(y * 0.45, a=0.001, r=0.005)


def vibrate(pulses: int = 2) -> np.ndarray:
    """Phone buzzing on a table: 165 Hz rough additive buzz (partials to 4 kHz) with a
    28 Hz rattle, in 0.32 s pulses."""
    pd, gap = 0.32, 0.12
    y = np.zeros(int((pd + gap) * pulses * SR))
    f = 165.0 * rng.uniform(0.97, 1.03)
    for p in range(pulses):
        t = tt(pd)
        v = np.zeros_like(t)
        for k in range(1, int(4000 // f) + 1):
            v += np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi)) / k ** 1.3
        v *= 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 14 * t))
        v = fade(v, a=0.01, r=0.02)
        s = int(p * (pd + gap) * SR)
        y[s:s + len(v)] += v
    return y * 0.16


def swoosh(dur: float = 0.16) -> np.ndarray:
    """'Sent' swoosh: noise through an SVF band-pass sweeping 900 Hz -> 7 kHz."""
    t = tt(dur)
    fc = 900 * (7000 / 900) ** (t / dur)
    y = svf_bandpass(noise(dur), fc, 2.0) * np.sin(np.pi * t / dur) ** 2
    y = sos_filter(y, "lowpass", 11000, order=4)
    return fade(y * 0.5, a=0.002, r=0.005)


def throb(dur: float = 0.26) -> np.ndarray:
    """Tense low pulse: pitch-dropping sine thump (mono, for the low bus)."""
    t = tt(dur)
    f = 52 + 60 * np.exp(-t / 0.03)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)
    return fade(y * 0.7, a=0.0015, r=0.02)


# ---------------------------------------------------------------- breath voice
def breath_env(dur: float, peak: float = 3.0) -> np.ndarray:
    """One breath: a small catch at the start, raised-cosine inhale to `peak`, then a
    longer raised-cosine exhale that reaches exactly 0 at the end."""
    t = tt(dur)
    rise = 0.5 - 0.5 * np.cos(np.pi * np.clip(t / peak, 0, 1))
    fall = 0.5 + 0.5 * np.cos(np.pi * np.clip((t - peak) / (dur - peak), 0, 1))
    env = np.where(t < peak, rise, fall)
    catch = 0.2 * np.exp(-t / 1.2) * (1 - np.exp(-t / 0.006))
    return np.maximum(env, catch)


def breath_swell(dur: float, peak: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
    """Returns (stereo breath, mono low D). Pinkish noise through resonators on the D
    harmonic series, an SVF 'mouth' filter that opens and closes with the breath, a thin
    air band, and a soft D sine underneath."""
    t = tt(dur)
    env = breath_env(dur, peak)
    flutter = 1 + 0.035 * np.sin(2 * np.pi * 4.3 * t) * env
    openness = np.where(t < peak, env, env ** 0.7)                 # filter lags behind on the exhale
    fc = 380 + 2400 * openness
    out = np.zeros((len(t), 2))
    tones = ((146.83, 0.9), (220.0, 0.8), (293.66, 1.0), (369.99, 0.55), (440.0, 0.6),
             (587.33, 0.4), (880.0, 0.22))
    for ch in range(2):
        src = sos_filter(noise(dur), "lowpass", 2500, order=1)    # gently pink-tilted
        res = np.zeros_like(t)
        for f, a in tones:
            res += a * sos_filter(src, "bandpass", [f * 0.988, f * 1.012], order=2) * np.sqrt(f / 293.66) * 4.5
        mouth = sos_filter(svf_bandpass(noise(dur), fc, 1.4), "lowpass", 5500, order=4) * 0.3
        air = sos_filter(noise(dur), "bandpass", [4000, 9000], order=4) * 0.025 * env ** 0.8
        out[:, ch] = (res * env ** 1.3 + mouth * env + air) * flutter
    d2 = np.sin(2 * np.pi * 73.42 * t) + 0.25 * np.sin(2 * np.pi * 146.83 * t)
    low = fade(d2 * env ** 1.5 * 0.12, a=0.01, r=0.05)
    return out, low


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
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    os = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os)) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 90.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. Never clips."""
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
    g = uniform_filter1d(g, size=L + 1, mode="nearest")
    return x * g[:, None]


def master(mix: np.ndarray) -> np.ndarray:
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y




# ---------------------------------------------------------------- arrangement
def render_storm() -> tuple[np.ndarray, np.ndarray]:
    """Returns (storm bus, storm low bus); both are silenced from CALM_T on."""
    bus = np.zeros((N, 2))
    low = np.zeros((N, 2))
    send = np.zeros((N, 2))
    end = CALM_T

    def fire(kind: str, t: float, g: float, pan: float) -> None:
        if kind == "two":
            m1 = float(rng.choice([88, 85, 91, 82, 87, 80]))
            x = two_tone(m1, m1 - float(rng.choice([4, 5, 6])))
        elif kind == "tri":
            x = tri_alert(float(rng.choice([73, 75, 78, 80, 82])),
                          ((0, 4, 7), (0, 3, 6), (0, 5, 11))[rng.integers(3)])
        elif kind == "pop":
            x = bubble_pop()
        elif kind == "vib":
            x = vibrate(int(rng.choice([1, 2])))
        else:
            x = swoosh(float(rng.uniform(0.12, 0.2)))
        place(bus, x, t, g, pan=pan)
        place(send, x, t, g * 0.35, pan=pan)

    # frame 0: the alert stack, five notifications at once
    for kind, pan in (("two", -0.6), ("tri", 0.5), ("pop", 0.0), ("vib", -0.2), ("two", 0.75)):
        fire(kind, 0.0, 0.9, pan)

    # the storm: Poisson arrivals that accelerate from ~3/s to ~24/s
    kinds = ("two", "tri", "pop", "vib", "swoosh")
    weights = np.array([0.28, 0.24, 0.24, 0.1, 0.14])
    t = 0.22
    while t < end - 0.04:
        x = t / end
        dens = 7.0 + 23.0 * x ** 1.4
        kind = kinds[rng.choice(len(kinds), p=weights)]
        fire(kind, t, (0.6 + 0.4 * x) * rng.uniform(0.75, 1.0), rng.uniform(-0.9, 0.9))
        t += rng.exponential(1.0 / dens)

    # tense pulse: eighths, then sixteenths for the last bar-and-a-bit
    t, i = 0.0, 0
    while t < end - 0.02:
        place(low, throb(), t, 0.75 if i % 2 == 0 else 0.55)
        t += BEAT / 2 if t < 2.4 else BEAT / 4
        i += 1

    bus = bus + reverb(send, rt60=0.8, predelay=0.012) * 0.6
    bus = sos_filter(bus, "highpass", 140, order=4)
    low = np.repeat(sos_filter(low.mean(axis=1, keepdims=True), "lowpass", 1500), 2, axis=1)

    # the mute: 3 ms raised-cosine fade reaching zero exactly on the cue sample
    nf = int(0.003 * SR)
    gate = np.ones(N)
    gate[CALM_S - nf:CALM_S] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf))
    gate[CALM_S:] = 0.0
    return bus * gate[:, None], low * gate[:, None]


def render_breath() -> tuple[np.ndarray, np.ndarray]:
    music = np.zeros((N, 2))
    low = np.zeros((N, 2))
    dur = DURATION_SEC - CALM_T - 0.05
    br, d = breath_swell(dur, peak=3.0)
    place(music, br, CALM_T, 1.0)
    place(low, d, CALM_T, 1.0)
    wet = reverb(music, rt60=2.2, predelay=0.04, band=(200, 6000))
    music = sos_filter(music + wet * 0.35, "highpass", 150, order=6)
    low = np.repeat(sos_filter(low.mean(axis=1, keepdims=True), "lowpass", 300), 2, axis=1)
    return music, low


def render() -> np.ndarray:
    storm, storm_low = render_storm()
    music, calm_low = render_breath()
    calm = music + calm_low
    calm[:CALM_S] = 0.0                                             # the breath starts on the cue sample
    mix = storm * 1.0 + storm_low * 0.7 + calm * 0.8
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 230, order=6)      # everything under ~200 Hz stays mono
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 17000, order=4)
    nf = int(0.3 * SR)                                              # guarantee exact silence at the end
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
