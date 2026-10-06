"""drop-impact-heavy: Opus Sound Directory

A 3-second cinematic heavy impact centred on low C, built for trailer-style
drops. It opens on a dark, distant rumble that slowly swells. From 1.0 s a
reversed "pre-suck" pulls the air inwards: reversed dark noise and a reversed
metal shimmer rise as their filter opens. The suck cuts off 60 ms before the hit
and leaves a short vacuum. On frame 45 (1.5 s) everything lands at once. A mono
sub boom drops in pitch from about 130 Hz down to C1, with a C2 octave for
small speakers. A sharp transient crack and a chesty body thump hit with it. A
clangy, inharmonic metal-plate ring on C beats and fades. A dark, wide noise and
reverb tail rolls off over about 1.5 s. The sub boom is the only content below
120 Hz, and it is mono.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 604545
DURATION_SEC = 3
BPM = 120
KEY = "C (low C1 sub)"
FPS = 30
CUE_FRAMES = (45,)             # frame 45 (1.5 s): the impact
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
HIT_T = CUE_FRAMES[0] / FPS    # 1.5 s = sample 72000
SUCK_START = 1.0
VACUUM = 0.060                 # silence between the end of the suck and the hit

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


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


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


def svf_lp(x: np.ndarray, fc: np.ndarray, q: float = 0.8) -> np.ndarray:
    """Zavalishin TPT state-variable low-pass with a per-sample cutoff (for sweeps)."""
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
        y[n] = v2
    return y


def reverb(x: np.ndarray, rt60: float, predelay: float, band=(150, 5000)) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (dark hall)."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60) * (1 - np.exp(-t / 0.012))
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", list(band)) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


# ---------------------------------------------------------------- voices
PLATE = ((1.000, 1.00, 1.10), (1.594, 0.70, 0.85), (2.136, 0.55, 0.70), (2.296, 0.45, 0.62),
         (2.653, 0.40, 0.50), (2.918, 0.32, 0.42), (3.156, 0.26, 0.36), (3.501, 0.22, 0.30),
         (4.060, 0.16, 0.24), (4.610, 0.12, 0.18))   # (ratio, amp, decay s): circular-plate-like modes


def metal(f0: float, dur: float, detune_cents: float) -> np.ndarray:
    """Inharmonic metal-plate ring; slight per-channel detune gives slow beating."""
    t = tt(dur)
    y = np.zeros_like(t)
    for ratio, amp, dec in PLATE:
        f = f0 * ratio * 2 ** (detune_cents / 1200)
        if f > 15000:
            continue
        y += amp * np.exp(-t / dec) * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return fade(y * 0.25, a=0.0015, r=0.08)


def rumble(dur: float) -> np.ndarray:
    """Distant dark rumble, kept above 120 Hz (the sub is reserved for the boom)."""
    t = tt(dur)
    env = (t / dur) ** 1.2
    out = np.stack([sos_filter(noise(dur), "bandpass", [160, 560], order=2) for _ in range(2)], 1)
    wob = 1 + 0.25 * np.sin(2 * np.pi * 3.1 * t[:, None] + np.array([[0.0, 1.7]]))
    return fade(out * env[:, None] * wob, a=0.05, r=0.01)


def pre_suck(dur: float) -> np.ndarray:
    """Reversed decaying noise + reversed metal shimmer, filter opening as it rises.
    Built forwards as a decay, then time-reversed, so it swells into a sharp cut."""
    t = tt(dur)
    env = np.exp(-t / (dur * 0.22))          # decay, reversed below into a swell
    fc = 9000 * np.exp(-t / (dur * 0.35)) + 250
    out = np.zeros((len(t), 2))
    for ch in range(2):
        out[:, ch] = svf_lp(noise(dur), fc, 0.9) * env
        out[:, ch] += 0.9 * metal(hz(72), dur, (-7, 7)[ch]) * np.exp(-t / (dur * 0.3))
    out = out[::-1]
    return fade(out, a=0.02, r=0.003)        # <=3 ms cut into the vacuum


def sub_boom(dur: float) -> np.ndarray:
    """Pitch-dropping sine: ~130 Hz -> C1 (32.7 Hz), plus a C2 octave layer that follows."""
    t = tt(dur)
    f = hz(24) + (130 - hz(24)) * np.exp(-t / 0.075)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-t / 0.62) * (1 - np.exp(-t / 0.0015))
    y = np.sin(ph) * env + 0.42 * np.sin(2 * ph) * np.exp(-t / 0.30)
    y = np.tanh(1.3 * y) / np.tanh(1.3)       # gentle saturation: harmonics for small speakers
    return fade(y, a=0.0008, r=0.25)


def crack(dur: float = 0.09) -> np.ndarray:
    t = tt(dur)
    y = sos_filter(noise(dur), "bandpass", [1200, 12000], order=2) * np.exp(-t / 0.0045)
    y += 0.6 * sos_filter(noise(dur), "bandpass", [2600, 5200], order=2) * np.exp(-t / 0.012)
    return fade(y, a=0.0004, r=0.01)


def body_thump(dur: float = 0.35) -> np.ndarray:
    t = tt(dur)
    y = sos_filter(noise(dur), "bandpass", [140, 450], order=2) * np.exp(-t / 0.045)
    return fade(y, a=0.0008, r=0.03)


def noise_tail(dur: float) -> np.ndarray:
    """Wide dark noise tail whose low-pass closes from 6 kHz to 500 Hz as it decays."""
    t = tt(dur)
    fc = 500 + 5500 * np.exp(-t / 0.28)
    env = np.exp(-t / 0.42) * (1 - np.exp(-t / 0.004))
    return np.stack([fade(svf_lp(noise(dur), fc, 0.7) * env, 0.001, 0.1) for _ in range(2)], 1)


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 120.0) -> np.ndarray:
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
    g = uniform_filter1d(g, size=L + 1, mode="nearest")  # edge-safe (no ramp at file start/end)
    return x * g[:, None]


def master(mix: np.ndarray) -> np.ndarray:
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.4
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        # gain riding on the asymmetric sub lobe leaves a little DC: block it, then re-catch overshoot
        y = sos_filter(y, "highpass", 18, order=2)
        y = soft_limiter(y, ceiling)
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    low = np.zeros((N, 2))      # sub boom: the only content below 120 Hz
    pre = np.zeros((N, 2))      # rumble + pre-suck (dry: the vacuum must stay empty)
    hit = np.zeros((N, 2))      # crack, thump, metal, noise tail
    send = np.zeros((N, 2))

    # --- intro: distant rumble swelling up to the suck, cut into the vacuum
    place(pre, rumble(HIT_T - VACUUM), 0.0, 0.6)

    # --- pre-suck: reversed swell, sharp cut 60 ms before the hit
    place(pre, pre_suck(HIT_T - VACUUM - SUCK_START), SUCK_START, 0.55)

    # --- payoff on frame 45
    place(low, sub_boom(1.45), HIT_T, 1.0)
    c = crack()
    place(hit, np.stack([c, c], 1), HIT_T, 0.7)
    place(send, np.stack([c, c], 1), HIT_T, 0.35)
    th = body_thump()
    place(hit, th, HIT_T, 0.9)
    place(send, th, HIT_T, 0.4)
    for side, det in ((-1, -9), (1, 9)):
        m = metal(hz(60), 1.4, det)                     # plate ring on C4
        place(hit, m, HIT_T + 0.004, 0.55, pan=0.6 * side)
        place(send, m, HIT_T, 0.3, pan=0.6 * side)
        m2 = metal(hz(48), 1.2, -det * 0.5)             # lower clang on C3
        place(hit, m2, HIT_T + 0.002, 0.35, pan=0.3 * side)
    nt = noise_tail(1.45)
    place(hit, nt, HIT_T, 0.45)
    place(send, nt, HIT_T, 0.4)

    hp = lambda x, f=140: sos_filter(x, "highpass", f, order=4)
    pre, hit = hp(pre, 150), hp(hit)
    wet = hp(reverb(send, rt60=2.2, predelay=0.02), 160) * 0.85
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)

    mix = low * 1.0 + pre + hit + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 120, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 16000, order=4)

    nf = int(0.3 * SR)
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
