#!/usr/bin/env python3
"""ui-morph-showreel-120 / take 2 (glassy Apple-keynote feel)

BRIEF
  A 14 s product-showreel bed for a code-made UI-morph video, where something happens on every beat.
  Music and UI sound design at once. Take angle: glassy keynote. Every UI sound is a marimba bar or a
  glass mallet (modal/additive synthesis, tuned to the chord under it), the plucked chords become an
  airy pad (detuned additive saws, low-passed, plus a breath-noise layer), the kick is softer and
  rounder, and the stereo image is wide (detuned L/R glass pairs, wide hats and clap, a 3-voice pad).
  Same form as the brief: groove = soft round kick on 1 and 3, closed 8th hats, soft clap on 2 and 4
  from bar 3, sub bass on the roots with 2nd/3rd harmonics, chords Amaj9 -> F#m11 -> Dmaj7 -> E6sus4;
  everything but the kick sidechain-ducked 4 dB (120 ms release). Bars 1-2 kick + UI, bars 3-5 full,
  bar 6 drums out (UI + pad + 1-bar riser, last 0.1 s true silence), frame 360 final hit (sub + clap +
  full chord + bright logo chime) ringing to true silence by frame 420.
  48 kHz stereo 16-bit, 672000 samples, about -14 LUFS, <= -1 dBTP, seed 43.

GRID
  120 BPM, 4/4, 7 bars = 28 beats. 1 beat = 0.5 s = 24000 samples = 15 frames @ 30 fps. Key A major.
  A beat's time is read from its frame column (t = frame / 30); "&" = the 8th after it (+7.5 frames).

CHORDS  name | bass root | pad voicing (+ root two octaves up) | chord tones (every pitched UI sound uses only these)
  Amaj9   | A1  | G#3 B3 C#4 E4          | A C# E G# B
  F#m11   | F#1 | A3 C#4 E4 B4           | F# A C# E B
  Dmaj7   | D2  | D3 A3 C#4 F#4          | D F# A C#
  E6sus4  | E2  | A3 B3 C#4 E4           | E A B C#
  FINAL   | A1  | E3 A3 C#4 G#4 B4 E5    | chime A6 C#7 E7
  Bar 7 resolves to the tonic Amaj9 (FINAL voicing) instead of continuing the cycle to Dmaj7.

UI SOUNDS (marimba = modes 1 : 4 : 10, glass = harmonic modes 1 : 2 : 3 in a +-3 cent L/R pair)
  tap     glass ping on the chord tone nearest 2 kHz
  toggle  glass two-note up-glide: chord tone nearest 880 Hz -> next chord tone >= a 4th above
  slide   airy filtered-noise swipe, band-pass 1.2 -> 9 kHz, panned hard L -> R (unpitched)
  flip    card flip: two marimba tocks 45 ms apart, chord tone near 1.2 kHz dropping to the one below
  bubble  noise through a resonant band-pass rising 0.45 f -> f (f = chord tone nearest 1.15 kHz), Haas-wide
  type    4 tiny glass ticks in 60 ms on chord tones between 2.8 and 4.6 kHz, alternating L/R
  check   rising minor-third marimba ding on the lowest chord-tone pair a m3 apart above 650 Hz
  drop    drag-and-drop: soft low marimba bar on the bar root in octave 3 + a felt puff
  logo    glass bell chord on the FINAL chime notes doubled by marimba an octave below
  Cycle order: tap, toggle, slide, flip, bubble, type, check, drop (one 2-bar phrase), x3 over beats 1-24.
  Extra layers: slide on beat 9, tap on beat 21 (section changes); bar 7 = logo + check, then echoes.
  Level: every UI sound is set 3 dB under the music (K-weighted 100 ms window vs. bars 3-5 groove).

BED CODES  K kick | H closed hats on the beat and its & | C clap | B bass root on the beat (0.9 beat)
           b bass root on the & (0.4 beat) | D airy pad, one swell per bar on that bar's chord
           R riser | Z last 0.1 s of the beat is true silence | X final hit | T final ring

CUE SHEET
 beat bar.bt frame chord   ui                bed
   1   1.1     0   Amaj9   tap               K
   2   1.2    15   Amaj9   toggle            -
   3   1.3    30   Amaj9   slide             K
   4   1.4    45   Amaj9   flip              -
   5   2.1    60   F#m11   bubble            K
   6   2.2    75   F#m11   type              -
   7   2.3    90   F#m11   check             K
   8   2.4   105   F#m11   drop              -
   9   3.1   120   Dmaj7   tap+slide@-4      K H B D
  10   3.2   135   Dmaj7   toggle            H C b D
  11   3.3   150   Dmaj7   slide             K H B D
  12   3.4   165   Dmaj7   flip              H C b D
  13   4.1   180   E6sus4  bubble            K H B D
  14   4.2   195   E6sus4  type              H C b D
  15   4.3   210   E6sus4  check             K H B D
  16   4.4   225   E6sus4  drop              H C b D
  17   5.1   240   Amaj9   tap               K H B D
  18   5.2   255   Amaj9   toggle            H C b D
  19   5.3   270   Amaj9   slide             K H B D
  20   5.4   285   Amaj9   flip              H C b D
  21   6.1   300   F#m11   bubble+tap        D R
  22   6.2   315   F#m11   type              D R
  23   6.3   330   F#m11   check             D R
  24   6.4   345   F#m11   drop              D R Z
  25   7.1   360   Amaj9   logo+check@-4     X
  26   7.2   375   Amaj9   bubble@-6         T
  27   7.3   390   Amaj9   toggle@-10        T
  28   7.4   405   Amaj9   tap@-14           T
  (end) frame 420 = 14.0 s = sample 672000: true silence.

MIX  kick + bass + final sub: mono, the only content below 120 Hz (everything else high-passed at 120 Hz).
     Duck: all but the kick -4 dB at each kick (3 ms look-ahead attack, 12 ms hold, 120 ms linear release).
     Master: 25 Hz DC high-pass -> loudness to -14 LUFS -> look-ahead 4:1 true-peak compressor + trim (-1.3 dBTP)
     -> silence gates (11.9-12.0 s, end) -> 16-bit.
"""
import re
import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 48000
N_SAMPLES = 672000
SEED = 43
FPS = 30
BEAT_FR = 15
TARGET_LUFS = -14.0
TP_CEIL_DB = -1.3
UI_UNDER_MUSIC_DB = -3.0
UI_CREST_MAX = 12.0          # dB: a UI sound's peak may sit at most this far above its loudness target
PEAK_RATIO = 4.0             # master true-peak compressor ratio
DUCK_DB = -4.0
DUCK_REL = 0.120
HP_STEREO = 120.0

