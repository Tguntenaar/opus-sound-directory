"""podcast-intro-10s: Opus Sound Directory

A bright, friendly 10-second podcast intro in Bb major at 135 BPM. It opens on a
full-band Bb hit at frame 0 with a soft splash, and a two-beat snare pickup and a
two-note lead pickup lead into one balanced four-bar phrase (Ebmaj9 | Dm7 G13 |
Cm9 | Cm9 F13) that resolves home on the button. A warm tine
electric piano (FM bark plus a short bell tine, gentle stereo tremolo) comps with
pushed off-beat stabs, a round finger-style electric bass plays a syncopated line
with a chromatic walk-up, and a tight, dry kit (warm kick, snappy snare with a
clap layer, swung hats) keeps it moving. A soft, whistle-like synth lead carries a
singable hook in bar 1, answers it in bar 2 and restates it higher in bar 3. Bar 3
lifts with a short noise swell, a quiet string pad and a shaker. Bar 4 builds with
a snare fill into an "and-of-four" band stab and a breath of silence. A Bb6/9
button (kick, bass, piano chord, lead on the tonic, splash) then lands exactly on
frame 240 (8.0 s) and decays to true silence by 10 s, so the host can start
talking over the ring-out. Everything below 120 Hz is a mono kick and bass.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 1200810
DURATION_SEC = 10
BPM = 135
KEY = "Bb major"
FPS = 30
CUE_FRAMES = (0, 240)          # frame 0: full-band intro hit, frame 240: button
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.444 s: a 2-beat intro hit + 4 bars = 18 beats = 8.0 s
OFF = 2                        # bar 1 of the phrase starts after the 2-beat intro hit
BUTTON_B = 16                  # phrase beat 16 = bar 5 downbeat = 8.0 s = frame 240
SW = 0.04                      # light 16th swing (fraction of a beat added to off-16ths)
assert abs((BUTTON_B + OFF) * BEAT - CUE_FRAMES[1] / FPS) < 1e-12

rng = np.random.default_rng(SEED)


def T(b: float) -> float:
    """Time of phrase beat b (beat 0 = bar-1 downbeat, after the intro hit)."""
    return (b + OFF) * BEAT


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Raised-cosine attack/release so nothing starts or stops with a click."""
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    sh = (slice(None),) + (None,) * (x.ndim - 1)
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na)))[sh]
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr)))[sh]
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


def human() -> float:
    """A few ms of timing looseness (never applied to cue events)."""
    return float(rng.uniform(-0.004, 0.004))


# ---------------------------------------------------------------- voices
def epiano(midi: float, dur: float, vel: float = 0.8, att: float = 0.002, ring: float = 1.0,
           rel: float = 0.06) -> np.ndarray:
    """Tine electric piano: 1:1 FM pair whose index falls fast (bark -> round body),
    a short bell tine at 7x, and a little even-order pickup asymmetry."""
    t = tt(dur)
    f = hz(midi)
    idx = vel * (1.7 * np.exp(-t / 0.08) + 0.3 * np.exp(-t / 1.2))
    ph = rng.uniform(0, 2 * np.pi)
    body = np.sin(2 * np.pi * f * t + ph + idx * np.sin(2 * np.pi * f * t))
    tine = (0.18 * vel ** 2 * np.sin(2 * np.pi * 7.0 * f * t + 0.5 * np.sin(2 * np.pi * f * t))
            * np.exp(-t / 0.03))
    y = body + tine
    y = y + 0.12 * y ** 2 - 0.06
    dec = 1.6 * ring * (440.0 / f) ** 0.3
    env = np.exp(-t / dec) * (0.72 + 0.28 * np.exp(-t / 0.2))
    return fade(y * env * 0.22 * vel, a=att, r=min(rel, dur * 0.4))


