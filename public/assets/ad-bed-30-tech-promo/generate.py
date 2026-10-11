"""ad-bed-30-tech-promo: Opus Sound Directory

A 30-second tech product promo bed in E major at 120 BPM (one beat = 15 frames at
30 fps), cut to a seven-scene app demo. Frame 0 is a hard opening hit (big kick,
crash and a bright E major stab), followed by three bell blips on the beat while a
16th-note hat pulse tightens. A digital glitch build (buffer-repeat stutters,
pitch-stepped slices, ring-mod bleeps) slams in on frame 75 (2.5 s) and a
four-on-the-floor groove starts: off-beat bass, syncopated chord plucks moving
I-V-vi-IV one chord per bar, claps on 2 and 4, shimmering hats. A bright major
bell chord sparkles at 7.0 s. At 9.0 s the groove drops out to sparse hats and a
riser, a second glitch slams in on frame 300 (10.0 s) over a tense C#-minor pad
and a sparse C# pulse, and a filtered whoosh rises into a heavy impact on frame
366 (12.2 s). From 14.0 s the full groove returns with a sixteenth-note arpeggio,
a riser builds into a crash at 21.0 s, the groove drops out at 24.0 s under a
reverse swell, and a rising four-note bell motif with a tonic stab lands on frame
735 (24.5 s) and rings out over a wide pad to silence at 30.0 s. Everything below
120 Hz is a mono kick, bass and impact boom.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 30120
DURATION_SEC = 30
BPM = 120
KEY = "E major"
FPS = 30
CUE_FRAMES = (0, 75, 300, 366, 735)   # opening hit, glitch slam, glitch slam, impact, logo sting
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM                      # 0.5 s = 15 frames
STEP = BEAT / 4

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


# ---------------------------------------------------------------- voices
def additive_pluck(f0: float, dur: float, bright: float = 1.0, decay: float = 6.0,
                   detune_cents: float = 0.0) -> np.ndarray:
    """Band-limited saw-like pluck. Each harmonic decays faster than the one below
    it, which gives a filter-envelope sound with no aliasing (all partials < 16 kHz)."""
    t = tt(dur)
    f = f0 * 2 ** (detune_cents / 1200)
    y = np.zeros_like(t)
    kmax = int(min(16000, 0.4 * SR) // f)
    for k in range(1, kmax + 1):
        amp = (1.0 / k) * np.exp(-((k - 1) * 0.18) / bright)
        if amp < 1e-4:
            break
        env = np.exp(-t * decay * (1 + 0.35 * (k - 1) / bright))
        y += amp * env * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    return fade(y / 1.6, a=0.002, r=0.02)


def stereo_pluck(midi, dur, bright=1.0, decay=6.0, spread=4.0):
    l = additive_pluck(hz(midi), dur, bright, decay, -spread)
    r = additive_pluck(hz(midi), dur, bright, decay, +spread)
    return np.stack([l, r], axis=1)


def pad_voice(midi: float, dur: float, att: float = 0.25, rel: float = 0.35) -> np.ndarray:
    """Soft detuned saw pad, harmonics rolled off above ~1.8 kHz, stereo detune."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for ch, cents in enumerate((-9, -3, 3, 9)):
        f = hz(midi) * 2 ** (cents / 1200)
        y = np.zeros_like(t)
        for k in range(1, int(9000 // f) + 1):
            a = (1 / k) / (1 + (k * f / 1800) ** 2)
            y += a * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
        out[:, ch % 2] += y
    env = np.ones_like(t)
    na, nr = int(att * SR), int(rel * SR)
    env[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    env[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return out * env[:, None] * 0.35


def kick(big: bool = False) -> np.ndarray:
    t = tt(0.42 if big else 0.32)
    f = 47 + (170 - 47) * np.exp(-t / 0.032)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    body *= np.exp(-t / (0.20 if big else 0.14))
    click = sos_filter(noise(len(t) / SR), "bandpass", [1500, 6000]) * np.exp(-t / 0.004) * 0.25
    return fade(np.tanh(1.6 * (body + click)) / np.tanh(1.6), a=0.0005, r=0.01)


def clap(gain_tail: float = 1.0) -> np.ndarray:
    t = tt(0.25)
    env = np.zeros_like(t)
    for off in (0.0, 0.009, 0.019):
        m = t >= off
        env[m] += np.exp(-(t[m] - off) / 0.005)
    m = t >= 0.026
    env[m] += gain_tail * 0.7 * np.exp(-(t[m] - 0.026) / 0.06)
    y = sos_filter(noise(0.25), "bandpass", [900, 4200], order=2) * env
    return fade(y * 0.45, a=0.0005, r=0.01)


def hat(open_: bool = False) -> np.ndarray:
    d = 0.22 if open_ else 0.05
    t = tt(d)
    y = sos_filter(noise(d), "highpass", 7000, order=4)
    y = sos_filter(y, "lowpass", 15500, order=4)
    y *= np.exp(-t / (0.075 if open_ else 0.014))
    return fade(y * 0.35, a=0.0005, r=0.005)


def crash(dur: float = 2.2) -> np.ndarray:
    t = tt(dur)
    l = sos_filter(noise(dur), "bandpass", [3800, 14500], order=2)
    r = sos_filter(noise(dur), "bandpass", [3800, 14500], order=2)
    env = np.exp(-t / 0.55)
    return np.stack([fade(l * env, 0.0005, 0.05), fade(r * env, 0.0005, 0.05)], axis=1) * 0.28


def bass_note(midi: float, dur: float) -> np.ndarray:
    t = tt(dur)
    f = hz(midi)
    y = np.sin(2 * np.pi * f * t) + 0.32 * np.sin(4 * np.pi * f * t) + 0.10 * np.sin(6 * np.pi * f * t)
    env = np.exp(-t / 0.22) * 0.6 + 0.4
    return fade(y * env * 0.55, a=0.004, r=0.03)


def bell(midi: float, dur: float = 1.2) -> np.ndarray:
    t = tt(dur)
    f = hz(midi)
    y = np.zeros_like(t)
    for ratio, amp, dec in ((1.0, 1.0, 0.5), (2.756, 0.45, 0.28), (5.404, 0.22, 0.14), (8.933, 0.10, 0.08)):
        if ratio * f < 16000:
            y += amp * np.exp(-t / dec) * np.sin(2 * np.pi * ratio * f * t)
    return fade(y * 0.3, a=0.0008, r=0.05)


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


def riser(dur: float) -> np.ndarray:
    t = tt(dur)
    fc = 350 * (9000 / 350) ** (t / dur) ** 1.4
    amp = (t / dur) ** 2.2
    l = svf_bandpass(noise(dur), fc, 2.5) * amp
    r = svf_bandpass(noise(dur), fc * 1.04, 2.5) * amp
    return np.stack([fade(l, 0.01, 0.004), fade(r, 0.01, 0.004)], axis=1) * 0.55


def reverse_swell(dur: float) -> np.ndarray:
    t = tt(dur)
    env = (t / dur) ** 3
    l = sos_filter(noise(dur), "bandpass", [2500, 12000]) * env
    r = sos_filter(noise(dur), "bandpass", [2500, 12000]) * env
    return np.stack([fade(l, 0.01, 0.003), fade(r, 0.01, 0.003)], axis=1) * 0.22


def reverb(x: np.ndarray, rt60: float = 1.4, predelay: float = 0.018) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (bright plate-ish)."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [250, 7500]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    out = np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                    signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)
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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 90.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak.
    The gain curve is held over the look-ahead window, recovers through a one-pole
    release, and is box-smoothed. It never clips the waveform."""
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
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3          # margin for dither + inter-sample
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y




# ---------------------------------------------------------------- stingers (synthesised)
def bleep(f0: float, dur: float) -> np.ndarray:
    """Ring-mod bleep: sine carrier times a sine modulator, band-limited by construction."""
    t = tt(dur)
    y = np.sin(2 * np.pi * f0 * t) * np.sin(2 * np.pi * f0 * 1.414 * t)
    return fade(y * np.exp(-t / (dur * 0.5)), 0.001, 0.004)


def glitch_build(dur: float = 0.6) -> np.ndarray:
    """Buffer-repeat stutter of a chord stab, slices shrinking and stepping up in pitch,
    with ring-mod bleeps and gated noise. Ends in 25 ms of silence so the slam that follows reads."""
    out = np.zeros((int(dur * SR), 2))
    src = np.zeros(int(0.12 * SR))
    for m in (64, 68, 71, 76):
        src += additive_pluck(hz(m), 0.12, bright=1.2, decay=9.0)
    t, k = 0.0, 0
    lengths = [0.0625] * 4 + [0.03125] * 6 + [0.015625] * 8
    end = dur - 0.025
    for L in lengths:
        if t + L > end:
            break
        ratio = 2 ** (k // 3 / 12)                       # pitch steps up a semitone every 3 slices
        n = int(L * SR)
        idx = np.arange(n) * ratio
        sl = np.interp(idx, np.arange(len(src)), src, right=0.0)
        sl = fade(sl, 0.0015, 0.003)
        g = 0.35 + 0.5 * (t / dur)
        place(out, np.stack([sl, sl], 1), t, g, pan=(-0.4 if k % 2 else 0.4))
        if k % 3 == 2:
            place(out, np.stack([bleep(1800 + 140 * k, 0.03)] * 2, 1), t, 0.12, pan=(0.6 if k % 2 else -0.6))
        nz = sos_filter(noise(L), "bandpass", [3000, 9000]) * 0.08
        place(out, np.stack([fade(nz, 0.001, 0.002)] * 2, 1), t, 1.0)
        t += L
        k += 1
    return out


def slam() -> tuple[np.ndarray, np.ndarray]:
    """Digital slam: (low mono boom, mid/high crack). Both start at sample 0."""
    t = tt(0.6)
    boom = np.sin(2 * np.pi * (48 + 60 * np.exp(-t / 0.03)) * t) * np.exp(-t / 0.18)
    crack = sos_filter(noise(0.25), "highpass", 1500) * np.exp(-tt(0.25) / 0.04)
    hi = np.stack([crack, sos_filter(noise(0.25), "highpass", 1500) * np.exp(-tt(0.25) / 0.04)], 1)
    return np.stack([fade(boom, 0.0005, 0.02)] * 2, 1), hi * 0.5


def whoosh(dur: float = 1.0) -> np.ndarray:
    """Filtered-noise whoosh rising into the impact, panning left to right, last 25 ms silent."""
    t = tt(dur)
    fc = 300 * (6000 / 300) ** (t / dur) ** 1.8
    amp = (t / dur) ** 2.5
    l = svf_bandpass(noise(dur), fc, 3.0) * amp
    r = svf_bandpass(noise(dur), fc * 1.03, 3.0) * amp
    pan = t / dur
    y = np.stack([l * np.cos(pan * np.pi / 2), r * np.sin(pan * np.pi / 2)], 1) * 0.7
    y[-int(0.025 * SR):] = 0.0
    y[:, 0] = fade(y[:, 0], 0.02, 0.004)
    y[:, 1] = fade(y[:, 1], 0.02, 0.004)
    return y


def logo_motif() -> np.ndarray:
    """Rising four-note bell motif (B5 E6 G#6 B6) with a shimmer on the last note."""
    out = np.zeros((int(2.6 * SR), 2))
    for i, m in enumerate((83, 88, 92, 95)):
        b = bell(m, 1.6 - 0.2 * i)
        place(out, np.stack([b, b], 1), 0.11 * i, 0.42, pan=(-0.45, -0.15, 0.15, 0.45)[i])
    sh = sos_filter(noise(1.6), "bandpass", [6000, 12000]) * np.exp(-tt(1.6) / 0.45) * 0.05
    place(out, np.stack([sh, sos_filter(noise(1.6), "bandpass", [6000, 12000]) * np.exp(-tt(1.6) / 0.45) * 0.05], 1), 0.33, 1.0)
    return out


# ---------------------------------------------------------------- arrangement
E, B, Cm, A = (64, 68, 71), (63, 66, 71), (61, 64, 68), (61, 64, 69)
ROOTS = {E: 40, B: 35, Cm: 37, A: 33}
PROG = [E, B, Cm, A]  # one chord per bar (2 s)


def chord_at(t):
    return PROG[int(t // 2.0) % 4]


def render() -> np.ndarray:
    low = np.zeros((N, 2))
    drums = np.zeros((N, 2))
    music = np.zeros((N, 2))
    fx = np.zeros((N, 2))
    send = np.zeros((N, 2))
    kicks = []

    def kick_at(t, g=0.9, big=False):
        kicks.append(t)
        place(low, kick(big=big), t, g)

    def stab(t, notes, g=0.3, bright=1.3, dur=1.0, decay=3.0):
        for m in notes:
            p = stereo_pluck(m, dur, bright=bright, decay=decay)
            place(music, p, t, g)
            place(send, p, t, g * 0.5)

    def slam_at(t, g=1.0):
        lo, hi = slam()
        place(low, lo, t, 0.8 * g)
        place(fx, hi, t, g)
        place(fx, crash(1.2), t, 0.5 * g)
        kick_at(t, 1.0, big=True)

    # ---- 0–2.5: opening hit, three bell blips, hat pulse, glitch build → slam (f75)
    kick_at(0.0, 1.0, big=True)
    stab(0.0, [52, 64, 68, 71, 76], 0.3)
    place(fx, crash(), 0.0, 0.7)
    for i, t in enumerate((0.5, 1.0, 1.5)):
        kick_at(t, 0.75)
        b = bell(83 + 2 * i, 0.5)
        place(fx, np.stack([b, b], 1), t, 0.3, pan=(-0.3, 0.3, 0.0)[i])
    place(fx, glitch_build(0.6), 1.9, 0.9)
    slam_at(2.5)

    # ---- groove helper
    def groove(t0, t1, plucks=True, bass=True, hats=True, claps=True, kick_g=0.9, bright=0.9, first_kick=True):
        nb = int(round((t1 - t0) / BEAT))
        for b in range(nb):
            t = t0 + b * BEAT
            if b > 0 or first_kick:
                kick_at(t, kick_g)
            beat_in_bar = int(round(t / BEAT)) % 4
            if claps and beat_in_bar in (1, 3):
                place(drums, clap(), t, 0.5)
                place(send, clap(), t, 0.2)
            if bass:
                place(low, bass_note(ROOTS[chord_at(t)], BEAT * 0.45), t + BEAT / 2, 0.55)
            if hats:
                for s in range(4):
                    ts = t + s * STEP
                    if s == 2:
                        place(drums, hat(open_=True), ts, 0.3, pan=0.2)
                    else:
                        place(drums, hat(), ts, (0.24 if s == 0 else 0.15) * rng.uniform(0.85, 1.1), pan=-0.25)
        if plucks:
            bar = t0 - (t0 % 2.0)
            while bar < t1:
                for st in (0, 3, 6, 10, 12):
                    t = bar + st * STEP
                    if t0 - 1e-9 <= t < t1 - 1e-9:
                        for i, m in enumerate(chord_at(t)):
                            p = stereo_pluck(m, 0.36, bright=bright, decay=7.0)
                            place(music, p, t + i * 0.002, (0.26 if st == 0 else 0.2) * rng.uniform(0.9, 1.05))
                            place(send, p, t, 0.05)
                bar += 2.0

    # ---- 2.5–9.0: groove; bright bell chord at 7.0
    groove(2.5, 9.0, first_kick=False)
    for i, m in enumerate((88, 92, 95)):
        b = bell(m, 1.1)
        place(fx, np.stack([b, b], 1), 7.0 + 0.025 * i, 0.32, pan=(-0.35, 0.35, 0)[i])
        place(send, np.stack([b, b], 1), 7.0, 0.1)

    # ---- 9.0–14.0: drop-out + riser, glitch slam (f300), C#m tension, whoosh → impact (f366)
    place(fx, riser(0.6), 9.0, 0.5)
    for s in range(4):
        place(drums, hat(), 9.0 + s * STEP * 2, 0.14)
    place(fx, glitch_build(0.6), 9.4, 1.0)
    slam_at(10.0)
    for b in range(1, int((12.0 - 10.0) / BEAT)):
        t = 10.0 + b * BEAT
        kick_at(t, 0.8)
    for b in range(int((12.0 - 10.0) / BEAT) - 1):
        t = 10.0 + b * BEAT
        place(low, bass_note(37, BEAT * 0.4), t + BEAT / 2, 0.5)  # C#
        place(drums, hat(), t + BEAT / 2, 0.16)
    for m in (61, 64, 68):
        pv = pad_voice(m, 2.0, rel=0.15)
        place(music, pv, 10.0, 0.22)
    place(fx, whoosh(1.0), 12.2 - 1.0, 1.0)
    slam_at(12.2, 1.1)
    place(low, bass_note(37, 0.8), 12.2, 0.55)
    groove(12.5, 14.0, plucks=False, claps=False)

    # ---- 14.0–21.0: full groove + 16th arpeggio, riser into 21.0
    place(fx, crash(), 14.0, 0.8)
    groove(14.0, 21.0, bright=1.1)
    arp = (0, 1, 2, 3, 2, 1, 0, 2)
    s, t = 0, 14.0
    while t < 21.0 - 1e-9:
        ch = chord_at(t)
        tones = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[0] + 24]
        p = additive_pluck(hz(tones[arp[s % 8]]), 0.2, bright=0.7, decay=11.0)
        place(music, p, t, 0.12, pan=0.35 if s % 2 else -0.35)
        s += 1
        t = 14.0 + s * STEP
    place(fx, riser(1.0), 20.0, 0.7)

    # ---- 21.0–24.5: crash, groove, drop-out under a reverse swell
    place(fx, crash(1.6), 21.0, 0.75)
    groove(21.0, 24.0, bright=1.0)
    place(fx, reverse_swell(0.46), 24.0, 0.9)

    # ---- 24.5 (f735): logo motif + tonic stab, pad rings out to silence
    kick_at(24.5, 1.0, big=True)
    place(low, bass_note(40, 1.2), 24.5, 0.55)
    stab(24.5, [52, 64, 68, 71, 76], 0.3, dur=2.0, decay=1.6)
    place(fx, logo_motif(), 24.5, 0.9)
    for m in E:
        pv = pad_voice(m, 4.6, att=0.4, rel=1.2)
        place(music, pv, 24.6, 0.2)
        place(send, pv, 24.6, 0.06)

    # ---- bus processing
    duck = np.ones(N)
    tk = tt(0.25)
    shape = 1 - 0.45 * np.exp(-tk / 0.07) * (1 - np.exp(-tk / 0.002))
    for k in kicks:
        s0 = int(round(k * SR))
        e = min(N, s0 + len(shape))
        duck[s0:e] = np.minimum(duck[s0:e], shape[: e - s0])
    music *= duck[:, None]
    hp = lambda x: sos_filter(x, "highpass", 150, order=4)
    music = hp(music)
    drums = hp(drums)
    fx = hp(fx)
    wet = hp(reverb(send, rt60=1.3)) * 0.5
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    mix = low * 0.95 + drums + music + fx * 0.85 + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 120, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 17500, order=4)
    nf = int(0.6 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    y = master(render())
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
