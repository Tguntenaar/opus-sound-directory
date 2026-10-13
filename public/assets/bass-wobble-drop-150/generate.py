"""bass-wobble-drop-150 -- take 3 (heavy riddim)

CREATIVE BRIEF
Bass music made entirely in code; the 8th-note grid is the master clock. 14.4 s at 150 BPM in F minor.
Take angle: heavy riddim. Minimal, darker and repetitive. The brief's build is kept: an accelerating snare roll
(4ths -> 8ths -> 16ths -> 32nds), a noise riser whose high-pass sweeps 200 Hz -> 8 kHz, a pitch riser on F, a
filtered Fm chord stab each bar, and 0.1 s of true silence before the drop. Frame 96 drops into half-time
(kick on 1, snare on 3). The bass is a square + FM riddim patch (a band-limited square on F2 plus an FM pair
with a swept index) into a resonant 24 dB/oct low-pass, chopped by tight LFO gates. Each gate pulse also
fires a filter envelope. The gate rate switches every half-bar and is mostly 1/16T, alternating with 1/8,
1/8T, 1/16 and one 1/4 as written below. The line is a pedal on F that touches Ab, Db and C only on the
second half of bars 4-6 (F-Ab-Db-C, little melody). The snare is metallic: a 200 Hz body, inharmonic
ring-modulated partials, 2 kHz band-passed noise and a short plate. A heavier pure-sine sub sits under 100 Hz
in mono. Bars 7-8 add a dark growl (u/o vowels, no speech) on the same gates and a 1-beat stutter fill.
Frame 384: kick + sub + reverse cymbal into it, ringing out to true silence before 14.4 s.
Mix chain (all ten steps named in master()): EQ, saturation, multiband split, sidechain to the kick,
stereo-widen only above 250 Hz, bus glue compression, soft clip, limiter, DC high-pass, final true-peak trim.
Every oscillator is additive with partials under 16 kHz, so nothing aliases.

CUE SHEET
Grid: 48 kHz; 1 frame = 1/30 s = 1600 samples; 150 BPM 4/4 -> 1 beat = 12 frames, 8th = 6 frames,
16th = 3 frames, 32nd = 1.5 frames, 1 bar = 48 frames. Total 432 frames = 14.4 s = 691200 samples.
Bass roots: 3 F | 4 F Ab | 5 F Db | 6 F C | 7 F | 8 F (half-bars); Fm stab in the build.
Gate/LFO rates: 1/4 = 1 cycle/beat, 1/8 = 2, 1/8T = 3, 1/16 = 4, 1/16T = 6 (restarting each half-bar).
The code parses the rows below; nothing else in the script carries timing.

frame  | bar:beat | EVENT    | value
-------+----------+----------+------------------------------------------
0      | 1:1.000  | PITCH    | F3->F5, to 93
0      | 1:1.000  | RISER    | noise HP 200->8000 Hz, to 93
0      | 1:1.000  | ROLL     | 1/4
0      | 1:1.000  | STAB     | lp=450
12     | 1:2.000  | ROLL     | 1/4
24     | 1:3.000  | ROLL     | 1/8
30     | 1:3.500  | ROLL     | 1/8
36     | 1:4.000  | ROLL     | 1/8
42     | 1:4.500  | ROLL     | 1/8
48     | 2:1.000  | ROLL     | 1/16
48     | 2:1.000  | STAB     | lp=1500
51     | 2:1.250  | ROLL     | 1/16
54     | 2:1.500  | ROLL     | 1/16
57     | 2:1.750  | ROLL     | 1/16
60     | 2:2.000  | ROLL     | 1/16
63     | 2:2.250  | ROLL     | 1/16
66     | 2:2.500  | ROLL     | 1/16
69     | 2:2.750  | ROLL     | 1/16
72     | 2:3.000  | ROLL     | 1/32
73.5   | 2:3.125  | ROLL     | 1/32
75     | 2:3.250  | ROLL     | 1/32
76.5   | 2:3.375  | ROLL     | 1/32
78     | 2:3.500  | ROLL     | 1/32
79.5   | 2:3.625  | ROLL     | 1/32
81     | 2:3.750  | ROLL     | 1/32
82.5   | 2:3.875  | ROLL     | 1/32
84     | 2:4.000  | ROLL     | 1/32
85.5   | 2:4.125  | ROLL     | 1/32
87     | 2:4.250  | ROLL     | 1/32
88.5   | 2:4.375  | ROLL     | 1/32
90     | 2:4.500  | ROLL     | 1/32
91.5   | 2:4.625  | ROLL     | 1/32
93     | 2:4.750  | SILENCE  | to 96 (true digital silence)
96     | 3:1.000  | KICK     | beat 1 (half-time)
96     | 3:1.000  | LFO      | 1/16T
96     | 3:1.000  | NOTE     | F1
120    | 3:3.000  | LFO      | 1/8
120    | 3:3.000  | SNARE    | beat 3 (half-time)
144    | 4:1.000  | KICK     | beat 1 (half-time)
144    | 4:1.000  | LFO      | 1/16T
144    | 4:1.000  | NOTE     | F1
168    | 4:3.000  | LFO      | 1/8T
168    | 4:3.000  | NOTE     | Ab1
168    | 4:3.000  | SNARE    | beat 3 (half-time)
192    | 5:1.000  | KICK     | beat 1 (half-time)
192    | 5:1.000  | LFO      | 1/16T
192    | 5:1.000  | NOTE     | F1
216    | 5:3.000  | LFO      | 1/16
216    | 5:3.000  | NOTE     | Db2
216    | 5:3.000  | SNARE    | beat 3 (half-time)
240    | 6:1.000  | KICK     | beat 1 (half-time)
240    | 6:1.000  | LFO      | 1/16T
240    | 6:1.000  | NOTE     | F1
264    | 6:3.000  | LFO      | 1/4
264    | 6:3.000  | NOTE     | C2
264    | 6:3.000  | SNARE    | beat 3 (half-time)
288    | 7:1.000  | GROWL    | u-o-u-a-u-o-u, to 372
288    | 7:1.000  | KICK     | beat 1 (half-time)
288    | 7:1.000  | LFO      | 1/16T
288    | 7:1.000  | NOTE     | F1
312    | 7:3.000  | LFO      | 1/8T
312    | 7:3.000  | SNARE    | beat 3 (half-time)
336    | 8:1.000  | KICK     | beat 1 (half-time)
336    | 8:1.000  | LFO      | 1/16T
336    | 8:1.000  | NOTE     | F1
360    | 8:3.000  | LFO      | 1/16
360    | 8:3.000  | REVCYM   | to 384, gap 25 ms before the hit
360    | 8:3.000  | SNARE    | beat 3 (half-time)
372    | 8:4.000  | SNARE    | fill source for stutter
372    | 8:4.000  | STUTTER  | 1/16 1/16 1/32 1/32 1/32 1/32, to 384, gate 55%
383.25 | 8:4.938  | SILENCE  | to 384 (25 ms of true silence before the end hit)
384    | 9:1.000  | END      | kick + sub F1, ring out
429    | 9:4.750  | SILENCE  | to end (true digital silence)
"""
import re
import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.special import jv

