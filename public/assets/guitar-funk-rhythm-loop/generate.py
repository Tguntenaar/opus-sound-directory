"""guitar-funk-rhythm-loop: Opus Sound Directory

A seamless 9.6-second, four-bar funk loop in F# minor at 100 BPM with a light sixteenth
swing, built around two physically modelled clean electric guitars. The rhythm guitar
(bright bridge-position single-coil, firmly compressed, panned left) keeps its picking
hand moving in constant down-up sixteenths: most strokes are fret-hand-muted scratches,
damped strings that die in a few periods under a dry pick click, and the accented strokes
press down into short, staccato ninth-chord stabs, F#m9 (x-9-7-9-9-9) and a B9 with the
root on the low string and the A string muted (7-x-7-8-7-9), each strum rolled across the
strings low-to-high on downstrokes and high-to-low on upstrokes, with a half-step-below
approach stab leading the turnaround back into the top. A second, rounder neck-side
single-coil guitar panned right answers with an original palm-muted single-note riff of
staccato notes, hammer-ons and dead-note ghosts. Underneath sit a syncopated round
finger-style bass with octave pops, ghost notes and a chromatic walk-up into the loop
point, and a minimal tight kit: punchy kick, crisp backbeat snare with ghost strokes and a
small fill in bar four, and accented closed hats. The loop starts with a chord stab, kick
and bass on sample 0 and is rendered circularly (three identical cycles, middle one kept),
so the last sample flows straight back into the first. Only the mono kick and bass sit
below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 1006100
DURATION_SEC = 9.6
BPM = 100
KEY = "F# minor (F#m9 / B9)"
FPS = 30
CUE_FRAMES = (0,)              # loop top: F#m9 stab + kick + bass on sample 0
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))   # one loop cycle = 460800 samples
CYC = 3                             # cycles rendered; the middle one is kept
BEAT = 60.0 / BPM                   # 0.6 s
STEP = BEAT / 4                     # sixteenth = 0.15 s
BAR = 4 * BEAT                      # 2.4 s; 4 bars = 9.6 s
SWING = 0.010                       # odd sixteenths land 10 ms late

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.0005, r: float = 0.005) -> np.ndarray:
    x = x.copy()
    na, nr = min(len(x), max(1, int(a * SR))), min(len(x), max(1, int(r * SR)))
    shp = (-1,) + (1,) * (x.ndim - 1)
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))).reshape(shp)
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))).reshape(shp)
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float | None = None) -> None:
    """Mix a snippet into the CYC-cycle bus at loop time t, once per cycle, so every
    event (and its tail) repeats identically and wraps across the loop point.
    A mono bus takes mono snippets; pan is only used for stereo buses."""
    if bus.ndim == 2 and x.ndim == 1:
        th = ((pan or 0.0) + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)
    t = t % DURATION_SEC
    for k in range(CYC):
        s = int(round(t * SR)) + k * N
        if s >= len(bus):
            continue
        e = min(len(bus), s + len(x))
        bus[s:e] += gain * x[: e - s]


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def peaking_eq(x, f0, gain_db, q):
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * a_, -2 * np.cos(w0), 1 - alpha * a_]
    a = [1 + alpha / a_, -2 * np.cos(w0), 1 - alpha / a_]
    return signal.lfilter(b, a, x, axis=0)


def reso_lowpass(x, f0, q):
    """RBJ resonant low-pass: the pickup coil's inductance against cable capacitance."""
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    c = np.cos(w0)
    b = [(1 - c) / 2, 1 - c, (1 - c) / 2]
    a = [1 + alpha, -2 * c, 1 - alpha]
    return signal.lfilter(b, a, x, axis=0)


def noise(n: int) -> np.ndarray:
    return rng.standard_normal(n)


def slot(bar: int, pos: int) -> float:
    """Loop time of sixteenth `pos` (0..15) in `bar`, with the light swing."""
    return bar * BAR + pos * STEP + (SWING if pos % 2 else 0.0)


