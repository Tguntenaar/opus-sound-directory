"""logo-sting-bright: Opus Sound Directory

A bright 2.5-second brand sting in D major at 120 BPM: a rising, memorable mallet motif that
resolves onto a sparkling tonic hit. A wooden marimba plays D5 on frame 0 (over a soft low D3
bar), then F#5 on the beat, A5 on the off-beat and a C#6 leading tone on beat 4, each note
doubled very quietly two octaves up by a glass bell. Exactly on frame 60 (2.0 s) the motif
resolves to D6: a full D major marimba chord, a ringing glass-bell triad, a short mono D2 sub
under it and a shimmer of tiny high glass pings and air that scatter across the stereo field.
Everything then decays fast and lands on true silence by 2.5 s. Nothing but the hit's sub sits
below 120 Hz, and the motif carries no drums so the logo stays the star.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d

SAMPLE_RATE = 48000
SEED = 25060
DURATION_SEC = 2.5
BPM = 120
KEY = "D major"
FPS = 30
CUE_FRAMES = (0, 60)            # frame 0: first motif note, frame 60: resolving hit + shimmer
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
BEAT = 60.0 / BPM               # 0.5 s
HIT_T = CUE_FRAMES[1] / FPS     # 2.0 s

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
def marimba(midi: float, dur: float = 0.9, hard: float = 1.0, ring: float = 1.0,
            attack: float = 0.0012) -> np.ndarray:
    """Modal marimba bar: tuned partials at 1 : 3.99 : 9.83 (the bar's tuned overtones), each
    decaying faster than the one below, plus a resonator-tube bloom on the fundamental and a
    short wooden mallet knock. Partials stop below 16 kHz (no aliasing)."""
    t = tt(dur)
    f = hz(midi)
    # higher notes ring shorter on a real bar
    base = ring * 0.42 * (523.25 / f) ** 0.35
    y = np.zeros_like(t)
    for ratio, amp, dec in ((1.0, 1.0, base), (3.99, 0.32 * hard, base * 0.28),
                            (9.83, 0.10 * hard, base * 0.10)):
        if ratio * f < 16000:
            y += amp * np.exp(-t / dec) * np.sin(2 * np.pi * ratio * f * t)
    # resonator: fundamental swells in over ~8 ms and holds a touch longer
    y += 0.35 * (1 - np.exp(-t / 0.008)) * np.exp(-t / (base * 1.3)) * np.sin(2 * np.pi * f * t + 0.6)
    knock = sos_filter(noise(dur), "bandpass", [f * 1.5, min(f * 6, 9000)], order=2)
    y += 0.22 * hard * knock * np.exp(-t / 0.0035)
    return fade(y * 0.45, a=attack, r=0.04)


def glass(midi: float, dur: float = 1.0, decay: float = 0.55) -> np.ndarray:
    """Glass bell: bright inharmonic partials (1 : 2.32 : 4.25 : 6.63) with a slow beating
    pair on the fundamental. Kept clear of the Chladni bell ratios used elsewhere."""
    t = tt(dur)
    f = hz(midi)
    y = np.zeros_like(t)
    for ratio, amp, dec in ((1.0, 1.0, decay), (1.0019, 0.5, decay), (2.32, 0.38, decay * 0.45),
                            (4.25, 0.18, decay * 0.22), (6.63, 0.08, decay * 0.12)):
        if ratio * f < 16000:
            y += amp * np.exp(-t / dec) * np.sin(2 * np.pi * ratio * f * t + rng.uniform(0, 2 * np.pi))
    return fade(y * 0.28, a=0.0008, r=0.03)


def sub(midi: float, dur: float = 0.45) -> np.ndarray:
    """Short mono sine sub with a small pitch settle; the only content below 120 Hz."""
    t = tt(dur)
    f = hz(midi) * (1 + 0.15 * np.exp(-t / 0.012))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
    return fade(y, a=0.0015, r=0.03)


def sparkle(dur: float = 0.5, count: int = 26) -> np.ndarray:
    """Shimmer: a spray of tiny glass pings (pentatonic D major, 2.3-9.4 kHz) that thins
    out over the tail, each panned randomly, plus a short breath of bright air."""
    out = np.zeros((int(round(dur * SR)), 2))
    pool = [86, 88, 90, 93, 95, 98, 100, 102, 105, 107, 110]   # D6.. D8 + pentatonic
    for i in range(count):
        when = dur * 0.72 * (i / count) ** 1.6 + rng.uniform(0, 0.01)
        m = pool[int(rng.integers(len(pool)))]
        tp = tt(0.12)
        ping = np.sin(2 * np.pi * hz(m) * tp + rng.uniform(0, 2 * np.pi)) * np.exp(-tp / rng.uniform(0.025, 0.05))
        ping = fade(ping, a=0.0006, r=0.01)
        gain = 0.16 * (1 - i / count) ** 0.6 * rng.uniform(0.6, 1.0)
        place(out, ping, when, gain, pan=float(rng.uniform(-0.85, 0.85)))
    ta = tt(dur)
    air_env = (1 - np.exp(-ta / 0.004)) * np.exp(-ta / 0.11)
    for ch in range(2):
        a = sos_filter(noise(dur), "bandpass", [6500, 14500], order=2) * air_env
        out[:, ch] += 0.05 * fade(a, 0.001, 0.02)
    return out


def reverb(x: np.ndarray, rt60: float = 0.7, predelay: float = 0.012) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (short bright room)."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [400, 9000]) * env
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
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. The gain curve is held
    over the look-ahead window, recovers through a one-pole release and is box-smoothed.
    It never clips the waveform."""
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
    g = np.convolve(g, np.ones(L + 1) / (L + 1), mode="same")
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
    low = np.zeros((N, 2))      # the hit's sub only
    mallets = np.zeros((N, 2))
    bells = np.zeros((N, 2))
    fx = np.zeros((N, 2))
    send = np.zeros((N, 2))

    # motif: D5 (beat 1), F#5 (beat 2), A5 (beat 2&), C#6 (beat 4) -> D6 on frame 60
    motif = ((0.0, 74, 0.80, -0.15), (BEAT, 78, 0.70, 0.05),
             (1.5 * BEAT, 81, 0.66, 0.20), (3 * BEAT, 85, 0.74, -0.05))
    for t, m, v, pan in motif:
        # the leading tone rings shorter so the resolution lands on a clean floor
        mk = marimba(m, 0.8, hard=1.0, ring=0.55 if m == 85 else 1.0)
        place(mallets, mk, t, v, pan)
        place(send, mk, t, v * 0.35, pan)
        gl = glass(m + 24, 0.5, decay=0.22)
        place(bells, gl, t + 0.004, v * 0.28, -pan)
        place(send, gl, t, v * 0.12)
    # soft low D3 bar under the opening note grounds the key (above 120 Hz)
    place(mallets, marimba(50, 1.4, hard=0.6, ring=0.6), 0.0, 0.16)
    # a tiny A4 grace under the leading tone keeps beat 4 warm
    place(mallets, marimba(69, 0.45, hard=0.5, ring=0.5), 3 * BEAT, 0.09, 0.3)

    # resolving hit on frame 60: D major marimba chord, glass triad, sub, shimmer
    for i, (m, v, pan) in enumerate(((62, 0.50, 0.0), (74, 0.75, -0.30), (78, 0.55, 0.30),
                                     (81, 0.55, -0.15), (86, 0.95, 0.10))):
        mk = marimba(m, 0.5, hard=1.2, ring=0.6, attack=0.0005)
        place(mallets, mk, HIT_T, v, pan)
        place(send, mk, HIT_T, v * 0.4, pan)
    for m, pan in ((86, -0.35), (90, 0.35), (93, 0.0)):
        gl = glass(m, 0.5, decay=0.15)
        place(bells, gl, HIT_T, 0.60, pan)
        place(send, gl, HIT_T, 0.25, pan)
    place(low, sub(38, 0.45), HIT_T, 0.32)
    sp = sparkle(0.5)
    place(fx, sp, HIT_T + 0.002, 1.0)
    place(send, sp, HIT_T, 0.5)

    hp = lambda x: sos_filter(x, "highpass", 150, order=4)
    mallets = hp(mallets)
    bells = hp(bells)
    fx = hp(fx)
    wet = hp(reverb(send, rt60=0.65)) * 0.45
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)

    mix = low * 0.9 + mallets + bells * 0.9 + fx * 0.9 + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 120, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)              # DC / subsonic
    mix = sos_filter(mix, "lowpass", 16500, order=4)

    # fast decay to silence: 0.25 s cosine tail-out so the last sample is exactly silent
    nf = int(0.25 * SR)
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
