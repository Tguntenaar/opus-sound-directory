"""heartbeat-tension-12s: Opus Sound Directory

A 12-second tension builder with no pitch centre, all in the low body. A heartbeat
starts on frame 0 at 60 BPM: each beat is a "lub-dub" pair of mono sub thumps (a
pitch-dropping sine with a muffled knock; the "dub" is shorter and a little higher).
The heart speeds up smoothly to about 150 BPM, and its thumps grow harder and closer
together. Above it, a faint high tinnitus ring fades in and slowly beats between the
ears. Underneath, a breath-like noise swell grows from slow, deep breaths into fast,
shallow panting. On frame 330 (11.0 s), mid-beat, everything flatlines: the whole bus
cuts to dead silence through a 2 ms fade that ends on the cue. After a held silence,
one distant, soft, muffled thud sounds in a small dark room and dies away. Only the
mono heart thumps sit below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 1133011
DURATION_SEC = 12
BPM = 60
KEY = "atonal (low sub thumps)"
FPS = 30
CUE_FRAMES = (0, 330)          # frame 0: first beat; frame 330 (11.0 s): flatline cut
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
CUT_T = CUE_FRAMES[1] / FPS    # 11.0 s
CUT_S = int(round(CUT_T * SR)) # 528000
THUD_T = 11.42                 # the single distant thud after the flatline
THUD_S = int(round(THUD_T * SR))
BPM_END = 150.0
TEMPO_CURVE = 1.3              # rate(t) = 1 + 1.5 (t / T) ^ 1.3 beats/s -> last lub at 10.93 s

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Raised-cosine attack/release so nothing starts or stops with a click."""
    x = x.copy()
    sh = (-1,) + (1,) * (x.ndim - 1)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))).reshape(sh)
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))).reshape(sh)
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a mono (L,) or stereo (L,2) snippet into a stereo bus at time t (equal-power pan)."""
    s = int(round(t * SR))
    if x.ndim == 1:
        th = (pan + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)
    e = min(len(bus), s + len(x))
    bus[s:e] += gain * x[: e - s]


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def noise(n: int) -> np.ndarray:
    return rng.standard_normal(n)


def smooth_random(n: int, rate_hz: float) -> np.ndarray:
    y = sos_filter(noise(n + SR), "lowpass", rate_hz, order=2)[SR:]
    return y / (np.abs(y).max() + 1e-12)


def reverb(x: np.ndarray, rt60: float, predelay: float, band=(140, 1500)) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (small dark room)."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60) * (1 - np.exp(-t / 0.004))
    irs = []
    for _ in range(2):
        ir = sos_filter(noise(len(t)), "bandpass", list(band)) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


# ---------------------------------------------------------------- the heart
def thump(f_hi: float, f_lo: float, tau: float, knock_gain: float, dur: float = 0.32) -> np.ndarray:
    """One heart sound: sine dropping f_hi -> f_lo with soft saturation, plus a muffled knock."""
    t = tt(dur)
    f = f_lo + (f_hi - f_lo) * np.exp(-t / 0.022)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) + 0.28 * np.sin(2 * ph + 0.3)
    body *= np.exp(-t / tau) * (1 - np.exp(-t / 0.0012))
    body = np.tanh(1.6 * body) / np.tanh(1.6)
    kn = sos_filter(noise(len(t)), "bandpass", [70, 320], order=2)
    kn *= np.exp(-t / 0.018) * knock_gain / (np.abs(kn).max() + 1e-12)
    return fade(body + kn, a=0.001, r=0.06)


def beat_times() -> np.ndarray:
    t = np.arange(CUT_S) / SR
    rate = 1 + (BPM_END / 60 - 1) * (t / CUT_T) ** TEMPO_CURVE
    ph = np.cumsum(rate) / SR
    k = np.floor(ph)
    idx = np.nonzero(np.diff(k))[0] + 1
    return np.concatenate([[0.0], idx / SR])


def heart() -> np.ndarray:
    bus = np.zeros(N)
    for i, tb in enumerate(beat_times()):
        x = tb / CUT_T
        rate = 1 + (BPM_END / 60 - 1) * x ** TEMPO_CURVE
        lev = 0.3 + 0.7 * x ** 1.3
        gap = 0.30 - 0.075 * (rate - 1) / 1.5              # lub -> dub spacing shrinks a little
        lub = thump(98.0, 50.0, 0.075 - 0.02 * x, 0.35)
        dub = thump(124.0, 66.0, 0.050 - 0.015 * x, 0.30, dur=0.24)
        s = int(round(tb * SR))
        e = min(N, s + len(lub)); bus[s:e] += lev * lub[: e - s]
        s2 = int(round((tb + gap) * SR))
        e2 = min(N, s2 + len(dub)); bus[s2:e2] += 0.72 * lev * dub[: e2 - s2]
    return bus


# ---------------------------------------------------------------- tinnitus + breath
def tinnitus() -> np.ndarray:
    """Faint high ring: 7.35 kHz in the left ear, 7 Hz higher in the right (slow inter-ear beating)."""
    t = np.arange(N) / SR
    env = np.clip((t - 0.8) / 6.0, 0, 1) ** 1.5
    env = 0.25 * env + 0.75 * env * np.clip((t - 6.0) / 5.0, 0, 1)
    wob = 1 + 0.15 * smooth_random(N, 0.8)
    out = np.zeros((N, 2))
    for ch, f in enumerate((7350.0, 7357.0)):
        out[:, ch] = np.sin(2 * np.pi * f * t + ch * 1.3) * env * wob
    return out


def breath() -> np.ndarray:
    """Breath-like noise: in/out cycles that speed up and grow; inhale brighter, exhale lower."""
    t = np.arange(N) / SR
    x = np.clip(t / CUT_T, 0, 1)
    rate = 0.22 + 0.55 * x ** 1.4                          # breaths per second
    ph = np.cumsum(rate) / SR
    frac = ph % 1.0
    inhale = np.sin(np.pi * np.clip(frac / 0.45, 0, 1)) ** 2
    exhale = np.sin(np.pi * np.clip((frac - 0.45) / 0.55, 0, 1)) ** 2
    swell = 0.12 + 0.88 * x ** 1.7
    out = np.zeros((N, 2))
    for ch in range(2):
        body = sos_filter(noise(N), "bandpass", [450, 1700], order=2)
        hiss = sos_filter(noise(N), "bandpass", [2200, 6500], order=2)
        low = sos_filter(noise(N), "bandpass", [260, 800], order=2)
        y = inhale * (0.8 * body + 0.7 * hiss) + exhale * (1.0 * low + 0.45 * body + 0.25 * hiss)
        out[:, ch] = y * swell
    return out


# ---------------------------------------------------------------- after the flatline
def distant_thud(dur: float) -> np.ndarray:
    t = tt(dur)
    f = 44 + 30 * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / 0.13) * (1 - np.exp(-t / 0.004))
    y += 0.35 * sos_filter(noise(len(t)), "lowpass", 180, order=2) * np.exp(-t / 0.04) * (1 - np.exp(-t / 0.004))
    y = sos_filter(y, "lowpass", 260, order=2)
    return fade(y, a=0.004, r=0.1)


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 3.0, rel_ms: float = 80.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak; never clips."""
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
    g = uniform_filter1d(g, size=L + 1, mode="nearest")  # edge-safe smoothing
    return x * g[:, None]


