"""chaos-calm-02: Opus Sound Directory

A 30-second traffic-glitch-to-strings bed in Db major at 90 BPM, for a city-to-calm
story ad. Frame 0 hits a sharp urban accent: a truck air-horn chord, two clashing
car horns and a low engine thump. For ten seconds the street gets denser. Idling
engines drone, cars pass with Doppler pitch drops and left-to-right pans, horns
honk on and off a 16th-note grid, and a distant siren wails closer. A digital
glitch layer chops the street into stutters, repeats and pitch-shifted slices, and
in the last beat it accelerates from 1/32 to 1/128 repeats. At frame 300 (10.0 s)
the whole street, echoes included, stops in a 3 ms fade that ends exactly on the
cue. Warm synthetic strings (detuned band-limited saw ensembles with vibrato) rise
from silence on the same sample. Over 20 s they build slowly: a dark low Db chord,
then a bowed contrabass, then a legato violin melody with portamento, then soft
8th-note viola pulses at 90 BPM, an octave doubling and an opening tone. The
progression is Db, Ab/C, Bbm7, Gbmaj7, Db/F, Gb, Absus4, Ab. It swells to a peak
and lands on a high Db chord at 26 s that rings to exact silence. Only engine
lows, the contrabass and a soft sub swell sit below 120 Hz, all mono.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import gaussian_filter1d, minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 230300
DURATION_SEC = 30
BPM = 90
KEY = "Db major"
FPS = 30
CUE_FRAMES = (0, 300)          # frame 0: urban hit, frame 300: traffic cuts, strings rise
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.6667 s = 32000 samples
BAR = 4 * BEAT                 # 2.6667 s
SIX = BEAT / 4                 # 16th = 8000 samples
CUT_T = CUE_FRAMES[1] / FPS    # 10.0 s
CUT_S = int(round(CUT_T * SR)) # 480000

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
    ea = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    er = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    if x.ndim == 2:
        ea, er = ea[:, None], er[:, None]
    x[:na] *= ea
    x[-nr:] *= er
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan=0.0) -> None:
    """Mix a mono (L,) or stereo (L,2) snippet into a stereo bus at time t.
    pan may be a scalar or a per-sample array (equal-power)."""
    s = int(round(t * SR))
    if s >= len(bus):
        return
    if x.ndim == 1:
        th = (np.asarray(pan) + 1) * np.pi / 4
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


def wander(n: int, smooth_s: float) -> np.ndarray:
    """Smoothed random control signal in [-1, 1], n samples."""
    hop = 240
    k = n // hop + 3
    w = gaussian_filter1d(rng.standard_normal(k), smooth_s * SR / hop)
    w = w / (np.abs(w).max() + 1e-12)
    return np.interp(np.arange(n), np.arange(k) * hop, w)


def additive(phase: np.ndarray, f_max: float, weights_fn, f_limit: float = 9000.0) -> np.ndarray:
    """Sum of harmonics sin(k*phase) with weights_fn(k) (scalar or per-sample), all < f_limit."""
    y = np.zeros(len(phase))
    for k in range(1, int(f_limit // max(f_max, 1.0)) + 1):
        w = weights_fn(k)
        if np.max(np.abs(w)) < 2e-4:
            continue
        y += w * np.sin(k * phase)
    return y


def reverb(x: np.ndarray, rt60: float, band=(250, 7500), predelay: float = 0.02) -> np.ndarray:
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


# ---------------------------------------------------------------- traffic voices
def horn(f1: float, f2: float | None, dur: float) -> np.ndarray:
    """Car horn: one or two brassy additive tones with a pitch scoop and a 2.5 kHz honk formant."""
    t = tt(dur)
    y = np.zeros_like(t)
    for f in ([f1] if f2 is None else [f1, f2]):
        scoop = 2 ** (-40 / 1200 * np.exp(-t / 0.025))
        ph = 2 * np.pi * np.cumsum(f * scoop * (1 + 0.002 * np.sin(2 * np.pi * 7 * t))) / SR
        y += additive(ph, f, lambda k: (1 / k ** 0.85) * (1.0 if k % 2 else 0.55), 6500)
    y = peaking_eq(y, 2500, 7, 1.2)
    y = sos_filter(y, "highpass", 250, order=2)
    env = np.minimum(1, t / 0.008) * (0.85 + 0.15 * np.exp(-t / 0.08))
    return fade(y * env / (np.abs(y).max() + 1e-9), a=0.002, r=0.025)


def engine_idle(f_fire: float, dur: float) -> np.ndarray:
    """Idling engine: harmonic series of the firing rate with jittery AM, rolled off by 1.5 kHz."""
    n = int(round(dur * SR))
    jit = 1 + 0.03 * wander(n, 0.15)
    ph = 2 * np.pi * np.cumsum(f_fire * jit) / SR
    y = additive(ph, f_fire, lambda k: (1 / k ** 0.7) / (1 + (k * f_fire / 600) ** 2), 2000)
    am = 0.75 + 0.25 * np.sin(ph / 2)          # uneven cylinder thump
    return y * am / (np.abs(y).max() + 1e-9)


def car_pass(f_eng: float, dur: float, speed: float, dist: float) -> tuple[np.ndarray, np.ndarray]:
    """Passing car centred at dur/2: Doppler-shifted engine + tyre noise. Returns (mono, pan curve)."""
    t = tt(dur)
    x = speed * (t - dur / 2)
    r = np.sqrt(x ** 2 + dist ** 2)
    v_r = speed * x / r                                # + when receding
    dop = 343.0 / (343.0 + v_r)
    ph = 2 * np.pi * np.cumsum(f_eng * dop) / SR
    eng = additive(ph, f_eng * 1.1, lambda k: (1 / k) / (1 + (k * f_eng / 900) ** 2), 4000)
    tyre = sos_filter(noise(dur), "bandpass", [400, 2600]) * 0.5
    amp = (dist / r) ** 1.3
    y = (eng / (np.abs(eng).max() + 1e-9) + tyre) * amp
    pan = np.clip(x / (np.abs(x).max() + 1e-9) * 1.6, -0.9, 0.9)
    return fade(y, a=0.05, r=0.05), pan


def siren(dur: float) -> np.ndarray:
    """Distant wail siren, 650 Hz .. 1.3 kHz, 3.2 s cycle, getting closer."""
    t = tt(dur)
    lfo = 0.5 - 0.5 * np.cos(2 * np.pi * t / 3.2)
    f = 650 * 2 ** lfo
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    return fade(y * (0.25 + 0.75 * (t / dur) ** 2), a=0.4, r=0.01)


def glitch(bus: np.ndarray, start_s: int, span: int, slice_len: int, pitch: tuple[int, int] | None = None) -> None:
    """Replace bus[start:start+span] with repeats of a slice (optionally resampled), 1.5 ms fades."""
    src = bus[start_s:start_s + slice_len].copy()
    if pitch is not None:
        up, down = pitch
        src = signal.resample_poly(bus[start_s:start_s + slice_len * up // down + 64], down, up, axis=0)[:slice_len]
    nf = int(0.0015 * SR)
    w = np.ones(len(src))
    w[:nf] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, nf))
    w[-nf:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf))
    rep = np.tile(src * w[:, None], (span // len(src) + 1, 1))[:span]
    edge = np.ones(span)
    edge[:nf] = w[:nf]
    edge[-nf:] = w[-nf:]
    seg = bus[start_s:start_s + span]
    bus[start_s:start_s + span] = seg * (1 - edge)[:, None] + rep * edge[:, None]


# ---------------------------------------------------------------- string voices
def ensemble(freq: np.ndarray, fc: np.ndarray, voices: int = 4, spread: float = 9.0,
             vib: np.ndarray | float = 0.004, f_limit: float = 9000.0) -> np.ndarray:
    """Synthetic string section: detuned band-limited saws, each with its own vibrato,
    partial weights rolled off by a time-varying brightness fc. Stereo (voices alternate L/R)."""
    n = len(freq)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    f_max = float(np.max(freq)) * (1 + spread / 1200 + 0.01)
    for v in range(voices):
        cents = spread * (2 * v / max(1, voices - 1) - 1)
        rate = rng.uniform(4.6, 5.8)
        drift = 1 + 0.0015 * wander(n, 0.4)
        f = freq * 2 ** (cents / 1200) * drift * (1 + vib * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.3)))
        ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 6.3)
        f0 = float(np.median(freq))
        y = additive(ph, f_max, lambda k: (1 / k) / np.sqrt(1 + (k * f0 / fc) ** 4),
                     min(f_limit, 5.0 * float(np.max(fc))))
        out[:, v % 2] += y
    return out / voices


def line_curve(notes, n: int, glide: float = 0.08) -> tuple[np.ndarray, np.ndarray]:
    """Legato pitch curve (Hz) with portamento, and an amplitude curve with soft re-bows.
    notes = [(start_s, dur_s, midi)] relative to the line start."""
    t = np.arange(n) / SR
    bt, bf = [], []
    for i, (s, d, m) in enumerate(notes):
        prev = np.log2(hz(notes[i - 1][2])) if i else np.log2(hz(m))
        bt += [s, s + (glide if i else 1e-4)]
        bf += [prev, np.log2(hz(m))]
    f = 2 ** np.interp(t, bt, bf)
    amp = np.zeros(n)
    for s, d, m in notes:
        i0, i1 = int(s * SR), min(n, int((s + d) * SR))
        u = np.arange(i1 - i0) / SR
        a = np.minimum(1, u / 0.18) * (0.88 + 0.12 * np.minimum(1, u / 0.8))     # bow in, then lean
        r = np.clip((d - u) / 0.12, 0, 1)
        amp[i0:i1] = np.maximum(amp[i0:i1], a * np.sin(np.pi / 2 * r) ** 2 * 0.85 + 0.15 * (u > 0))
    return f, gaussian_filter1d(amp, 0.02 * SR)


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


def bus_chain(x: np.ndarray) -> np.ndarray:
    """Master bus filters: mono below ~250 Hz (M/S high-pass on the side), subsonic + top trims."""
    mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    x = np.stack([mid + side, mid - side], axis=1)
    x = sos_filter(x, "highpass", 22, order=2)
    return sos_filter(x, "lowpass", 16500, order=4)


# ---------------------------------------------------------------- arrangement
def render_traffic() -> np.ndarray:
    S = CUT_S + int(0.01 * SR)
    t = np.arange(S) / SR
    street = np.zeros((S, 2))
    low = np.zeros((S, 2))
    send = np.zeros((S, 2))
    dens = 0.55 + 0.45 * (t / CUT_T) ** 1.3

    # idling engines (their lows go to the mono low bus, the rest stays panned)
    for f, pan, g in ((31.0, -0.5, 0.30), (38.5, 0.4, 0.26), (44.0, 0.1, 0.20)):
        e = engine_idle(f, S / SR) * dens
        place(low, sos_filter(e, "lowpass", 120, order=4), 0.0, g * 0.55)
        place(street, sos_filter(e, "highpass", 120, order=4), 0.0, g * 0.9, pan=pan)
    # road hiss
    for ch in range(2):
        street[:, ch] += 0.07 * sos_filter(noise(S / SR), "bandpass", [300, 3000]) * dens

    # passing cars with Doppler drops and pan sweeps
    for tc, f, sp, d, g in ((1.6, 92, 22, 5, 0.40), (3.9, 118, 27, 4, 0.45), (5.4, 76, 18, 7, 0.35),
                             (7.0, 104, 30, 3.5, 0.55), (8.6, 130, 25, 4, 0.5)):
        dur = 3.2
        y, pan = car_pass(f, dur, sp, d)
        place(street, y, tc - dur / 2, g, pan=pan if rng.random() < 0.5 else -pan)

    # siren drifting closer from 2.5 s
    place(street, siren(CUT_T - 2.5 + 0.01), 2.5, 0.10, pan=0.55)

    # honks, mostly on the 16th grid; pitches chosen to clash
    hp = [(392, 494), (415, None), (440, 554), (370, 466), (466, None), (523, 415), (349, None)]
    slots = sorted(set(rng.choice(np.arange(3, 56), 28, replace=False).tolist()))
    for i, sl in enumerate(slots):
        f1, f2 = hp[i % len(hp)]
        f1 *= rng.uniform(0.97, 1.03)
        dur = float(rng.choice([0.12, 0.16, 0.3, 0.55]))
        h = horn(f1, None if f2 is None else f2 * rng.uniform(0.98, 1.02), dur)
        tj = sl * SIX + (0.0 if rng.random() < 0.7 else rng.uniform(0.01, 0.06))
        pan = rng.uniform(-0.85, 0.85)
        g = 0.12 * (0.7 + 0.6 * tj / CUT_T)
        place(street, h, tj, g, pan=pan)
        place(send, h, tj, g * 0.6, pan=pan)
        if dur < 0.2 and rng.random() < 0.5:        # double honk
            place(street, h, tj + SIX, g * 0.85, pan=pan)

    # frame-0 urban hit: truck air-horn chord + two clashing car horns + engine thump
    air = horn(hz(51), hz(55), 0.9) + 0.8 * horn(hz(58), None, 0.9)       # Eb3/G3 + Bb3 air horn
    place(street, air, 0.0, 0.28)
    place(street, horn(440, 466, 0.45), 0.0, 0.16, pan=-0.4)
    place(send, air, 0.0, 0.2)
    tb = tt(0.6)
    thump = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-tb / 0.04)) / SR) * np.exp(-tb / 0.18)
    place(low, fade(thump, 0.001, 0.05), 0.0, 0.55)

    # street echoes: slapback reflections + a short reverb
    echo = np.zeros_like(send)
    for dl, g, ch in ((0.11, 0.35, 0), (0.17, 0.3, 1), (0.29, 0.18, 0), (0.37, 0.15, 1)):
        k = int(dl * SR)
        echo[k:, ch] += g * sos_filter(send[:-k, ch] + street[:-k, ch] * 0.3, "bandpass", [300, 4000])
    street = street + echo + 0.35 * sos_filter(reverb(send, 1.1, band=(300, 6000), predelay=0.01), "highpass", 200)

    # glitch layer: stutters / pitched slices on the 16th grid, accelerating roll into the cut
    sw = int(SIX * SR)
    for sl in sorted(rng.choice(np.arange(4, 54), 18, replace=False).tolist()):
        kind = rng.integers(0, 4)
        s0 = sl * sw
        if kind == 3:                                         # buffer dropout: a muted 32nd
            nf = int(0.0015 * SR)
            m = np.ones(sw)
            m[sw // 4 - nf:sw // 4] = np.linspace(1, 0, nf)
            m[sw // 4:3 * sw // 4] = 0.0
            m[3 * sw // 4:3 * sw // 4 + nf] = np.linspace(0, 1, nf)
            street[s0:s0 + sw] *= m[:, None]
        elif kind == 0:
            glitch(street, s0, sw, sw // 2)
        elif kind == 1:
            glitch(street, s0, sw * 2, sw // 4)
        else:
            glitch(street, s0, sw, sw // 2, pitch=(3, 2) if rng.random() < 0.5 else (2, 3))
    roll = 56 * sw
    glitch(street, roll, 2 * sw, sw // 2)                    # 1/32 repeats
    glitch(street, roll + 2 * sw, sw, sw // 4)               # 1/64
    glitch(street, roll + 3 * sw, sw, sw // 8, pitch=(3, 2)) # 1/128, pitched up

    street = sos_filter(street, "highpass", 120, order=4)
    low = sos_filter(low, "highpass", 26, order=2)              # keep the low bus DC-free before the cut
    return street + np.repeat(low.mean(axis=1, keepdims=True), 2, 1)


def render_strings() -> tuple[np.ndarray, np.ndarray]:
    music = np.zeros((N, 2))
    low = np.zeros((N, 2))
    send = np.zeros((N, 2))
    D = DURATION_SEC - CUT_T                         # 20 s
    nD = int(D * SR)
    tu = np.arange(nD + SR) / SR
    # the build: brightness and level rise to a peak around 25-26 s, then settle
    peak_u = 16.0
    rise = np.clip(tu / peak_u, 0, 1)
    fc_all = 650 * (3600 / 650) ** (rise ** 1.4)
    fc_all *= 1 - 0.3 * np.clip((tu - peak_u) / 4, 0, 1)
    lvl_all = 0.36 + 0.64 * rise ** 1.6
    lvl_all *= 1 - 0.25 * np.clip((tu - peak_u - 0.6) / 3.4, 0, 1)

    # chords (bar = 2.667 s from the cut); bar 5 splits Gb | Absus4 | Ab
    B = BAR
    chords = [
        (0.0, B, (49, 56, 61, 65)),                 # Db
        (B, B, (48, 51, 56, 60, 63)),               # Ab/C
        (2 * B, B, (46, 53, 56, 61, 65)),           # Bbm7
        (3 * B, B, (42, 49, 53, 58, 61)),           # Gbmaj7
        (4 * B, B, (41, 49, 56, 61, 65, 68)),       # Db/F
        (5 * B, 2 * BEAT, (42, 49, 54, 58, 61, 66)),  # Gb
        (5 * B + 2 * BEAT, BEAT, (44, 51, 56, 61, 63, 68)),  # Absus4
        (5 * B + 3 * BEAT, BEAT, (44, 51, 56, 60, 63, 68)),  # Ab
        (6 * B, D - 6 * B, (49, 56, 61, 65, 68, 73)),  # Db (landing)
    ]
    for ci, (s, d, notes) in enumerate(chords):
        last = ci == len(chords) - 1
        ov = 0.35                                    # legato overlap into the next chord
        dur = d + (0.0 if last else ov)
        i0 = int(s * SR)
        n = int(round(dur * SR))
        att = 0.9 if ci == 0 else 0.30
        env = np.ones(n)
        na = int(att * SR)
        env[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
        nr = int((2.8 if last else ov + 0.05) * SR)
        env[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
        for m in notes:
            fr = np.full(n, hz(m))
            y = ensemble(fr, fc_all[i0:i0 + n], voices=4, spread=10.0, vib=0.0035)
            g = 0.16 * env * lvl_all[i0:i0 + n]
            place(music, y * g[:, None], CUT_T + s)
            place(send, y * g[:, None], CUT_T + s, 0.6)

    # contrabass from bar 1: bowed roots, mono
    roots = [(B, B, 36), (2 * B, B, 34), (3 * B, B, 30), (4 * B, B, 29), (5 * B, 2 * BEAT, 30),
             (5 * B + 2 * BEAT, 2 * BEAT, 32), (6 * B, D - 6 * B, 37)]
    nb = [(s - B, d - 0.02, m) for s, d, m in roots]
    fb, ab = line_curve(nb, int((D - B) * SR), glide=0.05)
    ab = gaussian_filter1d(ab, 0.05 * SR)
    phb = 2 * np.pi * np.cumsum(fb * (1 + 0.002 * np.sin(2 * np.pi * 4.8 * np.arange(len(fb)) / SR))) / SR
    bass = additive(phb, 90, lambda k: (1 / k) / (1 + (k * 40 / 260) ** 2), 1200)
    lv = lvl_all[int(B * SR):int(B * SR) + len(bass)]
    bass = fade(bass * ab * lv * np.clip(np.arange(len(bass)) / (1.2 * SR), 0, 1), a=0.01, r=2.5)
    place(low, bass, CUT_T + B, 0.18)

    # violin melody from bar 2 (beats from bar 2's downbeat)
    mel = [(0, 2, 77), (2, 1, 75), (3, 1, 73),
           (4, 1.5, 73), (5.5, 0.5, 75), (6, 2, 77),
           (8, 2, 80), (10, 1, 77), (11, 1, 80),
           (12, 2, 82), (14, 1, 85), (15, 1, 84),
           (16, 5.5, 85)]
    t0 = 2 * B
    notes = [(b * BEAT, d * BEAT - 0.03, m) for b, d, m in mel]
    nm = int((D - t0) * SR)
    fm, am = line_curve(notes, nm, glide=0.09)
    j0 = int(t0 * SR)
    vib = 0.003 + 0.004 * np.clip(np.arange(nm) / (8 * SR), 0, 1)
    vln = ensemble(fm, fc_all[j0:j0 + nm] * 1.15, voices=3, spread=6.0, vib=vib, f_limit=11000)
    env_m = am * lvl_all[j0:j0 + nm]
    env_m = fade(env_m, a=0.3, r=3.0)
    place(music, vln * env_m[:, None], CUT_T + t0, 0.20)
    place(send, vln * env_m[:, None], CUT_T + t0, 0.16)
    # octave-below doubling (second violins / violas) from bar 4
    k0 = int(2 * B * SR)
    dbl = ensemble(fm[k0:] / 2, fc_all[j0 + k0:j0 + nm], voices=3, spread=8.0, vib=0.004)
    env_d = env_m[k0:] * np.clip(np.arange(nm - k0) / (1.5 * SR), 0, 1)
    place(music, dbl * env_d[:, None], CUT_T + t0 + 2 * B, 0.12)
    place(send, dbl * env_d[:, None], CUT_T + t0 + 2 * B, 0.08)

    # viola 8th-note pulse (bars 3-5): soft re-bowed chord tones, crescendo
    for e in range(int(3 * B / (BEAT / 2))):
        ts = 3 * B + e * BEAT / 2
        ch = [c for c in chords if c[0] <= ts + 1e-6][-1][2]
        m = ch[2] if e % 2 == 0 else ch[3]
        d = BEAT / 2 * 0.9
        y = ensemble(np.full(int(d * SR), hz(m)), np.full(int(d * SR), 1800.0), voices=2, spread=6.0, vib=0.002,
                     f_limit=6000)
        env = np.sin(np.pi * np.clip(np.arange(len(y)) / len(y), 0, 1)) ** 1.5
        g = 0.05 + 0.07 * e / (6 * B / BEAT)
        place(music, y * env[:, None], CUT_T + ts, g * (1.0 if e % 2 == 0 else 0.8))
        place(send, y * env[:, None], CUT_T + ts, g * 0.5)

    # soft sub swell into the landing (mono Db1), and its gentle bloom after 26 s
    ts = tt(6.0)
    sw = np.sin(2 * np.pi * hz(25) * ts) * np.clip(ts / 2.6, 0, 1) ** 2 * np.exp(-np.clip(ts - 2.67, 0, None) / 1.4)
    place(low, fade(sw, a=0.01, r=0.5), CUT_T + 5 * B, 0.30)

    music = sos_filter(music, "highpass", 110, order=2)
    wet = sos_filter(reverb(send, 3.0, band=(180, 7000), predelay=0.035), "highpass", 160, order=2)
    music = music + 0.5 * wet
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    return music, low


def render() -> np.ndarray:
    traffic = np.zeros((N, 2))
    tr = render_traffic()
    traffic[: len(tr)] = tr
    traffic = bus_chain(traffic)                  # filter BEFORE the gate: nothing rings past the cut
    nf = int(0.003 * SR)
    gate = np.ones(N)
    na = int(0.001 * SR)                          # frame-0 hit: ~1 ms raised-cosine attack
    gate[:na] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    gate[CUT_S - nf:CUT_S] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf))
    gate[CUT_S:] = 0.0
    traffic *= gate[:, None]
    # truncating the high-passed street at the cut leaves a tiny DC residue; remove it with a
    # 0..10 s Hann bump of equal area (a ~0.1 Hz correction, no steps, zero at both ends)
    bump = np.zeros(N)
    bump[:CUT_S] = np.hanning(CUT_S)
    traffic -= np.outer(bump / bump.sum(), traffic[:CUT_S].sum(axis=0))

    strings, low = render_strings()
    mix = 1.4 * traffic + bus_chain(strings + low)

    nf = int(1.5 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    # the limiter's gain moves on asymmetric peaks and leaves ~3e-5 of DC; trim it with a
    # full-length Hann bump of equal area (sub-0.1 Hz, zero at both ends, no effect on the edges)
    hb = np.hanning(N)
    y = y - np.outer(hb / hb.sum(), y.sum(axis=0))
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