# ---------------------------------------------------------------- the string model
def ks_string(f0: float, dur: float, *, t60: float, damp: float, pick_fc: float, vel: float,
              pluck: float, pickup: float, release: float | None = None, rel_tau: float = 0.010,
              scrape: float = 0.0) -> np.ndarray:
    """Extended Karplus-Strong string via one lfilter call.

    Loop = z^-M * first-order Thiran allpass (fractional tuning) * one-zero loss filter
    ((1-damp) + damp z^-1, so upper partials die faster) * per-period gain g (sets T60 of
    the fundamental). Excitation = a pick pulse (one-pole low-passed impulse: brighter for a
    harder/thinner pick) plus a tiny pick-scrape noise burst, both comb-filtered at the
    pluck position (|sin(n pi p)| spectral notches). Output is comb-filtered again at the
    pickup position. `release` = time the fret hand lifts: the string is then choked with a
    ~10 ms exponential and a darker tail (finger flesh damping)."""
    P = SR / f0
    w = 2 * np.pi * f0 / SR
    d_lp = np.arctan2(damp * np.sin(w), (1 - damp) + damp * np.cos(w)) / w
    R = P - d_lp
    M = int(np.floor(R - 0.5))
    d = R - M
    ap = (1 - d) / (1 + d)
    g = np.exp(-6.91 / (f0 * t60))
    a = np.zeros(M + 3)
    a[0] = 1.0
    a[1] += ap
    a[M] -= g * ap * (1 - damp)
    a[M + 1] -= g * (ap * damp + (1 - damp))
    a[M + 2] -= g * damp
    b = np.array([1.0, ap])

    L = int(round(dur * SR))
    exc = np.zeros(L)
    exc[0] = 1.0
    k = np.exp(-2 * np.pi * pick_fc / SR)
    exc = signal.lfilter([1 - k], [1, -k], exc)
    if scrape > 0:
        ns = int(0.0025 * SR)
        sc = noise(ns) * np.hanning(ns) * scrape
        exc[:ns] += sos_filter(sc, "bandpass", [1500, 6500])
    kp = max(1, int(round(pluck * P)))
    exc[kp:] -= exc[:-kp].copy()
    y = signal.lfilter(b, a, exc * vel)
    kq = max(1, int(round(pickup * P)))
    y[kq:] -= y[:-kq].copy()
    if release is not None:
        t = np.arange(L) / SR
        r = np.clip(t - release, 0, None)
        env = np.exp(-r / rel_tau)
        dark = sos_filter(y, "lowpass", 1200)
        mix = np.exp(-r / 0.004)           # brightness goes first as the finger touches
        y = (y * mix + dark * (1 - mix)) * env
    return fade(y, a=0.0002, r=0.004)


def pick_click(vel: float) -> np.ndarray:
    """Dry plectrum tick on the winding: a ~1.5 ms band-passed noise burst."""
    n = int(0.003 * SR)
    t = np.arange(n) / SR
    y = sos_filter(noise(n), "bandpass", [1800, 6000]) * np.exp(-t / 0.0007)
    return fade(y * vel, a=0.0001, r=0.0005)


# ---------------------------------------------------------------- guitar 1: rhythm
# standard tuning, string order low E -> high e; None = string muted by a fretting finger
TUNING = (40, 45, 50, 55, 59, 64)
SHAPES = {
    "F#m9": (None, 54, 57, 64, 68, 73),     # x-9-7-9-9-9
    "B9":   (47, None, 57, 63, 66, 73),     # 7-x-7-8-7-9
    "Fm9":  (None, 53, 56, 63, 67, 72),     # x-8-6-8-8-8 (half-step approach)
}
# per bar: chord + sixteenth pattern. A = accented chord stab (fretted, rings), a = lighter
# stab, x = fret-hand-muted scratch, . = air stroke (misses the strings), - = hold the stab,
# F = approach chord stab
RHYTHM = [
    ("F#m9", "A.xxxxA.xxAxx.xx"),
    ("F#m9", ".xxAxxxa.xxxxx.A"),     # last stroke: B9 anticipation (see below)
    ("B9",   "--xxxxAxxAxxxxAx"),
    ("F#m9", "A.xxxxA.xxAxxxF."),
]


