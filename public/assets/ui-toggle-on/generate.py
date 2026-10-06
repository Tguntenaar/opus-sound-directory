"""ui-toggle-on: Opus Sound Directory

A 0.4-second tactile switch flipping ON, tuned around A. On frame 0 a small plastic lever clicks: a
dry, short "t-tk" made of a contact tick and a latch snap 17 ms later, each a burst of band-passed
grit over a few inharmonic plastic-housing modes, with a tiny mono thock of body underneath. Riding
out of the click is a small, quick upward blip: a soft sine with a whisper of second harmonic that
glides smoothly from A5 up to E6 in about 25 ms, holds for a moment and fades. It is a continuous
glide, not a stepped beep. A very short, close room adds a hint of space. The top end rolls off
above 9 kHz and nothing rings for long, so it stays neutral and satisfying on the hundredth flip.
Everything is gone by about 0.3 s, and the last 60 ms fade to silence.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 20201
DURATION_SEC = 0.4
BPM = None
KEY = "A (blip A5 -> E6)"
FPS = 30
CUE_FRAMES = (0,)               # frame 0: the switch click
TARGET_LUFS = -17.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
LATCH_T = 0.017                 # latch snap after the contact tick
BLIP_T = 0.010                  # blip starts while the click is still sounding

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
def plastic_tick(modes, bright: float, dur: float = 0.03, grit_decay: float = 0.0012) -> np.ndarray:
    """One plastic contact: a 0.4 ms raised-cosine onset, a burst of band-passed grit and a few
    damped inharmonic housing modes (all under 7 kHz, so the click is crisp but never spitty)."""
    t = tt(dur)
    grit = sos_filter(noise(dur), "bandpass", [1400, 6500], order=2)
    grit /= np.max(np.abs(grit[:96])) + 1e-9
    y = bright * grit * np.exp(-t / grit_decay)
    for f, amp, dec in modes:
        y += amp * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / dec)
    na = int(0.0004 * SR)
    y[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    return fade(y, a=0.0004, r=0.004)


def thock(dur: float = 0.06) -> np.ndarray:
    """Tiny body knock under the click: a sine falling 230 -> 170 Hz, 9 ms decay (kept mono)."""
    t = tt(dur)
    f = 170 + 60 * np.exp(-t / 0.006)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.009) * (1 - np.exp(-t / 0.0007))
    return fade(y, a=0.0005, r=0.01)


def blip(dur: float = 0.24) -> np.ndarray:
    """The ON blip: soft sine gliding A5 -> E6 (fast exponential approach, ~25 ms), a little
    2nd harmonic and a faint 3rd, 3 ms bloom, ~45 ms exponential fade with a soft tail."""
    t = tt(dur)
    f0, f1 = hz(81), hz(88)                     # A5 -> E6
    f = f1 - (f1 - f0) * np.exp(-t / 0.009)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.10 * np.sin(2 * ph + 0.4) + 0.025 * np.sin(3 * ph + 1.1)
    env = (1 - np.exp(-t / 0.003)) * (0.75 * np.exp(-t / 0.040) + 0.25 * np.exp(-t / 0.085))
    return fade(y * env, a=0.002, r=0.03)


def room(x: np.ndarray, rt60: float = 0.12, predelay: float = 0.003) -> np.ndarray:
    """Very small, close room: decorrelated stereo exponential-noise IR, band-limited."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [400, 7000]) * env
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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 1.5, rel_ms: float = 40.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. Held over the
    look-ahead window, one-pole release, edge-safe box smoothing; it never clips the waveform."""
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
    click = np.zeros((N, 2))
    low = np.zeros((N, 2))
    tone = np.zeros((N, 2))
    send = np.zeros((N, 2))

    # contact tick (frame 0): fuller, lower housing modes
    tick = plastic_tick([(2350, 0.55, 0.0035), (3870, 0.35, 0.0022), (5620, 0.20, 0.0013)], bright=0.9)
    place(click, tick, 0.0, 1.0, pan=-0.05)
    place(send, tick, 0.0, 0.25, pan=-0.05)
    # latch snap: smaller and a touch higher, the "k" in "t-tk"
    snap = plastic_tick([(2910, 0.45, 0.0025), (4480, 0.30, 0.0016), (6150, 0.15, 0.0010)],
                        bright=0.7, grit_decay=0.0009)
    place(click, snap, LATCH_T, 0.55, pan=0.05)
    place(send, snap, LATCH_T, 0.20, pan=0.05)
    place(low, thock(), 0.0, 0.55)

    # the ON blip, a hair right of centre with a slightly wider room send
    b = blip()
    place(tone, b, BLIP_T, 0.42, pan=0.04)
    place(send, b, BLIP_T, 0.30, pan=0.04)

    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    wet = room(send) * 0.30
    mix = click + low + tone + wet
    mix = sos_filter(mix, "lowpass", 9000, order=4)              # no fizzy top, nothing near 19 kHz
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 300, order=6)            # low end strictly centred
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 40, order=2)               # DC / subsonic

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
