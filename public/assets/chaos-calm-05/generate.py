"""chaos-calm-05: Opus Sound Directory

A 20-second storm that cuts to sunrise, at 80 BPM, for a documentary or brand ad.
It opens on a close thunder crack and a mono sub rumble at frame 0. Over the next
eight seconds the storm builds: wide hissing rain with tiny water plinks, howling
wind gusts that wander through a band-pass, and a low dissonant cluster (B, C, F,
F#) that bends slowly flat and swells. More thunder rolls in at 3.0 s, 5.75 s and
7.1 s. At frame 240 (8.0 s) the whole storm, reverb included, stops in a 3 ms fade
that ends exactly on the cue. A Bb Lydian sunrise begins on the same sample: a
soft low Bb thump and a pad that slowly opens from dark to bright through Bbmaj9,
C/Bb, Bbmaj7#11 and Bb(add9) over a Bb pedal. A breathy flute-like melody leans on
the raised fourth (E natural), synthetic bird chirps appear at the edges of the
stereo field, and high shimmer tones fade in like light. The ending rings out to
exact silence. Only the thunder sub and the Bb pedal sit below 120 Hz, in mono.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import gaussian_filter1d, minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 520240
DURATION_SEC = 20
BPM = 80
KEY = "Bb Lydian"
FPS = 30
CUE_FRAMES = (0, 240)          # frame 0: thunder crack, frame 240: storm cuts to sunrise
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.75 s
BAR = 4 * BEAT                 # 3.0 s
CUT_T = CUE_FRAMES[1] / FPS    # 8.0 s
CUT_S = int(round(CUT_T * SR)) # 384000

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


def wander(dur: float, smooth_s: float) -> np.ndarray:
    """Smoothed random walk in roughly [-1, 1] (control signal for gusts, rolls, drift)."""
    n = int(round(dur * SR))
    hop = 240
    k = n // hop + 3
    w = gaussian_filter1d(rng.standard_normal(k), smooth_s * SR / hop)
    w = w / (np.abs(w).max() + 1e-12)
    return np.interp(np.arange(n), np.arange(k) * hop, w)


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


# ---------------------------------------------------------------- storm voices
def thunder(size: float, near: float) -> tuple[np.ndarray, np.ndarray]:
    """Returns (stereo crack+roll, mono sub rumble). near in [0,1] sets the crack/roll ratio."""
    dur = 3.2
    t = tt(dur)
    # crack: a cluster of noise bursts in the first ~200 ms, the first on sample 0
    env = np.zeros_like(t)
    offs = [0.0] + sorted(rng.uniform(0.015, 0.22, 4).tolist())
    for i, o in enumerate(offs):
        m = t >= o
        dec = rng.uniform(0.010, 0.030)
        env[m] += (1.0 if i == 0 else rng.uniform(0.35, 0.8)) * np.exp(-(t[m] - o) / dec)
    crack = np.stack([sos_filter(noise(dur), "bandpass", [180, 7000]) * env,
                      sos_filter(noise(dur), "bandpass", [180, 7000]) * env], axis=1)
    # roll: low-mid noise, slow attack, tumbling amplitude
    att = 1 - np.exp(-t / 0.06)
    roll_env = att * np.exp(-t / (1.1 + 0.6 * size)) * (0.65 + 0.35 * wander(dur, 0.07))
    roll = np.stack([sos_filter(noise(dur), "bandpass", [140, 700]) * roll_env,
                     sos_filter(noise(dur), "bandpass", [140, 700]) * roll_env], axis=1)
    # sub rumble: mono, below ~90 Hz
    sub_env = (1 - np.exp(-t / 0.08)) * np.exp(-t / (1.4 + 0.8 * size)) * (0.75 + 0.25 * wander(dur, 0.12))
    sub = sos_filter(noise(dur), "lowpass", 85, order=4) * sub_env
    sub = sub / (np.abs(sub).max() + 1e-12)
    st = crack * (0.55 * near) + roll * 0.9
    return fade(st * size, a=0.001, r=0.2), fade(sub * size, a=0.001, r=0.3)


def droplet_grain(f: float, dur: float = 0.006) -> np.ndarray:
    t = tt(dur)
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.3 * t / dur)) / SR      # small upward chirp: a water "plink"
    return np.sin(ph) * np.hanning(len(t))


def cluster_tone(midi: float, dur: float, bend_cents: float) -> np.ndarray:
    """Dark detuned additive saw (partials < 2.5 kHz) with a slow downward bend: stereo."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for ch, det in enumerate((-8.0, 8.0)):
        cents = det + bend_cents * (t / dur) ** 1.5
        f = hz(midi) * 2 ** (cents / 1200)
        ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 2 * np.pi)
        y = np.zeros_like(t)
        for k in range(1, int(2500 // hz(midi)) + 1):
            y += (1 / k) / (1 + (k * hz(midi) / 900) ** 2) * np.sin(k * ph)
        out[:, ch] = y
    return out


# ---------------------------------------------------------------- sunrise voices
def pad_note(midi: float, dur: float, fc: np.ndarray, att: float, rel: float) -> np.ndarray:
    """Warm detuned additive pad whose brightness follows fc (Hz per sample): stereo."""
    t = tt(dur)
    n = len(t)
    fc = fc[:n]
    out = np.zeros((n, 2))
    f0 = hz(midi)
    for ch, cents in enumerate((-6.0, 6.0, -2.0, 2.0)):
        f = f0 * 2 ** (cents / 1200)
        ph = 2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)
        for k in range(1, int(7000 // f) + 1):
            w = (1 / k) / np.sqrt(1 + (k * f / fc) ** 4)
            out[:, ch % 2] += w * np.sin(k * ph + rng.uniform(0, 2 * np.pi))
    env = np.ones(n)
    na, nr = int(att * SR), int(rel * SR)
    env[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    env[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return out * env[:, None] * 0.2


def bird_chirp(f0: float, f1: float, dur: float) -> np.ndarray:
    """Pure-sine chirp with a fast up-and-over pitch trajectory."""
    t = tt(dur)
    u = t / dur
    f = f0 + (f1 - f0) * np.sin(np.pi * u) ** 0.7 - 0.25 * (f1 - f0) * u
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.12 * np.sin(2 * ph)
    return y * np.hanning(len(t))


def flute_line(notes, t_total: float) -> np.ndarray:
    """Legato breathy lead. notes = [(start_s, dur_s, midi)] relative to the line start: mono."""
    n = int(round(t_total * SR))
    t = np.arange(n) / SR
    # pitch curve with ~70 ms glides between notes
    bt, bf = [], []
    for i, (s, d, m) in enumerate(notes):
        g = 0.07 if i else 0.0
        bt += [s, s + g]
        bf += [np.log2(hz(notes[i - 1][2])) if i else np.log2(hz(m)), np.log2(hz(m))]
    lf = np.interp(t, bt, bf)
    vib_depth = np.zeros(n)
    amp = np.zeros(n)
    for s, d, m in notes:
        i0, i1 = int(s * SR), min(n, int((s + d) * SR))
        u = (np.arange(i1 - i0) / SR)
        vib_depth[i0:i1] = 0.0035 * np.clip((u - 0.25) / 0.4, 0, 1)
        a = np.minimum(1, u / 0.09) * (1 - 0.18 * np.exp(-u / 0.25))        # soft onset, slight bloom
        r = np.clip(((s + d) - (s + u)) / 0.16, 0, 1)                       # 160 ms release
        amp[i0:i1] = np.maximum(amp[i0:i1], a * np.sin(np.pi / 2 * r) ** 2)
    amp = gaussian_filter1d(amp, 0.004 * SR)
    f = 2 ** lf * (1 + vib_depth * np.sin(2 * np.pi * 5.1 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.22 * np.sin(2 * ph + 0.4) + 0.07 * np.sin(3 * ph + 1.1) + 0.02 * np.sin(4 * ph)
    breath = sos_filter(noise(t_total), "bandpass", [1200, 4500], order=3) * 0.035
    return (tone + breath) * amp


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


# ---------------------------------------------------------------- arrangement
def render_storm() -> tuple[np.ndarray, np.ndarray]:
    """Storm bus (stereo, >120 Hz) and its mono sub, both 0..CUT_T (+ tails cut later)."""
    S = CUT_S + int(0.01 * SR)
    t = np.arange(S) / SR
    storm = np.zeros((S, 2))
    sub = np.zeros((S, 2))
    send = np.zeros((S, 2))
    build = (t / CUT_T) ** 1.8

    # rain bed: wide hiss, intensity rises, breathes with the gusts
    gust = 0.5 + 0.5 * wander(S / SR, 0.35)
    rain_env = (0.45 + 0.55 * build) * (0.8 + 0.35 * gust)
    for ch in range(2):
        r = sos_filter(noise(S / SR), "bandpass", [420, 9500], order=2)
        r = sos_filter(r, "lowpass", 4200, order=1)
        storm[:, ch] += 0.30 * r * rain_env
    # droplets: sparse impulse trains through short chirped grains
    for ch in range(2):
        for f in np.exp(rng.uniform(np.log(1600), np.log(7200), 14)):
            dens = 38
            imp = np.zeros(S)
            k = rng.poisson(dens * S / SR)
            pos = rng.integers(0, S, k)
            np.add.at(imp, pos, rng.lognormal(0, 0.45, k))
            g = droplet_grain(f, dur=rng.uniform(0.004, 0.008))
            storm[:, ch] += 0.11 * signal.fftconvolve(imp, g)[:S] * rain_env
    # wind: band-pass sweeps wandering 300 Hz .. 1.6 kHz, two independent channels
    wind_amp = (0.35 + 0.65 * build) * (0.3 + 0.7 * gust ** 1.5)
    for ch in range(2):
        fc = 650 * 2 ** (1.25 * wander(S / SR, 0.25))
        w = svf_bandpass(noise(S / SR), fc, 3.5)
        storm[:, ch] += 0.55 * w * wind_amp
    # dissonant cluster: B2 C3 F3 F#3, bends flat, swells into the cut
    cl_env = np.clip((t - 0.8) / (CUT_T - 0.8), 0, 1) ** 2.2
    trem = 0.8 + 0.2 * np.sin(2 * np.pi * 3.3 * t + 1.0)
    for i, m in enumerate((47, 48, 53, 54, 59)):
        ct = cluster_tone(m, S / SR, bend_cents=-35 - 10 * i)
        ct = sos_filter(ct, "highpass", 130, order=2)
        storm += 0.075 * ct * (cl_env * trem)[:, None]
        send += 0.03 * ct * cl_env[:, None]

    # thunder: frame-0 crack, distant roll, near strike, rolling tail into the cut
    for t0, size, near in ((0.0, 1.0, 1.0), (3.0, 0.55, 0.25), (5.75, 0.9, 0.9), (7.1, 0.7, 0.5)):
        st, sb = thunder(size, near)
        place(storm, st, t0, 1.15, pan=0.0)
        place(send, st, t0, 0.35)
        place(sub, np.stack([sb, sb], 1), t0, 0.42)

    storm = sos_filter(storm, "highpass", 140, order=2)
    storm = storm + 0.4 * sos_filter(reverb(send, 2.2, band=(180, 4000)), "highpass", 140, order=2)
    return storm, sub


def render_sunrise() -> tuple[np.ndarray, np.ndarray]:
    """Sunrise bus (stereo) and its mono Bb pedal, starting exactly at CUT_T."""
    music = np.zeros((N, 2))
    low = np.zeros((N, 2))
    send = np.zeros((N, 2))
    D = DURATION_SEC - CUT_T                    # 12 s
    tu = np.arange(int(D * SR) + SR) / SR       # sunrise-relative clock
    bright = 420 * (2600 / 420) ** np.clip(tu / 8.0, 0, 1) ** 1.3    # the pad opens over 8 s

    # chords per bar (3 s each) over a Bb pedal: Bbmaj9 | C/Bb | Bbmaj7#11 | Bb(add9), tenor voice F3/E3 for warmth
    chords = [(53, 58, 65, 69, 72, 74), (52, 60, 64, 67, 72, 76), (53, 58, 65, 69, 76, 81), (53, 58, 65, 70, 72, 74)]
    levels = (0.75, 0.9, 1.0, 0.85)
    for b, ch in enumerate(chords):
        s = b * BAR
        dur = BAR + (0.9 if b < 3 else D - 3 * BAR - BAR)
        att = 0.35 if b == 0 else 0.9
        rel = 1.0 if b < 3 else 2.2
        for m in ch:
            p = pad_note(m, dur, bright[int(s * SR):], att, rel)
            place(music, p, CUT_T + s, 0.5 * levels[b])
            place(send, p, CUT_T + s, 0.25 * levels[b])

    # first light: a soft low Bb thump on the cue sample (Bb1 + Bb2 + F3)
    tb = tt(2.2)
    thump = (np.sin(2 * np.pi * hz(34) * tb) + 0.45 * np.sin(2 * np.pi * hz(46) * tb)) * np.exp(-tb / 0.9)
    place(low, fade(thump, a=0.03, r=0.3), CUT_T, 0.42)
    warm = (np.sin(2 * np.pi * hz(53) * tb) + 0.3 * np.sin(2 * np.pi * hz(65) * tb)) * np.exp(-tb / 0.6)
    place(music, fade(warm, a=0.02, r=0.3), CUT_T, 0.10)
    place(send, fade(warm, a=0.02, r=0.3), CUT_T, 0.10)

    # Bb pedal: sine + soft 2nd harmonic, slow swell, mono
    pd = D
    tp = tt(pd)
    ped = np.sin(2 * np.pi * hz(34) * tp) + 0.25 * np.sin(2 * np.pi * hz(46) * tp)
    ped_env = np.clip((tp - 0.6) / 3.0, 0, 1) ** 1.5 * (1 - 0.15 * np.clip((tp - 9) / 3, 0, 1))
    place(low, fade(ped * ped_env, a=0.01, r=1.5), CUT_T, 0.18)

    # high shimmer "light rays": E6, A6, D7 (the #11 and the 7th), slow tremolo
    for i, m in enumerate((88, 93, 98)):
        d = D - 2.0 - i * 0.6
        ts = tt(d)
        y = np.sin(2 * np.pi * hz(m) * ts + rng.uniform(0, 6.3)) * (0.7 + 0.3 * np.sin(2 * np.pi * (0.23 + 0.07 * i) * ts))
        env = np.clip(ts / 3.5, 0, 1) ** 2
        place(music, fade(y * env, a=0.05, r=1.6), CUT_T + 2.0 + i * 0.6, 0.022, pan=(-0.6, 0.6, 0.0)[i])
        place(send, fade(y * env, a=0.05, r=1.6), CUT_T + 2.0 + i * 0.6, 0.02)

    # gentle melody (beats relative to the cut): leans on E natural, the Lydian colour
    mel = [(2, 1, 77), (3, 1, 81),
           (4, 1.5, 79), (5.5, 0.5, 76), (6, 1, 79), (7, 1, 84),
           (8, 2, 81), (10, 1, 77), (11, 1, 76),
           (12, 1, 72), (13, 2.4, 74)]
    notes = [(b * BEAT, d * BEAT - 0.02, m) for b, d, m in mel]
    fl = flute_line(notes, D)
    fl = fade(fl, a=0.01, r=0.3)
    place(music, fl, CUT_T, 0.16, pan=-0.12)
    place(send, np.stack([fl, fl], 1), CUT_T, 0.09)

    # birds: short chirp phrases at the edges of the field from bar 2
    for t0 in (3.3, 4.6, 6.2, 7.1, 8.4, 9.5):
        pan = rng.choice([-0.8, 0.75]) * rng.uniform(0.8, 1.0)
        base = rng.uniform(2800, 3800)
        for j in range(int(rng.integers(2, 5))):
            d = rng.uniform(0.05, 0.11)
            c = bird_chirp(base * rng.uniform(0.9, 1.05), base * rng.uniform(1.25, 1.5), d)
            tj = CUT_T + t0 + j * rng.uniform(0.09, 0.15)
            place(music, c, tj, 0.035 * rng.uniform(0.7, 1.0), pan=pan)
            place(send, np.stack([c, c], 1), tj, 0.02)

    music = sos_filter(music, "highpass", 130, order=2)
    wet = sos_filter(reverb(send, 2.8, band=(200, 9000), predelay=0.03), "highpass", 140, order=2)
    music = music + 0.5 * wet
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    return music, low


def bus_chain(x: np.ndarray) -> np.ndarray:
    """Master bus filters: mono below ~250 Hz (M/S high-pass on the side), subsonic + top trims."""
    mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    x = np.stack([mid + side, mid - side], axis=1)
    x = sos_filter(x, "highpass", 22, order=2)
    return sos_filter(x, "lowpass", 16500, order=4)


def render() -> np.ndarray:
    storm, storm_sub = render_storm()
    storm_full = np.zeros((N, 2))
    storm_full[: len(storm)] = storm + np.repeat(storm_sub.mean(axis=1, keepdims=True), 2, 1)
    # the bus filters run BEFORE the gate so no filter ringing leaks past the cut
    storm_full = bus_chain(storm_full)
    # the cut: storm (dry + reverb + sub) ends in a 3 ms raised-cosine fade landing on the cue sample
    nf = int(0.003 * SR)
    gate = np.ones(N)
    gate[CUT_S - nf:CUT_S] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf))
    gate[CUT_S:] = 0.0
    na = int(0.001 * SR)                         # frame-0 hit: ~1 ms raised-cosine attack on the whole storm
    gate[:na] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    storm_full *= gate[:, None]

    sunrise, low = render_sunrise()
    mix = storm_full + bus_chain(sunrise * 0.5 + low * 0.3)

    nf = int(1.2 * SR)
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
