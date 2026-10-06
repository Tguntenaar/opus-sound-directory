"""ad-bed-6-bumper: Opus Sound Directory

A 6-second cold-open bumper in F# minor at 140 BPM. It slams in at frame 0 with
a kick, a crash, a short F# minor brass stab and the first note of a gritty saw
bass hook, so the hook is there from the very first sample. Two bars of
breakbeat drums follow (syncopated kicks, a cracking snare on 2 and 4 with ghost
notes, tight hats) under the bass riff (F#-A-B-C#), with punchy brass-like
stabs answering on the i-VI-VII chords (F#m, D, E). A half bar of octave-pumping
bass ramps the energy. A five-stroke triplet snare fill then rides over a noise
riser, a swelling E-major brass chord and the bass gliding up an octave. Everything
chokes into a 40 ms air gap, and the big hit lands exactly on frame 150 (5.0 s):
a sub-dropping kick, the F# bass, a wide F# minor brass chord that falls off in
pitch, a crash and snare, ringing out over a short room tail to silence by 6 s.
Only the kick and bass live below 120 Hz, in mono.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 140006
DURATION_SEC = 6
BPM = 140
KEY = "F# minor"
FPS = 30
CUE_FRAMES = (0, 150)          # frame 0: cold-open hit, frame 150: the big hit
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.428571 s
S16 = BEAT / 4                 # sixteenth
TRIP = BEAT / 3                # eighth-note triplet
HIT_T = CUE_FRAMES[1] / FPS    # 5.0 s  (= 35 triplets after 0, so the fill lands on it)
FILL_T = 10 * BEAT             # 4.2857 s: triplet fill starts on beat 11
CHOKE_END = HIT_T - 0.040      # groove fully silent 40 ms before the hit

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


def svf(x: np.ndarray, fc: np.ndarray, q: float, mode: str = "lp") -> np.ndarray:
    """Zavalishin TPT state-variable filter with a per-sample cutoff (lp or bp)."""
    g = np.tan(np.pi * np.clip(fc, 20, 0.45 * SR) / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    y = np.empty(len(x))
    ic1 = ic2 = 0.0
    lp = mode == "lp"
    for n, (xn, b1, b2, b3) in enumerate(zip(x.tolist(), a1.tolist(), a2.tolist(), a3.tolist())):
        v3 = xn - ic2
        v1 = b1 * ic1 + b2 * v3
        v2 = ic2 + b2 * ic1 + b3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[n] = v2 if lp else v1
    return y


def drive_os(x: np.ndarray, drive: float) -> np.ndarray:
    """tanh saturation at 4x oversampling, so the new harmonics do not alias."""
    up = signal.resample_poly(x, 4, 1, axis=0)
    return signal.resample_poly(np.tanh(drive * up) / np.tanh(drive), 1, 4, axis=0)[: len(x)]


# ---------------------------------------------------------------- voices
def saw_bank(freq: np.ndarray, top: float = 7000.0) -> np.ndarray:
    """Band-limited saw from a per-sample frequency curve: additive partials, each one
    faded out smoothly before it reaches `top` Hz, so glides never alias."""
    ph = 2 * np.pi * np.cumsum(freq) / SR
    y = np.zeros_like(freq)
    for k in range(1, int(top // freq.min()) + 1):
        w = np.clip((top - k * freq) / 1500.0, 0.0, 1.0)
        if not w.any():
            break
        y += w * np.sin(k * ph) / k
    return y


def brass(midi: float, dur: float, bright: float = 1.0, fall: float = 0.0,
          att: float = 0.010, swell: bool = False) -> np.ndarray:
    """Brass-like stab: 3 detuned additive saws whose harmonic brightness blooms
    ~20 ms after the attack (the 'blat'), a pitch scoop up into the note, and an
    optional fall-off (semitones) over the second half. Stereo (L, C, R voices)."""
    t = tt(dur)
    f0 = float(hz(midi))
    scoop = -45 * np.exp(-t / 0.022)
    bend = np.zeros_like(t)
    if fall:
        u = np.clip((t - 0.5 * dur) / (0.5 * dur), 0, 1)
        bend = -100 * fall * u ** 2
    if swell:
        fc = f0 * (1.4 + 7 * bright * (t / dur) ** 1.6)
        amp = 0.25 + 0.75 * (t / dur) ** 1.4
    else:
        fc = f0 * (1.6 + 9 * bright * (1 - np.exp(-t / 0.016)) * np.exp(-t / 0.16)) + 900 * bright
        amp = 0.62 + 0.38 * np.exp(-t / 0.09)
    out = np.zeros((len(t), 2))
    for i, (cents, gl, gr) in enumerate(((-8, 1.0, 0.25), (0, 0.7, 0.7), (8, 0.25, 1.0))):
        f = f0 * 2 ** ((scoop + bend + cents) / 1200)
        ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 2 * np.pi)
        y = np.zeros_like(t)
        for k in range(1, int(14000 // (f0 * 1.02)) + 1):
            w = 1.0 / np.sqrt(1 + (k * f / fc) ** 4)
            y += (w / k) * np.sin(k * ph)
        out[:, 0] += gl * y
        out[:, 1] += gr * y
    return fade(out * amp[:, None] * 0.22, a=att, r=0.035)


def kick(big: bool = False) -> np.ndarray:
    """Tight breakbeat kick; the big one has a long sub tail that drops to F#1."""
    t = tt(0.75 if big else 0.30)
    if big:
        f = 46.25 + (190 - 46.25) * np.exp(-t / 0.045)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.55 * np.exp(-t / 0.09) + 0.45 * np.exp(-t / 0.42))
    else:
        f = 54 + (210 - 54) * np.exp(-t / 0.022)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)
    click = sos_filter(noise(len(t) / SR), "bandpass", [2000, 7000]) * np.exp(-t / 0.003) * 0.35
    return fade(np.tanh(1.8 * (body + click)) / np.tanh(1.8), a=0.0008, r=0.02)