def strum(shape, *, down: bool, kind: str, vel: float, hold: float, n_strings: int | None = None):
    """One strum across the strings: returns (mono signal, offset of its first contact).
    Downstrokes go low->high over all strings; upstrokes catch the top 3-4 strings."""
    order = list(range(6)) if down else list(range(5, -1, -1))
    if not down:
        order = order[: (n_strings or 4)]
    elif n_strings:
        order = order[6 - n_strings:] if kind == "x" else order
    if kind in ("x",) and down:
        order = order[1:] if len(order) == 6 else order       # scratches skip the low E
    spread = (0.016 if kind != "x" else 0.012) * rng.uniform(0.8, 1.2)
    gap = spread / max(1, len(order) - 1)
    dur = hold + 0.12 if kind != "x" else 0.14
    out = np.zeros(int(round((dur + spread + 0.01) * SR)))
    for i, s in enumerate(order):
        midi = shape[s]
        v = vel * rng.uniform(0.82, 1.08) * (0.85 if s == 0 else 1.0)
        off = int(round((i * gap + rng.uniform(-0.0006, 0.0006) * (i > 0)) * SR))
        if midi is None or kind == "x":
            # damped string: fingers rest on it, so it sounds a few periods of a smeared pitch
            base = midi if midi is not None else TUNING[s] + 5
            f = hz(base + rng.uniform(-0.3, 0.3))
            y = ks_string(f, 0.12, t60=rng.uniform(0.045, 0.08), damp=0.42, pick_fc=5200,
                          vel=v * 0.9, pluck=0.11, pickup=0.065, scrape=0.5)
        else:
            f = hz(midi + rng.uniform(-0.04, 0.04))           # a few cents of intonation spread
            y = ks_string(f, dur, t60=2.6 - 0.1 * s, damp=0.08 + 0.02 * (5 - s), pick_fc=4800 + 500 * vel,
                          vel=v, pluck=0.11, pickup=0.065, release=hold, rel_tau=0.012, scrape=0.25)
        y = y + np.pad(pick_click(0.05 * v), (0, max(0, len(y) - int(0.003 * SR))))[: len(y)]
        e = min(len(out), off + len(y))
        out[off:e] += y[: e - off]
    return out


def humanise(dt: float = 0.003) -> float:
    return float(rng.uniform(-dt, dt))


def when(bar: int, pos: int, dt: float) -> float:
    """Humanised event time; the loop-top downbeat stays exactly on sample 0."""
    h = humanise(dt)
    return 0.0 if (bar, pos) == (0, 0) else slot(bar, pos) + h


# ---------------------------------------------------------------- guitar 2: muted single-note riff
# (bar, pos, midi or None for a dead note, kind n=picked / h=hammer-on, length in 16ths)
RIFF = [
    (0, 7, None, "n", 1), (0, 8, 54, "n", 1), (0, 10, 57, "n", 1), (0, 11, 59, "h", 1),
    (0, 12, None, "n", 1), (0, 13, 61, "n", 1), (0, 14, 59, "n", 1), (0, 15, 57, "n", 1),
    (1, 0, 54, "n", 2), (1, 6, None, "n", 1), (1, 7, 52, "n", 1), (1, 8, 54, "h", 1),
    (1, 10, None, "n", 1), (1, 11, 57, "n", 1), (1, 13, 54, "n", 1), (1, 14, None, "n", 1),
    (2, 7, None, "n", 1), (2, 8, 59, "n", 1), (2, 10, 63, "n", 1), (2, 11, 64, "h", 1),
    (2, 12, None, "n", 1), (2, 13, 63, "n", 1), (2, 14, 61, "n", 1), (2, 15, 59, "n", 1),
    (3, 0, 57, "n", 2), (3, 3, None, "n", 1), (3, 7, 54, "n", 1), (3, 8, None, "n", 1),
    (3, 10, 57, "n", 1), (3, 11, None, "n", 1), (3, 12, 61, "n", 1), (3, 13, 59, "h", 1),
]