NOTE_PC = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6,
           'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
PC_NAME = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


# ----------------------------------------------------------------------------- cue sheet
def midi(n):
    m = re.fullmatch(r'([A-G][#b]?)(-?\d)', n)
    return 12 * (int(m.group(2)) + 1) + NOTE_PC[m.group(1)]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def mname(m):
    return f"{PC_NAME[m % 12]}{m // 12 - 1}"


def parse_sheet(doc):
    chords, final, cues = {}, None, []
    for line in doc.splitlines():
        m = re.match(r'^\s*(\S+)\s*\|\s*([A-G][#b]?-?\d)\s*\|([^|]+)\|([^|]+)$', line)
        if m:
            name, root, voicing, tail = m.group(1), m.group(2), m.group(3).split(), m.group(4).split()
            if name == 'FINAL':
                final = dict(root=root, voicing=voicing, chime=tail[1:])
            else:
                chords[name] = dict(root=root, voicing=voicing, pcs={NOTE_PC[t] for t in tail})
            continue
        m = re.match(r'^\s*(\d+)\s+(\d)\.(\d)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s*$', line)
        if m:
            ui = []
            for tok in m.group(6).split('+'):
                nm, _, g = tok.partition('@')
                ui.append((nm, float(g) if g else 0.0))
            bed = [] if m.group(7).strip() == '-' else m.group(7).split()
            cues.append(dict(beat=int(m.group(1)), bar=int(m.group(2)), bt=int(m.group(3)),
                             frame=int(m.group(4)), chord=m.group(5), ui=ui, bed=bed))
    for c in cues:
        assert c['frame'] == (c['beat'] - 1) * BEAT_FR, c
        assert c['chord'] in chords, c
    return chords, final, cues


# ----------------------------------------------------------------------------- dsp helpers
def tvec(dur):
    return np.arange(int(round(dur * SR))) / SR


def env_ad(n, att, tau):
    t = np.arange(n) / SR
    a = np.clip(t / max(att, 1e-6), 0, 1)
    a = 0.5 - 0.5 * np.cos(np.pi * a)
    return a * np.exp(-np.maximum(t - att, 0) / tau)


def fade_tail(x, ms=8.0):
    k = min(len(x), int(ms * SR / 1000))
    w = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, k))
    x = x.copy()
    x[-k:] = (x[-k:].T * w).T
    return x


def sos(kind, f, order=2):
    return signal.butter(order, f, btype=kind, fs=SR, output='sos')