def snare(tail: float = 1.0) -> np.ndarray:
    """Breakbeat snare: pitch-dropping tonal body + bright crack + rattly noise tail."""
    t = tt(0.32)
    f = 188 + 90 * np.exp(-t / 0.008)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.045)
    body += 0.45 * np.sin(2 * np.pi * 334 * t) * np.exp(-t / 0.028)
    crack = sos_filter(noise(0.32), "highpass", 3500) * np.exp(-t / 0.0035)
    rattle = sos_filter(noise(0.32), "bandpass", [1400, 9000]) * np.exp(-t / (0.10 * tail))
    y = 0.9 * body + 0.55 * crack + 0.75 * rattle
    return fade(np.tanh(1.4 * y) * 0.6, a=0.0006, r=0.02)


def hat(open_: bool = False) -> np.ndarray:
    d = 0.20 if open_ else 0.045
    t = tt(d)
    y = sos_filter(noise(d), "bandpass", [7500, 14500], order=3)
    y += 0.25 * np.sin(2 * np.pi * 9310 * t) * sos_filter(noise(d), "lowpass", 600)  # metallic ring
    y *= np.exp(-t / (0.06 if open_ else 0.011))
    return fade(y * 0.32, a=0.0005, r=0.004)


def crash(dur: float = 1.6, tau: float = 0.5) -> np.ndarray:
    t = tt(dur)
    env = np.exp(-t / tau)
    l = sos_filter(noise(dur), "bandpass", [3200, 14000], order=2) * env
    r = sos_filter(noise(dur), "bandpass", [3200, 14000], order=2) * env
    return fade(np.stack([l, r], axis=1) * 0.30, 0.0008, 0.08)


def riser(dur: float) -> np.ndarray:
    t = tt(dur)
    fc = 500 * (11000 / 500) ** (t / dur) ** 1.3
    amp = (t / dur) ** 1.8
    l = svf(noise(dur), fc, 3.0, "bp") * amp
    r = svf(noise(dur), fc * 1.05, 3.0, "bp") * amp
    return fade(np.stack([l, r], axis=1), 0.02, 0.005) * 0.5


