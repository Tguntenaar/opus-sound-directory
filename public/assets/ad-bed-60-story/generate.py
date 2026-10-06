"""ad-bed-60-story: Opus Sound Directory

A 60-second story-arc ad bed at 92 BPM that turns from A minor to C major. It opens
at frame 0 on a soft low boom and a hollow reed-like chord. A quiet triplet pulse
then ticks through Am, Fmaj7, Dm7 and Em7, while a breathy ocarina-style lead
sings a slow melody and a sine bass and heartbeat kick slip in underneath. At
frame 900 (30 s) the build starts with a kick, boom and soft crash. A triplet bass
pushes Am-F-C-G, shakers, toms and a rim backbeat thicken, a brassy swell pad
opens its filter, and a band-pass noise riser climbs. A seven-hit triplet tom fill
and a short breath of silence then drop onto the emotional peak at frame 1500
(50 s): a big kick, taiko-like boom, crash, and a full C major chord with an
octave-doubled pulse and the lead at its highest note. The peak moves C to F and
resolves at 55.2 s onto a rolled C major chord that rings out to silence. Only
the mono kick, boom, toms and bass sit below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 92060
DURATION_SEC = 60
BPM = 92
KEY = "A minor -> C major"
FPS = 30
CUE_FRAMES = (0, 900, 1500)    # cold open, build, emotional peak
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.65217 s
TRIP = BEAT / 3                # triplet eighth
BAR = 4 * BEAT
T_BUILD = CUE_FRAMES[1] / FPS  # 30.0 s = exactly 46 beats (11 bars of 4/4 + one 2/4 bar)
T_PEAK = CUE_FRAMES[2] / FPS   # 50.0 s = build start + 7 bars + 8 triplet eighths
T_END = T_PEAK + 2 * BAR       # 55.22 s: resolution chord

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Raised-cosine attack/release so nothing starts or stops with a click."""
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    na, nr = min(na, len(x)), min(nr, len(x))
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))).reshape((-1,) + (1,) * (x.ndim - 1))
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))).reshape((-1,) + (1,) * (x.ndim - 1))
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