def flatline(x: np.ndarray) -> np.ndarray:
    """The cut: 2 ms raised-cosine fade ending exactly on the cue sample, dead silence after."""
    x = x.copy()
    nf = int(0.002 * SR)
    x[CUT_S - nf:CUT_S] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf + 1)[1:]))[:, None]
    x[CUT_S:] = 0.0
    return x


def master(pre: np.ndarray, post: np.ndarray) -> np.ndarray:
    """Gain to target, true-peak limit. The pre-cut bus is limited and DC-blocked (the limiter
    adds DC on the asymmetric thumps) BEFORE the flatline fade, so nothing rings past the cut."""
    gain_db = TARGET_LUFS - integrated_lufs(flatline(pre) + post)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.4
    for _ in range(12):
        g = 10 ** (gain_db / 20)
        a = soft_limiter(pre * g, ceiling)
        a = sos_filter(a, "highpass", 18, order=2)
        a = flatline(soft_limiter(a, ceiling))
        b = soft_limiter(post * g, ceiling)
        b[:THUD_S] = 0.0
        # DC trim: the HP tail is truncated by the flatline, leaving a small net offset; remove it
        # with a 0.25 s-ramped (sub-audio) constant so the first sample and the cut stay at zero
        w = np.zeros(N)
        r = int(0.25 * SR)
        w[:CUT_S] = 1.0
        w[:r] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, r))
        w[CUT_S - r:CUT_S] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, r))
        y = a + b
        y -= (y.sum(axis=0) / w.sum())[None, :] * w[:, None]
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


def mono_low(x: np.ndarray, f: float = 250.0) -> np.ndarray:
    """Steep high-pass on the side channel only: everything low stays mono."""
    m, s = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    s = sos_filter(s, "highpass", f, order=8)
    return np.stack([m + s, m - s], axis=1)


# ---------------------------------------------------------------- arrangement
def render() -> tuple[np.ndarray, np.ndarray]:
    # --- pre-cut bus: heart (mono), tinnitus, breath
    h = heart()
    h = sos_filter(h, "lowpass", 900, order=2)
    pre = np.repeat(h[:, None], 2, axis=1) * 1.0
    br = sos_filter(breath(), "highpass", 250, order=4)
    pre += br * 0.075
    pre += tinnitus() * 0.0045
    pre = mono_low(pre)
    pre = sos_filter(pre, "highpass", 20, order=2)
    pre = sos_filter(pre, "lowpass", 15000, order=4)
    # --- after: one distant soft thud in a small dark room
    post = np.zeros((N, 2))
    th = distant_thud(N / SR - THUD_T)
    place(post, th, THUD_T, 0.3)
    room = reverb(sos_filter(post, "highpass", 90, order=2), rt60=0.6, predelay=0.012) * 0.25
    post = post + sos_filter(room, "highpass", 140, order=4)
    post = mono_low(post)
    post = sos_filter(post, "highpass", 20, order=2)
    post[:THUD_S] = 0.0                                   # causal filters: nothing before the thud

    nt = int(0.15 * SR)
    post[-nt:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nt)))[:, None]
    return pre, post


def main() -> None:
    pre, post = render()
    y = master(pre, post)
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