SEED = 44
SR = 48000
FPS = 30
SPF = SR // FPS                      # samples per frame
N = 691200
BEAT_FR = 12
BEAT_S = BEAT_FR / FPS               # 0.4 s
TARGET_LUFS = -14.0
TP_TARGET_DB = -1.2
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- cue sheet (single clock)
_ROW = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*\|\s*\S+\s*\|\s*([A-Z]+)\s*\|\s*(.*?)\s*$")
CUES = [(float(m.group(1)), m.group(2), m.group(3)) for m in map(_ROW.match, __doc__.splitlines()) if m]
END_FRAME = N / SPF


def cues(ev):
    return sorted([(f, v) for f, e, v in CUES if e == ev], key=lambda r: r[0])


def S(frame):
    return int(round(frame * SPF))


def until(v):
    if "to end" in v:
        return END_FRAME
    return float(re.search(r"to (\d+(?:\.\d+)?)", v).group(1))


RATE = {"1/4": 1.0, "1/8": 2.0, "1/8T": 3.0, "1/16": 4.0, "1/16T": 6.0}   # LFO cycles per beat
_NOTE = {"C": 0, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "Gb": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def hz(name):
    m = re.match(r"([A-G]b?)(-?\d)", name)
    midi = 12 * (int(m.group(2)) + 1) + _NOTE[m.group(1)]
    return 440.0 * 2 ** ((midi - 69) / 12)


# ---------------------------------------------------------------- DSP helpers
def ladder_gain(f, fc, k):
    """|H| of a 4-pole (24 dB/oct) resonant ladder low-pass, H = (1+k)/((1+s)^4+k), s = jf/fc."""
    x = f / fc
    x2 = x * x
    re_ = 1 - 6 * x2 + x2 * x2 + k
    im_ = 4 * x - 4 * x * x2
    return (1 + k) / np.sqrt(re_ * re_ + im_ * im_)


def hp_gain(f, fc, order=4):
    r = (f / fc) ** order
    return r / np.sqrt(1 + r * r)


def top_gate(f):
    """1 below 14.5 kHz, 0 above 15.5 kHz: keeps every partial under 16 kHz."""
    return np.clip((15500.0 - f) / 1000.0, 0.0, 1.0)


def additive(f_t, gain_fn, ph0=0.0, amp=lambda k: 1.0 / k, kmax=400):
    """Band-limited oscillator: sum_k amp(k) * gain_fn(k f) * sin(k phase)."""
    ph = 2 * np.pi * np.cumsum(f_t) / SR + ph0
    out = np.zeros(len(f_t))
    K = min(kmax, int(15500.0 / f_t.min()))
    for k in range(1, K + 1):
        fk = k * f_t
        g = gain_fn(fk) * top_gate(fk) * amp(k)
        out += g * np.sin(k * ph)
    return out


def place(buf, x, start):
    end = min(len(buf), start + len(x))
    if end > start:
        buf[start:end] += x[: end - start]


def sos_bp(lo, hi, order=2):
    return signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")


def rbj(kind, f0, gain_db=0.0, q=0.707):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    c, s = np.cos(w), np.sin(w)
    if kind == "peak":
        al = s / (2 * q)
        b = [1 + al * A, -2 * c, 1 - al * A]
        a = [1 + al / A, -2 * c, 1 - al / A]
    else:
        al = s / 2 * np.sqrt(2)
        sa = 2 * np.sqrt(A) * al
        if kind == "lowshelf":
            b = [A * ((A + 1) - (A - 1) * c + sa), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sa)]
            a = [(A + 1) + (A - 1) * c + sa, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sa]
        else:
            b = [A * ((A + 1) + (A - 1) * c + sa), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sa)]
            a = [(A + 1) - (A - 1) * c + sa, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sa]
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return np.concatenate([b, a])[None, :]


