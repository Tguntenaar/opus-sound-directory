"""ui-message-sent: Opus Sound Directory

A quick, optimistic 0.6-second "message sent" in G. It opens on frame 0 with a soft puff of air
that swells into an upward swish. Two decorrelated noise bands sweep from about 600 Hz to 9 kHz
and glide from slightly left to slightly right, and a faint breathy D5-to-G6 whistle rides
inside them to give the motion a pitch direction. At 140 ms the swish resolves into a light
glassy pluck: a G6 with a quieter D7 fifth above and a soft G5 body. Its partials follow
glass-like inharmonic ratios, with a tiny bright tink on the attack and a short, airy room.
Nothing heavy sits below 150 Hz and the stereo width lives only above 650 Hz. The pluck rings
out in about a third of a second and the file ends in silence, so it is gone before the next
thing happens.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 3303
DURATION_SEC = 0.6
BPM = None
KEY = "G major"
FPS = 30
CUE_FRAMES = (0,)               # frame 0: the swish starts (air puff, 0.5 ms attack)
TARGET_LUFS = -17.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
SWISH_DUR = 0.20                # noise sweep length
PLUCK_T = 0.140                 # the swish resolves into the pluck here

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Raised-cosine attack/release (sample 0 is exactly 0) so nothing starts or stops with a click."""
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na)))[(slice(None),) + (None,) * (x.ndim - 1)]
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr)))[(slice(None),) + (None,) * (x.ndim - 1)]
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
    """Zavalishin TPT state-variable band-pass, unity peak gain, per-sample cutoff (for sweeps)."""
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
        y[n] = k * v1
    return y


# ---------------------------------------------------------------- voices
def swish() -> np.ndarray:
    """Airy upward swish: two decorrelated noise bands sweeping ~600 Hz -> 9 kHz (stereo, drifting
    left -> right), a quiet breath puff at sample 0, and a faint D5 -> G6 whistle glide inside."""
    t = tt(SWISH_DUR)
    u = t / SWISH_DUR
    fc = 600 * (9000 / 600) ** np.clip(t / (PLUCK_T + 0.01), 0, 1) ** 1.2
    # body swells to a peak just before the pluck, then thins out quickly
    swell = (np.sin(np.pi * np.clip(t / (PLUCK_T + 0.012), 0, 1) * 0.5) ** 2.2)
    decay = np.where(t < PLUCK_T, 1.0, np.exp(-(t - PLUCK_T) / 0.022))
    puff = 0.30 * np.exp(-t / 0.018)                       # soft breath onset on the cue
    env = np.maximum(swell * decay, 0) + puff
    l = svf_bandpass(noise(SWISH_DUR), fc * 0.97, 3.2) * env
    r = svf_bandpass(noise(SWISH_DUR), fc * 1.03, 3.2) * env
    # pan drift: left-leaning at the start, right-leaning at the peak (the message "leaves")
    p = -0.35 + 0.7 * np.clip(u / 0.75, 0, 1)
    th = (p + 1) * np.pi / 4
    st = np.stack([l * np.cos(th), r * np.sin(th)], axis=1) * np.sqrt(2)
    # breathy whistle glide (sine, band-limited by construction), sits ~18 dB under the noise
    f = hz(74) * (hz(91) / hz(74)) ** np.clip(t / PLUCK_T, 0, 1) ** 1.3
    ph = 2 * np.pi * np.cumsum(f) / SR
    wh = 0.16 * np.sin(ph) * swell * decay * (1 + 0.3 * svf_bandpass(noise(SWISH_DUR), f, 3.0))
    st += wh[:, None]
    return fade(st, a=0.0005, r=0.02)


def glass_note(midi: float, dur: float, decay: float) -> np.ndarray:
    """Glassy pluck: inharmonic glass-like partials (1, 2.32, 4.25, 6.63) with faster decay for the
    higher modes, a 0.4 ms attack and slight beating from a 1.5-cent detuned twin of the fundamental.
    All partials stay far below 16 kHz (G6 x 6.63 = 10.4 kHz)."""
    t = tt(dur)
    f0 = hz(midi)
    y = np.zeros_like(t)
    for ratio, amp, dk in ((1.0, 1.0, 1.0), (2.32, 0.32, 0.45), (4.25, 0.14, 0.22), (6.63, 0.06, 0.12)):
        if f0 * ratio > 15000:
            continue
        y += amp * np.exp(-t / (decay * dk)) * np.sin(2 * np.pi * f0 * ratio * t + rng.uniform(0, 2 * np.pi))
    y += 0.35 * np.exp(-t / decay) * np.sin(2 * np.pi * f0 * 2 ** (1.5 / 1200) * t + rng.uniform(0, 2 * np.pi))
    return fade(y, a=0.0004, r=0.03)


def tink(dur: float = 0.012) -> np.ndarray:
    """Tiny bright 'tink' on the pluck attack: band-passed noise, ~2 ms decay."""
    t = tt(dur)
    y = sos_filter(noise(dur), "bandpass", [4500, 11000], order=2) * np.exp(-t / 0.002)
    return fade(y, a=0.0004, r=0.004)


def room(x: np.ndarray, rt60: float = 0.30, predelay: float = 0.008) -> np.ndarray:
    """Small bright airy room: decorrelated stereo exponential-noise IR."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [600, 9000]) * env
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
    air = np.zeros((N, 2))
    glass = np.zeros((N, 2))
    send = np.zeros((N, 2))

    sw = swish()
    place(air, sw, 0.0, 1.0)
    place(send, sw, 0.0, 0.10)

    # light glassy pluck: G6 lead, D7 fifth above (quieter, a hair later), soft G5 body
    g6 = glass_note(91, 0.40, decay=0.068)
    d7 = glass_note(98, 0.28, decay=0.048)
    g5 = glass_note(79, 0.32, decay=0.052)
    place(glass, g6, PLUCK_T, 0.60, pan=0.10)
    place(glass, d7, PLUCK_T + 0.004, 0.24, pan=0.30)
    place(glass, g5, PLUCK_T, 0.22, pan=-0.05)
    place(glass, tink(), PLUCK_T, 0.20, pan=0.15)
    for x, gn, p in ((g6, 0.30, 0.10), (d7, 0.14, 0.30)):
        place(send, x, PLUCK_T, gn, pan=p)

    wet = room(send) * 0.45
    mix = air + glass + wet
    mix = sos_filter(mix, "lowpass", 13000, order=4)          # keep the air short of the ultrasonic band
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    mid = sos_filter(mid, "highpass", 140, order=2)           # nothing heavy: it is a light UI sound
    side = sos_filter(side, "highpass", 650, order=8)         # width only above the low-mids (mono low end)
    mix = np.stack([mid + side, mid - side], axis=1)

    # cosine tail-out so the last sample is exactly silent
    nf = int(0.07 * SR)
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
