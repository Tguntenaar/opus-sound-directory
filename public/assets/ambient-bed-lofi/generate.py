"""ambient-bed-lofi: Opus Sound Directory

A 12-second seamless lo-fi bed at 75 BPM: fifteen beats, laid out as five bars of a
lazy, swung 3/4. A mellow FM electric-piano (bell-ish tine, soft bark, stereo
tremolo and slow tape wow) comps rootless Ebmaj9 and Eb6/9, Fm9 for two bars, and
a Bb13 turnaround that leans back into the top of the loop. Under it sit a round
sine bass, dusty soft drums (a pillowy kick, a band-limited brushy snare on beat
3, low-passed swung hats) and a vinyl layer of hiss and soft crackle. The loop
starts with a kick and chord strike on frame 0 and is rendered circularly: three
identical cycles are synthesised, tails, reverb, wow and limiting run across
them, and the middle cycle is kept, so the last sample flows straight back into
the first with no fade. Only the mono kick and bass sit below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 75012
DURATION_SEC = 12
BPM = 75
KEY = "Eb major (Ebmaj9 / Fm9)"
FPS = 30
CUE_FRAMES = (0,)              # loop top: kick + chord strike on sample 0
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR          # one loop cycle
CYC = 3                        # cycles rendered; the middle one is kept
BEAT = 60.0 / BPM              # 0.8 s; 15 beats = 12 s = 5 bars of 3/4
BAR = 3 * BEAT
SWING = 0.60                   # off-beat eighth lands at 60 % of the beat

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    x = x.copy()
    na, nr = min(len(x), max(1, int(a * SR))), min(len(x), max(1, int(r * SR)))
    shp = (-1,) + (1,) * (x.ndim - 1)
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))).reshape(shp)
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))).reshape(shp)
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a snippet into the CYC-cycle bus at loop time t, once per cycle, so every
    event (and its tail) repeats identically and wraps across the loop point."""
    if x.ndim == 1:
        th = (pan + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)
    t = t % DURATION_SEC                       # an event nudged before 0 wraps to the loop end
    for k in range(CYC):
        s = int(round(t * SR)) + k * N
        if s >= len(bus):
            continue
        e = min(len(bus), s + len(x))
        bus[s:e] += gain * x[: e - s]


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


def slot(bar: int, eighth: int) -> float:
    """Loop time of a swung eighth (0..5) in a 3/4 bar."""
    beat, off = divmod(eighth, 2)
    return bar * BAR + (beat + SWING * off) * BEAT


# ---------------------------------------------------------------- voices
def epiano(midi: float, dur: float, vel: float = 1.0) -> np.ndarray:
    """FM electric piano: 1:1 carrier/modulator whose index decays (soft bark into a
    round sustain), plus a short 14:1 tine partial. Sidebands stay well under 10 kHz."""
    t = tt(dur)
    f = hz(midi)
    idx = vel * (1.5 * np.exp(-t / 0.22) + 0.25)
    ph0 = rng.uniform(0, 2 * np.pi)
    y = np.sin(2 * np.pi * f * t + ph0 + idx * np.sin(2 * np.pi * f * t))
    tine = 0.12 * vel * np.sin(2 * np.pi * f * 14 * t) * np.exp(-t / 0.018) if f * 14 < 9000 else 0.0
    env = np.exp(-t / 2.2) * (0.6 + 0.4 * np.exp(-t / 0.4))
    return fade((y * env + tine) * 0.3 * vel, a=0.002, r=min(0.25, dur * 0.3))


def sine_bass(midi: float, dur: float) -> np.ndarray:
    t = tt(dur)
    f = hz(midi)
    y = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t) + 0.05 * np.sin(6 * np.pi * f * t)
    env = 0.6 + 0.4 * np.exp(-t / 0.3)
    return fade(y * env * 0.5, a=0.008, r=0.12)


def kick() -> np.ndarray:
    t = tt(0.45)
    f = 52 + (115 - 52) * np.exp(-t / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2)
    knock = sos_filter(noise(0.45), "bandpass", [600, 2200]) * np.exp(-t / 0.006) * 0.12
    y = np.tanh(1.4 * (body + knock)) / np.tanh(1.4)
    return fade(sos_filter(y, "lowpass", 2500), a=0.0008, r=0.03)


