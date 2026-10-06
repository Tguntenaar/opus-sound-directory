"""ad-bed-30-lifestyle: Opus Sound Directory

A relaxed 30-second lifestyle stroll in G major at 105 BPM with a light swing, for a
sunny everyday-product ad. It opens on a warm nylon-string strum of Gmaj9 at frame 0
with a soft kick and the bass. Two bars of Karplus-Strong fingerpicking follow
through the sunny Gmaj9-Cmaj9-Em9-D6/9 loop. In bars 3-4 a round finger bass, a
soft kick and lightly swung hats join. Bars 5-8 open up with a side-stick on 2 and
4, a swung shaker, a soft pad and a singing high-string melody. A three-beat
turnaround bar (Am9 to D9sus) pushes and stops for a breath. The end tag then lands
exactly on frame 600 (20.0 s): a bright Gmaj9 strum, kick, bass and a rising
three-note motif. The groove thins out over three gentle bars, and a final Gmaj9
strum with a high echo of the motif rings out to silence. Only the kick and bass
sit below 120 Hz, in mono. The bed is softly scooped around 2.5 kHz so a voiceover
sits on top.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 105030
DURATION_SEC = 30
BPM = 105
KEY = "G major"
FPS = 30
CUE_FRAMES = (0, 600)          # frame 0: opening strum, frame 600: end tag
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.5714 s
BAR = 4 * BEAT                 # 2.2857 s
SWING = 0.62                   # off-beat 8th lands at 62 % of the beat (light swing)
TAG_T = CUE_FRAMES[1] / FPS    # 20.0 s = 35 beats = 8 bars of 4 + one 3-beat turnaround bar
BREAK_T = 8 * BAR              # 18.286 s
CHOKE_END = TAG_T - 0.060      # 60 ms breath before the tag

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi):
    return 440.0 * 2 ** ((np.asarray(midi, dtype=float) - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Raised-cosine attack/release so nothing starts or stops with a click."""
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    ea = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    er = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    if x.ndim == 2:
        ea, er = ea[:, None], er[:, None]
    x[:na] *= ea
    x[-nr:] *= er
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