def lead(midi: float, dur: float, prev: float | None = None, vel: float = 1.0, att: float = 0.012,
         rel: float = 0.05, tail: float | None = None) -> np.ndarray:
    """Soft whistle-like synth lead: a few additive harmonics, a breath of band-passed
    noise, a 15 ms legato glide from the previous note and delayed vibrato."""
    t = tt(dur)
    f0 = hz(midi)
    f = np.full_like(t, f0)
    if prev is not None:
        f = f0 * 2 ** ((prev - midi) / 12 * np.exp(-t / 0.015))
    vib = 1 + 0.0105 * np.sin(2 * np.pi * 5.4 * t) * np.clip((t - 0.18) / 0.25, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = (np.sin(ph) + 0.30 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph) + 0.04 * np.sin(4 * ph))
    br = sos_filter(noise(dur), "bandpass", [1.6 * f0, 3.2 * f0], order=2) * 0.05
    env = (1 - np.exp(-t / att)) * (0.82 + 0.18 * np.exp(-t / 0.15))
    if tail is not None:
        env *= np.exp(-t / tail)
    return fade((y + br) * env * 0.2 * vel, a=0.002, r=min(rel, dur * 0.4))


def ebass(midi: float, dur: float, vel: float = 1.0, att: float = 0.002, rel: float = 0.03,
          tail: float = 0.9) -> np.ndarray:
    """Round finger-style electric bass: additive partials whose upper harmonics die
    fast (a closing 'filter'), a tiny pitch settle and a soft finger thump."""
    t = tt(dur)
    f = hz(midi) * (1 + 0.006 * np.exp(-t / 0.02))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros_like(t)
    for k in range(1, 9):
        if k * hz(midi) > 3000:
            break
        y += (1 / k ** 1.25) * np.sin(k * ph) * np.exp(-t * (0.6 + 9.0 * (k - 1)))
    thump = sos_filter(noise(dur), "bandpass", [200, 900]) * np.exp(-t / 0.008) * 0.25
    env = 0.8 * np.exp(-t / tail) + 0.2
    return fade((y * env + thump) * 0.45 * vel, a=att, r=min(rel, dur * 0.3))


def kick(vel: float = 1.0, att: float = 0.0008) -> np.ndarray:
    t = tt(0.45)
    f = 60 + (165 - 60) * np.exp(-t / 0.025)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
    click = sos_filter(noise(0.45), "bandpass", [1500, 4500]) * np.exp(-t / 0.0025) * 0.12
    return fade((np.tanh(1.4 * y) / np.tanh(1.4) + click) * 0.75 * vel, a=att, r=0.04)


def snare(vel: float = 1.0, clap: bool = True, att: float = 0.0006) -> np.ndarray:
    """Snappy snare: two drum-head modes, band-passed wire noise, optional clap layer."""
    d = 0.4
    t = tt(d)
    head = (np.sin(2 * np.pi * 185 * t) * 0.6 + np.sin(2 * np.pi * 330 * t) * 0.3) * np.exp(-t / 0.045)
    wires = sos_filter(noise(d), "bandpass", [1800, 8500], order=2) * np.exp(-t / 0.085)
    y = head * 0.7 + wires
    if clap:
        cl = sos_filter(noise(d), "bandpass", [900, 3200], order=2)
        e = np.zeros_like(t)
        for k, dt in enumerate((0.0, 0.009, 0.018)):
            e += (t >= dt) * np.exp(-np.maximum(t - dt, 0) / (0.006 if k < 2 else 0.06))
        y += cl * e * 0.45
    return fade(y * 0.5 * vel, a=att, r=0.04)


def hat(vel: float = 1.0, open_: bool = False) -> np.ndarray:
    d = 0.35 if open_ else 0.09
    t = tt(d)
    y = sos_filter(noise(d), "bandpass", [7000, 14500], order=3)
    ring = sum(np.sin(2 * np.pi * fr * t + rng.uniform(0, 6.3)) for fr in (6100, 7900, 9300, 11200)) * 0.05
    y = (y + ring) * np.exp(-t / (0.12 if open_ else 0.022))
    return fade(y * 0.25 * vel, a=0.0008, r=0.02)