def riff_note(midi, kind, length, vel):
    hold = length * STEP * 0.72
    if midi is None:
        f = hz(57 + rng.uniform(-1, 1))
        y = ks_string(f, 0.1, t60=0.05, damp=0.45, pick_fc=3800, vel=vel * 0.8, pluck=0.16,
                      pickup=0.19, scrape=0.6)
    else:
        soft = kind == "h"
        y = ks_string(hz(midi), hold + 0.08, t60=0.22, damp=0.5, pick_fc=1200 if soft else 2200,
                      vel=vel * (0.7 if soft else 1.0), pluck=0.16, pickup=0.19, release=hold,
                      rel_tau=0.015, scrape=0.0 if soft else 0.3)
    if kind != "h":
        y[: int(0.003 * SR)] += pick_click(0.04 * vel)
    return y


# ---------------------------------------------------------------- bass
# (bar, pos, midi, length in 16ths, kind n / p=pop / g=ghost)
BASS = [
    (0, 0, 30, 2.0, "n"), (0, 3, 30, 0.6, "g"), (0, 6, 42, 0.7, "p"), (0, 7, 40, 1.0, "n"),
    (0, 10, 30, 2.0, "n"), (0, 13, 33, 0.8, "n"), (0, 14, 35, 1.5, "n"),
    (1, 0, 30, 1.5, "n"), (1, 2, 30, 0.5, "g"), (1, 5, 42, 0.7, "p"), (1, 6, 40, 1.0, "n"),
    (1, 8, 37, 1.5, "n"), (1, 10, 30, 1.5, "n"), (1, 13, 33, 0.8, "n"), (1, 14, 34, 0.8, "n"),
    (2, 0, 35, 2.0, "n"), (2, 3, 35, 0.6, "g"), (2, 6, 47, 0.6, "p"), (2, 7, 45, 1.0, "n"),
    (2, 10, 35, 1.5, "n"), (2, 13, 37, 0.8, "n"), (2, 14, 39, 1.0, "n"),
    (3, 0, 30, 1.5, "n"), (3, 3, 30, 0.6, "g"), (3, 6, 42, 0.6, "p"), (3, 7, 40, 0.8, "n"),
    (3, 8, 37, 1.0, "n"), (3, 10, 33, 1.0, "n"), (3, 12, 35, 1.0, "n"), (3, 14, 28, 0.9, "n"),
    (3, 15, 29, 0.9, "n"),
]


def bass_note(midi, length, kind, vel):
    hold = length * STEP * 0.9
    if kind == "g":
        return ks_string(hz(midi), 0.12, t60=0.06, damp=0.4, pick_fc=900, vel=vel * 0.7, pluck=0.22,
                         pickup=0.22)
    pop = kind == "p"
    return ks_string(hz(midi), hold + 0.1, t60=1.0 if pop else 2.4, damp=0.2 if pop else 0.42,
                     pick_fc=2500 if pop else 500, vel=vel, pluck=0.08 if pop else 0.24,
                     pickup=0.2, release=hold, rel_tau=0.02)


# ---------------------------------------------------------------- drums
def kick() -> np.ndarray:
    t = tt(0.26)
    f = 50 + (140 - 50) * np.exp(-t / 0.02)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)
    beater = sos_filter(noise(len(t)), "bandpass", [1500, 5000]) * np.exp(-t / 0.0025) * 0.25
    return fade(np.tanh(1.6 * (body + beater)) / np.tanh(1.6), a=0.0003, r=0.01)


def snare(vel: float = 1.0, ghost: bool = False) -> np.ndarray:
    d = 0.1 if ghost else 0.22
    t = tt(d)
    tone = (np.sin(2 * np.pi * 205 * t) + 0.45 * np.sin(2 * np.pi * 345 * t)) * np.exp(-t / 0.035)
    nz = sos_filter(noise(len(t)), "bandpass", [1800, 9500]) * np.exp(-t / (0.03 if ghost else 0.075))
    crack = sos_filter(noise(len(t)), "highpass", 2500) * np.exp(-t / 0.003)
    y = 0.6 * tone + 0.9 * nz + 0.45 * crack
    return fade(y * vel * (0.16 if ghost else 0.5), a=0.0003, r=0.008)