def snare(ghost: bool = False) -> np.ndarray:
    d = 0.35
    t = tt(d)
    body = np.sin(2 * np.pi * 185 * t + 0.6 * np.sin(2 * np.pi * 330 * t)) * np.exp(-t / 0.04) * 0.5
    brush = sos_filter(noise(d), "bandpass", [700, 5200], order=2)
    brush *= (1 - np.exp(-t / 0.004)) * np.exp(-t / (0.06 if ghost else 0.11))
    return fade((body + brush) * (0.4 if ghost else 0.8), a=0.001, r=0.03)


def hat(vel: float) -> np.ndarray:
    d = 0.08
    t = tt(d)
    y = sos_filter(noise(d), "bandpass", [5500, 10500], order=2)
    y *= (1 - np.exp(-t / 0.0015)) * np.exp(-t / 0.022)
    return fade(y * 0.3 * vel, a=0.001, r=0.01)


def reverb(x: np.ndarray, rt60: float = 1.1, predelay: float = 0.012) -> np.ndarray:
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60) * (1 - np.exp(-t / 0.01))
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [250, 4500]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, i], irs[i])[: len(x)] for i in range(2)], axis=1)


def vinyl() -> np.ndarray:
    """One loop cycle of vinyl surface: band-passed hiss plus soft crackle blips
    (Poisson-spaced, each a raised-cosine-windowed band-passed burst of ~0.4-1.2 ms)."""
    hiss = np.stack([sos_filter(noise(DURATION_SEC), "bandpass", [900, 8000]) for _ in range(2)], 1) * 0.012
    out = hiss
    n_pops = rng.poisson(9 * DURATION_SEC)
    times = rng.uniform(0, DURATION_SEC - 0.01, n_pops)
    for t0 in times:
        ln = int(rng.uniform(0.0004, 0.0012) * SR)
        b = noise(ln / SR) * np.hanning(ln)
        b = sos_filter(b, "bandpass", [1500, 6000])
        a = 0.04 * rng.lognormal(0, 0.5)
        pan = rng.uniform(-0.8, 0.8)
        th = (pan + 1) * np.pi / 4
        s = int(t0 * SR)
        out[s:s + ln, 0] += a * b * np.cos(th)
        out[s:s + ln, 1] += a * b * np.sin(th)
    return out


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
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. Runs on the
    periodic multi-cycle buffer with wrap-around windows, so the kept middle cycle
    has a gain curve that is itself periodic."""
    ceil = 10 ** (ceiling_db / 20)
    os = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = os[: len(x) * 4].reshape(len(x), 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    L = int(look_ms * 1e-3 * SR)
    held = minimum_filter1d(need, size=2 * L + 1, mode="wrap")
    rc = np.exp(-1.0 / (rel_ms * 1e-3 * SR))
    g = np.empty_like(held)
    prev = 1.0
    for n, h in enumerate(held.tolist()):
        prev = min(h, prev * rc + (1 - rc))
        g[n] = prev
    g = uniform_filter1d(g, size=L + 1, mode="wrap")
    return x * g[:, None]


def mid_cycle(x: np.ndarray) -> np.ndarray:
    return x[N:2 * N]


def master(mix: np.ndarray) -> np.ndarray:
    """Normalise the kept cycle to TARGET_LUFS; limit the whole periodic buffer."""
    gain_db = TARGET_LUFS - integrated_lufs(mid_cycle(mix))
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(mid_cycle(y))
        if abs(err) < 0.03:
            break
        gain_db += err
    y = mid_cycle(y)
    return y - y.mean(axis=0)          # constant offset only, so the loop seam is untouched


# ---------------------------------------------------------------- arrangement
EB9, EB69, FM9, BB13 = (55, 58, 62, 65), (55, 60, 62, 65), (56, 60, 63, 67), (56, 60, 62, 67)
BARS = [(EB9, 39), (EB69, 39), (FM9, 41), (FM9, 41), (BB13, 34)]   # (EP voicing, bass root)
TOPLINE = [(1, 4, 70), (1, 5, 67), (3, 4, 72), (3, 5, 68), (4, 3, 74), (4, 5, 70)]   # (bar, eighth, midi)


def render() -> np.ndarray:
    L = CYC * N
    low = np.zeros((L, 2))
    drums = np.zeros((L, 2))
    keys = np.zeros((L, 2))
    send = np.zeros((L, 2))

    def hum(dt: float = 0.008) -> float:
        return rng.uniform(-dt, dt)

    # ---- electric piano comping
    for b, (ch, root) in enumerate(BARS):
        t0 = slot(b, 0)
        for i, m in enumerate(ch):
            v = 0.9 * rng.uniform(0.9, 1.05)
            e = epiano(m, BAR + 0.5, v)
            tt0 = t0 + (0 if b == 0 else hum(0.004)) + 0.009 * i * (b > 0)   # gentle roll after the top
            place(keys, e, tt0, 0.5, pan=-0.25 + 0.17 * i)
            place(send, e, tt0, 0.18, pan=-0.25 + 0.17 * i)
        # soft re-strike of the upper two notes on the swung "2-and"
        for m in ch[2:]:
            e = epiano(m, BEAT * 1.2, 0.6)
            t = slot(b, 3) + hum()
            place(keys, e, t, 0.32, pan=0.2)
            place(send, e, t, 0.12)
    for b, e8, m in TOPLINE:
        e = epiano(m, BEAT * 0.9, 0.75)
        t = slot(b, e8) + hum()
        place(keys, e, t, 0.34, pan=0.3)
        place(send, e, t, 0.15)

    # ---- bass: root on 1, a fifth or octave pickup on the 3-and
    for b, (ch, root) in enumerate(BARS):
        place(low, sine_bass(root, BEAT * 1.8), slot(b, 0), 0.55)
        nxt = BARS[(b + 1) % len(BARS)][1]
        pick = root + 7 if b in (0, 2) else (root + 12 if b == 1 else nxt - 1 if b == 3 else root + 5)
        place(low, sine_bass(pick, BEAT * 0.38), slot(b, 5), 0.5 if b == 4 else 0.38)

    # ---- dusty drums
    for b in range(5):
        place(low, kick(), slot(b, 0), 0.8)
        if b in (1, 3, 4):
            place(low, kick(), slot(b, 3) + (hum() if b else 0), 0.45)
        if b == 4:                                   # pickup kick on the last 3-and, into the loop top
            place(low, kick(), slot(b, 5), 0.68)
        sn = snare()
        place(drums, sn, slot(b, 4) + 0.012, 0.6, pan=0.05)
        place(send, sn, slot(b, 4) + 0.012, 0.22)
        if b in (2, 4):
            place(drums, snare(ghost=True), slot(b, 5) + hum(), 0.35, pan=0.1)
        for e8 in range(6):
            v = (1.0 if e8 % 2 == 0 else 0.65) * rng.uniform(0.8, 1.1)
            place(drums, hat(v), slot(b, e8) + hum(0.005), 0.5, pan=-0.3)

    # ---- bus processing (all on the periodic 3-cycle buffer)
    n = np.arange(L) / SR
    # tape wow: slow periodic fractional delay on the keys (0.25 Hz -> 3 cycles per loop)
    d = (0.0025 + 0.0007 * np.sin(2 * np.pi * 0.25 * n)) * SR
    idx = np.arange(L) - d
    keys = np.stack([np.interp(idx, np.arange(L), keys[:, c]) for c in range(2)], 1)
    # stereo tremolo, 1.25 Hz (15 cycles per loop)
    trem = 0.18 * np.sin(2 * np.pi * 1.25 * n)
    keys *= np.stack([1 + trem, 1 - trem], 1)
    keys = sos_filter(sos_filter(keys, "lowpass", 4200, order=2), "highpass", 150, order=4)
    drums = np.tanh(1.5 * drums) / 1.5
    drums = sos_filter(sos_filter(drums, "lowpass", 7000, order=2), "highpass", 150, order=4)
    wet = sos_filter(reverb(send, rt60=1.1), "highpass", 180, order=4) * 0.45
    vin = np.tile(vinyl(), (CYC, 1))
    vin = sos_filter(vin, "highpass", 300, order=2)
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    low = sos_filter(low, "lowpass", 1800, order=2)

    # gentle pump on keys from the downbeat kicks
    duck = np.ones(L)
    tk = tt(0.4)
    shape = 1 - 0.22 * np.exp(-tk / 0.12) * (1 - np.exp(-tk / 0.004))
    for k in range(CYC):
        for b in range(5):
            s0 = int(round(slot(b, 0) * SR)) + k * N
            e = min(L, s0 + len(shape))
            duck[s0:e] = np.minimum(duck[s0:e], shape[: e - s0])
    keys *= duck[:, None]

    mix = low + drums * 0.9 + keys + wet + vin
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 260, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 15000, order=4)
    return mix


def main() -> None:
    y = master(render())
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP  "
          f"seam step {np.abs(f[0] - f[-1]).max():.4f}")


if __name__ == "__main__":
    main()
