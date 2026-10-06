"""chaos-calm-04: Opus Sound Directory

An 8-second chaos-to-calm bed at 110 BPM for a "put the phone down" moment. It opens
on frame 0 with a flick: a burst of scroll-wheel detent ticks, a mid "thock" and a
fast swipe whoosh. For three seconds the scrolling turns frantic. Momentum flicks
overlap, each a run of tiny resonant ticks whose spacing stretches out as it coasts,
and every stream has its own pitch and place in the stereo field. A sixteenth-note
ratchet on the 110 BPM grid tightens to thirty-seconds, swipe whooshes cross the
image, and a jittery band of digital fizz swells underneath. All ticks are enveloped
(0.3 ms attack) and band-limited below 7.5 kHz. On frame 90 (3.0 s) the frenzy
collapses: everything stops through a 2 ms fade that ends on the cue sample, and a
focused, steady low hum on A starts on that same sample with a soft sub thud. The hum
is A1 and A2 with a quiet fifth and a few warm harmonics under 1 kHz, slowly beating,
mono below 120 Hz. It holds until the end and fades to silence.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 110490
DURATION_SEC = 8
BPM = 110
KEY = "A (drone)"
FPS = 30
CUE_FRAMES = (0, 90)           # frame 0: flick hit, frame 90: collapse into the hum
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM
CALM_T = CUE_FRAMES[1] / FPS   # 3.0 s
CALM_S = int(round(CALM_T * SR))
QUIET_BEFORE = 0.030           # no new tick onsets in the last 30 ms of the chaos
A1 = 55.0

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def cos_in(n: int) -> np.ndarray:
    return 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, max(1, n)))


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= cos_in(na)
    x[-nr:] *= cos_in(nr)[::-1]
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    s = int(round(t * SR))
    if s >= len(bus):
        return
    if x.ndim == 1:
        th = (np.clip(pan, -1, 1) + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)
    e = min(len(bus), s + len(x))
    bus[s:e] += gain * x[: e - s]


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def noise(n: int) -> np.ndarray:
    return rng.standard_normal(n)


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


def reverb(x: np.ndarray, rt60: float, band=(400, 7000), predelay: float = 0.008) -> np.ndarray:
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", list(band)) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


# ---------------------------------------------------------------- chaos voices
TICK_BP = signal.butter(2, [900, 7500], btype="bandpass", fs=SR, output="sos")


def tick(f_res: float, bright: float = 1.0) -> np.ndarray:
    """One scroll-wheel detent: two damped resonant modes plus a tiny noise burst,
    0.3 ms raised-cosine attack, band-limited 0.9-7.5 kHz."""
    t = tt(0.014)
    tau = rng.uniform(0.0012, 0.0024)
    y = (np.sin(2 * np.pi * f_res * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / tau)
         + 0.45 * np.sin(2 * np.pi * f_res * 1.63 * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / (tau * 0.6)))
    y += 0.5 * bright * noise(len(t)) * np.exp(-t / 0.0005)
    y = signal.sosfilt(TICK_BP, y)
    y[:15] *= cos_in(15)               # 0.3 ms attack
    y[-96:] *= cos_in(96)[::-1]
    return y


def flick_times(t0: float, n: int, first_gap: float, growth: float) -> list[float]:
    """Momentum scroll: tick spacing grows geometrically as the list coasts to a stop."""
    ts, t, g = [], t0, first_gap
    for _ in range(n):
        ts.append(t)
        t += g * rng.uniform(0.9, 1.1)
        g *= growth
    return ts


def whoosh(dur: float, f0: float, f1: float, q: float = 2.2) -> np.ndarray:
    t = tt(dur)
    fc = f0 * (f1 / f0) ** (t / dur)
    y = svf_bandpass(noise(len(t)), fc, q)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    pan_path = np.linspace(-0.8, 0.8, len(t)) * rng.choice([-1, 1])
    th = (pan_path + 1) * np.pi / 4
    y = y * env
    return np.stack([y * np.cos(th), y * np.sin(th)], axis=1) * np.sqrt(2)


def thock() -> np.ndarray:
    t = tt(0.09)
    y = sos_filter(noise(len(t)), "bandpass", [320, 1400], order=2) * np.exp(-t / 0.014)
    y += 0.6 * np.sin(2 * np.pi * 520 * t) * np.exp(-t / 0.02)
    return fade(y, a=0.001, r=0.01)


def haptic() -> np.ndarray:
    t = tt(0.05)
    f = 240 * (1 + 0.15 * np.exp(-t / 0.004))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.012)
    y += 0.3 * np.sin(2 * np.pi * 2.03 * np.cumsum(f) / SR) * np.exp(-t / 0.007)
    return fade(y, a=0.001, r=0.008)


def opening_thump() -> np.ndarray:
    t = tt(0.22)
    f = 62 * (1 + 1.4 * np.exp(-t / 0.012))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.06)
    return fade(y, a=0.001, r=0.03)


def fizz_bed() -> np.ndarray:
    """Jittery band of digital fizz under the frenzy, swelling toward the collapse."""
    n = CALM_S
    x = sos_filter(noise(2 * n).reshape(n, 2), "bandpass", [1800, 6500], order=2)
    steps = rng.uniform(0.25, 1.0, size=(int(CALM_T * 40) + 2, 2))      # 25 ms sample-and-hold jitter
    jit = np.repeat(steps, int(SR / 40), axis=0)[:n]
    jit = sos_filter(jit, "lowpass", 90, order=1)                        # rounded, no zipper clicks
    u = np.arange(n) / n
    return x * jit * (0.15 + 0.85 * u ** 1.6)[:, None]


# ---------------------------------------------------------------- calm voice
def hum() -> np.ndarray:
    """Focused A drone: A1 + A2 (+ E3, A3 and soft harmonics < 1 kHz), two slightly
    detuned voices beating slowly; starts on the cue with a 1 ms attack and a sub thud."""
    d = N / SR - CALM_T
    t = tt(d)
    out = np.zeros((len(t), 2))
    partials = ((1, 1.00), (2, 0.55), (3, 0.16), (4, 0.20), (5, 0.06), (6, 0.08), (8, 0.04),
                (10, 0.025), (12, 0.02), (16, 0.01))
    # partials below 130 Hz: one mono voice (no detune, so the fundamental never cancels)
    core = sum(a * np.sin(2 * np.pi * k * A1 * t) for k, a in partials if k * A1 < 130)
    out += 2 * core[:, None] / np.sqrt(2)
    # upper partials: two voices +-1.5 cents, panned, beating very slowly
    for v, (cents, pan) in enumerate(((-1.5, -0.3), (1.5, 0.3))):
        f = A1 * 2 ** (cents / 1200)
        y = np.zeros(len(t))
        for k, a in partials:
            if k * A1 < 130 or k * f > 1000:
                continue
            y += a * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
        th = (pan + 1) * np.pi / 4
        out[:, 0] += y * np.cos(th)
        out[:, 1] += y * np.sin(th)
    breathe = 1 + 0.05 * np.sin(2 * np.pi * (BPM / 60 / 8) * t)        # one slow swell per two bars
    settle = 0.78 + 0.22 * np.exp(-t / 0.35)                            # arrives a touch hot, settles
    out *= (breathe * settle)[:, None] * 0.15
    # soft sub thud on the arrival
    f = A1 * (1 + 0.5 * np.exp(-t / 0.02))
    thud = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2) * 0.55
    out += thud[:, None]
    na = int(0.001 * SR)
    out[:na] *= cos_in(na)[:, None]
    return out


# ---------------------------------------------------------------- loudness / peak
def k_weight(x: np.ndarray) -> np.ndarray:
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def integrated_lufs(x: np.ndarray) -> float:
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
def render() -> np.ndarray:
    ticks = np.zeros((CALM_S, 2))
    fx = np.zeros((CALM_S, 2))
    low = np.zeros((N, 2))
    last_onset = CALM_T - QUIET_BEFORE

    def put_tick(t, f, g, pan, bright=1.0):
        if t < last_onset:
            place(ticks, tick(f, bright), t, g, pan)

    # --- frame 0: the opening flick
    place(fx, thock(), 0.0, 0.55)
    place(low, opening_thump(), 0.0, 0.5)
    w = whoosh(0.22, 7000, 900, q=1.8)
    w[:48] *= cos_in(48)[:, None]
    place(fx, w, 0.0, 0.5)
    for i, t in enumerate(flick_times(0.0, 14, 0.009, 1.13)):
        put_tick(t, 3400 - 60 * i, 0.9 - 0.04 * i, -0.2 + 0.03 * i, bright=1.3 if i == 0 else 1.0)

    # --- momentum flicks: Poisson starts, rate rising from ~2.5/s to ~11/s
    t = 0.18
    while t < last_onset:
        u = t / CALM_T
        f_res = rng.uniform(1700, 5200)
        pan = rng.uniform(-0.9, 0.9)
        n = int(rng.integers(10, 30))
        gap0 = rng.uniform(0.007, 0.018) * (1 - 0.35 * u)
        growth = rng.uniform(1.05, 1.13)
        lev = rng.uniform(0.35, 0.7) * (0.45 + 0.75 * u)
        drift = rng.uniform(-25, 25)
        for i, tk in enumerate(flick_times(t, n, gap0, growth)):
            put_tick(tk, f_res + drift * i, lev * (1 - 0.6 * i / n), pan + 0.01 * i * np.sign(-pan))
        if rng.uniform() < 0.35 + 0.3 * u:
            dur = rng.uniform(0.12, 0.28)
            up = rng.uniform() < 0.5
            fa, fb = rng.uniform(500, 1500), rng.uniform(3500, 8000)
            place(fx, whoosh(dur, fa if up else fb, fb if up else fa), t, 0.24 * (0.5 + 0.8 * u))
        t += rng.exponential(1.0 / (2.5 + 8.5 * u ** 1.4))

    # --- grid ratchet on 110 BPM: 16ths, tightening to 32nds in the last beat, pitch creeping up
    t, i = 0.0, 0
    while t < last_onset:
        sub = BEAT / 8 if t >= CALM_T - BEAT else BEAT / 4
        accent = 1.0 if abs((t / BEAT) - round(t / BEAT)) < 1e-6 else 0.6
        put_tick(t + 0.0005, 2300 * 2 ** (t / CALM_T * 0.7), 0.42 * accent * (0.7 + 0.5 * t / CALM_T),
                 0.15 * (-1) ** i, bright=0.6)
        t += sub
        i += 1

    # --- haptic taps: short low-mid buzz on 8ths, 16ths in the last beat, getting harder
    t = BEAT / 2
    while t < last_onset:
        u = t / CALM_T
        place(fx, haptic(), t, 0.25 + 0.45 * u ** 1.3, pan=rng.uniform(-0.2, 0.2))
        t += BEAT / 4 if t >= CALM_T - BEAT else BEAT / 2

    bed = fizz_bed()

    # --- chaos bus: short bright room, all high-passed; everything stops on the cue sample
    chaos = ticks * 1.0 + fx * 1.0 + bed * 0.13
    chaos = chaos + reverb(ticks * 0.5 + fx * 0.3, rt60=0.35) * 0.25
    chaos = sos_filter(chaos, "highpass", 250, order=4)
    chaos = sos_filter(chaos, "lowpass", 15000, order=4)
    nf = int(0.002 * SR)
    chaos[-nf:] *= cos_in(nf + 1)[::-1][1:][:, None]          # 2 ms fade ending on the cue sample

    # --- calm: the hum (mono below 120 Hz) with a little dark air
    h = hum()
    air = sos_filter(noise(2 * len(h)).reshape(len(h), 2), "bandpass", [200, 900], order=2) * 0.004
    air[: int(0.4 * SR)] *= cos_in(int(0.4 * SR))[:, None]
    calm = sos_filter(h, "highpass", 20, order=2) + air

    mix = low.copy()
    mix[:CALM_S] += chaos
    mix[CALM_S:] += calm
    # mono-ize below 120 Hz (M/S high-pass on the side channel), per section so nothing leaks over the cut
    for a, b in ((0, CALM_S), (CALM_S, N)):
        m_, s_ = (mix[a:b, 0] + mix[a:b, 1]) / 2, (mix[a:b, 0] - mix[a:b, 1]) / 2
        s_ = sos_filter(s_, "highpass", 120, order=4)
        mix[a:b] = np.stack([m_ + s_, m_ - s_], axis=1)

    # final 0.6 s cosine fade so the hum ends in silence
    nt = int(0.6 * SR)
    mix[-nt:] *= cos_in(nt)[::-1][:, None]
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