def hat(vel: float) -> np.ndarray:
    d = 0.045
    t = tt(d)
    y = sos_filter(noise(len(t)), "highpass", 7000, order=4)
    y = sos_filter(y, "lowpass", 14000, order=4)
    y *= np.exp(-t / 0.011)
    return fade(y * 0.25 * vel, a=0.0003, r=0.004)


KICKS = [(0, 3, 10), (0, 7, 10), (0, 3, 10), (0, 7, 10, 14)]
GHOSTS = [(9,), (6, 15), (9, 11), (13, 14, 15)]


def reverb(x: np.ndarray, rt60: float, band=(300, 6000), predelay: float = 0.006) -> np.ndarray:
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60) * (1 - np.exp(-t / 0.003))
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", list(band)) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, i], irs[i])[: len(x)] for i in range(2)], axis=1)


# ---------------------------------------------------------------- guitar rig
def compressor(x: np.ndarray, thr_db: float, ratio: float, att: float, rel: float) -> np.ndarray:
    """Feed-forward peak compressor (0.5 ms control rate, attack/release ballistics),
    run over the whole periodic buffer so its gain curve is itself periodic."""
    hop = 24
    nb = len(x) // hop
    pk = np.abs(x[: nb * hop]).reshape(nb, hop).max(axis=1)
    lv = 20 * np.log10(pk + 1e-9)
    over = np.maximum(0.0, lv - thr_db)
    target = -over * (1 - 1 / ratio)
    ca, cr = np.exp(-hop / (att * SR)), np.exp(-hop / (rel * SR))
    gr = np.empty(nb)
    prev = 0.0
    for i, tg in enumerate(target.tolist()):
        c = ca if tg < prev else cr
        prev = tg + c * (prev - tg)
        gr[i] = prev
    g = np.interp(np.arange(len(x)), np.arange(nb) * hop + hop / 2, 10 ** (gr / 20))
    return x * g


def amp(x: np.ndarray, drive: float, bias: float) -> np.ndarray:
    """Clean tube-ish preamp: 4x-oversampled asymmetric tanh, just touching the curve."""
    up = signal.resample_poly(x, 4, 1)
    y = (np.tanh(drive * (up + bias)) - np.tanh(drive * bias)) / drive
    return signal.resample_poly(y, 1, 4)[: len(x)]