def pan2(x, p):
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1) * np.sqrt(2)


def as_st(x):
    return x if x.ndim == 2 else np.stack([x, x], 1)


def put(bus, sig, t, align='peak'):
    """Add sig into bus so that its |peak| (or its start) lands on time t. Returns the peak sample."""
    pk = 0
    if align == 'peak':
        pk = int(np.argmax(np.abs(sig) if sig.ndim == 1 else np.abs(sig).sum(1)))
    s0 = max(0, int(round(t * SR)) - pk)
    e = min(len(bus), s0 + len(sig))
    if e > s0:
        bus[s0:e] += sig[:e - s0]
    return s0 + pk


def click(rng, ms=1.0):
    n = max(8, int(ms * SR / 1000))
    x = rng.standard_normal(n) * np.hanning(n)
    x = signal.sosfilt(sos('lowpass', 14000, 8), np.concatenate([x, np.zeros(64)]))
    return x / (np.abs(x).max() + 1e-12)


def svf_bp(x, fc, q):
    """TPT state-variable band-pass with per-sample cutoff (short signals only)."""
    g = np.tan(np.pi * np.clip(fc, 20, 0.45 * SR) / SR)
    k = 1.0 / q
    a1 = 1 / (1 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    y = np.zeros_like(x)
    ic1 = ic2 = 0.0
    for i in range(len(x)):
        v3 = x[i] - ic2
        v1 = a1[i] * ic1 + a2[i] * v3
        v2 = ic2 + a2[i] * ic1 + a3[i] * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[i] = v1
    return y


def stft_sweep(noise, fc_of_t, width_oct, nper=512, hop=64):
    """Time-varying band-pass by STFT masking (vectorised). fc_of_t: seconds -> Hz."""
    f, tt, Z = signal.stft(noise, SR, nperseg=nper, noverlap=nper - hop, boundary='zeros')
    fc = fc_of_t(tt)[None, :]
    mask = np.exp(-0.5 * (np.log2(np.maximum(f[:, None], 1.0) / fc) / width_oct) ** 2)
    mask[f > 15500] = 0
    _, y = signal.istft(Z * mask, SR, nperseg=nper, noverlap=nper - hop, boundary=True)
    return y[:len(noise)]


def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def kdb(x):
    """Ungated K-weighted level of a (mono or stereo) segment, BS.1770 channel sum."""
    y = k_weight(as_st(x))
    return -0.691 + 10 * np.log10(np.mean(y ** 2, axis=0).sum() + 1e-20)


def lufs(x):
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_db(x):
    return 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)


def peak_comp(x, thr_db, ratio, hold_ms=4.0):
    """Look-ahead true-peak compressor: peaks above thr are reduced ratio:1 (monotonic, so the
    loudest hit stays the loudest), gain held/smoothed over +-hold_ms so it never undershoots."""
    thr = 10 ** (thr_db / 20)
    up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = np.maximum(up[:len(x) * 4].reshape(len(x), 4).max(axis=1), 1e-12)
    need = np.where(pk > thr, thr * (pk / thr) ** (1 / ratio) / pk, 1.0)
    h = int(hold_ms * SR / 1000)
    g = minimum_filter1d(need, 2 * h + 1, mode='nearest')
    g = uniform_filter1d(g, 2 * h + 1, mode='nearest')
    return x * g[:, None]


def master(x, hp, ratio=PEAK_RATIO):
    """Loudness to TARGET_LUFS with true peak <= TP_CEIL_DB. The peak compressor is applied once to the
    un-compressed mix (after the 25 Hz DC high-pass); its threshold is found by bisection (never
    compounding); an 8 Hz 1st-order DC blocker follows it (gain riding can add DC), then re-normalise."""
    norm = lambda y: y * 10 ** ((TARGET_LUFS - lufs(y)) / 20)
    x = norm(signal.sosfilt(hp, x, axis=0))                     # 25 Hz DC high-pass
    dcb = signal.butter(1, 8, 'highpass', fs=SR, output='sos')   # gentle DC blocker after gain riding
    run = lambda thr: norm(x if thr is None else signal.sosfilt(dcb, peak_comp(x, thr, ratio), axis=0))
    y = run(None)
    if true_peak_db(y) <= TP_CEIL_DB:
        return y
    lo, hi = TP_CEIL_DB - 24.0, TP_CEIL_DB
    best = run(lo)
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        y = run(mid)
        if true_peak_db(y) <= TP_CEIL_DB:
            lo, best = mid, y
        else:
            hi = mid
    return best


