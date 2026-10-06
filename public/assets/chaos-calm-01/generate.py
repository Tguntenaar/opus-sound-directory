"""chaos-calm-01: Opus Sound Directory

A 15-second chaos-to-calm bed at 120 BPM that resolves into F major. It opens on
a jarring hit at frame 0: a glitch kick, a burst of noise and a dissonant cluster
of pings. For five seconds, clocks tick at clashing rates (on the beat, every
0.6 s, every 0.43 s, every 0.71 s, plus one that speeds up into the cut). Single
off-key notification pings come in more and more often. Glitchy drums stutter on
a broken sixteenth grid, and a band-passed noise riser climbs underneath. At
frame 150 (5.0 s) everything stops within 3 ms and a soft felt-piano dyad lands
on the downbeat. A warm Fmaj9 pad swells in, and the piece moves through Fmaj9,
Bbmaj9, Dm9, Gm9 and C9sus4 back to Fmaj9. Soft piano-like plucks play a slow
melody, a sine bass and a gentle half-time pulse keep the low end mono, and a
long room reverb carries the last chord. It fades to silence by 15 s.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d

SAMPLE_RATE = 48000
SEED = 150801
DURATION_SEC = 15
BPM = 120
KEY = "chaos -> F major"
FPS = 30
CUE_FRAMES = (0, 150)          # frame 0: opening hit, frame 150: chaos stops, calm begins
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.5 s
STEP = BEAT / 4                # 16th = 0.125 s
CALM_T = CUE_FRAMES[1] / FPS   # 5.0 s
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


# ---------------------------------------------------------------- chaos voices
def clock_tick(f_body: float, dur: float = 0.06) -> np.ndarray:
    """Escapement tick: a 1 ms noise strike into a narrow band-pass plus two inharmonic
    modes of a small metal part (ratio 1 : 2.76), all decaying within ~40 ms."""
    t = tt(dur)
    strike = noise(dur) * np.exp(-t / 0.0012)
    y = sos_filter(strike, "bandpass", [f_body * 0.8, min(f_body * 1.25, 15000)], order=2) * 1.6
    for ratio, amp, dec in ((1.0, 0.55, 0.018), (2.76, 0.25, 0.008)):
        if ratio * f_body < 15000:
            y += amp * np.exp(-t / dec) * np.sin(2 * np.pi * ratio * f_body * t + rng.uniform(0, 2 * np.pi))
    return fade(y * 0.5, a=0.0004, r=0.004)


def ping(midi: float, dur: float = 0.32) -> np.ndarray:
    """Single sine notification ping: tiny upward pitch blip, faint octave partial."""
    t = tt(dur)
    f = hz(midi) * (1 - 0.03 * np.exp(-t / 0.008))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + 0.18 * np.sin(2 * ph)) * np.exp(-t / 0.09)
    return fade(y * 0.4, a=0.001, r=0.02)


def glitch_kick(f_end: float = 50.0, dur: float = 0.22) -> np.ndarray:
    t = tt(dur)
    f = f_end + (190 - f_end) * np.exp(-t / 0.025)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)
    return fade(np.tanh(1.8 * body) / np.tanh(1.8), a=0.0006, r=0.012)


def kick_click(dur: float = 0.02) -> np.ndarray:
    t = tt(dur)
    return fade(sos_filter(noise(dur), "bandpass", [1500, 6000]) * np.exp(-t / 0.003) * 0.35, 0.0004, 0.004)


def snare(dur: float = 0.16, tone: float = 195.0) -> np.ndarray:
    t = tt(dur)
    n = sos_filter(noise(dur), "bandpass", [1200, 7000]) * np.exp(-t / 0.05)
    b = np.sin(2 * np.pi * tone * t) * np.exp(-t / 0.035) * 0.6
    return fade((n + b) * 0.45, a=0.0006, r=0.01)


def hat(dur: float = 0.045) -> np.ndarray:
    t = tt(dur)
    y = sos_filter(sos_filter(noise(dur), "highpass", 7000, order=4), "lowpass", 14500, order=4)
    return fade(y * np.exp(-t / 0.012) * 0.35, a=0.0005, r=0.004)


def glitch_blip(f0: float, dur: float) -> np.ndarray:
    """Band-limited square-ish blip (odd partials only up to 12 kHz) chopped by a
    stepped 'buffer-error' gate."""
    t = tt(dur)
    y = np.zeros_like(t)
    for k in range(1, int(12000 // f0) + 1, 2):
        y += np.sin(2 * np.pi * k * f0 * t) / k
    steps = np.repeat(rng.uniform(0.2, 1.0, int(dur / 0.006) + 2), int(0.006 * SR))[: len(t)]
    steps = np.convolve(steps, np.ones(48) / 48, mode="same")       # de-click the steps
    return fade(y * steps * 0.25, a=0.001, r=0.004)


# ---------------------------------------------------------------- calm voices
def piano(midi: float, dur: float, vel: float = 1.0) -> np.ndarray:
    """Soft felt-piano: two slightly detuned strings, stiff-string inharmonicity,
    upper partials decaying faster (two-stage decay), a muffled hammer thump."""
    t = tt(dur)
    f0 = hz(midi)
    B = 0.00035
    t_long = 2.6 * (440 / f0) ** 0.35
    out = np.zeros((len(t), 2))
    for ch, cents in enumerate((-0.9, 0.9)):
        f = f0 * 2 ** (cents / 1200)
        y = np.zeros_like(t)
        for k in range(1, 40):
            fk = k * f * np.sqrt(1 + B * k * k)
            if fk > 9000:
                break
            amp = k ** -1.15 * np.exp(-(k - 1) * 0.42 / (0.6 + 0.4 * vel))     # felt: dark top
            tk = t_long / (1 + 0.55 * (k - 1))
            env = 0.55 * np.exp(-t / (0.25 * tk)) + 0.45 * np.exp(-t / tk)
            y += amp * env * np.sin(2 * np.pi * fk * t + rng.uniform(0, 2 * np.pi))
        out[:, ch] = y
    thump = sos_filter(noise(dur), "lowpass", 900) * np.exp(-t / 0.006) * 0.25
    out += thump[:, None]
    return fade(out * 0.32 * vel, a=0.0025, r=0.08)


def pad_voice(midi: float, dur: float, att: float, rel: float, cutoff: float = 950.0) -> np.ndarray:
    """Warm detuned saw pad, partials rolled off above `cutoff`, slow per-partial shimmer."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for i, cents in enumerate((-7, -2.5, 2.5, 7)):
        f = hz(midi) * 2 ** (cents / 1200)
        y = np.zeros_like(t)
        for k in range(1, int(7000 // f) + 1):
            a = (1 / k) / (1 + (k * f / cutoff) ** 2)
            lfo = 1 + 0.15 * np.sin(2 * np.pi * rng.uniform(0.08, 0.3) * t + rng.uniform(0, 2 * np.pi))
            y += a * lfo * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
        out[:, i % 2] += y
    env = np.ones_like(t)
    na, nr = int(att * SR), int(rel * SR)
    env[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    env[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return out * env[:, None] * 0.3


def sine_bass(midi: float, dur: float) -> np.ndarray:
    t = tt(dur)
    f = hz(midi)
    y = np.sin(2 * np.pi * f * t) + 0.12 * np.sin(4 * np.pi * f * t)
    env = 1 - np.exp(-t / 0.06)
    return fade(y * env * 0.5, a=0.01, r=0.25)


def soft_pulse() -> np.ndarray:
    """Half-time heartbeat: round low thump, no click."""
    t = tt(0.45)
    f = 46 + 30 * np.exp(-t / 0.04)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
    return fade(y * 0.6, a=0.004, r=0.03)


def brush(dur: float = 0.18) -> np.ndarray:
    t = tt(dur)
    y = sos_filter(noise(dur), "bandpass", [2500, 9000]) * (1 - np.exp(-t / 0.02)) * np.exp(-t / 0.05)
    return fade(y * 0.25, a=0.002, r=0.02)


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
    g = np.convolve(g, np.ones(L + 1) / (L + 1), mode="same")
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
def render_chaos() -> tuple[np.ndarray, np.ndarray]:
    """Returns (chaos bus, chaos low bus); both are silenced from CALM_T on."""
    bus = np.zeros((N, 2))
    low = np.zeros((N, 2))
    send = np.zeros((N, 2))
    end = CALM_T

    # opening hit (frame 0): kick, noise burst, dissonant ping cluster
    place(low, glitch_kick(45, 0.4), 0.0, 1.0)
    place(bus, kick_click(), 0.0, 1.0)
    burst = sos_filter(noise(0.5), "bandpass", [600, 9000]) * np.exp(-tt(0.5) / 0.09)
    place(bus, fade(np.stack([burst, np.roll(burst, 97)], 1) * 0.4, 0.001, 0.05), 0.0)
    for m, p in ((83, -0.5), (84, 0.5), (90, 0.0)):              # B5, C6, F#6: a tritone smear
        place(bus, ping(m, 0.5), 0.0, 0.55, pan=p)
        place(send, ping(m, 0.5), 0.0, 0.3, pan=p)

    # clocks at clashing rates (period s, tick Hz, tock Hz, pan, start)
    clocks = ((0.50, 3200, 2650, -0.65, 0.0), (0.60, 4300, 3700, 0.55, 0.17),
              (0.43, 1900, 1550, -0.25, 0.31), (0.71, 5400, 4800, 0.85, 0.09))
    for period, f1, f2, pan, start in clocks:
        t, i = start, 0
        while t < end - 0.03:
            g = 0.5 + 0.35 * (t / end)
            place(bus, clock_tick(f1 if i % 2 == 0 else f2), t, g * rng.uniform(0.85, 1.0), pan=pan)
            t += period * rng.uniform(0.995, 1.005)
            i += 1
    # a fifth clock spins up into the cut, sweeping across the stereo field
    t, i = 2.2, 0
    while t < end - 0.02:
        x = (t - 2.2) / (end - 2.2)
        place(bus, clock_tick(2900 + 1600 * x), t, 0.45 + 0.4 * x, pan=np.sin(2 * np.pi * 1.3 * t) * 0.8)
        t += 0.32 * (1 - x) + 0.055 * x
        i += 1

    # notification pings: off-key, sparse at first, then piling up
    ping_notes = (83, 84, 86, 88, 90, 92, 95, 82)
    t = 0.35
    while t < end - 0.05:
        dens = 1.5 + 7.0 * (t / end) ** 2
        m = ping_notes[rng.integers(len(ping_notes))]
        p = rng.uniform(-0.8, 0.8)
        g = rng.uniform(0.25, 0.45)
        place(bus, ping(m), t, g, pan=p)
        place(send, ping(m), t, g * 0.5, pan=p)
        t += rng.exponential(1.0 / dens)

    # glitch drums on a broken 16th grid
    kicks = (0, 3, 6, 10, 11, 14)
    snares = (4, 12)
    for s in range(1, int(end / STEP)):
        t = s * STEP
        bar_pos = s % 16
        late = t / end
        if bar_pos in kicks and rng.uniform() < 0.85:
            place(low, glitch_kick(rng.choice([42, 50, 58])), t, 0.85)
            place(bus, kick_click(), t, 0.6)
        if bar_pos in snares or (late > 0.5 and rng.uniform() < 0.12):
            place(bus, snare(), t, 0.65, pan=rng.uniform(-0.2, 0.2))
            place(send, snare(), t, 0.25)
        if rng.uniform() < 0.8:
            place(bus, hat(), t + rng.uniform(0, 0.012), rng.uniform(0.25, 0.45), pan=0.35)
        if rng.uniform() < 0.25 + 0.35 * late:                    # stutter ratchet
            n_r = int(rng.choice([3, 4, 6]))
            for r in range(n_r):
                place(bus, snare(0.05, 195 * 1.12 ** r), t + r * STEP / n_r, 0.32 * (1 - r / (n_r + 1)),
                      pan=0.5 * (-1) ** r)
        if rng.uniform() < 0.18 + 0.3 * late:                     # digital blip
            d = rng.choice([0.03, 0.05, 0.08])
            place(bus, glitch_blip(rng.uniform(300, 1400), d), t + STEP / 2, 0.35, pan=rng.uniform(-0.9, 0.9))

    # band-passed noise riser underneath the last 2.5 s
    rd = 2.5
    tr = tt(rd)
    fc = 400 * (8000 / 400) ** (tr / rd) ** 1.3
    amp = (tr / rd) ** 1.8
    rs = np.stack([svf_bandpass(noise(rd), fc, 3.0), svf_bandpass(noise(rd), fc * 1.05, 3.0)], 1) * amp[:, None]
    place(bus, rs * 0.42, end - rd)

    bus = bus + reverb(send, rt60=0.7, predelay=0.01) * 0.5
    bus = sos_filter(bus, "highpass", 140, order=4)
    low = np.repeat(sos_filter(low.mean(axis=1, keepdims=True), "lowpass", 2500), 2, axis=1)

    # the cut: 3 ms raised-cosine fade that reaches zero exactly on the cue sample
    nf = int(0.003 * SR)
    gate = np.ones(N)
    gate[CALM_S - nf:CALM_S] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf))
    gate[CALM_S:] = 0.0
    return bus * gate[:, None], low * gate[:, None]


def render_calm() -> tuple[np.ndarray, np.ndarray]:
    music = np.zeros((N, 2))
    low = np.zeros((N, 2))
    send = np.zeros((N, 2))
    T = CALM_T
    bar = 4 * BEAT

    # chords per bar (pad voicing, bass midi); Gm9 -> C9sus4 shares bar 3
    chords = [
        (T + 0 * bar, 2 * BEAT * 4, (53, 57, 60, 64, 67), 41),      # Fmaj9  F A C E G
        (T + 1 * bar, bar, (58, 62, 65, 69, 72), 34),              # Bbmaj9 Bb D F A C
        (T + 2 * bar, bar, (53, 57, 60, 62, 64), 38),              # Dm9   F A C D E
        (T + 3 * bar, bar / 2, (55, 58, 62, 65, 69), 31),          # Gm9   G Bb D F A
        (T + 3.5 * bar, bar / 2, (55, 58, 62, 65, 67), 36),        # C9sus4 G Bb D F G (no root in pad)
        (T + 4 * bar, N / SR - T - 4 * bar, (53, 57, 60, 64, 67, 72), 41),  # Fmaj9 home
    ]
    # bar 0 holds Fmaj9 (listed once with a single long voice to avoid re-attacks)
    chords[0] = (T, bar, chords[0][2], 41)
    for i, (t0, d, notes, root) in enumerate(chords):
        att = 0.6 if i == 0 else 0.35
        for m in notes:
            pv = pad_voice(m, d + 0.6, att=att, rel=0.6)
            place(music, pv, t0, 0.15)
            place(send, pv, t0, 0.12)
        place(low, sine_bass(root, d + 0.2), t0 + (0.08 if i == 0 else 0.0), 0.32)

    # felt-piano melody: (beat offset from the cue, midi notes, velocity)
    mel = [
        (0, (65, 72), 1.0), (1.5, (69,), 0.7), (2, (72,), 0.75), (3, (67,), 0.65),
        (4, (65, 74), 0.85), (5.5, (72,), 0.7), (6, (69,), 0.7), (7, (65,), 0.6),
        (8, (69, 76), 0.85), (9.5, (74,), 0.7), (10, (72,), 0.7), (11, (69,), 0.6),
        (12, (70, 74), 0.8), (13.5, (72,), 0.65), (14, (67,), 0.65), (15, (70,), 0.6),
        (16, (65, 69, 72), 0.8), (18, (77,), 0.5), (19.5, (72,), 0.4),
    ]
    for b, notes, v in mel:
        for j, m in enumerate(notes):
            p = piano(m, 3.2, v)
            t = T + b * BEAT + j * 0.012 * (b > 0)                 # gentle roll except on the cue dyad
            place(music, p, t, 0.9)
            place(send, p, t, 0.45)

    # half-time pulse (every 2 beats) and soft brushes, bars 1-3
    for b in range(4, 16, 2):
        place(low, soft_pulse(), T + b * BEAT, 0.45)
    for b in range(4, 16):
        place(music, brush(), T + b * BEAT + BEAT / 2, 0.2, pan=0.3)

    wet = reverb(send, rt60=2.6, predelay=0.03, band=(200, 5000))
    music = sos_filter(music + wet * 0.6, "highpass", 135, order=4)
    low = np.repeat(sos_filter(low.mean(axis=1, keepdims=True), "lowpass", 400), 2, axis=1)
    return music, low


def render() -> np.ndarray:
    chaos, chaos_low = render_chaos()
    music, calm_low = render_calm()
    calm = music + calm_low
    calm[:CALM_S] = 0.0                                             # calm starts on the cue sample
    mix = chaos * 1.35 + chaos_low * 0.8 + calm * 0.5
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 150, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 17000, order=4)
    nf = int(2.0 * SR)                                              # soft ending, exactly 0 at the end
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