def peaking_eq(x, f0, gain_db, q):
    """RBJ cookbook peaking biquad."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * a_, -2 * np.cos(w0), 1 - alpha * a_]
    a = [1 + alpha / a_, -2 * np.cos(w0), 1 - alpha / a_]
    return signal.lfilter(b, a, x, axis=0)


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


def swung(beat: float) -> float:
    """Map a straight beat position to its swung position (8th-note swing)."""
    k = np.floor(beat)
    f = beat - k
    return float(k + (f / 0.5 * SWING if f < 0.5 else SWING + (f - 0.5) / 0.5 * (1 - SWING)))


def T(bar: int, beat: float) -> float:
    """Main section time (bars 0-8 from 0 s)."""
    return bar * BAR + swung(beat) * BEAT


def TG(bar: int, beat: float) -> float:
    """End-tag section time (bars counted from frame 600)."""
    return TAG_T + bar * BAR + swung(beat) * BEAT


# ---------------------------------------------------------------- voices
def ks_string(midi: float, dur: float, vel: float = 1.0, bright: float = 0.22,
              t60: float = 2.6, pos: float = 0.18) -> np.ndarray:
    """Karplus-Strong nylon string, vectorised one period at a time.
    Loop filter = 3-tap damping low-pass [b, 1-2b, b] convolved with a linear
    fractional delay, so every tap sits at >= L samples and a whole period can be
    computed per numpy step. A soft, low-passed thumb-like excitation with a
    pluck-position comb gives the warm nylon tone."""
    f0 = float(hz(midi))
    D = SR / f0
    L = int(np.floor(D - 1.0))
    p = D - 1.0 - L
    b = bright * 0.5
    h = np.convolve([b, 1 - 2 * b, b], [1 - p, p])        # taps at delays L..L+3
    g = 10 ** (-3.0 / (f0 * t60))                          # per-period loss for the T60
    n = int(round(dur * SR))
    exc = noise((L + 4) / SR)
    a = 0.55 - 0.25 * vel                                  # softer pluck = darker
    exc = signal.lfilter([1 - a], [1, -a], exc)
    k = max(1, int(pos * L))
    exc = exc - np.roll(exc, k)
    exc *= np.hanning(len(exc)) ** 0.5
    exc /= np.max(np.abs(exc)) + 1e-12
    H = L + 3
    y = np.zeros(H + n)
    y[H:H + min(n, len(exc))] += exc[:n]
    for s in range(H, H + n, L):
        e = min(s + L, H + n)
        idx = np.arange(s, e)
        y[idx] += g * (h[0] * y[idx - L] + h[1] * y[idx - L - 1] + h[2] * y[idx - L - 2] + h[3] * y[idx - L - 3])
    y = y[H:]
    # nylon body: a little air at ~220 Hz and ~480 Hz, soft top
    y = peaking_eq(y, 220, 3.0, 1.2)
    y = peaking_eq(y, 480, 1.5, 1.5)
    y = sos_filter(y, "lowpass", 6500, order=2)
    return fade(y * 1.2 * vel, a=0.0012, r=0.04)


def strum(chord, dur: float, vel: float = 1.0, spread: float = 0.013, bright: float = 0.22):
    """Downstroke strum (low to high, first string exactly at t=0), stereo spread."""
    n = int(round(dur * SR))
    out = np.zeros((n, 2))
    for i, m in enumerate(chord):
        off = int(round(i * spread * SR))
        v = vel * (0.85 + 0.15 * i / max(1, len(chord) - 1)) * rng.uniform(0.92, 1.05)
        s = ks_string(m, (n - off) / SR, v, bright=bright, t60=2.8)
        pan = -0.45 + 0.9 * i / max(1, len(chord) - 1)
        th = (pan + 1) * np.pi / 4
        out[off:, 0] += s * np.cos(th) * np.sqrt(2)
        out[off:, 1] += s * np.sin(th) * np.sqrt(2)
    return out * 0.55


def bass_note(midi: float, dur: float, vel: float = 1.0) -> np.ndarray:
    """Round finger bass: sine + soft 2nd/3rd harmonic, thumb-pluck envelope."""
    t = tt(dur)
    f = float(hz(midi))
    y = np.sin(2 * np.pi * f * t) + 0.28 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
    env = 0.55 * np.exp(-t / 0.12) + 0.45 * np.exp(-t / 0.9)
    return fade(y * env * 0.6 * vel, a=0.004, r=0.04)


def kick(vel: float = 1.0) -> np.ndarray:
    t = tt(0.32)
    f = 50 + (125 - 50) * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    thump = sos_filter(noise(0.32), "bandpass", [400, 1800]) * np.exp(-t / 0.004) * 0.12
    return fade(np.tanh(1.3 * (body + thump)) / np.tanh(1.3) * vel, a=0.001, r=0.02)


def side_stick(vel: float = 1.0) -> np.ndarray:
    """Woody side-stick: two short resonant modes + a tiny band-passed click."""
    t = tt(0.12)
    y = np.sin(2 * np.pi * 1650 * t) * np.exp(-t / 0.012) * 0.6
    y += np.sin(2 * np.pi * 520 * t) * np.exp(-t / 0.022) * 0.8
    y += sos_filter(noise(0.12), "bandpass", [1500, 5000]) * np.exp(-t / 0.003) * 0.5
    return fade(y * 0.35 * vel, a=0.0008, r=0.01)


def hat(vel: float = 1.0, open_: bool = False) -> np.ndarray:
    d = 0.16 if open_ else 0.05
    t = tt(d)
    y = sos_filter(noise(d), "bandpass", [6500, 13000], order=2)
    y *= np.exp(-t / (0.05 if open_ else 0.013))
    return fade(y * 0.22 * vel, a=0.001, r=0.006)


def shaker(vel: float = 1.0) -> np.ndarray:
    """Soft shaker: band-passed noise with a ~10 ms swell (beads), not a click."""
    t = tt(0.09)
    env = (1 - np.exp(-t / 0.008)) * np.exp(-t / 0.028)
    y = sos_filter(noise(0.09), "bandpass", [4500, 11000], order=2) * env
    return fade(y * 0.30 * vel, a=0.003, r=0.01)


def pad_voice(midi: float, dur: float, att: float = 0.5, rel: float = 0.6) -> np.ndarray:
    """Warm detuned additive pad, harmonics rolled off above ~1.2 kHz."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for ch, cents in enumerate((-7, -2, 2, 7)):
        f = float(hz(midi)) * 2 ** (cents / 1200)
        y = np.zeros_like(t)
        for k in range(1, int(6000 // f) + 1):
            a = (1 / k) / (1 + (k * f / 1200) ** 2)
            y += a * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
        out[:, ch % 2] += y
    env = np.ones_like(t)
    na, nr = int(att * SR), int(rel * SR)
    env[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    env[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return out * env[:, None] * 0.25


def cymbal_swell(dur: float) -> np.ndarray:
    t = tt(dur)
    env = (t / dur) ** 2.5
    l = sos_filter(noise(dur), "bandpass", [3000, 11000]) * env
    r = sos_filter(noise(dur), "bandpass", [3000, 11000]) * env
    return fade(np.stack([l, r], axis=1) * 0.18, 0.05, 0.02)


def reverb(x: np.ndarray, rt60: float = 1.6, predelay: float = 0.02, band=(200, 6000)) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (warm room)."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", list(band)) * env
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
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. The gain is
    held over the look-ahead window, released by a one-pole, then box-smoothed."""
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


# ---------------------------------------------------------------- harmony
GMAJ9 = (55, 62, 66, 69, 71)   # G3 D4 F#4 A4 B4
CMAJ9 = (52, 59, 62, 64, 67)   # E3 B3 D4 E4 G4   (bass plays C)
EM9 = (52, 59, 62, 66, 67)     # E3 B3 D4 F#4 G4
D69 = (54, 57, 62, 64, 69)     # F#3 A3 D4 E4 A4
AM9 = (55, 60, 64, 67, 71)     # G3 C4 E4 G4 B4   (bass plays A)
D9SUS = (55, 57, 60, 64, 69)   # G3 A3 C4 E4 A4   (bass plays D)
G_STRUM = (55, 59, 62, 66, 69, 74)   # G3 B3 D4 F#4 A4 D5
LOOP = [(GMAJ9, 43), (CMAJ9, 48), (EM9, 40), (D69, 38)]   # (voicing, bass root)
PICK = [(0, 3), (2,), (1,), (4,), (0, 2), (3,), (1,), (2,)]  # Travis-ish 8th pattern


def render() -> np.ndarray:
    g = {k: np.zeros((N, 2)) for k in ("low", "drums", "gtr", "lead", "pad", "fx", "send")}
    h = {k: np.zeros((N, 2)) for k in ("low", "drums", "gtr", "lead", "pad", "fx", "send")}

    def pick_bar(bus, tf, bar, chord, vel, density=8, skip_first=False):
        for i, voices in enumerate(PICK[:density] if density == 8 else PICK[:density]):
            if skip_first and i == 0:
                continue
            for j, vi in enumerate(voices):
                m = chord[vi]
                v = vel * (1.0 if i % 2 == 0 else 0.78) * (0.85 if j else 1.0) * rng.uniform(0.9, 1.06)
                s = ks_string(m, 1.6, v, bright=0.22, t60=1.9)
                pan = -0.35 + 0.7 * vi / 4
                place(bus["gtr"], s, tf(bar, i * 0.5) + j * 0.004, 0.62, pan)
                place(bus["send"], s, tf(bar, i * 0.5), 0.16, pan)

    def bass_bar(bus, tf, bar, root, nxt, vel=1.0, sparse=False):
        five = root + 7
        notes = [(0, root, 1.3), (1.5, root, 0.3), (2, five, 0.9), (3, root + 12 if root < 40 else root, 0.45),
                 (3.5, nxt - 1 if nxt > root else nxt + 2, 0.3)]
        if sparse:
            notes = [(0, root, 1.8), (2, five, 1.6)]
        for beat, m, ln in notes:
            place(bus["low"], bass_note(m, ln * BEAT), tf(bar, beat), 0.62 * vel)

    def drums_bar(bus, tf, bar, level):
        """level 1: kick + hats, 2: + side-stick + shaker, 3 (outro): hats + shaker only."""
        if level in (1, 2):
            for beat, v in ((0, 1.0), (1.5, 0.55), (2, 0.85)):
                place(bus["low"], kick(v), tf(bar, beat), 0.8)
        for i in range(8):
            beat = i * 0.5
            v = (0.9 if i % 2 else 0.55) * rng.uniform(0.85, 1.1)
            if level == 3 and i % 2 == 0:
                continue
            place(bus["drums"], hat(v, open_=(i == 7 and level == 2)), tf(bar, beat), 0.65, pan=0.35)
        if level == 2:
            for beat in (1, 3):
                place(bus["drums"], side_stick(), tf(bar, beat), 0.7, pan=-0.1)
                place(bus["send"], side_stick(), tf(bar, beat), 0.25)
        if level in (2, 3):
            for i in range(8):
                v = (1.0 if i % 2 else 0.6) * rng.uniform(0.85, 1.1) * (0.7 if level == 3 else 1.0)
                place(bus["drums"], shaker(v), tf(bar, i * 0.5), 0.55, pan=-0.4)

    # ---------------- frame 0: opening strum + kick + bass
    st = strum(G_STRUM, 3.0, vel=1.0)
    place(g["gtr"], st, 0.0, 0.9)
    place(g["send"], st, 0.0, 0.25)
    place(g["low"], kick(0.8), 0.0, 0.8)
    place(g["low"], bass_note(43, 1.6 * BEAT), 0.0, 0.55)

    # ---------------- bars 0-7: intro (0-1), groove (2-3), full with melody (4-7)
    for bar in range(8):
        chord, root = LOOP[bar % 4]
        nxt = LOOP[(bar + 1) % 4][1]
        vel = 0.75 if bar < 2 else 0.9 if bar < 4 else 1.0
        pick_bar(g, T, bar, chord, vel, skip_first=(bar == 0))
        if bar >= 2:
            bass_bar(g, T, bar, root, nxt)
            drums_bar(g, T, bar, 1 if bar < 4 else 2)
        elif bar == 1:
            for i in range(8):     # hint of hats in bar 2 of the intro
                if i % 2:
                    place(g["drums"], hat(0.6), T(bar, i * 0.5), 0.5, pan=0.35)
        if bar >= 4:
            for m in chord[1:4]:
                pv = pad_voice(m + 12 if m < 60 else m, BAR + 0.5)
                place(g["pad"], pv, T(bar, 0), 0.30)
    place(g["fx"], cymbal_swell(BAR), T(3, 0), 0.8)          # into the full section

    # melody, bars 4-7 (beats in straight terms; swing is applied by T)
    mel = [(4, 0, 74, 1.0), (4, 1, 71, .5), (4, 1.5, 74, .5), (4, 2, 76, 1.5), (4, 3.5, 74, .5),
           (5, 0, 79, 1.0), (5, 1, 76, .5), (5, 1.5, 74, .5), (5, 2, 71, 1.5), (5, 3.5, 69, .5),
           (6, 0, 71, .5), (6, 0.5, 74, .5), (6, 1, 76, 1.0), (6, 2, 79, .5), (6, 2.5, 78, .5), (6, 3, 76, 1.0),
           (7, 0, 78, 1.5), (7, 1.5, 76, .5), (7, 2, 74, 1.0), (7, 3, 69, 1.0)]
    for bar, beat, m, ln in mel:
        s = ks_string(m, max(1.2, ln * BEAT + 0.8), 1.0, bright=0.16, t60=1.6, pos=0.12)
        place(g["lead"], s, T(bar, beat), 0.62, 0.15)
        place(g["send"], s, T(bar, beat), 0.3, 0.15)

    # ---------------- break bar (3 beats): Am9 push, D9sus push, stop for a breath
    place(g["gtr"], strum(AM9, 1.4, 0.95), T(8, 0), 0.85)
    place(g["gtr"], strum(D9SUS, 1.2, 1.0), T(8, 1.5), 0.85)
    place(g["low"], kick(0.9), T(8, 0), 0.8)
    place(g["low"], bass_note(45, 1.4 * BEAT), T(8, 0), 0.62)
    place(g["low"], kick(0.7), T(8, 1.5), 0.8)
    place(g["low"], bass_note(38, 1.3 * BEAT), T(8, 1.5), 0.62)
    for i, beat in enumerate((2.0, 2.5)):                    # two side-stick pickups into the tag
        place(g["drums"], side_stick(0.7 + 0.2 * i), T(8, beat), 0.7, pan=-0.1)
    for i in range(5):
        place(g["drums"], hat(0.7), T(8, i * 0.5), 0.6, pan=0.35)
    place(g["fx"], cymbal_swell(CHOKE_END - T(8, 1.0)), T(8, 1.0), 0.9)

    # ---------------- frame 600: the end tag
    st = strum(G_STRUM + (79,), 3.2, vel=1.1, bright=0.26)
    place(h["gtr"], st, TAG_T, 1.0)
    place(h["send"], st, TAG_T, 0.3)
    place(h["low"], kick(1.0), TAG_T, 0.85)
    place(h["low"], bass_note(43, 2.5 * BEAT), TAG_T, 0.65)
    for beat, m in ((0.5, 71), (1.0, 74), (1.5, 79)):        # rising tag motif B-D-G
        s = ks_string(m, 2.0, 1.0, bright=0.15, t60=2.2, pos=0.12)
        place(h["lead"], s, TG(0, beat), 0.7, 0.2)
        place(h["send"], s, TG(0, beat), 0.35, 0.2)
    for m in (62, 66, 69, 71):
        pv = pad_voice(m, 3 * BAR, att=0.25, rel=1.5)
        place(h["pad"], pv, TAG_T, 0.32)
    # tag bars 1-3: thinning groove (Cmaj9, Am9 | D9sus), then the final strum
    pick_bar(h, TG, 0, GMAJ9, 0.75, skip_first=True)
    drums_bar(h, TG, 0, 3)
    pick_bar(h, TG, 1, CMAJ9, 0.8)
    bass_bar(h, TG, 1, 48, 45, 0.9, sparse=True)
    drums_bar(h, TG, 1, 3)
    for i, (ch, root) in enumerate(((AM9, 45), (D9SUS, 38))):
        for k, voices in enumerate(PICK[:4]):
            for vi in voices:
                s = ks_string(ch[vi], 1.6, 0.7 * (1.0 if k % 2 == 0 else 0.8), t60=1.9)
                place(h["gtr"], s, TG(2, 2 * i + k * 0.5), 0.6, -0.35 + 0.7 * vi / 4)
                place(h["send"], s, TG(2, 2 * i + k * 0.5), 0.16)
        place(h["low"], bass_note(root, 1.8 * BEAT, 0.85), TG(2, 2 * i), 0.62)
    for i in range(8):
        if i % 2:
            place(h["drums"], shaker(0.5), TG(2, i * 0.5), 0.5, pan=-0.4)
    end_t = TG(3, 0)                                          # 26.857 s
    st = strum(G_STRUM, N / SR - end_t, vel=0.9, spread=0.022)
    place(h["gtr"], st, end_t, 0.85)
    place(h["send"], st, end_t, 0.35)
    place(h["low"], bass_note(43, 2.4), end_t, 0.55)
    place(h["low"], kick(0.6), end_t, 0.8)
    for beat, m in ((1.0, 83), (1.5, 86), (2.0, 91)):        # high echo of the motif
        s = ks_string(m, 2.2, 0.7, bright=0.14, t60=2.0, pos=0.1)
        place(h["lead"], s, TG(3, beat), 0.45, -0.25)
        place(h["send"], s, TG(3, beat), 0.4, -0.25)

    # ---------------- buses
    def bus_mix(d):
        hp = lambda x, f=130: sos_filter(x, "highpass", f, order=4)
        gtr = peaking_eq(hp(d["gtr"]), 2500, -2.5, 0.9)                # VO pocket
        lead = peaking_eq(hp(d["lead"], 200), 2500, -1.5, 0.9)
        pad = sos_filter(hp(d["pad"], 160), "lowpass", 3500, order=2)
        wet = hp(reverb(d["send"], rt60=1.7), 160) * 0.55
        low = np.repeat(d["low"].mean(axis=1, keepdims=True), 2, axis=1)
        return low * 0.55 + hp(d["drums"], 300) + gtr * 1.4 + lead * 1.2 + pad + hp(d["fx"], 300) + wet

    groove = bus_mix(g)
    tag = bus_mix(h)
    ch = np.ones(N)
    c1 = int(round(CHOKE_END * SR))
    c0 = c1 - int(0.060 * SR)
    ch[c0:c1] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, c1 - c0))
    ch[c1:] = 0.0
    mix = groove * ch[:, None] + tag

    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 120, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 25, order=2)
    mix = sos_filter(mix, "lowpass", 16000, order=4)
    nf = int(1.2 * SR)                                         # final ring-out to silence
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    # remove residual DC with a sub-1 Hz Hann-shaped offset (ends stay at zero)
    w = np.hanning(N)
    y = y - (y.sum(axis=0) / w.sum())[None, :] * w[:, None]
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