# ----------------------------------------------------------------------------- pitch choices
def tone_near(pcs, f):
    m0 = 69 + 12 * np.log2(f / 440)
    cands = [m for m in range(int(m0) - 8, int(m0) + 9) if m % 12 in pcs]
    return min(cands, key=lambda m: (abs(m - m0), m))


def tones_in(pcs, lo, hi):
    return [m for m in range(int(69 + 12 * np.log2(lo / 440)), int(69 + 12 * np.log2(hi / 440)) + 2)
            if m % 12 in pcs and lo <= hz(m) <= hi]


def ui_pitches(name, ch, final):
    pcs = ch['pcs']
    if name == 'tap':
        return [tone_near(pcs, 2000)]
    if name == 'toggle':
        a = tone_near(pcs, 880)
        b = min(m for m in range(a + 5, a + 13) if m % 12 in pcs)
        return [a, b]
    if name == 'flip':
        a = tone_near(pcs, 1200)
        b = max(m for m in range(a - 9, a - 1) if m % 12 in pcs)
        return [a, b]
    if name == 'bubble':
        return [tone_near(pcs, 1150)]
    if name == 'type':
        lad = tones_in(pcs, 2800, 4600)
        return [lad[i % len(lad)] for i in (0, 2, 1, 3)]
    if name == 'check':
        a = min(m for m in range(72, 100) if m % 12 in pcs and (m + 3) % 12 in pcs and hz(m) >= 650)
        return [a, a + 3]
    if name == 'drop':
        r = midi(ch['root']) % 12
        return [12 * 4 + r]                      # octave 3
    if name == 'logo':
        return [midi(n) for n in final['chime']]
    return []                                    # slide: unpitched


# ----------------------------------------------------------------------------- mallet models
def marimba(f, n, tau=None, mallet=0.25, rng=None):
    """Tuned marimba bar: modes 1 : 4 : 10 (two octaves; three octaves + major third), felt mallet."""
    t = np.arange(n) / SR
    tau = tau or float(np.clip(0.45 * (220 / f) ** 0.5, 0.05, 0.6))
    y = np.zeros(n)
    for ratio, a, tr in ((1.0, 1.0, 1.0), (4.0, 0.3, 0.2), (10.0, 0.07, 0.06)):
        if f * ratio < 15000:
            y += a * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / (tau * tr))
    y *= np.clip(t / 0.001, 0, 1) * (1 + 0.9 * np.exp(-t / 0.004))
    if rng is not None and mallet > 0:
        m = signal.sosfilt(sos('lowpass', min(4 * f, 9000), 2), rng.standard_normal(n)) * env_ad(n, 0.0003, 0.0015)
        y += mallet * m / (np.abs(m).max() + 1e-12)
    return y


def glass(f, n, tau=0.3, cents=3.0, rng=None, tink=0.15):
    """Glass mallet: harmonic modes 1 : 2 : 3, a +-cents detuned pair -> L/R (wide shimmer)."""
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for ch, c in ((0, -cents), (1, cents)):
        ff = f * 2 ** (c / 1200)
        for k, a, tr in ((1, 1.0, 1.0), (2, 0.3, 0.4), (3, 0.14, 0.25)):
            if ff * k < 15000:
                out[:, ch] += a * np.sin(2 * np.pi * ff * k * t + 0.3 * ch) * np.exp(-t / (tau * tr))
    out *= (np.clip(t / 0.0008, 0, 1) * (1 + 1.2 * np.exp(-t / 0.003)))[:, None]
    if rng is not None and tink > 0:
        k = signal.sosfilt(sos('bandpass', [6000, 13000], 4), rng.standard_normal((n, 2)), axis=0)
        out += tink * k * env_ad(n, 0.0002, 0.0012)[:, None] / (np.abs(k).max() + 1e-12)
    return out


# ----------------------------------------------------------------------------- bed instruments
def kick():
    """Softer, rounder kick: pure pitch-dropping sine, no drive, gentle 5 ms accent (still the peak)."""
    t = tvec(0.5)
    f = 50 + 100 * np.exp(-t / 0.02)             # 150 -> ~55 Hz by 60 ms, settles at 50 Hz
    ph = 2 * np.pi * (np.cumsum(f) / SR - 150 * 0.0006) + np.pi / 2   # cosine crest at 0.6 ms = the peak
    y = (np.sin(ph) + 0.08 * np.sin(2 * ph)) * env_ad(len(t), 0.0004, 0.16)
    y *= 1 + 0.9 * np.exp(-t / 0.005)
    y = signal.sosfilt(sos('highpass', 25, 2), y)
    return fade_tail(y, 30)