def eq(x, *sections):
    return signal.sosfilt(np.vstack(sections), x, axis=0)


def lr4(x, fc, kind):
    sos = signal.butter(2, fc, kind, fs=SR, output="sos")
    return signal.sosfilt(sos, signal.sosfilt(sos, x, axis=0), axis=0)


def os_tanh(x, drive, bias=0.0):
    """4x oversampled tanh waveshaper (no aliasing from the new harmonics)."""
    up = signal.resample_poly(x, 4, 1, axis=0)
    y = (np.tanh(drive * (up + bias)) - np.tanh(drive * bias)) / np.tanh(drive)
    return signal.resample_poly(y, 1, 4, axis=0)[: len(x)]


def true_peak_db(x):
    return 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)


def lufs(x):
    """BS.1770-4 integrated loudness (same as the checker)."""
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    p = np.cumsum(np.concatenate([[0.0], (y ** 2).sum(axis=1)]))
    st = np.arange(0, len(y) - blk + 1, hop)
    z = (p[st + blk] - p[st]) / blk
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def short_term(x, t_end):
    """3 s short-term loudness ending at t_end (ungated)."""
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)
    e = int(t_end * SR)
    seg = y[max(0, e - 3 * SR):e]
    return -0.691 + 10 * np.log10((seg ** 2).sum(axis=1).sum() / (3 * SR) + 1e-20)


# ---------------------------------------------------------------- instruments
def kick(dur=0.55, f_hi=165.0, f_lo=44.0, tp=0.032, ta=0.26, click=0.45, ph0=0.0):
    """Pitch-dropping sine + click."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f_lo + (f_hi - f_lo) * np.exp(-tt / tp)
    body = np.sin(2 * np.pi * (np.cumsum(f) - f[0]) / SR + ph0) * np.exp(-tt / ta)
    nz = signal.sosfilt(sos_bp(1500, 9000), rng.standard_normal(n))
    nz = nz / (np.abs(nz[:480]).max() + 1e-9) * np.exp(-tt / 0.0022)
    y = body + click * nz
    y *= np.minimum(1.0, tt / 0.0003) * np.clip((dur - tt) / 0.03, 0, 1)
    return y / np.abs(y).max()


def snare(dur=0.32, f_body=200.0, bp=2000.0, tone=0.8, noise=1.0, nd=0.085):
    """200 Hz body tone + noise through a 2 kHz band-pass (the plate is a send, see plate_ir)."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f_body * (1 + 0.18 * np.exp(-tt / 0.01))
    body = np.sin(2 * np.pi * (np.cumsum(f) - f[0]) / SR) * np.exp(-tt / 0.06)
    nz = signal.sosfilt(sos_bp(bp / 1.7, bp * 1.7), rng.standard_normal(n))
    nz = nz / (3 * np.sqrt(np.mean(nz[: min(n, 4800)] ** 2))) * np.exp(-tt / nd)
    y = tone * body + noise * nz
    y *= np.minimum(1.0, tt / 0.0004) * np.clip((dur - tt) / 0.02, 0, 1)
    return y / np.abs(y).max()