def adsr(n: int, att: float, rel: float) -> np.ndarray:
    env = np.ones(n)
    na, nr = min(n, max(1, int(att * SR))), min(n, max(1, int(rel * SR)))
    env[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    env[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return env


# ---------------------------------------------------------------- tonal voices
def reed_pulse(midi: float, dur: float, bright: float = 1.0, decay: float = 5.0) -> np.ndarray:
    """Hollow reed-like pluck: mostly odd harmonics (square-ish, band-limited and
    additive) with a whisper of the 2nd. Upper partials die faster."""
    t = tt(dur)
    f = hz(midi)
    y = np.zeros_like(t)
    for k in range(1, 16):
        if k * f > 9000:
            break
        amp = (1.0 / k) * np.exp(-(k - 1) * 0.30 / bright) * (1.0 if k % 2 else 0.18)
        env = np.exp(-t * decay * (1 + 0.5 * (k - 1) / bright))
        y += amp * env * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    return fade(y * 0.5, a=0.003, r=0.03)


def ocarina(midi: float, dur: float) -> np.ndarray:
    """Breathy ocarina/flute-style lead: near-sine tone with delayed vibrato plus
    band-passed breath noise and a soft chiff at the attack."""
    t = tt(dur)
    f0 = hz(midi)
    vib = 1 + (2 ** (11 / 1200) - 1) * np.clip((t - 0.35) / 0.6, 0, 1) * np.sin(2 * np.pi * 5.1 * t)
    ph = 2 * np.pi * np.cumsum(f0 * vib) / SR + rng.uniform(0, 2 * np.pi)
    tone = np.sin(ph) + 0.10 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    br = sos_filter(noise(dur), "bandpass", [f0 * 0.9, min(f0 * 5, 12000)], order=2)
    chiff = sos_filter(noise(dur), "bandpass", [f0 * 2, min(f0 * 8, 14000)]) * np.exp(-t / 0.03)
    env = adsr(len(t), 0.07, min(0.25, dur * 0.4)) * (0.85 + 0.15 * np.clip(t / dur, 0, 1))
    return (tone * 0.42 + br * 0.05 + chiff * 0.08) * env


def warm_pad(midi: float, dur: float, att: float = 1.2, rel: float = 1.5) -> np.ndarray:
    """Triangle-ish pad (odd harmonics, 1/k^2), four detuned voices spread in stereo."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for ch, cents in enumerate((-7, -2, 2, 7)):
        f = hz(midi) * 2 ** (cents / 1200)
        y = np.zeros_like(t)
        for k in range(1, 12, 2):
            if k * f > 4500:
                break
            y += ((-1) ** ((k - 1) // 2)) / k ** 2 * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
        out[:, ch % 2] += y
    return out * adsr(len(t), att, rel)[:, None] * 0.25


def brass_swell(midi: float, dur: float, fc0: float, fc1: float, tau: float,
                att: float = 0.6, rel: float = 1.0) -> np.ndarray:
    """Brassy saw pad: additive saw whose partials sit under a moving 4th-order low-pass
    (fc0 -> fc1 with time constant tau), so the filter 'opens' as the swell grows."""
    t = tt(dur)
    fc = fc1 + (fc0 - fc1) * np.exp(-t / tau)
    out = np.zeros((len(t), 2))
    for ch, cents in enumerate((-5, 5)):
        f = hz(midi) * 2 ** (cents / 1200)
        ph = 2 * np.pi * f * t + 0.004 * np.sin(2 * np.pi * 0.23 * t + ch)
        y = np.zeros_like(t)
        for k in range(1, 40):
            if k * f > 12000:
                break
            amp = (1.0 / k) / np.sqrt(1 + (k * f / fc) ** 4)
            y += amp * np.sin(k * ph + rng.uniform(0, 2 * np.pi))
        out[:, ch] = y
    return out * adsr(len(t), att, rel)[:, None] * 0.22


def sine_bass(midi: float, dur: float, rel: float = 0.08) -> np.ndarray:
    t = tt(dur)
    f = hz(midi)
    y = np.sin(2 * np.pi * f * t) + 0.28 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
    env = 0.55 + 0.45 * np.exp(-t / 0.35)
    return fade(y * env * 0.5, a=0.006, r=rel)


# ---------------------------------------------------------------- drums / fx
def kick(kind: str = "mid") -> np.ndarray:
    big = kind == "big"
    t = tt(0.6 if big else 0.4)
    f_end, f_start = (42, 150) if big else (50, 130)
    f = f_end + (f_start - f_end) * np.exp(-t / (0.04 if big else 0.03))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.32 if big else 0.16))
    if kind == "soft":                          # heartbeat: no click, rounder
        y = body * 0.8
    else:
        click = sos_filter(noise(len(t) / SR), "bandpass", [1200, 5000]) * np.exp(-t / 0.004) * 0.22
        y = np.tanh(1.5 * (body + click)) / np.tanh(1.5)
    return fade(y, a=0.0005, r=0.02)


def boom(dur: float = 2.0, f_start: float = 70, f_end: float = 36) -> np.ndarray:
    """Sub boom: pitch-dropping sine with a slow decay (mono, low bus)."""
    t = tt(dur)
    f = f_end + (f_start - f_end) * np.exp(-t / 0.12)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (dur * 0.33))
    return fade(y, a=0.001, r=0.1)


def tom(f0: float, dur: float = 0.55) -> np.ndarray:
    t = tt(dur)
    f = f0 * (1 + 0.35 * np.exp(-t / 0.025))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)
    skin = sos_filter(noise(dur), "bandpass", [300, 2500]) * np.exp(-t / 0.02) * 0.35
    return fade(np.tanh(1.3 * (body + skin)) * 0.8, a=0.0005, r=0.03)


def shaker() -> np.ndarray:
    d = 0.09
    t = tt(d)
    y = sos_filter(sos_filter(noise(d), "highpass", 5000, order=4), "lowpass", 13000, order=2)
    env = (1 - np.exp(-t / 0.006)) * np.exp(-t / 0.028)
    return fade(y * env * 0.5, a=0.001, r=0.01)


def rim() -> np.ndarray:
    d = 0.22
    t = tt(d)
    body = np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.03) * 0.5
    snap = sos_filter(noise(d), "bandpass", [1500, 7000]) * np.exp(-t / 0.045)
    return fade((body + snap) * 0.45, a=0.0005, r=0.02)


def crash(dur: float = 3.0, decay: float = 0.9) -> np.ndarray:
    t = tt(dur)
    env = np.exp(-t / decay)
    ch = [sos_filter(noise(dur), "bandpass", [3500, 14000], order=2) * env for _ in range(2)]
    return np.stack([fade(c, 0.0005, 0.1) for c in ch], axis=1) * 0.28


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
    fc = 300 * (7000 / 300) ** ((t / dur) ** 1.5)
    amp = (t / dur) ** 2.4
    ch = [svf_bandpass(noise(dur), fc * m, 2.2) * amp for m in (1.0, 1.05)]
    return np.stack([fade(c, 0.05, 0.003) for c in ch], axis=1) * 0.5


def reverb(x: np.ndarray, rt60: float = 2.4, predelay: float = 0.03) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (dark hall)."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60) * (1 - np.exp(-t / 0.02))
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [200, 5500]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, i], irs[i])[: len(x)] for i in range(2)], axis=1)


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
    held over the look-ahead window, recovers through a one-pole release and is
    box-smoothed. It never clips the waveform."""
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


# ---------------------------------------------------------------- harmony + melody
Am, F, Dm, Em, G, Gs, C = ((57, 60, 64, 71), (53, 57, 60, 64), (50, 57, 60, 65), (52, 59, 62, 67),
                           (55, 59, 62, 67), (55, 60, 62, 67), (55, 60, 64, 67))
ROOT = {Am: 33, F: 29, Dm: 38, Em: 28, G: 31, Gs: 31, C: 36}
# (section start, [(start beat, beats, chord), ...])
A_CHORDS = [(0, 8, Am), (8, 8, F), (16, 8, Am), (24, 4, F), (28, 4, G), (32, 4, Dm), (36, 4, Em),
            (40, 4, F), (44, 2, Gs)]
B_CHORDS = [(0, 4, Am), (4, 4, F), (8, 4, C), (12, 4, G), (16, 4, Am), (20, 4, F), (24, 4 + 8 / 3, Gs)]
C_CHORDS = [(0, 4, C), (4, 4, F)]
A_MEL = [(16, 3, 76), (19, 1, 72), (20, 2, 71), (22, 2, 69), (24, 3, 72), (27, 1, 74), (28, 2, 74),
         (30, 2, 71), (32, 3, 69), (35, 1, 72), (36, 4, 71), (40, 2, 72), (42, 2, 76), (44, 1.5, 74)]
B_MEL = [(0, 2, 76), (2, 1, 72), (3, 1, 74), (4, 3, 77), (7, 1, 76), (8, 2, 76), (10, 2, 79),
         (12, 3, 79), (15, 1, 74), (16, 2, 76), (18, 2, 81), (20, 2, 81), (22, 1, 79), (23, 1, 77),
         (24, 3.5, 79)]
C_MEL = [(0, 2, 79), (2, 2, 84), (4, 2, 81), (6, 2, 77), (8, 6, 76)]


def render() -> np.ndarray:
    low = np.zeros((N, 2))      # kick, boom, toms, bass: the only content below 120 Hz
    drums = np.zeros((N, 2))
    music = np.zeros((N, 2))
    lead = np.zeros((N, 2))
    fx = np.zeros((N, 2))
    send = np.zeros((N, 2))

    def at(sec0, beat):
        return sec0 + beat * BEAT

    # ======== A: quiet intro (0 - 30 s) ========
    place(low, boom(3.0, 62, 33), 0.0, 0.55)
    for i, m in enumerate((45, 57, 64, 71)):
        p = reed_pulse(m, 2.5, bright=0.7, decay=1.4)
        place(music, p, 0.0, 0.32, pan=(-0.3, 0.1, -0.1, 0.3)[i])
        place(send, np.stack([p, p], 1), 0.0, 0.25)
    for b0, nb, ch in A_CHORDS:
        t0 = at(0, b0)
        dur = nb * BEAT + 1.4
        for m in ch:
            pv = warm_pad(m, dur, att=1.4 if b0 == 0 else 0.8, rel=1.4)
            g = 0.13 + 0.11 * b0 / 44
            if b0 == 44:
                pv = pv[: int(1.5 * BEAT * SR)]
                pv = fade(pv, 0.01, 0.3)
            place(music, pv, t0, g)
            place(send, pv, t0, g * 0.5)
        # pulse: quarters in bars 0-1, triplets after
        pat = (0, 1, 2, 3, 2, 1)
        for bt in range(int(np.ceil(nb))):
            for s in range(3):
                beat = b0 + bt + s / 3
                if beat >= 45.0 or (beat < 8 and s != 0) or beat < 1:
                    continue
                m = ch[pat[int(round((beat * 3))) % 6]]
                bright = 0.55 + 0.35 * beat / 46
                vel = (0.20 if s == 0 else 0.13) * (0.65 + 0.5 * beat / 46) * rng.uniform(0.9, 1.08)
                p = reed_pulse(m + 12 * (s == 2 and beat > 24), 0.45, bright=bright, decay=6.0)
                place(music, p, at(0, beat), vel, pan=0.25 * np.sin(beat * 1.3))
                place(send, np.stack([p, p], 1), at(0, beat), vel * 0.35)
    for b0, nb, m in A_MEL:
        o = ocarina(m, nb * BEAT * 0.97)
        g = 0.26 + 0.10 * b0 / 44
        place(lead, o, at(0, b0), g, pan=0.05)
        place(send, np.stack([o, o], 1), at(0, b0), g * 0.5)
    # bass from bar 6: long roots
    for b0, nb, ch in A_CHORDS:
        if b0 >= 24:
            place(low, sine_bass(ROOT[ch], nb * BEAT * (0.75 if b0 == 44 else 0.98), rel=0.2), at(0, b0), 0.42)
    # heartbeat kick from bar 8 (lub-dub on 1)
    for bt in range(32, 44, 2):
        place(low, kick("soft"), at(0, bt), 0.45)
        place(low, kick("soft"), at(0, bt) + TRIP, 0.28)

    # ======== B: build (30 - 50 s) ========
    S = T_BUILD
    place(low, kick("big"), S, 0.9)
    place(low, boom(2.4, 66, 34), S, 0.5)
    place(fx, crash(3.0, 1.0), S, 0.55)
    nbB = 28 + 8 / 3
    for b0, nb, ch in B_CHORDS:
        t0 = at(S, b0)
        prog = b0 / 28
        dur = nb * BEAT + (0.25 if b0 == 24 else 1.0)
        for m in ch:
            pv = warm_pad(m, dur, att=0.4, rel=0.25 if b0 == 24 else 1.0)
            place(music, pv, t0, 0.20 + 0.06 * prog)
            place(send, pv, t0, 0.12)
        if b0 >= 12:     # brassy swell opens up in the second half of the build
            for m in ch:
                bs = brass_swell(m, dur, 350 + 500 * prog, 900 + 1800 * prog, nb * BEAT * 0.6,
                                 att=nb * BEAT * 0.5, rel=0.25 if b0 == 24 else 0.6)
                place(music, bs, t0, 0.10 + 0.16 * prog)
                place(send, bs, t0, 0.12)
        pat = (0, 1, 2, 3, 2, 1)
        for i in range(int(round(nb * 3))):
            beat = b0 + i / 3
            if beat >= 28 + 7 / 3 - 1e-9:      # pulse stops with the riser, one triplet before the peak
                break
            s = i % 3
            m = ch[pat[i % 6]]
            pr = beat / nbB
            vel = (0.24 if s == 0 else 0.16) * (0.9 + 0.35 * pr) * rng.uniform(0.92, 1.06)
            p = reed_pulse(m, 0.42, bright=0.8 + 0.7 * pr, decay=6.5)
            place(music, p, at(S, beat), vel, pan=-0.3 if s == 1 else 0.3 if s == 2 else 0.0)
            if b0 >= 16:
                p2 = reed_pulse(m + 12, 0.3, bright=1.0 + 0.5 * pr, decay=9.0)
                place(music, p2, at(S, beat), vel * 0.5, pan=0.45 if s == 1 else -0.45)
            place(send, np.stack([p, p], 1), at(S, beat), vel * 0.3)
        # triplet-feel bass: on the beat and the last triplet of each beat
        for bt in range(int(np.floor(nb))):
            if b0 + bt >= 28:
                break
            place(low, sine_bass(ROOT[ch], BEAT * 0.6), at(S, b0 + bt), 0.42 + 0.1 * prog)
            if b0 >= 8:
                place(low, sine_bass(ROOT[ch] + 12 * (bt % 2), TRIP * 0.85), at(S, b0 + bt + 2 / 3), 0.28)
    for b0, nb, m in B_MEL:
        o = ocarina(m, nb * BEAT * 0.97)
        place(lead, o, at(S, b0), 0.48, pan=0.05)
        place(send, np.stack([o, o], 1), at(S, b0), 0.25)
    for bt in range(28):
        bar, beat = divmod(bt, 4)
        if beat in (0, 2) or bar >= 3:
            if bt > 0:
                place(low, kick("mid"), at(S, bt), 0.5 + 0.15 * bt / 28)
        if bar >= 3 and beat in (1, 3):
            place(drums, rim(), at(S, bt), 0.26 + 0.16 * bt / 28, pan=0.08)
            place(send, rim()[:, None].repeat(2, 1), at(S, bt), 0.12)
        for s in range(3):
            if bar >= 1:
                v = (0.16 if s == 0 else 0.11) * (0.6 + 0.5 * bt / 28) * rng.uniform(0.85, 1.1)
                place(drums, shaker(), at(S, bt + s / 3), v, pan=0.35)
        if bar >= 4 and beat == 3:
            place(low, tom(150), at(S, bt + 1 / 3), 0.35)
            place(low, tom(120), at(S, bt + 2 / 3), 0.4)
    # riser from bar 4 of the build to one triplet before the peak
    r0, r1 = at(S, 16), T_PEAK - TRIP
    place(fx, riser(r1 - r0), r0, 0.45)
    # seven-hit triplet fill (crescendo, descending toms) then a breath before the peak
    for i in range(7):
        t = at(S, 28 + i / 3)
        place(low, tom((200, 185, 170, 155, 140, 128, 118)[i]), t, 0.28 + 0.05 * i)
        place(drums, rim(), t, 0.16 + 0.04 * i, pan=(-0.3, 0.3)[i % 2])
        place(send, rim()[:, None].repeat(2, 1), t, 0.1)

    # ======== C: emotional peak (50 s) and resolution (55.2 s) ========
    P = T_PEAK
    place(low, kick("big"), P, 0.85)
    place(low, boom(3.5, 75, 33), P, 0.5)
    place(low, tom(95, 0.9), P, 0.4)
    place(fx, crash(4.0, 1.4), P, 0.95)
    peak_c = (48, 55, 60, 64, 67, 72, 76)
    for m in peak_c:
        bs = brass_swell(m, BAR + 0.6, 2600, 1800, 1.5, att=0.012, rel=0.6)
        place(music, bs, P, 0.5)
        place(send, bs, P, 0.2)
        if m >= 55:
            pv = warm_pad(m, BAR + 0.6, att=0.05, rel=0.6)
            place(music, pv, P, 0.30)
    for m in (53, 57, 60, 65, 69, 72):           # F (add the 9 on top later in the bar)
        bs = brass_swell(m, BAR + 1.2, 1500, 2200, 0.8, att=0.15, rel=1.0)
        place(music, bs, at(P, 4), 0.30)
        place(send, bs, at(P, 4), 0.2)
        pv = warm_pad(m, BAR + 1.2, att=0.2, rel=1.0)
        place(music, pv, at(P, 4), 0.22)
    for b0, nb, ch in C_CHORDS:
        for i in range(int(nb * 3)):
            beat = b0 + i / 3
            s = i % 3
            m = ch[(0, 1, 2, 3, 2, 1)[i % 6]]
            vel = (0.40 if s == 0 else 0.28) * rng.uniform(0.93, 1.05) * (1.0 - 0.18 * beat / 8)
            p = reed_pulse(m, 0.42, bright=1.5, decay=6.5)
            place(music, p, at(P, beat), vel, pan=-0.3 if s == 1 else 0.3 if s == 2 else 0.0)
            p2 = reed_pulse(m + 12, 0.3, bright=1.4, decay=9.0)
            place(music, p2, at(P, beat), vel * 0.55, pan=0.45 if s == 1 else -0.45)
            place(send, np.stack([p, p], 1), at(P, beat), vel * 0.3)
        for bt in range(int(nb)):
            place(low, sine_bass(ROOT[ch], BEAT * 0.9), at(P, b0 + bt), 0.55)
            place(low, sine_bass(ROOT[ch] + 12, TRIP * 0.85), at(P, b0 + bt + 2 / 3), 0.3)
            if b0 + bt > 0:
                place(low, kick("mid"), at(P, b0 + bt), 0.75)
            if bt in (1, 3):
                place(drums, rim(), at(P, b0 + bt), 0.5, pan=0.08)
            for s in range(3):
                place(drums, shaker(), at(P, b0 + bt + s / 3), (0.2 if s == 0 else 0.14) * rng.uniform(0.85, 1.1), pan=0.35)
    place(low, tom(140), at(P, 7 + 1 / 3), 0.45)
    place(low, tom(118), at(P, 7 + 2 / 3), 0.5)
    for b0, nb, m in C_MEL:
        o = ocarina(m, nb * BEAT * 0.97 if b0 < 8 else 4.2)
        place(lead, o, at(P, b0), 0.62, pan=0.05)
        place(send, np.stack([o, o], 1), at(P, b0), 0.3)
    # resolution: soft kick + boom, rolled C major, long pad and low C
    E = T_END
    place(low, kick("soft"), E, 0.6)
    place(low, boom(4.0, 58, 32), E, 0.4)
    place(fx, crash(4.0, 1.6), E, 0.3)
    for i, m in enumerate((48, 55, 60, 64, 67, 72, 76)):
        p = reed_pulse(m, 4.6 - i * TRIP, bright=1.0, decay=1.1)
        place(music, p, E + i * TRIP, 0.30, pan=(-0.5 + i / 6))
        place(send, np.stack([p, p], 1), E + i * TRIP, 0.28)
    for m in (48, 55, 60, 64, 67):
        pv = warm_pad(m, DURATION_SEC - E, att=0.3, rel=3.0)
        place(music, pv, E, 0.26)
        place(send, pv, E, 0.15)
    place(low, sine_bass(36, DURATION_SEC - E - 0.2, rel=2.5), E, 0.45)

    # ======== bus processing ========
    hp = lambda x: sos_filter(x, "highpass", 150, order=4)
    music = peaking_eq(hp(music), 2600, -2.0, 0.9)          # leave room for a voiceover
    lead = peaking_eq(hp(lead), 2600, -1.5, 1.0)
    drums = hp(drums)
    fx = hp(fx)
    wet = hp(reverb(send, rt60=2.4)) * 0.5
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    low = sos_filter(low, "lowpass", 3000, order=2) * 0.9

    mix = low + drums + music + lead + fx * 0.8 + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 260, order=8)   # keep the low end (and its 4th-order skirt) mono
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 16500, order=4)

    nf = int(1.2 * SR)                                       # cosine tail-out to exact silence
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