def hat(rng, tau=0.012):
    n = int(0.08 * SR)
    x = rng.standard_normal((n, 2))                      # fully decorrelated L/R: wide
    x = signal.sosfilt(sos('highpass', 8000, 4), x, axis=0)
    x = signal.sosfilt(sos('lowpass', 14000, 8), x, axis=0)
    x = x * env_ad(n, 0.001, tau)[:, None]
    return fade_tail(x, 10) / (np.abs(x).max() + 1e-12)


def clap(rng, tail=0.09, bursts=(0.0, 0.01, 0.02), main=0.03, spike=0.5, sat=True):
    n = int((main + 6 * tail + 0.02) * SR)
    t = np.arange(n) / SR
    env = np.zeros(n)
    for b in bursts:
        env += 0.5 * (t >= b) * np.exp(-np.maximum(t - b, 0) / 0.004)
    env += (t >= main) * (np.exp(-np.maximum(t - main, 0) / tail) + spike * np.exp(-np.maximum(t - main, 0) / 0.0025))
    x = rng.standard_normal((n, 2))                      # decorrelated L/R: wide, soft
    x = signal.sosfilt(sos('bandpass', [1100, 4500], 2), x, axis=0) * env[:, None]
    if sat:
        x = np.tanh(1.8 * x / np.abs(x).max()) / np.tanh(1.8)
    return fade_tail(x, 10)


def bass_note(f, dur):
    t = tvec(dur + 0.05)
    ph = 2 * np.pi * f * t
    env = env_ad(len(t), 0.008, 0.9)
    rel = np.clip((dur + 0.05 - t) / 0.05, 0, 1)
    return (np.sin(ph) + 0.38 * np.sin(2 * ph) + 0.16 * np.sin(3 * ph)) * env * rel


def airy_pad(freqs, dur, rng, att=0.12, rel=0.15, bright=3.5, decay=None, air=0.08):
    """3 detuned additive saws per note (L / C / R), soft low-pass slope, plus a breath-noise layer."""
    t = tvec(dur)
    n = len(t)
    out = np.zeros((n, 2))
    for f in freqs:
        for cents, pan in ((-9, -0.8), (0, 0.0), (9, 0.8)):
            ff = f * 2 ** (cents / 1200)
            K = int(min(14, 12000 / ff))
            k = np.arange(1, K + 1)[:, None]
            amp = (1 / k) / (1 + (k / bright) ** 3)
            ph = rng.uniform(0, 2 * np.pi, (K, 1))
            v = (amp * np.sin(2 * np.pi * ff * k * t[None, :] + ph)).sum(0)
            out += pan2(v, pan)
    lfo = 1 + 0.08 * np.sin(2 * np.pi * 0.5 * t + rng.uniform(0, 6.28))
    nz = rng.standard_normal((n, 2))
    nz = signal.sosfilt(sos('bandpass', [2500, 9000], 2), nz, axis=0)
    out = out / (np.abs(out).max() + 1e-12) + air * nz / (np.abs(nz).max() + 1e-12)
    a = np.clip(t / att, 0, 1) ** 2
    r = np.clip((dur - t) / rel, 0, 1)
    e = a * r * lfo
    if decay:
        e = e * np.exp(-t / decay)
    return out * e[:, None]


def riser(rng, dur):
    n = int(dur * SR)
    x = rng.standard_normal((n, 2))
    y = np.stack([stft_sweep(x[:, c], lambda tt: 500 * (10000 / 500) ** np.clip(tt / dur, 0, 1),
                             0.55, nper=1024, hop=128) for c in (0, 1)], 1)
    u = np.arange(n) / n
    y *= (0.03 + u ** 2.2)[:, None]
    return y


# ----------------------------------------------------------------------------- UI sounds
def ui_tap(rng, ms):
    return fade_tail(glass(hz(ms[0]), int(0.3 * SR), tau=0.09, rng=rng, tink=0.3), 30)


def ui_toggle(rng, ms):
    f1, f2 = hz(ms[0]), hz(ms[1])
    t = tvec(0.3)
    u = np.clip((t - 0.035) / 0.03, 0, 1)
    u = 0.5 - 0.5 * np.cos(np.pi * u)
    out = np.zeros((len(t), 2))
    for ch, c in ((0, -3), (1, 3)):
        f = f1 * (f2 / f1) ** u * 2 ** (c / 1200)
        ph = 2 * np.pi * np.cumsum(f) / SR
        out[:, ch] = (np.sin(ph) + 0.25 * np.sin(2 * ph) * np.exp(-t / 0.05) + 0.1 * np.sin(3 * ph) * np.exp(-t / 0.03))
    out *= (env_ad(len(t), 0.0008, 0.11) * (1 + 0.8 * np.exp(-t / 0.003)))[:, None]
    return fade_tail(out, 30)