def shaker(vel: float = 1.0) -> np.ndarray:
    d = 0.11
    t = tt(d)
    y = sos_filter(noise(d), "bandpass", [4500, 11000], order=2)
    env = (t / 0.018) ** 1.5 * np.exp(1.5 * (1 - t / 0.018))   # rounded swell, peak at 18 ms
    return fade(y * env * 0.09 * vel, a=0.002, r=0.02)


def splash(dur: float = 1.4, vel: float = 1.0, att: float = 0.0008, tau: float = 0.45) -> np.ndarray:
    t = tt(dur)
    out = []
    for _ in range(2):
        wash = sos_filter(noise(dur), "bandpass", [3500, 13000], order=2)
        bell = sum(np.sin(2 * np.pi * 2600 * r * rng.uniform(0.99, 1.01) * t + rng.uniform(0, 6.3))
                   for r in (1.0, 1.43, 1.79, 2.37, 2.91)) * 0.04
        out.append(fade((wash + bell) * np.exp(-t / tau), a=att, r=0.1))
    return np.stack(out, axis=1) * 0.13 * vel


def pad(chord, dur: float, vel: float = 1.0) -> np.ndarray:
    """Quiet string-like pad: detuned band-limited saws (additive), slow attack, stereo."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for m in chord:
        for ch, det in ((0, -0.07), (1, 0.07), (0, 0.025), (1, -0.025)):
            f = hz(m + det)
            ph = rng.uniform(0, 2 * np.pi)
            y = sum(np.sin(k * (2 * np.pi * f * t + ph)) / k for k in range(1, 12) if k * f < 4000)
            out[:, ch] += y
    env = (1 - np.exp(-t / 0.35))
    return fade(out * env[:, None] * 0.018 * vel, a=0.005, r=0.08)


def swell(dur: float, vel: float = 1.0) -> np.ndarray:
    """Short noise swell into bar 3: a band-pass that sweeps up as it grows."""
    t = tt(dur)
    x = noise(dur)
    lo = sos_filter(x, "bandpass", [600, 2200], order=2)
    hi = sos_filter(x, "bandpass", [2500, 9000], order=2)
    p = t / dur
    y = (lo * (1 - p) + hi * p) * p ** 2.2
    return fade(y * 0.18 * vel, a=0.01, r=0.012)


def reverb(x: np.ndarray, rt60: float = 1.0, predelay: float = 0.012, band=(300, 7000)) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR."""
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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 90.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. Gain is held
    over the look-ahead window, released through a one-pole, then box-smoothed
    (edge-safe). It never clips the waveform."""
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


def glue(x: np.ndarray, thresh_db: float = -16.0, ratio: float = 2.0) -> np.ndarray:
    """Gentle bus compressor (RMS detector, ~10 ms attack / 150 ms release) for glue."""
    det = uniform_filter1d((x ** 2).mean(axis=1), size=int(0.01 * SR), mode="nearest")
    lvl = 10 * np.log10(det + 1e-12)
    over = np.maximum(0, lvl - thresh_db)
    gr = over * (1 - 1 / ratio)
    rc = np.exp(-1.0 / (0.15 * SR))
    g = np.empty_like(gr)
    prev = 0.0
    for n, v in enumerate(gr.tolist()):
        prev = v if v > prev else prev * rc + v * (1 - rc)
        g[n] = prev
    g = uniform_filter1d(g, size=int(0.003 * SR), mode="nearest")
    return x * (10 ** (-g / 20))[:, None]


def master(mix: np.ndarray) -> np.ndarray:
    mix = glue(mix, thresh_db=10 * np.log10(np.mean(mix ** 2) * 2) + 5.0)
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
EBMAJ9 = (55, 58, 62, 65)        # G Bb D F (rootless)
DM7 = (53, 57, 60, 62)           # F A C D
G13 = (53, 59, 62, 64)           # F B D E
CM9 = (51, 55, 58, 62)           # Eb G Bb D
F13 = (51, 55, 57, 62)           # Eb G A D
BUTTON = (50, 55, 60, 65, 70, 74)  # Bb6/9: D G C F Bb D

# (beat, chord, length in beats, velocity)
COMP = [(0, EBMAJ9, 1.4, 1.0), (1.5, EBMAJ9, 0.35, 0.7), (2.5, EBMAJ9, 1.3, 0.75),
        (4, DM7, 1.4, 0.85), (5.5, G13, 2.3, 0.8),
        (8, CM9, 1.4, 0.9), (9.5, CM9, 0.35, 0.7), (10.5, CM9, 1.3, 0.78),
        (12, CM9, 1.4, 0.85), (13.5, F13, 1.6, 0.82), (15.5, F13, 0.22, 0.95)]

# (beat, midi, length in beats): hook, answer, hook up, turnaround + pickup
MELODY = [(-1, 74, 0.5), (-0.5, 77, 0.5),
          (0, 79, 1.0), (1, 77, 0.5), (1.5, 79, 1.5), (3, 82, 0.5), (3.5, 79, 0.5),
          (4, 77, 1.0), (5, 74, 0.5), (5.5, 77, 1.5), (7, 79, 0.5), (7.5, 77, 0.5),
          (8, 79, 1.0), (9, 77, 0.5), (9.5, 79, 1.5), (11, 84, 0.5), (11.5, 82, 0.5),
          (12, 82, 1.0), (13, 81, 0.5), (13.5, 77, 1.5), (15, 79, 0.45), (15.5, 81, 0.24)]

# (beat, midi, length in beats): syncopated finger bass with a chromatic walk-up
BASS = [(0, 39, 0.8), (1.5, 39, 0.45), (2.5, 46, 0.45), (3, 39, 0.45), (3.5, 38, 0.45),
        (4, 38, 0.8), (5.5, 43, 0.9), (6.5, 43, 0.45), (7, 41, 0.45), (7.5, 35, 0.45),
        (8, 36, 0.8), (9.5, 36, 0.45), (10.5, 43, 0.45), (11, 46, 0.45), (11.5, 43, 0.45),
        (12, 41, 0.8), (13.5, 41, 0.45), (14, 36, 0.45), (14.5, 37, 0.45), (15, 38, 0.45),
        (15.5, 33, 0.24)]


def render() -> np.ndarray:
    keys = np.zeros((N, 2))      # EP comping (gets the tremolo)
    lead_bus = np.zeros((N, 2))
    pads = np.zeros((N, 2))
    drums = np.zeros((N, 2))
    low = np.zeros((N, 2))       # bass + kick: the only content below 120 Hz (mono)
    verb = np.zeros((N, 2))      # medium room send
    kick_times = []
    stop = T(15.5) + 0.12        # band stab released before the breath into the button

    # --- EP comping
    pans = (-0.3, -0.1, 0.1, 0.3)
    for b, ch, ln, vel in COMP:
        t0 = T(b) + (0 if b == 0 else human())
        dur = min(ln * BEAT, stop - t0) if b >= 15 else ln * BEAT
        for j, m in enumerate(ch):
            v = epiano(m, dur, vel, att=0.001 if b == 0 else 0.002, rel=0.05 if b < 15 else 0.03)
            place(keys, v, t0 + (0.003 * j if b not in (0, 15.5) else 0), 0.5, pans[j])
            place(verb, v, t0, 0.12, pans[j])

    # --- lead hook
    prev = None
    for i, (b, m, ln) in enumerate(MELODY):
        t0 = T(b) + (0 if b == 0 else 0.006 + human())
        legato = i > 0 and abs(MELODY[i - 1][0] + MELODY[i - 1][2] - b) < 1e-9 and b not in (8, 15.5)
        dur = ln * BEAT + (0.02 if legato else -0.02)
        v = lead(m, dur, prev if legato else None, 1.0 if b == int(b) else 0.85,
                 att=0.004 if b == 0 else 0.012, rel=0.04 if b < 15 else 0.025)
        place(lead_bus, v, t0, 1.0, pan=0.04)
        place(verb, v, t0, 0.22, pan=0.04)
        prev = m

    # --- bass
    for b, m, ln in BASS:
        t0 = T(b) + (0 if b == 0 else human() * 0.5)
        place(low, ebass(m, ln * BEAT, 1.1 if b % 4 == 0 else 0.9, att=0.001 if b == 0 else 0.002,
                         rel=0.02 if b >= 15 else 0.03), t0)

    # --- drums, bars 1-4
    for bar in range(4):
        o = bar * 4
        last = bar == 3
        for kb in (0, 2, 2.5):
            v = 1.0 if kb == 0 else 0.8
            place(low, kick(v, att=0.0008), T(o + kb))
            kick_times.append(T(o + kb))
        for sb in (1, 3):
            if last and sb == 3:
                continue
            t0 = T(o + sb) + human()
            sv, clap = (0.8, False) if bar < 2 else (0.95, True)    # the clap joins for the lift
            place(drums, snare(sv, clap), t0, 1.0, pan=-0.05)
            place(verb, snare(sv, clap), t0, 0.35, pan=-0.05)
        if bar == 1:
            place(drums, snare(0.25, clap=False), T(o + 3.75) + SW * BEAT, 1.0, pan=-0.05)  # ghost
        # hats: 8ths (16ths in bars 3-4), open hat on the "and of 4" in bar 2
        steps = np.arange(0, 4, 0.25) if bar >= 2 else np.arange(0, 4, 0.5)
        for s in steps:
            if last and s >= 3.5:
                break
            if bar == 1 and s == 3.5:
                place(drums, hat(0.75, open_=True), T(o + s) + human(), 1.0, pan=0.3)
                continue
            frac = s % 1
            sw = SW * BEAT if frac in (0.25, 0.75) else 0.0
            vel = (0.85 if frac == 0 else 0.6 if frac == 0.5 else 0.35) * (0.8 if bar < 2 else 1.0)
            place(drums, hat(vel), T(o + s) + sw + human(), 1.0, pan=0.3)
        # shaker 16ths from bar 3
        if bar >= 2:
            for s in np.arange(0, 4, 0.25):
                if last and s >= 3.0:
                    break
                sw = SW * BEAT if s % 0.5 else 0.0
                place(drums, shaker(1.0 if s % 1 == 0.5 else 0.7), T(o + s) + sw + human(), 1.0, pan=-0.35)

    # bar 4 fill: snare 16ths with a crescendo into the band stab on the "and of 4"
    for k, s in enumerate((3.0, 3.25, 3.375)):
        place(drums, snare(0.45 + 0.15 * k, clap=False), T(12 + s) + human() * 0.5, 1.0, pan=-0.05)
    place(drums, snare(1.0), T(15.5), 1.0, pan=-0.05)
    place(low, kick(0.9), T(15.5))
    kick_times.append(T(15.5))

    # intro hit on frame 0 (Bb: kick, bass, piano, splash) and a snare pickup into bar 1
    place(drums, splash(1.6, 1.0, att=0.0006), 0.0)
    place(low, kick(1.0, att=0.0006), 0.0)
    kick_times.append(0.0)
    place(low, ebass(34, 2 * BEAT - 0.03, 1.1, att=0.0006), 0.0)
    for j, m in enumerate((50, 55, 60, 65)):
        v = epiano(m, 2 * BEAT - 0.02, 1.0, att=0.0006)
        place(keys, v, 0.0, 0.5, pans[j])
        place(verb, v, 0.0, 0.14, pans[j])
    place(drums, snare(0.85), 0.0, 0.8, pan=-0.05)
    for k, b in enumerate((-1, -0.5, -0.25)):
        place(drums, snare(0.4 + 0.15 * k, clap=False), T(b) + human() * 0.5, 1.0, pan=-0.05)

    # bar-3 lift
    place(drums, swell(T(8) - T(6.5), 1.0), T(6.5), 1.0)
    place(drums, splash(1.3, 0.6), T(8))
    for b, ch, ln in ((8, CM9, 4.0), (12, CM9, 1.5), (13.5, F13, 1.8)):
        place(pads, pad(tuple(m + 12 for m in ch[1:]) + (ch[0],), ln * BEAT - 0.03), T(b))

    # --- the breath: choke every dry bus shortly after the stab, silent until the button
    tb = T(BUTTON_B)
    g = np.ones(N)
    s0, s1 = int(round(stop * SR)), int(round(tb * SR))
    nf = int(0.02 * SR)
    g[s0 - nf:s0] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf))
    g[s0:s1] = 0.0
    for bus in (keys, lead_bus, pads, drums, low):
        bus *= g[:, None]

    # --- button on frame 240 (8.0 s): kick, bass, Bb6/9, lead on the tonic, splash
    ring = DURATION_SEC - tb
    place(low, kick(1.15, att=0.0004), tb)
    kick_times.append(tb)
    place(low, ebass(34, ring, 1.25, att=0.0004, rel=0.3, tail=0.55), tb)
    for j, m in enumerate(BUTTON):
        v = epiano(m, ring, 0.95, att=0.0004, ring=0.42, rel=0.3)
        pan = (-0.35, -0.2, -0.05, 0.1, 0.25, 0.35)[j]
        place(keys, v, tb, 0.5, pan)
        place(verb, v, tb, 0.18, pan)
    v = lead(82, ring, None, 1.0, att=0.0015, rel=0.3, tail=0.55)
    place(lead_bus, v, tb, 1.0, pan=0.04)
    place(verb, v, tb, 0.22, pan=0.04)
    place(drums, splash(ring, 1.15, att=0.0004, tau=0.5), tb)
    place(drums, snare(0.8), tb, 0.9, pan=-0.05)
    place(verb, snare(0.8), tb, 0.3)

    # --- bus processing
    tr = 1 + 0.15 * np.sin(2 * np.pi * 4.2 * np.arange(N) / SR)        # gentle stereo tremolo
    keys = keys * np.stack([tr, 2 - tr], axis=1)
    keys = sos_filter(keys, "highpass", 150, order=4)
    keys = sos_filter(keys, "lowpass", 8000, order=2)
    lead_bus = sos_filter(lead_bus, "highpass", 250, order=4)
    pads = sos_filter(sos_filter(pads, "highpass", 200, order=4), "lowpass", 3500, order=2)
    drums = sos_filter(drums, "highpass", 170, order=4)
    wet = sos_filter(reverb(verb, rt60=0.9), "highpass", 220, order=4) * 0.45

    # bass ducks ~3 dB under each kick (kick stays on top without extra low-end level)
    duck = np.ones(N)
    for t0 in kick_times:
        s = int(round(t0 * SR))
        n = min(N - s, int(0.18 * SR))
        duck[s:s + n] *= 1 - 0.3 * np.exp(-np.arange(n) / (0.06 * SR))
    duck = uniform_filter1d(duck, size=int(0.004 * SR), mode="nearest")
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    low = sos_filter(low, "lowpass", 2200, order=2) * duck[:, None]
    low = sos_filter(low, "highpass", 42, order=2)

    mix = low * 0.5 + keys * 1.25 + lead_bus * 0.78 + pads * 1.6 + drums * 0.95 + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 20, order=2)
    mix = sos_filter(mix, "lowpass", 16500, order=4)

    nf = int(0.3 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    y = y - y.mean(axis=0, keepdims=True)                 # constant per-channel DC trim
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    pcm[0] = 0
    pcm[-48:] = 0
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