def plate_ir(dur=0.8, rt=0.5, pre=0.006):
    """Short stereo plate: dense decorrelated noise, highs decaying faster than mids."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    w = rng.standard_normal((n, 2))
    hi = signal.sosfilt(signal.butter(2, 3500, "highpass", fs=SR, output="sos"), w, axis=0)
    ir = (w - hi) * np.exp(-6.9 * tt / rt)[:, None] + hi * np.exp(-6.9 * tt / (0.55 * rt))[:, None]
    ir = signal.sosfilt(sos_bp(300, 11000), ir, axis=0)
    ir[: int(pre * SR)] = 0
    ir *= np.clip((dur - tt) / 0.05, 0, 1)[:, None]
    return ir / np.sqrt((ir ** 2).sum(axis=0))


def conv_stereo(mono, ir):
    return np.stack([signal.fftconvolve(mono, ir[:, c])[: len(mono)] for c in range(2)], axis=1)


def noise_riser(n, f_a, f_b):
    """Stereo white noise through a 24 dB/oct high-pass sweeping f_a -> f_b (STFT-domain, time-varying)."""
    x = rng.standard_normal((2, n))
    f, tt, Z = signal.stft(x, SR, nperseg=2048, noverlap=1536)
    frac = np.clip(tt / (n / SR), 0, 1)
    fc = f_a * (f_b / f_a) ** frac
    r = np.maximum(f[:, None], 1.0) / fc[None, :]
    mask = hp_gain(r, 1.0, 4) * (1 + 1.5 * np.exp(-0.5 * (np.log2(r) / 0.3) ** 2)) * top_gate(f)[:, None]
    _, y = signal.istft(Z * mask[None], SR, nperseg=2048, noverlap=1536)
    y = y[:, :n].T
    return y / np.abs(y).max()


def pitch_riser(n, f_a, f_b):
    tt = np.arange(n) / SR
    f = f_a * (f_b / f_a) ** (tt / tt[-1])
    out = np.zeros((n, 2))
    for c, det in enumerate((-9, 9)):
        out[:, c] = additive(f * 2 ** (det / 1200), lambda fk: hp_gain(fk, 150, 2), ph0=c * 1.3,
                             amp=lambda k: 1.0 / k ** 1.4, kmax=8)
    return out / np.abs(out).max()


def stab(notes, fc0, dur=0.42, k=1.4):
    """Filtered Fm stab: three detuned additive saws per note into a resonant ladder low-pass."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    fc = fc0 * (1 + 1.5 * np.exp(-tt / 0.05))
    out = np.zeros((n, 2))
    for f0 in notes:
        for det, pan in ((-8, 0.15), (0, 0.5), (8, 0.85)):
            v = additive(np.full(n, f0 * 2 ** (det / 1200)), lambda fk: ladder_gain(fk, fc, k),
                         ph0=rng.uniform(0, 2 * np.pi))
            out[:, 0] += v * np.cos(pan * np.pi / 2)
            out[:, 1] += v * np.sin(pan * np.pi / 2)
    env = np.minimum(1, tt / 0.003) * np.exp(-tt / 0.16) * np.clip((dur - tt) / 0.04, 0, 1)
    out *= env[:, None]
    return out / np.abs(out).max()


VOWELS = {  # formant centre (Hz), bandwidth (Hz), relative gain
    "u": ((325, 700, 2530), (90, 110, 170), (1.0, 0.45, 0.15)),
    "o": ((450, 800, 2830), (90, 110, 170), (1.0, 0.6, 0.2)),
    "a": ((730, 1090, 2440), (110, 120, 170), (1.0, 0.7, 0.3)),
    "e": ((530, 1840, 2480), (90, 140, 200), (1.0, 0.55, 0.35)),
    "i": ((300, 2290, 3010), (80, 160, 220), (0.9, 0.5, 0.45)),
}


def formant_gain(f, F, B, A):
    g = 0.03
    for i in range(3):
        g = g + A[i] / np.sqrt(1 + ((f * f - F[i] ** 2) / (f * B[i])) ** 2)
    return g