def ui_slide(rng, ms):
    dur = 0.2
    n = int(dur * SR)
    x = rng.standard_normal((n, 2))
    y = np.stack([stft_sweep(x[:, c], lambda tt: 1200 * (9000 / 1200) ** np.clip(tt / dur, 0, 1), 0.6,
                             nper=256, hop=32) for c in (0, 1)], 1)
    u = np.arange(n) / n
    y *= (np.sin(np.pi * u ** 0.75) ** 2)[:, None]
    p = (u - 0.5) * 2 * 0.95                            # hard L -> R
    a = (p + 1) * np.pi / 4
    y = np.stack([y[:, 0] * np.cos(a), y[:, 1] * np.sin(a)], 1) * np.sqrt(2)
    return fade_tail(y, 5)


def ui_flip(rng, ms):
    n = int(0.16 * SR)
    y = np.zeros(n)
    for m, a, off in ((ms[0], 1.0, 0.0), (ms[1], 0.75, 0.045)):
        s = int(off * SR)
        y[s:] += a * marimba(hz(m), n - s, tau=0.07, mallet=0.5, rng=rng)
    return fade_tail(y, 15)


def ui_bubble(rng, ms):
    f = hz(ms[0])
    n = int(0.11 * SR)
    t = np.arange(n) / SR
    fc = f * (0.45 + 0.55 * np.clip(t / 0.024, 0, 1) ** 0.7)
    exc = rng.standard_normal(n) * np.exp(-t / 0.012)
    y = svf_bp(exc, fc, 45.0)
    y *= np.exp(-np.maximum(t - 0.03, 0) / 0.03)
    d = int(0.0006 * SR)                                # Haas: right channel 0.6 ms late -> wide
    st = np.stack([y, np.concatenate([np.zeros(d), y[:-d]])], 1)
    return fade_tail(st, 10)


def ui_type(rng, ms):
    n = int(0.12 * SR)
    y = np.zeros((n, 2))
    for j, m in enumerate(ms):
        s = int(j * 0.02 * SR)
        a = (1.0, 0.78, 0.86, 0.7)[j] * (1 + 0.06 * rng.standard_normal())
        g = glass(hz(m), n - s, tau=0.014, cents=2.0, rng=rng, tink=0.4)
        y[s:] += a * g * np.array([[1.0, 0.35]] if j % 2 == 0 else [[0.35, 1.0]])
    return fade_tail(y, 10)


def ui_check(rng, ms):
    n = int(0.5 * SR)
    y = np.zeros((n, 2))
    y += as_st(marimba(hz(ms[0]), n, tau=0.16, mallet=0.3, rng=rng))
    s = int(0.075 * SR)
    y[s:] += 0.62 * as_st(marimba(hz(ms[1]), n - s, tau=0.25, mallet=0.3, rng=rng))
    y[s:] += 0.12 * glass(2 * hz(ms[1]), n - s, tau=0.2)          # glass octave sheen
    return fade_tail(y, 30)


def ui_drop(rng, ms):
    f = hz(ms[0])
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    y = marimba(f, n, tau=0.13, mallet=0.0)
    puff = signal.sosfilt(sos('lowpass', 700, 2), rng.standard_normal(n)) * env_ad(n, 0.002, 0.012)
    y += 0.35 * puff / (np.abs(puff).max() + 1e-12)
    return fade_tail(y, 30)


def ui_logo(rng, ms):
    n = int(1.95 * SR)
    y = np.zeros((n, 2))
    for j, m in enumerate(ms):
        y += (1.0 - 0.2 * j) * glass(hz(m), n, tau=0.45, cents=4.0, rng=rng, tink=0.3) \
            * np.array([[1.0, 0.55]] if j == 0 else [[0.55, 1.0]] if j == 1 else [[0.85, 0.85]])
        y += 0.45 * pan2(marimba(hz(m) / 2, n, tau=0.4, mallet=0.0), (-0.6, 0.6, 0.0)[j])
    return fade_tail(y, 50)


UI = dict(tap=ui_tap, toggle=ui_toggle, slide=ui_slide, flip=ui_flip, bubble=ui_bubble,
          type=ui_type, check=ui_check, drop=ui_drop, logo=ui_logo)
UI_PAN = dict(tap=-0.65, toggle=0.65, slide=0.0, flip=-0.7, bubble=0.6, type=0.0, check=0.5,
              drop=0.0, logo=0.0)


