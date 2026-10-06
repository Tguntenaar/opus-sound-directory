"""synthwave-drive-20s: Opus Sound Directory

A 20-second 80s night-drive cue in A minor at 100 BPM, moving i-VI-III-VII (Am, F, C, G).
Frame 0 is a triplet pickup: a big gated-reverb snare with a tom, a lower tom on the next
triplet, and the first downbeat at 0.4 s. The verse drives on an octave-bouncing
band-limited saw bass in sixteenths, a lush detuned juno-style pad that slowly opens, a
ping-pong 25 % pulse arpeggio, kick and eighth hats. Gated snares join in bar 3, a noise
riser sweeps up through bar 4, and a gated tom fill drops into a short breath of
near-silence. On frame 300 (10.0 s) the chorus lands with a crash, four-on-the-floor kick,
sixteenth hats and a pulse-width-modulated lead hook with portamento, vibrato, delay and
hall. Bar 8 stops short after a tom fill. On frame 570 (19.0 s) a final hit lands: kick,
gated snare, crash, a wide Am saw stab, A1 bass and a high A on the lead. It rings into
a one-second hall tail that fades to silence. Below 120 Hz there is only the mono kick
and bass.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 9100570
DURATION_SEC = 20
BPM = 100
KEY = "A minor"
FPS = 30
CUE_FRAMES = (0, 300, 570)     # frame 0: pickup hit, 300: lead hook + chorus, 570: final hit
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.6 s
S16 = BEAT / 4                 # 0.15 s
GRID0 = 0.4                    # first downbeat: frame 0 is a two-triplet pickup into it
HOOK_T = CUE_FRAMES[1] / FPS   # 10.0 s = bar 5 downbeat
END_T = CUE_FRAMES[2] / FPS    # 19.0 s = bar 8, beat 4
BREAK_T = HOOK_T - 0.3         # breath before the chorus
STOP_T = END_T - 0.3           # stop-time before the final hit

rng = np.random.default_rng(SEED)


def bar(k: int) -> float:
    return GRID0 + 4 * BEAT * k


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    sh = (slice(None),) + (None,) * (x.ndim - 1)
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na)))[sh]
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr)))[sh]
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
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


# ---------------------------------------------------------------- band-limited oscillators
TBL = 8192


def saw_table(kmax: int, fc_ratio: float | None = None) -> np.ndarray:
    """One cycle of a band-limited saw (harmonics 1..kmax), optional baked-in 24 dB/oct
    roll-off at harmonic number fc_ratio. Zero mean. Wrapped by one sample for interp."""
    ph = np.arange(TBL) / TBL
    y = np.zeros(TBL)
    for k in range(1, max(1, kmax) + 1):
        a = 1.0 / k
        if fc_ratio:
            a /= np.sqrt(1 + (k / fc_ratio) ** 4)
        y += a * np.sin(2 * np.pi * k * ph)
    return np.append(y, y[0])


def wt(table: np.ndarray, phase: np.ndarray) -> np.ndarray:
    """Read a single-cycle table at phase (cycles, any real); linear interpolation."""
    p = np.mod(phase, 1.0) * TBL
    return np.interp(p, np.arange(TBL + 1), table)


def kmax_for(fmax: float, limit: float = 15000.0) -> int:
    return int(limit // fmax)


# ---------------------------------------------------------------- voices
def pad_chord(midis, dur: float, bright0: float, bright1: float) -> np.ndarray:
    """Juno-ish pad: per note four detuned saws with slow chorus drift, a dark and a bright
    table crossfaded to open the 'filter', soft attack and release. Stereo."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    b = np.linspace(bright0, bright1, len(t))
    for m in midis:
        f0 = hz(m)
        km = kmax_for(f0 * 1.01, 12000)
        dark, light = saw_table(km, 900 / f0), saw_table(km, 3200 / f0)
        for i, cents in enumerate((-11, -4, 4, 11)):
            drift = 1 + 0.0018 * np.sin(2 * np.pi * (0.23 + 0.07 * i) * t + rng.uniform(0, 6.28))
            ph = np.cumsum(f0 * 2 ** (cents / 1200) * drift) / SR + rng.uniform()
            y = (1 - b) * wt(dark, ph) + b * wt(light, ph)
            pan = (-0.8, -0.3, 0.3, 0.8)[i]
            th = (pan + 1) * np.pi / 4
            out[:, 0] += y * np.cos(th)
            out[:, 1] += y * np.sin(th)
    env = np.ones(len(t))
    na, nr = int(0.12 * SR), int(0.25 * SR)
    env[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    env[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return out * env[:, None] * 0.05


def bass_note(midi: float, dur: float, accent: float = 1.0) -> np.ndarray:
    """Saw bass with a plucked low-pass envelope (additive, so the 'filter' never aliases)
    and a sine sub. Mono."""
    t = tt(dur)
    f = hz(midi)
    fc = 260 + 1500 * accent * np.exp(-t / 0.06)
    y = np.zeros_like(t)
    for k in range(1, int(4000 // f) + 1):
        a = (1 / k) / np.sqrt(1 + (k * f / fc) ** 4)
        y += a * np.sin(2 * np.pi * k * f * t)
    y += 0.5 * np.sin(2 * np.pi * f * t)
    env = 0.75 + 0.25 * np.exp(-t / 0.05)
    return fade(y * env * 0.33, a=0.0015, r=0.012)


def arp_note(midi: float, dur: float, bright: float) -> np.ndarray:
    """25 % pulse pluck: Fourier series of the pulse, upper harmonics decaying faster."""
    t = tt(dur)
    f = hz(midi)
    y = np.zeros_like(t)
    for k in range(1, kmax_for(f, 14000) + 1):
        a = (2 / (np.pi * k)) * np.sin(np.pi * k * 0.25)
        if abs(a) < 1e-6:
            continue
        a *= np.exp(-(k - 1) * 0.12 / bright)
        y += a * np.exp(-t * (9 + 2.2 * k / bright)) * np.sin(2 * np.pi * k * f * t)
    return fade(y * 0.3, a=0.001, r=0.01)


def lead_voice(notes, t0: float, dur: float) -> np.ndarray:
    """PWM lead: difference of two band-limited saws (exact band-limited pulse), width
    swept by a slow LFO; 45 ms portamento between notes, delayed vibrato, retriggered
    envelope. notes = [(start_s, length_s, midi)] relative to t0."""
    n = int(round(dur * SR))
    t = np.arange(n) / SR
    logf = np.full(n, np.log2(hz(notes[0][2])))
    amp = np.zeros(n)
    vib_on = np.zeros(n)
    for st, ln, m in notes:
        s = int(round(st * SR))
        logf[s:] = np.log2(hz(m))
        e = min(n, int(round((st + ln) * SR)))
        tl = np.arange(e - s) / SR
        a_ = np.minimum(1, tl / 0.004) * (0.8 + 0.2 * np.exp(-tl / 0.12))
        rel = np.clip((tl - (ln - 0.03)) / 0.03, 0, 1)
        amp[s:e] = np.maximum(amp[s:e], a_ * (0.5 + 0.5 * np.cos(np.pi * rel)))
        vib_on[s:e] = np.clip((tl - 0.22) / 0.25, 0, 1)
    # portamento: one-pole glide in the log-frequency domain
    a = np.exp(-1 / (0.045 * SR))
    logf = signal.lfilter([1 - a], [1, -a], logf, zi=[a * logf[0]])[0]
    vib = 1 + 0.006 * vib_on * np.sin(2 * np.pi * 5.6 * t)
    f = 2 ** logf * vib
    km = kmax_for(f.max() * 1.01, 15000)
    tab = saw_table(km, 11.0)
    ph = np.cumsum(f) / SR
    width = 0.5 + 0.32 * np.sin(2 * np.pi * 0.55 * t + 1.0)
    y = wt(tab, ph) - wt(tab, ph + width)
    y2 = wt(tab, ph * 1.003) - wt(tab, ph * 1.003 + width * 0.92)   # slight unison
    amp = uniform_filter1d(amp, 48, mode="nearest")
    return np.stack([(y + 0.5 * y2) * amp, (0.5 * y + y2) * amp], axis=1) * 0.11


def stab_chord(midis, dur: float) -> np.ndarray:
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for m in midis:
        f0 = hz(m)
        tab = saw_table(kmax_for(f0 * 1.01, 14000), 4500 / f0)
        for i, c in enumerate((-9, 9)):
            ph = np.cumsum(np.full(len(t), f0 * 2 ** (c / 1200))) / SR + rng.uniform()
            out[:, i] += wt(tab, ph)
    env = np.exp(-t / 0.45)
    return fade(out * env[:, None] * 0.09, a=0.0008, r=0.08)


def kick(big: bool = False) -> np.ndarray:
    t = tt(0.45 if big else 0.32)
    f = 48 + (160 - 48) * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.2 if big else 0.13))
    beater = sos_filter(noise(len(t) / SR), "bandpass", [1500, 6000]) * np.exp(-t / 0.003) * 0.3
    return fade(np.tanh(1.7 * (body + beater)) / np.tanh(1.7), a=0.0004, r=0.01)


def snare_dry(big: bool = False) -> np.ndarray:
    d = 0.25
    t = tt(d)
    tone = (np.sin(2 * np.pi * 185 * t) + 0.45 * np.sin(2 * np.pi * 320 * t)) * np.exp(-t / 0.05)
    nz = sos_filter(noise(d), "bandpass", [1200, 9500]) * np.exp(-t / 0.09)
    crack = sos_filter(noise(d), "highpass", 2500) * np.exp(-t / 0.005)
    return fade((0.6 * tone + nz + 0.6 * crack) * (0.55 if big else 0.42), a=0.0004, r=0.01)


def tom(f0: float) -> np.ndarray:
    t = tt(0.35)
    f = f0 * (1 + 0.6 * np.exp(-t / 0.03))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    y += sos_filter(noise(0.35), "bandpass", [600, 4000]) * np.exp(-t / 0.01) * 0.25
    return fade(y * 0.5, a=0.0004, r=0.02)


def hat(open_: bool = False) -> np.ndarray:
    d = 0.2 if open_ else 0.045
    t = tt(d)
    y = sos_filter(noise(d), "highpass", 7500, order=4)
    y = sos_filter(y, "lowpass", 15000, order=4)
    y *= np.exp(-t / (0.06 if open_ else 0.011))
    return fade(y * 0.26, a=0.0004, r=0.005)


def crash(dur: float = 2.0) -> np.ndarray:
    t = tt(dur)
    env = np.exp(-t / 0.6)
    ch = [sos_filter(sos_filter(noise(dur), "bandpass", [3500, 14500]), "lowpass", 15000) for _ in range(2)]
    return np.stack([fade(c * env, 0.0004, 0.05) for c in ch], axis=1) * 0.24


def svf_bandpass(x: np.ndarray, fc: np.ndarray, q: float) -> np.ndarray:
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
    u = t / dur
    fc = 400 * (8000 / 400) ** (u ** 1.3)
    amp = u ** 2
    l = svf_bandpass(noise(dur), fc, 3.0) * amp
    r = svf_bandpass(noise(dur), fc * 1.05, 3.0) * amp
    return np.stack([fade(l, 0.01, 0.02), fade(r, 0.01, 0.02)], axis=1) * 0.5


def reverb(x: np.ndarray, rt60: float, band=(250, 7000), predelay: float = 0.02) -> np.ndarray:
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", list(band)) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


def pingpong(x: np.ndarray, delay: float, fb: float, taps: int = 6) -> np.ndarray:
    d = int(round(delay * SR))
    m = x.mean(axis=1)
    out = np.zeros_like(x)
    for i in range(1, taps + 1):
        s = d * i
        if s >= len(x):
            break
        tap = sos_filter(m[: len(x) - s], "lowpass", 5000 / i ** 0.3) * fb ** (i - 1)
        out[s:, (i + 1) % 2] += tap
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
AM, F, C, G = "Am", "F", "C", "G"
PAD = {AM: (57, 60, 64, 69), F: (53, 57, 60, 64), C: (55, 60, 64, 67), G: (55, 59, 62, 67)}
ROOT = {AM: 33, F: 29, C: 36, G: 31}                     # A1 F1 C2 G1
ARP = {AM: (69, 72, 76, 81), F: (65, 69, 72, 77), C: (67, 72, 76, 79), G: (67, 71, 74, 79)}
PROG = (AM, F, C, G, AM, F, C, G)


def render() -> np.ndarray:
    low = np.zeros((N, 2))         # kick + bass, mono
    drums = np.zeros((N, 2))
    gate_send = np.zeros((N, 2))   # snare/toms into the gated plate
    music = np.zeros((N, 2))       # pad, arp (pumped)
    lead = np.zeros((N, 2))
    fx = np.zeros((N, 2))
    hall_send = np.zeros((N, 2))
    gate_hits = []
    kicks = []

    def gated(x, t, gain, pan=0.0, send=0.9):
        place(drums, x, t, gain, pan)
        place(gate_send, x, t, gain * send, pan)
        gate_hits.append(t)

    # --- frame 0 pickup: two triplet eighths into the first downbeat
    gated(snare_dry(big=True), 0.0, 1.0)
    gated(tom(150), 0.0, 0.7)
    gated(tom(118), 0.2, 0.8, pan=-0.15)

    # --- drums, verse (bars 1-4) and chorus (bars 5-8)
    for k in range(8):
        b0 = bar(k)
        nb = 3 if k == 7 else 4
        for bt in range(nb):
            t = b0 + bt * BEAT
            chorus = k >= 4
            if k == 7 and bt == 2:
                continue                                  # fill beat
            if k == 3 and bt == 3:
                continue                                  # fill beat
            if chorus or k >= 2 or bt in (0, 2):
                place(low, kick(), t, 0.95 if chorus else 0.8)
                kicks.append(t)
            if bt in (1, 3) and k >= 2:
                gated(snare_dry(), t, 0.95 if chorus else 0.75)
        # hats
        n16 = nb * 4
        for i in range(n16):
            t = b0 + i * S16
            if (k == 3 and t >= BREAK_T - 0.3) or (k == 7 and t >= bar(7) + 2 * BEAT):
                break
            if k < 2 and i % 2:
                continue
            if k >= 4 and i % 4 == 2:
                place(drums, hat(open_=True), t, 0.5, pan=0.25)
                continue
            acc = (1.0, 0.55, 0.8, 0.55)[i % 4] * rng.uniform(0.9, 1.05)
            place(drums, hat(), t, acc * (0.8 if k < 4 else 1.0), pan=-0.3)
    # pickup flam end of bar 2 into the snare entry
    gated(snare_dry(), bar(2) - 2 * S16, 0.45, pan=0.1)
    gated(snare_dry(), bar(2) - S16, 0.6, pan=-0.1)
    # tom fills: into the chorus and into the final hit
    for i, f0 in enumerate((165, 135)):
        gated(tom(f0), bar(3) + 3 * BEAT + i * S16, 0.9, pan=(0.35, -0.3)[i])
    for i, f0 in enumerate((170, 140)):
        gated(tom(f0), bar(7) + 2 * BEAT + i * S16, 0.95, pan=(0.35, -0.3)[i])
    place(fx, crash(), GRID0, 0.55)
    place(fx, crash(), HOOK_T, 1.0)

    # --- bass: sixteenth octave bounce
    for k in range(8):
        root = ROOT[PROG[k]]
        for i in range(16):
            t = bar(k) + i * S16
            if (BREAK_T - 1e-6 <= t < HOOK_T) or t >= STOP_T - 1e-6:
                continue
            m = root + (12 if i % 2 else 0)
            acc = 1.0 if i % 4 == 0 else 0.7
            place(low, bass_note(m, S16 + 0.004, acc), t, 0.9 if k >= 4 else 0.8)

    # --- pad: one chord per bar, opening across the verse, bright in the chorus
    for k in range(8):
        t0 = bar(k)
        d = 4 * BEAT + 0.25
        if k == 7:
            d = STOP_T - t0 + 0.1
        br0, br1 = (k / 4, (k + 1) / 4) if k < 4 else (0.85, 1.0)
        pv = pad_chord(PAD[PROG[k]], d, min(br0, 1), min(br1, 1))
        place(music, pv, t0, 0.9 if k >= 4 else 0.8)
        place(hall_send, pv, t0, 0.35)
    # pre-roll pad from frame 0 (soft swell into bar 1)
    place(music, pad_chord(PAD[AM], GRID0 + 0.3, 0.0, 0.1), 0.0, 0.5)

    # --- arp: sixteenth ping-pong pulse plucks
    arp_bus = np.zeros((N, 2))
    pat = (0, 1, 2, 3, 2, 1, 2, 3)
    for k in range(8):
        tones = ARP[PROG[k]]
        for i in range(16):
            t = bar(k) + i * S16
            if (BREAK_T - 1e-6 <= t < HOOK_T) or t >= bar(7) + 2 * BEAT - 1e-6:
                continue
            br = 0.35 + 0.15 * k if k < 4 else 1.0
            m = tones[pat[i % 8]] + (12 if (k >= 4 and i % 8 == 3) else 0) - 12
            vel = (0.55 if k < 2 else 0.75 if k < 4 else 0.7) * (1.0 if i % 4 == 0 else 0.75)
            place(arp_bus, arp_note(m, S16 * 1.6, br), t, vel, pan=0.35 * (-1) ** i)
    music += arp_bus
    music += pingpong(arp_bus, 3 * S16, 0.45) * 0.45

    # --- riser through bar 4 into the break
    place(fx, riser(BREAK_T - bar(3)), bar(3), 0.5)

    # --- lead hook from frame 300
    q = BEAT
    melody = [(0, 1.5, 76), (1.5, 0.5, 74), (2, 1, 72), (3, 1, 69),
              (4, 1.5, 72), (5.5, 0.5, 74), (6, 1.5, 77), (7.5, 0.5, 76),
              (8, 1.5, 79), (9.5, 0.5, 77), (10, 1, 76), (11, 1, 72),
              (12, 1, 74), (13, 0.5, 71), (13.5, 0.75, 74)]
    notes = [(b * q, d * q - 0.01, m) for b, d, m in melody]
    lv = lead_voice(notes, HOOK_T, STOP_T - HOOK_T)
    place(lead, lv, HOOK_T)

    # --- final hit, frame 570
    place(low, kick(big=True), END_T, 1.0)
    kicks.append(END_T)
    gated(snare_dry(big=True), END_T, 1.0)
    place(low, bass_note(33, 0.9, 1.2), END_T, 1.0)
    place(fx, crash(), END_T, 1.0)
    st = stab_chord((45, 52, 57, 60, 64, 69), 1.0)
    place(music, st, END_T, 1.0)
    place(hall_send, st, END_T, 0.6)
    fin = lead_voice([(0.0, 0.85, 81)], END_T, 0.9)
    place(lead, fin, END_T, 0.8)

    # --- buses
    # sidechain pump on the pad/arp bus from every kick
    duck = np.ones(N)
    tk = tt(0.3)
    shape = 1 - 0.4 * np.exp(-tk / 0.09) * (1 - np.exp(-tk / 0.003))
    for kt in kicks:
        s0 = int(round(kt * SR))
        e = min(N, s0 + len(shape))
        duck[s0:e] = np.minimum(duck[s0:e], shape[: e - s0])
    music *= duck[:, None]

    # gated plate: dense bright reverb, hard (but smoothed) gate ~210 ms after each hit
    plate = reverb(sos_filter(gate_send, "highpass", 150, order=2), 2.2, band=(300, 9000), predelay=0.004)
    gate = np.zeros(N)
    ga = tt(0.24)
    gshape = np.where(ga < 0.2, 1.0, 0.5 + 0.5 * np.cos(np.pi * np.clip((ga - 0.2) / 0.04, 0, 1)))
    gshape *= np.minimum(1, ga / 0.002)
    for gt in gate_hits:
        s0 = int(round(gt * SR))
        e = min(N, s0 + len(gshape))
        gate[s0:e] = np.maximum(gate[s0:e], gshape[: e - s0])
    plate = plate * gate[:, None] * 1.1

    lead = sos_filter(lead, "highpass", 200, order=2)
    lead_fx = pingpong(lead, 3 * S16, 0.35, taps=4) * 0.3
    hall_send += lead * 0.5
    hall = sos_filter(reverb(hall_send, 2.6, band=(250, 6500), predelay=0.03), "highpass", 200, order=2) * 0.45

    hp = lambda x, f: sos_filter(x, "highpass", f, order=4)
    music = hp(music, 150)
    drums = hp(drums, 110)
    fx = hp(fx, 300)
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    low = sos_filter(low, "lowpass", 3500, order=2)

    mix = low * 0.9 + drums * 0.9 + plate * 0.6 + music * 1.0 + lead * 1.3 + lead_fx + fx * 0.7 + hall
    # steep side high-pass: everything below ~250 Hz is mono
    m_, s_ = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    s_ = sos_filter(s_, "highpass", 250, order=8)
    mix = np.stack([m_ + s_, m_ - s_], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 16500, order=4)

    nt = int(0.35 * SR)
    mix[-nt:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nt)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    y -= y.mean(axis=0, keepdims=True)            # constant per-channel DC trim
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