def growl(f0, vowel_seq, n_beats, lfo):
    """Formant-filtered saw; the vowel target moves one step per beat with a smooth sweep between targets."""
    n = len(f0)
    pos = np.arange(n) / (BEAT_S * SR)                       # in beats
    j = np.minimum(np.floor(pos).astype(int), len(vowel_seq) - 2)
    fr = np.clip(pos - j, 0, 1)
    fr = fr * fr * (3 - 2 * fr)
    F, B, A = [], [], []
    for i in range(3):
        a = np.array([VOWELS[v][0][i] for v in vowel_seq])
        b = np.array([VOWELS[v][1][i] for v in vowel_seq])
        g = np.array([VOWELS[v][2][i] for v in vowel_seq])
        F.append(a[j] * (a[j + 1] / a[j]) ** fr)
        B.append(b[j] + (b[j + 1] - b[j]) * fr)
        A.append(g[j] + (g[j + 1] - g[j]) * fr)
    y = additive(f0, lambda fk: formant_gain(fk, F, B, A) * hp_gain(fk, 110, 4), ph0=0.4)
    return y * (0.3 + 0.7 * lfo)


def rev_cymbal(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    met = np.zeros(n)
    for f in (3170, 4290, 5310, 6620, 7930, 9470, 11180, 12890):
        met += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6.28)) * np.sin(2 * np.pi * (f * 0.37) * tt)
    nz = signal.sosfilt(signal.butter(4, [4500, 15000], "bandpass", fs=SR, output="sos"),
                        rng.standard_normal((n, 2)), axis=0)
    nz /= np.abs(nz).max()
    x = (0.35 * met / np.abs(met).max())[:, None] + nz
    x *= np.exp(-tt / 0.35)[:, None]
    x = x[::-1].copy()                                       # reversed: swells into the hit
    x *= (np.minimum(1, tt / 0.05) * np.clip((dur - tt) / 0.0015, 0, 1))[:, None]
    return x / np.abs(x).max()


def end_sub(dur, f):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    fr = f * (1 + 0.2 * np.exp(-tt / 0.05))
    ph = 2 * np.pi * (np.cumsum(fr) - fr[0]) / SR
    y = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
    y *= np.minimum(1, tt / 0.002) * np.exp(-tt / 0.42) * np.clip((dur - tt) / 0.35, 0, 1)
    return y / np.abs(y).max()