# ----------------------------------------------------------------------------- render
def render():
    rng = np.random.default_rng(SEED)
    chords, final, cues = parse_sheet(__doc__)
    beat_s = BEAT_FR / FPS
    t_of = lambda c: c['frame'] / FPS

    kick_bus = np.zeros(N_SAMPLES)
    low_bus = np.zeros(N_SAMPLES)                        # bass / sub, mono
    st = {k: np.zeros((N_SAMPLES, 2)) for k in ('hats', 'clap', 'pad', 'riser', 'final')}
    final_low = np.zeros(N_SAMPLES)
    kick_times, events = [], []

    for c in cues:
        t0, ch, bed = t_of(c), chords[c['chord']], c['bed']
        if 'K' in bed:
            put(kick_bus, kick(), t0)
            kick_times.append(t0)
        if 'H' in bed:
            put(st['hats'], 0.5 * pan2(hat(rng)[:, 0], -0.6), t0)
            put(st['hats'], pan2(hat(rng)[:, 1], 0.6), t0 + beat_s / 2)
        if 'C' in bed:
            put(st['clap'], clap(rng), t0)
        root = hz(midi(ch['root']))
        if 'B' in bed:
            put(low_bus, bass_note(root, 0.9 * beat_s), t0, align='start')
        if 'b' in bed:
            put(low_bus, bass_note(root, 0.4 * beat_s), t0 + beat_s / 2, align='start')
    # airy pad: one swell per bar on that bar's chord (overlapping release into the next bar)
    for bar in sorted({c['bar'] for c in cues if 'D' in c['bed']}):
        bc = [c for c in cues if c['bar'] == bar and 'D' in c['bed']]
        ch = chords[bc[0]['chord']]
        a = t_of(bc[0])
        cut = any('Z' in c['bed'] for c in bc)
        b = t_of(bc[-1]) + beat_s + (-0.1 if cut else 0.15)
        fr = [hz(midi(n)) for n in ch['voicing']] + [hz(midi(ch['root']) + 24)]
        sig = airy_pad(fr, b - a, rng, att=0.12 if bar < 6 else 0.4, rel=0.06 if cut else 0.2)
        put(st['pad'], fade_tail(sig, 4), a - 0.01, align='start')
    # riser
    span = [c for c in cues if 'R' in c['bed']]
    a, b = t_of(span[0]), t_of(span[-1]) + beat_s - 0.1
    put(st['riser'], fade_tail(riser(rng, b - a), 4), a, align='start')
    # final hit: round sub + soft wide clap + marimba/glass chord + airy pad swell (+ logo in the UI column)
    xc = [c for c in cues if 'X' in c['bed']][0]
    tx = t_of(xc)
    t = tvec(1.95)
    fsub = hz(midi(final['root']))
    f = fsub + 20 * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * env_ad(len(t), 0.002, 0.33)
    put(final_low, fade_tail(sub, 40), tx - 0.0005, align='start')
    put(st['final'], 1.3 * clap(rng, tail=0.12, bursts=(), main=0.0, spike=2.5, sat=False), tx - 0.0005,
        align='start')
    chord_sig = np.zeros((len(t), 2))
    for i, nn in enumerate(final['voicing']):
        fq = hz(midi(nn))
        chord_sig += pan2(marimba(fq, len(t), tau=0.5, mallet=0.2, rng=rng), -0.8 + 0.32 * i)
        if fq > 400:
            chord_sig += 0.5 * glass(fq, len(t), tau=0.5, cents=4.0)
    chord_sig += 0.35 * airy_pad([hz(midi(n)) for n in final['voicing']], 1.95, rng, att=0.06, rel=0.3,
                                 decay=0.5)
    put(st['final'], chord_sig, tx - 0.0005, align='start')

    # stereo elements: nothing below 120 Hz
    hp = sos('highpass', HP_STEREO, 4)
    for k in st:
        st[k] = signal.sosfilt(hp, st[k], axis=0)

    # stem levels (ungated K-weighted dB over their region)
    g3 = slice(int(4 * SR), int(10 * SR))
    def level(x, region, target):
        return x * 10 ** ((target - kdb(x[region])) / 20)
    kick_bus = level(kick_bus, g3, -21)
    low_bus = level(low_bus, g3, -19.5)
    pad_full = level(st['pad'], g3, -17)
    st['pad'] = pad_full
    st['hats'] = level(st['hats'], g3, -28)
    st['clap'] = level(st['clap'], g3, -24)
    r6 = slice(int(10 * SR), int(11.9 * SR))
    st['riser'] = level(st['riser'], r6, -25)
    rf = slice(int(tx * SR), int((tx + 0.5) * SR))
    fin_st, fin_lo = st['final'], final_low
    gfin = 10 ** ((-16 - kdb(fin_st[rf] + as_st(fin_lo[rf]))) / 20)
    st['final'], final_low = fin_st * gfin, fin_lo * gfin

    # sidechain duck (everything but the kick)
    duck_db = np.zeros(N_SAMPLES)
    for tk in kick_times:
        seg = np.concatenate([np.linspace(0, 1, int(0.003 * SR)), np.ones(int(0.012 * SR)),
                              np.linspace(1, 0, int(DUCK_REL * SR))])
        s = int((tk - 0.003) * SR)                 # 3 ms look-ahead: full depth on the beat
        seg, s = (seg[-s:], 0) if s < 0 else (seg, s)
        e = min(N_SAMPLES, s + len(seg))
        duck_db[s:e] = np.maximum(duck_db[s:e], seg[:e - s])
    duck = 10 ** (DUCK_DB * duck_db / 20)

    music_st = sum(st.values())
    music_low = low_bus + final_low
    music = (music_st + as_st(music_low)) * duck[:, None] + as_st(kick_bus)
    music_ref = kdb(music[g3])

    # UI events, each 3 dB under the music
    ui_bus = np.zeros((N_SAMPLES, 2))
    for c in cues:
        ch = chords[c['chord']]
        for name, gdb in c['ui']:
            ms = ui_pitches(name, ch, final)
            for m in ms:
                assert m % 12 in ch['pcs'], (c['beat'], name, mname(m))
            sig = UI[name](rng, ms)
            if sig.ndim == 1:
                sig = pan2(sig, UI_PAN[name] * (1 if c['beat'] % 2 else -1))
            elif UI_PAN[name]:
                p = UI_PAN[name] * (1 if c['beat'] % 2 else -1)
                sig = sig * np.array([[np.sqrt(1 - max(p, 0)), np.sqrt(1 + min(p, 0))]])
            sig = signal.sosfilt(hp, sig, axis=0)
            pk = int(np.argmax(np.abs(sig).sum(1)))
            w = sig[max(0, pk - int(0.02 * SR)):pk + int(0.08 * SR)]
            target = music_ref + UI_UNDER_MUSIC_DB + gdb + (1.5 if name == 'logo' else 0.0)
            g_loud = target - kdb(w)
            g_peak = target + UI_CREST_MAX - 20 * np.log10(np.abs(sig).max())
            sig = sig * 10 ** (min(g_loud, g_peak) / 20)
            at = put(ui_bus, sig, t_of(c))
            events.append(dict(beat=c['beat'], name=name, chord=c['chord'], midi=ms, t=t_of(c),
                               peak=at / SR, start=at - pk, sig=sig))
    ui_bus *= duck[:, None]

    mix = music + ui_bus
    hp25 = sos('highpass', 25, 2)

    # loudness + true-peak
    mix = master(mix, hp25)
    tp = true_peak_db(mix)
    if tp > TP_CEIL_DB:                          # final true-peak trim
        mix *= 10 ** ((TP_CEIL_DB - tp) / 20)

    # silence gates: last 0.1 s of bar 6, and the end
    gate = np.ones(N_SAMPLES)
    zc = [c for c in cues if 'Z' in c['bed']][0]
    z0, z1 = int((t_of(zc) + beat_s - 0.1) * SR), int((tx - 0.002) * SR)
    k = int(0.004 * SR)
    gate[z0 - k:z0] = np.linspace(1, 0, k)
    gate[z0:z1] = 0
    e0, e1 = int(13.5 * SR), int(13.96 * SR)
    gate[e0:e1] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, e1 - e0))
    gate[e1:] = 0
    mix *= gate[:, None]
    return mix, dict(events=events, cues=cues, chords=chords, gate=gate)


def write_wav(path, x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'take-2.wav'
    mix, info = render()
    assert mix.shape == (N_SAMPLES, 2) and np.all(np.isfinite(mix))
    write_wav(out, mix)
    print(f"wrote {out}: {len(mix)} samples, {lufs(mix):.2f} LUFS, {true_peak_db(mix):.2f} dBTP")
    for e in info['events']:
        notes = ' '.join(mname(m) for m in e['midi']) or '(noise)'
        print(f"  beat {e['beat']:2d} {e['chord']:7s} {e['name']:7s} peak {e['peak']*1000:8.1f} ms "
              f"(cue {e['t']*1000:7.1f})  {notes}")


if __name__ == '__main__':
    main()
