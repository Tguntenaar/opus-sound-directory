"""ui-error-soft: Opus Sound Directory

A gentle 0.4-second "nope" for a UI error, with a C minor feel. Two soft felt-on-wood taps fall a
minor third: Eb4 on frame 0, then C4 about 105 ms later, a little softer, with a quiet C3 body
underneath it. Each tap is a muted wooden bar with felt-mallet harmonics and a soft knock. Its
pitch sags by a few cents as it rings, so the pair reads as a shrug rather than an alarm.
Everything sits under a gentle low-pass near 1.8 kHz with a small, dark room, and nothing is
bright or sharp, so it stays pleasant on the hundredth repeat. The second tap fades out to
silence well before the end, and the low end stays centred.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 4004
DURATION_SEC = 0.4
BPM = None
KEY = "C minor"
FPS = 30
CUE_FRAMES = (0,)               # frame 0: first tap
TARGET_LUFS = -17.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
TAP2_T = 0.105                  # second tap, a quick "no-no" pair

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
    x[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    x[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
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


# ---------------------------------------------------------------- voices
def felt_tap(midi: float, dur: float, decay: float, sag_cents: float = 18.0) -> np.ndarray:
    """Muted wooden bar struck with a felt mallet. The felt keeps the spectrum near-harmonic
    and soft (1, 2, 3 with a weak 2.76 wood mode). Every partial dies fast, the pitch sags a few
    cents, and a low-passed knock gives the 'tock'. All partials stay far below 16 kHz."""
    t = tt(dur)
    f0 = hz(midi)
    sag = 2 ** (-(sag_cents / 1200) * (1 - np.exp(-t / 0.06)))
    phase = 2 * np.pi * np.cumsum(f0 * sag) / SR
    y = np.zeros_like(t)
    for ratio, amp, dec in ((1.0, 1.0, decay), (2.0, 0.30, decay * 0.45),
                            (2.76, 0.12, decay * 0.25), (3.0, 0.08, decay * 0.3)):
        y += amp * np.exp(-t / dec) * np.sin(ratio * phase + rng.uniform(0, 2 * np.pi))
    # felt softens the strike: the body blooms over ~3 ms instead of snapping
    y *= 1 - np.exp(-t / 0.003)
    knock = sos_filter(noise(dur), "bandpass", [f0 * 0.8, f0 * 3.2], order=2)
    y += 0.30 * knock * np.exp(-t / 0.006) * (1 - np.exp(-t / 0.0012))
    return fade(y, a=0.001, r=0.02)


def body(midi: float, dur: float) -> np.ndarray:
    """Quiet low wooden body resonance under the second tap (sine, short decay)."""
    t = tt(dur)
    y = np.sin(2 * np.pi * hz(midi) * t) * np.exp(-t / 0.07) * (1 - np.exp(-t / 0.004))
    return fade(y, a=0.002, r=0.02)


def room(x: np.ndarray, rt60: float = 0.22, predelay: float = 0.006) -> np.ndarray:
    """Small dark room: decorrelated stereo exponential-noise IR, low-passed."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [250, 2500]) * env
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
    """BS.1770-4 integrated loudness: 400 ms blocks, 75 % overlap, -70 LUFS abs + -10 LU rel gates.
    (A 0.4 s file is exactly one gating block.)"""
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    starts = range(0, len(y) - blk + 1, hop)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in starts])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    os = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os)) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 60.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. Held over the
    look-ahead window, one-pole release, box-smoothed; it never clips the waveform."""
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
    # edge-padded box smoothing (zero padding would ramp the gain over the first/last 1 ms)
    g = uniform_filter1d(g, size=L + 1, mode="nearest")
    return x * g[:, None]


def master(mix: np.ndarray) -> np.ndarray:
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3          # margin for dither + inter-sample
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    taps = np.zeros((N, 2))
    low = np.zeros((N, 2))
    send = np.zeros((N, 2))

    # tap 1: Eb4, short and a little brighter; tap 2: C4, softer, longer ring + C3 body
    t1 = felt_tap(63, 0.22, decay=0.055, sag_cents=12)
    place(taps, t1, 0.0, 0.85, pan=-0.08)
    place(send, t1, 0.0, 0.30, pan=-0.08)
    t2 = felt_tap(60, 0.26, decay=0.075, sag_cents=22)
    place(taps, t2, TAP2_T, 0.70, pan=0.08)
    place(send, t2, TAP2_T, 0.30, pan=0.08)
    place(low, body(48, 0.22), TAP2_T, 0.25)

    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    wet = room(send) * 0.35
    mix = taps + low + wet
    # felt: gentle 1.8 kHz low-pass, plus a second pole pair at 4.5 kHz so nothing bright or alarming survives
    mix = sos_filter(mix, "lowpass", 1800, order=2)
    mix = sos_filter(mix, "lowpass", 4500, order=2)
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    # keep the low end centred: the fundamentals (131-311 Hz) and the room's low half are mono,
    # only the woody overtones and room air carry width
    side = sos_filter(side, "highpass", 420, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 60, order=2)              # DC / subsonic

    # 60 ms cosine tail-out so the last sample is exactly silent
    nf = int(0.06 * SR)
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