def reverb(x: np.ndarray, rt60: float = 0.8, predelay: float = 0.012, band=(300, 7000)) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (small bright room)."""
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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 80.0) -> np.ndarray:
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


# ---------------------------------------------------------------- arrangement
FSM = (54, 57, 61, 66)         # F#m: F#3 A3 C#4 F#4
DMA = (54, 57, 62, 66)         # D/F#: F#3 A3 D4 F#4
EMA = (56, 59, 64, 68)         # E: G#3 B3 E4 G#4


def bass_line() -> np.ndarray:
    """The gritty saw hook as one phase-continuous voice (mono), steps in 16ths."""
    notes = [  # (step, midi, length in 16ths, accent)
        (0, 30, 2, 1.0), (2, 30, 1, .6), (3, 42, 1, .9), (5, 33, 2, .8), (7, 35, 1, .7),
        (8, 37, 2, .9), (10, 35, 1, .6), (11, 33, 1, .6), (12, 30, 2, .9), (14, 40, 1, .7), (15, 37, 1, .7),
        (16, 30, 2, 1.0), (18, 30, 1, .6), (19, 42, 1, .9), (21, 33, 2, .8), (23, 35, 1, .7),
        (24, 37, 2, .9), (26, 40, 1, .7), (27, 42, 1, .8), (28, 45, 2, 1.0), (30, 44, 1, .8), (31, 40, 1, .8),
        (32, 30, 1, 1.), (33, 42, 1, .8), (34, 30, 1, .9), (35, 42, 1, .8),
        (36, 33, 1, .9), (37, 45, 1, .8), (38, 35, 1, .9), (39, 47, 1, 1.0),
    ]
    end = int(CHOKE_END * SR) + 1
    target = np.full(end, 30.0)
    amp = np.zeros(end)
    fc = np.full(end, 300.0)
    for st, m, ln, acc in notes:
        s0, s1 = int(round(st * S16 * SR)), int(round((st + ln) * S16 * SR))
        n = s1 - s0
        tn = np.arange(n) / SR
        target[s0:s1] = m
        env = 0.78 + 0.22 * np.exp(-tn / 0.05)
        rl = int(0.014 * SR)
        env[-rl:] *= np.linspace(1, 0.15, rl)          # dip between notes = articulation
        amp[s0:s1] = env * (0.75 + 0.25 * acc)
        fc[s0:s1] = 260 + 3600 * acc * np.exp(-tn / 0.075)
    # triplet fill: hold C#2 and glide up an octave to C#3, filter opening
    s0 = int(round(FILL_T * SR))
    u = np.linspace(0, 1, end - s0)
    target[s0:] = 37 + 12 * u ** 1.5
    amp[s0:] = 0.85 + 0.15 * u
    fc[s0:] = 600 + 4200 * u ** 1.2
    # 8 ms portamento in pitch, gentle smoothing of the filter contour
    a = np.exp(-1 / (0.008 * SR))
    pitch = signal.lfilter([1 - a], [1, -a], target - 30, zi=[a * 0.0])[0] + 30
    fc = signal.lfilter([1 - a], [1, -a], fc, zi=[a * fc[0]])[0]
    b = np.exp(-1 / (0.0012 * SR))                     # ~1 ms amp smoothing: no steps
    amp = signal.lfilter([1 - b], [1, -b], amp)
    freq = hz(pitch)
    raw = saw_bank(freq, top=7000)
    filt = svf(raw, fc, 1.6, "lp") * amp
    grit = drive_os(filt * 1.0, 2.6)
    sub = np.sin(2 * np.pi * np.cumsum(freq) / SR) * amp * 0.55
    y = sos_filter(grit, "lowpass", 4800, order=4) * 0.55 + sub
    y = fade(y, a=0.001, r=0.012)
    out = np.zeros(N)
    out[:end] = y
    return out


def hit_bass(dur: float = 0.95) -> np.ndarray:
    t = tt(dur)
    f = np.full(len(t), float(hz(30)))
    raw = saw_bank(f, top=7000)
    fc = 220 + 3800 * np.exp(-t / 0.12)
    env = np.exp(-t / 0.55)
    y = sos_filter(drive_os(svf(raw, fc, 1.4, "lp") * env, 2.4), "lowpass", 4800, order=4) * 0.55
    y += np.sin(2 * np.pi * f * t) * env * 0.6
    return fade(y, a=0.001, r=0.25)


def render() -> np.ndarray:
    g = {k: np.zeros((N, 2)) for k in ("low", "drums", "music", "fx", "room")}   # the groove
    h = {k: np.zeros((N, 2)) for k in ("low", "drums", "music", "fx", "room")}   # the frame-150 hit
    kicks = []

    # ----- drums: two bars of break + half bar, then the triplet fill
    bar_k = {0: (0, 2, 10, 11), 1: (0, 2, 10, 13)}
    bar_s = {0: (4, 12), 1: (4, 12)}
    bar_gh = {0: (7, 9, 15), 1: (7, 9, 14, 15)}
    for bar in (0, 1):
        for st in bar_k[bar]:
            t = (bar * 16 + st) * S16
            place(g["low"], kick(), t, 1.0 if st == 0 else 0.85)
            kicks.append(t)
        for st in bar_s[bar]:
            t = (bar * 16 + st) * S16
            place(g["drums"], snare(), t, 0.75)
            place(g["room"], snare(), t, 0.35)
        for st in bar_gh[bar]:
            t = (bar * 16 + st) * S16
            place(g["drums"], snare(tail=0.5), t, 0.16 * rng.uniform(0.85, 1.15), pan=0.1)
        for st in range(16):
            t = (bar * 16 + st) * S16
            if st == 14 and bar == 1:
                place(g["drums"], hat(open_=True), t, 0.5, pan=0.3)
            elif st % 2 == 0:
                place(g["drums"], hat(), t, (0.55 if st % 4 == 2 else 0.4) * rng.uniform(0.9, 1.1), pan=0.3)
            elif bar == 1:
                place(g["drums"], hat(), t, 0.18 * rng.uniform(0.8, 1.1), pan=0.3)
    # half bar (steps 32-39): driving kick/snare, 16th hats
    for st in (32, 34, 37):
        place(g["low"], kick(), st * S16, 0.9)
        kicks.append(st * S16)
    place(g["drums"], snare(), 36 * S16, 0.78)
    place(g["room"], snare(), 36 * S16, 0.35)
    for st in (38, 39):
        place(g["drums"], snare(tail=0.5), st * S16, 0.28 + 0.08 * (st - 38))
    for st in range(32, 40):
        place(g["drums"], hat(), st * S16, (0.45 if st % 2 == 0 else 0.25) * rng.uniform(0.9, 1.1), pan=0.3)
    # triplet fill: 5 snare strokes crescendo, toms-ish pan sweep, kick on the first
    place(g["low"], kick(), FILL_T, 0.95)
    kicks.append(FILL_T)
    for i in range(5):
        t = FILL_T + i * TRIP
        place(g["drums"], snare(tail=0.8), t, 0.45 + 0.11 * i, pan=-0.3 + 0.15 * i)
        place(g["room"], snare(), t, 0.25 + 0.06 * i)
    place(g["fx"], riser(CHOKE_END - (FILL_T - BEAT)), FILL_T - BEAT, 0.75)

    # ----- cold-open hit at frame 0
    place(g["fx"], crash(1.6, 0.45), 0.0, 1.0)
    place(g["drums"], snare(), 0.0, 0.5)
    b0 = brass(FSM[0] + 12, 0.36, bright=1.2, att=0.001)
    for m in FSM:
        st = brass(m, 0.36, bright=1.2, att=0.001)
        place(g["music"], st, 0.0, 0.62)
        place(g["room"], st, 0.0, 0.18)
    place(g["music"], b0, 0.0, 0.35)

    # ----- the bass hook (one continuous voice, ends in the glide)
    bl = bass_line()
    g["low"] += bl[:, None] * 0.75

    # ----- brass stabs (step, chord, length in 16ths, brightness)
    stabs = [(6, FSM, 1, .8), (10, DMA, 2, 1.0), (14, EMA, 2, 1.0),
             (22, FSM, 1, .8), (26, DMA, 1, .9), (28, EMA, 3, 1.1),
             (35, FSM, 1, 1.0), (38, EMA, 1, 1.1)]
    for st, ch, ln, br in stabs:
        dur = ln * S16 * 0.92
        for m in ch:
            b = brass(m, dur, bright=br)
            place(g["music"], b, st * S16, 0.55)
            place(g["room"], b, st * S16, 0.15)
    # swelling E chord under the fill (pulls to the F#m hit)
    for m in EMA + (71,):
        b = brass(m, CHOKE_END - FILL_T, bright=1.1, att=0.03, swell=True)
        place(g["music"], b, FILL_T, 0.42)
        place(g["room"], b, FILL_T, 0.12)

    # ----- the big hit at frame 150
    place(h["low"], kick(big=True), HIT_T, 1.0)
    place(h["low"], hit_bass()[:, None].repeat(2, 1), HIT_T, 0.8)
    place(h["drums"], snare(tail=1.6), HIT_T, 0.85)
    place(h["room"], snare(tail=1.6), HIT_T, 0.5)
    place(h["fx"], crash(1.0, 0.38), HIT_T, 1.1)
    for m in FSM + (69, 73):
        b = brass(m, 0.92, bright=1.4, fall=3.0, att=0.001)
        place(h["music"], b, HIT_T, 0.62)
        place(h["room"], b, HIT_T, 0.30)

    # ----- buses
    def bus_mix(d, rt60):
        # light sidechain on the music bus from the groove kicks
        duck = np.ones(N)
        tk = tt(0.18)
        shape = 1 - 0.30 * np.exp(-tk / 0.05) * (1 - np.exp(-tk / 0.002))
        for k in kicks if d is g else ():
            s0 = int(round(k * SR))
            e = min(N, s0 + len(shape))
            duck[s0:e] = np.minimum(duck[s0:e], shape[: e - s0])
        hp = lambda x: sos_filter(x, "highpass", 140, order=4)
        music = peaking_eq(hp(d["music"] * duck[:, None]), 2800, -2.0, 0.9)
        wet = hp(reverb(d["room"], rt60=rt60)) * 0.5
        low = np.repeat(d["low"].mean(axis=1, keepdims=True), 2, axis=1)
        return low * 0.9 + hp(d["drums"]) + music + hp(d["fx"]) * 0.8 + wet

    groove = bus_mix(g, 0.7)
    hit = bus_mix(h, 1.1)
    # choke: groove (incl. its room) cut with a 25 ms cosine ending 40 ms before the hit
    ch = np.ones(N)
    c1 = int(round(CHOKE_END * SR))
    c0 = c1 - int(0.025 * SR)
    ch[c0:c1] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, c1 - c0))
    ch[c1:] = 0.0
    # arc: cold-open hit full, groove sits ~3 dB under, half bar + fill climb back up,
    # so the frame-150 hit is the loudest moment
    tg = np.arange(N) / SR
    arc = np.interp(tg, [0.0, 0.12, 0.40, 32 * S16, CHOKE_END], [1.0, 1.0, 0.70, 0.72, 1.0])
    mix = groove * (ch * arc)[:, None] + hit * 1.15

    # mono below 120 Hz (M/S high-pass on the side), DC/subsonic, top band-limit
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 120, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 25, order=2)
    mix = sos_filter(mix, "lowpass", 17000, order=4)
    nf = int(0.25 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    # remove residual DC (asymmetric kick transients) with a sub-1 Hz Hann-shaped
    # offset, so both ends stay exactly at zero
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