def guitar_rig(x: np.ndarray, *, pickup_f: float, pickup_q: float, thr: float, ratio: float,
               drive: float, bright: float) -> np.ndarray:
    x = reso_lowpass(x, pickup_f, pickup_q)
    x = compressor(x, thr, ratio, 0.002, 0.07)
    x = sos_filter(x, "highpass", 90)
    x = amp(x, drive, 0.12)
    x = peaking_eq(x, 450, -3.0, 0.9)               # tone stack: slight mid scoop
    x = peaking_eq(x, 2600, bright, 1.0)            # presence
    # 1x12 open-back cab: resonance + steep top roll-off (no fizz above ~7 kHz)
    x = peaking_eq(x, 1900, 2.0, 1.4)
    x = sos_filter(x, "lowpass", 5800, order=4)
    x = sos_filter(x, "highpass", 140, order=2)
    return x


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 80.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak, with wrap-around
    windows so the kept middle cycle has a periodic gain curve."""
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
def render() -> np.ndarray:
    L = CYC * N
    g1 = np.zeros(L)           # rhythm guitar (mono DI before the rig)
    g2 = np.zeros(L)           # riff guitar
    low = np.zeros(L)          # bass + kick, mono
    drums = np.zeros((L, 2))
    send = np.zeros((L, 2))

    # ---- guitar 1: constant down-up sixteenth motion
    for b, (chord, pat) in enumerate(RHYTHM):
        for p, sym in enumerate(pat):
            if sym in ".-":
                continue
            down = p % 2 == 0
            t = when(b, p, 0.003)
            if sym in "AaF":
                shape = SHAPES["Fm9" if sym == "F" else chord]
                if b == 1 and p == 15:
                    shape = SHAPES["B9"]                       # anticipates bar 3
                n_hold = 1
                while p + n_hold < 16 and pat[p + n_hold] == "-":
                    n_hold += 1
                if b == 1 and p == 15:
                    n_hold += 2                                # tied over the bar line
                hold = n_hold * STEP * 0.8
                vel = {"A": 1.0, "a": 0.75, "F": 0.8}[sym]
                y = strum(shape, down=down, kind=sym, vel=vel, hold=hold, n_strings=None if down else 4)
            else:
                accent = 1.0 if p in (4, 12) else (0.85 if down else 0.7)
                y = strum(SHAPES[chord], down=down, kind="x", vel=0.55 * accent * rng.uniform(0.9, 1.1),
                          hold=0.0, n_strings=5 if down else 3)
            place(g1, y, t)

    # ---- guitar 2: palm-muted single-note answer
    for b, p, midi, kind, length in RIFF:
        vel = rng.uniform(0.85, 1.05) * (0.7 if midi is None else 1.0)
        place(g2, riff_note(midi, kind, length, vel), when(b, p, 0.004))

    # ---- bass
    for b, p, midi, length, kind in BASS:
        vel = {"n": 1.0, "p": 0.9, "g": 0.7}[kind] * rng.uniform(0.92, 1.05)
        t = when(b, p, 0.003)
        place(low, bass_note(midi, length, kind, vel), t, 1.0)

    # ---- drums
    kk = np.zeros(L)
    for b in range(4):
        for p in KICKS[b]:
            place(kk, kick(), when(b, p, 0.002), 0.9 if p == 0 else 0.75)
        for p in (4, 12):
            sn = snare(rng.uniform(0.95, 1.05))
            t = when(b, p, 0.002)
            place(drums, sn, t, 1.0, pan=0.0)
            place(send, sn, t, 0.35, pan=0.0)
        for i, p in enumerate(GHOSTS[b]):
            v = 0.7 + 0.15 * i if b == 3 else rng.uniform(0.7, 1.0)
            place(drums, snare(v, ghost=True), when(b, p, 0.004), 1.0, pan=0.05)
        for p in range(16):
            v = (1.0 if p % 4 == 0 else 0.75 if p % 2 == 0 else 0.45) * rng.uniform(0.85, 1.1)
            if p in (4, 12):
                v *= 0.7
            place(drums, hat(v), when(b, p, 0.003), 1.0, pan=0.3)

    # ---- guitar rigs (on the periodic 3-cycle buffer)
    g1 = guitar_rig(g1, pickup_f=4300, pickup_q=1.6, thr=-14, ratio=4.0, drive=2.2, bright=3.0)
    g2 = guitar_rig(g2, pickup_f=2800, pickup_q=1.0, thr=-18, ratio=3.0, drive=2.6, bright=0.5)
    g1 /= np.sqrt(np.mean(g1 ** 2)) + 1e-12
    g2 /= np.sqrt(np.mean(g2 ** 2)) + 1e-12

    def pan2(sig, pan, gain):
        th = (pan + 1) * np.pi / 4
        return np.stack([sig * np.cos(th), sig * np.sin(th)], axis=1) * np.sqrt(2) * gain

    gtr_g1, gtr_g2 = pan2(g1, -0.5, 1.0), pan2(g2, 0.55, 0.65)
    gtr = gtr_g1 + gtr_g2
    send += gtr * 0.25

    low = sos_filter(low, "lowpass", 1400, order=4)
    low = np.tanh(1.3 * low / (np.max(np.abs(low)) + 1e-9)) / np.tanh(1.3)
    low = compressor(low, -10, 3.0, 0.004, 0.09)
    low /= np.sqrt(np.mean(low ** 2)) + 1e-12
    kk /= np.sqrt(np.mean(kk ** 2)) + 1e-12
    drums /= np.sqrt(np.mean(drums ** 2)) + 1e-12

    wet = sos_filter(reverb(send, rt60=0.45), "highpass", 250, order=4)
    mono = (low * 0.42 + kk * 0.38)[:, None]
    mix = gtr * 0.20 + drums * 0.12 + np.repeat(mono, 2, axis=1) * 0.5 + wet * 0.10

    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
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