def metal_snare(dur=0.3, f_body=200.0):
    """Metallic snare: 200 Hz body + ring-modulated inharmonic partials + 2 kHz band-passed noise."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f_body * (1 + 0.15 * np.exp(-tt / 0.01))
    body = np.sin(2 * np.pi * (np.cumsum(f) - f[0]) / SR) * np.exp(-tt / 0.05)
    met = np.zeros(n)
    for fi, a in ((540, 1.0), (797, 0.8), (1131, 0.7), (1468, 0.6), (1913, 0.5), (2650, 0.4), (3410, 0.35)):
        met += a * np.sin(2 * np.pi * fi * tt + rng.uniform(0, 6.28))
    met *= np.sin(2 * np.pi * 317.0 * tt + 0.5)                       # ring modulation
    met = met / np.abs(met).max() * np.exp(-tt / 0.075)
    nz = signal.sosfilt(sos_bp(2000 / 1.7, 2000 * 1.7), rng.standard_normal(n))
    nz = nz / (3 * np.sqrt(np.mean(nz[:4800] ** 2))) * np.exp(-tt / 0.06)
    y = 0.7 * body + 0.75 * met + 0.8 * nz
    y *= np.minimum(1.0, tt / 0.0004) * np.clip((dur - tt) / 0.02, 0, 1)
    return y / np.abs(y).max()


# ---------------------------------------------------------------- arrangement
def render():
    kickbus = np.zeros(N)          # kicks + end sub (never ducked)
    snare_dry = np.zeros(N)
    roll_dry = np.zeros(N)         # build roll (lighter plate send)
    bass = np.zeros(N)             # riddim bass + growl (mono)
    sub = np.zeros(N)              # pure sine sub (mono, < 100 Hz)
    music = np.zeros((N, 2))       # build: stabs, risers
    fx = np.zeros((N, 2))          # reverse cymbal

    build_end = cues("SILENCE")[0][0]                        # first true-silence window ends the build
    BUILD = 0.80                                             # build bus level (keeps the drop > 6 LU louder)

    # --- build ---------------------------------------------------------
    div = {"1/4": 0.12, "1/8": 0.09, "1/16": 0.06, "1/32": 0.04}
    for f, v in cues("ROLL"):
        p = f / build_end
        g = BUILD * 10 ** ((-26 + 18 * p) / 20)
        place(roll_dry, g * snare(dur=0.25, f_body=200 * (1 + 0.25 * p), nd=div[v]), S(f))
    for f, v in cues("STAB"):
        fc0 = float(re.search(r"lp=(\d+)", v).group(1))
        place(music, BUILD * 0.22 * stab([hz("F3"), hz("Ab3"), hz("C4"), hz("F4")], fc0, k=2.0), S(f))
    for f, v in cues("RISER"):
        n = S(until(v)) - S(f)
        ramp = (np.arange(n) / n) ** 2.2
        place(music, BUILD * 0.36 * noise_riser(n, 200, 8000) * ramp[:, None], S(f))
    for f, v in cues("PITCH"):
        n = S(until(v)) - S(f)
        ramp = (np.arange(n) / n) ** 1.6
        place(music, BUILD * 0.10 * pitch_riser(n, hz("F3"), hz("F5")) * ramp[:, None], S(f))

    # --- drop: drums ----------------------------------------------------
    kick_frames = [f for f, _ in cues("KICK")]
    for f in kick_frames:
        place(kickbus, 0.85 * kick(dur=0.6, f_hi=150.0, f_lo=42.0, ta=0.30), S(f))
    for f, v in cues("SNARE"):
        place(snare_dry, 0.62 * metal_snare(), S(f))

    # --- drop: riddim bass, sub, growl ----------------------------------
    end_f = cues("END")[0][0]
    notes = cues("NOTE")
    d0, d1 = S(notes[0][0]), S(end_f)
    n = d1 - d0
    tt = np.arange(n) / SR
    logf = np.zeros(n)
    for i, (f, v) in enumerate(notes):
        a = S(f) - d0
        b = (S(notes[i + 1][0]) if i + 1 < len(notes) else d1) - d0
        logf[a:b] = np.log(hz(v))
    f1 = np.exp(uniform_filter1d(logf, int(0.012 * SR), mode="nearest"))
    ph1 = 2 * np.pi * np.cumsum(f1) / SR
    gate = np.zeros(n)                                       # tight LFO gate, 0/1 with 2.5 ms edges
    penv = np.zeros(n)                                       # per-pulse filter envelope
    lfos = cues("LFO")
    for i, (f, v) in enumerate(lfos):
        a = S(f) - d0
        b = (S(lfos[i + 1][0]) if i + 1 < len(lfos) else d1) - d0
        ph = (np.arange(b - a) / SR / BEAT_S * RATE[v]) % 1.0
        duty = 0.5 if RATE[v] >= 4 else 0.62
        gate[a:b] = ph < duty
        penv[a:b] = np.exp(-3.0 * ph / duty)
    gate = uniform_filter1d(gate, int(0.0025 * SR))
    fc = 130.0 * (2600.0 / 130.0) ** (gate * penv)
    k_res = 3.0
    idx = 0.8 + 3.5 * gate * penv                            # FM index swept by each pulse
    coef = {}                                                # harmonic m of f1 -> time-varying amplitude
    for j in range(0, 200):                                  # band-limited square on F2: odd harmonics of 2*f1
        m = 2 * (2 * j + 1)
        if m * 41.0 > 15500:
            break
        coef[m] = coef.get(m, 0) + 0.8 / (2 * j + 1)
    nmax = int(np.ceil(idx.max())) + 6
    for k in range(-nmax, nmax + 1):                         # FM pair: carrier 2*f1 (F2), modulator f1 (F1)
        m = 2 + k
        J = jv(k, idx)
        if m == 0 or np.abs(J).max() < 2e-4:
            continue
        sgn = 1.0 if m > 0 else -1.0
        coef[abs(m)] = coef.get(abs(m), 0) + 0.9 * sgn * J
    rid = np.zeros(n)
    for m, c in coef.items():
        fk = m * f1
        rid += c * ladder_gain(fk, fc, k_res) * hp_gain(fk, 75.0, 4) * top_gate(fk) * np.sin(m * ph1)
    rid *= 0.06 + 0.94 * gate
    rid *= np.minimum(1, tt / 0.003) * np.clip((n - 1 - np.arange(n)) / (0.004 * SR), 0, 1)
    rid /= np.sqrt(np.mean(rid ** 2))
    place(bass, 0.17 * rid, d0)

    subw = np.sin(ph1) * np.minimum(1, tt / 0.004) * np.clip((n - 1 - np.arange(n)) / (0.004 * SR), 0, 1)
    place(sub, 0.55 * subw, d0)

    for f, v in cues("GROWL"):
        a, b = S(f) - d0, S(until(v)) - d0
        seq = re.match(r"([a-z\-]+)", v).group(1).split("-")
        gr = growl(2 * f1[a:b], seq, len(seq), gate[a:b])
        gr = signal.sosfilt(signal.butter(4, 1800, "lowpass", fs=SR, output="sos"), gr)   # dark growl
        gr *= 0.08 + 0.92 * gate[a:b]                                                       # on the same tight gates
        gr *= np.minimum(1, np.arange(b - a) / (0.01 * SR)) * np.clip((b - a - 1 - np.arange(b - a)) / (0.005 * SR), 0, 1)
        gr /= np.sqrt(np.mean(gr ** 2))
        place(bass, 0.09 * gr, S(f))

    # --- 1-beat stutter fill (dry buses, before the plate) --------------
    for f, v in cues("STUTTER"):
        s0 = S(f)
        lens = [int(round(BEAT_S * SR * {"1/16": 0.25, "1/32": 0.125}[t])) for t in v.split(",")[0].split()]
        fade = int(0.0015 * SR)
        gate_s = float(re.search(r"gate (\d+)%", v).group(1)) / 100
        for buf in (snare_dry, bass, sub):
            src = buf[s0:s0 + max(lens)].copy()
            pos = s0
            for L in lens:
                seg = src[:L].copy()
                on = int(gate_s * L) if L < max(lens) else L - fade
                seg[on:] = 0
                seg[:fade] *= np.linspace(0, 1, fade)
                seg[on - fade:on] *= np.linspace(1, 0, fade)
                buf[pos:pos + L] = seg
                pos += L

    snare_wet = conv_stereo(snare_dry + 0.35 * roll_dry, plate_ir(dur=0.6, rt=0.38))
    snare_dry = snare_dry + roll_dry

    # --- end hit -----------------------------------------------------------
    for f, v in cues("REVCYM"):
        gap = S(float(re.search(r"gap (\d+) ms", v).group(1)) / 1000 * FPS)
        n_c = S(until(v)) - S(f) - gap
        place(fx, 0.28 * rev_cymbal(n_c / SR), S(f))
    for f, v in cues("END"):
        place(kickbus, 1.0 * kick(dur=1.2, f_hi=170, f_lo=hz("F1"), ta=0.36, click=0.8, ph0=np.pi / 2), S(f))
        place(kickbus, 0.62 * end_sub(1.5, hz("F1")), S(f))

    return dict(kick=kickbus, snare_dry=snare_dry, snare_wet=snare_wet, bass=bass, sub=sub, music=music, fx=fx,
                kick_frames=kick_frames + [end_f])


# ---------------------------------------------------------------- mix chain
def duck_env(frames, depth, tau, hold=0.02, att=0.003):
    d = np.zeros(N)
    for f in frames:
        s = S(f)
        L = min(N - s, int((hold + 8 * tau) * SR))
        t = np.arange(L) / SR
        d[s:s + L] = np.maximum(d[s:s + L], np.minimum(1, t / att) * np.exp(-np.maximum(0, t - hold) / tau))
    return 1 - depth * d


LP16 = signal.butter(8, 15500, "lowpass", fs=SR, output="sos")


def master(b):
    st = lambda m: np.stack([m, m], axis=1)
    # 1. EQ
    bass = eq(b["bass"], rbj("peak", 320, -3.0, 1.0), rbj("highshelf", 2500, 2.0))
    snare = eq(st(b["snare_dry"]) + 0.30 * b["snare_wet"], signal.butter(2, 120, "highpass", fs=SR, output="sos"),
               rbj("peak", 2000, 1.5, 0.8), LP16)
    music = eq(b["music"], signal.butter(2, 150, "highpass", fs=SR, output="sos"), LP16)
    fx = eq(b["fx"], signal.butter(2, 400, "highpass", fs=SR, output="sos"), LP16)
    kick = eq(b["kick"], rbj("peak", 55, 2.0, 1.0), rbj("peak", 3500, 1.0, 1.0))
    sub = eq(b["sub"], rbj("lowshelf", 70, 2.0))                    # more sub weight
    # 2. Saturation (bass bus, 4x oversampled, slight bias for even harmonics)
    pk = np.abs(bass).max()
    sat = os_tanh(bass / pk, 3.2, 0.15) * pk                       # heavier drive
    sat = eq(sat, signal.butter(8, 15500, "lowpass", fs=SR, output="sos"))
    bass = 0.2 * bass + 0.8 * sat * np.sqrt(np.mean(bass ** 2) / np.mean(sat ** 2))
    bass = eq(bass, rbj("highshelf", 4000, -4.0))                  # darker
    nonkick = st(bass) + st(sub) + snare + music + fx
    # 3. Multiband split (LR4 at 120 Hz and 250 Hz); below 120 Hz is summed to mono
    low = lr4(nonkick, 120, "lowpass")
    rest = lr4(nonkick, 120, "highpass")
    low = lr4(low, 250, "lowpass") + lr4(low, 250, "highpass")      # phase-match the 250 Hz crossover
    mid = lr4(rest, 250, "lowpass")
    high = lr4(rest, 250, "highpass")
    low = st(low.mean(axis=1))
    # 4. Sidechain to the kick
    kf = b["kick_frames"]
    low *= duck_env(kf, 0.80, 0.09)[:, None]
    mid *= duck_env(kf, 0.65, 0.08)[:, None]
    high *= duck_env(kf, 0.45, 0.07)[:, None]
    # 5. Stereo-widen only above 250 Hz (M/S: side gain + a delayed, decorrelated mid in the side)
    M = high.mean(axis=1)
    Sd = 0.5 * (high[:, 0] - high[:, 1])
    haas = np.concatenate([np.zeros(int(0.011 * SR)), M[: -int(0.011 * SR)]])
    Sd = 1.15 * Sd + 0.15 * haas
    high = np.stack([M + Sd, M - Sd], axis=1)
    mix = low + mid + high + st(kick)
    # 6. Bus glue compression (2:1, RMS detector, smoothed gain)
    lev = 10 * np.log10(uniform_filter1d((mix ** 2).mean(axis=1), int(0.01 * SR)) + 1e-12)
    thr = np.percentile(lev[lev > -60], 85) - 2.0
    gr = np.minimum(0, (thr - lev) * 0.5)
    a = np.exp(-1 / (0.06 * SR))
    mix *= (10 ** (signal.lfilter([1 - a], [1, -a], gr) / 20))[:, None]

    def finish(x, gain_db):
        x = x * 10 ** (gain_db / 20)
        # 7. Soft clip (4x oversampled)
        x = 0.98 * os_tanh(x / 0.98, 1.0)
        # 8. Limiter (true-peak aware lookahead, ceiling -1.3 dBTP)
        c = 10 ** (-1.3 / 20)
        up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)[: 4 * len(x)].reshape(-1, 4).max(axis=1)
        red = 1 - np.minimum(1, c / np.maximum(np.maximum(up, np.abs(x).max(axis=1)), 1e-9))
        L = int(0.0015 * SR)
        red = minimum_filter1d(-red, 2 * L + 1) * -1                  # running max of the reduction
        ar = np.exp(-1 / (0.05 * SR))
        red = np.maximum(red, signal.lfilter([1 - ar], [1, -ar], red))
        red = uniform_filter1d(red, L + 1)
        x = x * (1 - red)[:, None]
        # 9. DC high-pass (25 Hz) + re-impose the true-silence windows from the cue sheet
        x = signal.sosfilt(signal.butter(2, 25, "highpass", fs=SR, output="sos"), x, axis=0)
        for f, v in cues("SILENCE"):
            a0, a1 = S(f), min(N, S(until(v)))
            fo = int(0.004 * SR)
            x[a0 - fo:a0] *= np.linspace(1, 0, fo)[:, None]
            x[a0:a1] = 0
        x[: int(0.0003 * SR)] *= np.linspace(0, 1, int(0.0003 * SR))[:, None]
        # 10. Final true-peak trim
        tp = true_peak_db(x)
        if tp > TP_TARGET_DB:
            x *= 10 ** ((TP_TARGET_DB - tp) / 20)
        return x

    g = TARGET_LUFS - lufs(mix)
    for _ in range(6):
        y = finish(mix, g)
        err = TARGET_LUFS - lufs(y)
        if abs(err) < 0.05:
            break
        g += err
    return y


def write_wav(path, x):
    y = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "take-3.wav"
    y = master(render())
    assert y.shape == (N, 2) and np.all(np.isfinite(y))
    write_wav(out, y)
    b = short_term(y, S(cues("KICK")[0][0]) / SR)
    d = np.median([short_term(y, t) for t in np.arange(6.4, 12.81, 0.1)])
    print(f"{out}: {lufs(y):.2f} LUFS, {true_peak_db(y):.2f} dBTP, build S {b:.1f} vs drop S {d:.1f} "
          f"(+{d - b:.1f} LU)")


if __name__ == "__main__":
    main()
