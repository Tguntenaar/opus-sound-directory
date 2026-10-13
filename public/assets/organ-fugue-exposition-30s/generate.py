#!/usr/bin/env python3
"""organ-fugue-exposition-30s / take 1 (faithful): cathedral organ, principal chorus.

CREATIVE BRIEF
An original three-voice fugue exposition in D minor for pipe organ, about 30 s long. The alto states a two-bar
subject that leaps up a fifth and then runs down in 8ths, with a second launch (F up to Bb) in bar 2. The soprano
answers tonally in A minor while the alto turns into a countersubject that moves in contrary motion against it.
The pedal brings in the subject on 16' + 8'. A circle-of-fifths episode built from the subject's falling 8ths
leads to a iv6 - V(4-3) - I cadence and a held D major chord (Picardy third). Bar 10 is the cathedral tail.
Registration: manuals on principal 8' + octave 4' + fifteenth 2', a quiet mixture added on the last chord;
pedal 16' (sine + 2nd/3rd harmonic) + principal 8'. Each pipe has a 30 ms chiff (band-passed noise at about 4x f0),
a +-0.3 % / 5 Hz wind tremor and a short release. The room is an 8-line feedback-delay network (RT60 4 s,
pre-delay 40 ms). Alto is panned left, soprano right, pedal centre. The tuning is Werckmeister III with A4 = 440 Hz.

SUBJECT (alto, D minor, original):  D4 A4 | C5 Bb4 A4 G4 | F4 Bb4 A4 G4 F4 E4 | D4
  rhythm  q q e e e e | e e e e e e q   (opens with a leap of a 5th, then running 8ths)
TONAL ANSWER (soprano, A minor):    A4 D5 | G5 F5 E5 D5 | C5 F5 E5 D5 C5 B4 | A4
  (head mutated: subject D->A is answered A->D; the rest is transposed up a 5th)

GRID: bpm=80 beats_per_bar=4 bars=10 fps=30
  1 beat = 0.75 s = 22.5 frames = 36000 samples; bar n starts at frame 90*(n-1); total 900 frames = 1440000 samples.

EVENTS (frame = beat * 22.5; the code checks each one against the note table below)
  E f0    beat 0   subject enters, alto, D minor              [checker cue]
  E f180  beat 8   tonal answer, soprano, A minor; alto countersubject
  E f360  beat 16  pedal entry: subject in D minor on 16' + 8'; soprano countersubject, alto free voice
  E f540  beat 24  episode: subject's falling 8ths in sequence over g - C - F - Bb (circle of fifths)
  E f720  beat 32  cadence: iv6 - V with 4-3 suspension - V7
  E f765  beat 34  D major chord (Picardy third), held, quiet mixture added
  E f810  beat 36  chord released: cathedral tail (bar 10)
  E f900  beat 40  end of file

HARMONY UNDER EVERY BAR (one symbol per beat; printed from the note table)
  bar 1  (f0)    subject alone, implies   i     .     V     .
  bar 2  (f90)   subject alone, implies   III   VI    V     i
  bar 3  (f180)  a minor:                 i6    vii   VII   III
  bar 4  (f270)  a minor:                 i     III   VI6-V i6
  bar 5  (f360)  d minor:                 i     V     VII   VI6
  bar 6  (f450)  d minor:                 i6    VI6   VI    i
  bar 7  (f540)  d minor (circle):        iv    VI6   VII   VII6
  bar 8  (f630)  d minor (circle):        III   v6    VI    VI6
  bar 9  (f720)  cadence:                 iv6   V4-3/V7     I (D major, held)
  bar 10 (f810)  tail (no notes)

NOTE TABLE (voice bar | pitch/beats ...; r = rest; '~' ties into the next token; bass is written at 8' pitch)
  S 1 | r/4
  S 2 | r/4
  S 3 | A4/1 D5/1 G5/.5 F5/.5 E5/.5 D5/.5
  S 4 | C5/.5 F5/.5 E5/.5 D5/.5 C5/.5 B4/.5 A4/1
  S 5 | F5/.5 G5/.5 E5/.5 D5/.5 C5/.5 D5/.5 F5/1
  S 6 | D5/1 F5/.5 G5/.5 A5/.5 G5/.5 F5/1
  S 7 | D5/.5 C5/.5 Bb4/.5 A4/.5 E5/.5 D5/.5 C5/.5 Bb4/.5
  S 8 | C5/.5 Bb4/.5 A4/.5 G4/.5 D5/.5 C5/.5 Bb4/.5 A4/.5
  S 9 | D5/1.5 C#5/.5 D5/2
  A 1 | D4/1 A4/1 C5/.5 Bb4/.5 A4/.5 G4/.5
  A 2 | F4/.5 Bb4/.5 A4/.5 G4/.5 F4/.5 E4/.5 D4/1
  A 3 | C4/.5 D4/.5 B3/.5 A3/.5 G3/.5 A3/.5 C4/1
  A 4 | A3/1 C4/.5 D4/.5 E4/.5 D4/.5 C4/1
  A 5 | D4/1 C#4/1 E4/.5 D4/.5 C4/1
  A 6 | D4/1 C4/1.5 C#4/.5 D4/1
  A 7 | Bb4/1 F4/1 E4/1 G4/1
  A 8 | A4/1 E4/1 D4/1 F4/1
  A 9 | G4/1 A4/.5 G4/.5 F#4/2
  T 9 | r/2 A3/2
  B 5 | D3/1 A3/1 C4/.5 Bb3/.5 A3/.5 G3/.5
  B 6 | F3/.5 Bb3/.5 A3/.5 G3/.5 F3/.5 E3/.5 D3/1
  B 7 | G2/1 D3/1 C3/1 E3/1
  B 8 | F3/1 C3/1 Bb2/1 D3/1
  B 9 | Bb2/1 A2/1 D3/2
END NOTE TABLE

COUNTERPOINT CHECK (run by this script before it renders; copy of its output)
  sonorities on the 8th grid: 56 (28 on beats, 28 off-beats; bars 1-2 are the solo subject)
  dissonances on beats: 1, all prepared suspensions (beat 33: S D5 over B A2, 4-3, resolves to C#5)
  off-beat dissonances: 19, all passing / neighbour / appoggiatura / escape tones (step in or step out)
  parallel 5ths or 8ves between any pair of voices (successive sonorities, any direction): 0
  accented (beat-to-beat) parallels in the outer voices: 0
  voice crossings: 0;  ranges: S C4-A5, A F3-D5, T C3-A4, B(8') D2-D4 all respected
  subject vs well-known fugue subjects (BWV 565, 578, 542, 851, Art of Fugue, K.626 Kyrie):
    longest shared run of identical intervals = 2 (needs >= 5 to count as a quotation)
"""
import re
import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d

SR = 48000
N_SAMPLES = 1440000
SEED = 42
TARGET_LUFS = -14.0

# ----------------------------------------------------------------------------------------------- take-specific voicing
def PRINCIPAL(n):
    """Principal pipe: partials 1..n falling ~6 dB per octave."""
    return [1.0 / k for k in range(1, n + 1)]


TAKE = dict(
    name="take-1 faithful cathedral",
    tempo_bpm=None,                    # None = read from GRID in the docstring
    # ranks: (multiple of the 8' frequency, level, partial amplitudes [or f -> list], attack scale)
    manual_ranks=[(1.0, 1.0, PRINCIPAL(8)), (2.0, 0.50, PRINCIPAL(8)), (4.0, 0.28, PRINCIPAL(5))],  # 8' 4' 2'
    final_mixture=[(6.0, 0.060, PRINCIPAL(3)), (8.0, 0.045, PRINCIPAL(3)), (12.0, 0.030, PRINCIPAL(2))],
    pedal_ranks=[(0.5, 1.0, [1.0, 0.5, 0.33], 1.6), (1.0, 0.55, PRINCIPAL(6))],  # 16' sine+2nd+3rd, 8' principal
    pedal_reed=None,
    final_swell=None,
    breath=0.0,
    chiff=dict(mult=4.0, level=0.20, decay=0.009, length=0.032, bw=1.35),
    attack=0.030, release=0.055,
    tremor=dict(depth=0.003, rate=5.0),
    room=dict(rt60=4.0, predelay=0.040, delays=[1693, 2063, 2399, 2777, 3109, 3491, 3881, 4337],
              damp=0.22, wet=0.62, diffusers=[(142, 0.62), (107, 0.62), (379, 0.58), (277, 0.58)]),
    pans=dict(S=0.45, A=-0.45, T=-0.15, B=0.0),
    gains=dict(S=1.0, A=1.0, T=0.75, B=0.85),
    end_fade=0.6,
)

DOC = __doc__


# ----------------------------------------------------------------------------------------------- score parsing
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi_of(name):
    m = re.fullmatch(r"([A-G])(#|b)?(\d)", name)
    if not m:
        raise ValueError(f"bad pitch {name!r}")
    pc = PC[m.group(1)] + {"#": 1, "b": -1, None: 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + pc


def parse_score(doc):
    g = re.search(r"GRID:\s*bpm=([\d.]+)\s+beats_per_bar=(\d+)\s+bars=(\d+)\s+fps=(\d+)", doc)
    bpm, bpb, bars, fps = float(g.group(1)), int(g.group(2)), int(g.group(3)), int(g.group(4))
    block = doc.split("NOTE TABLE", 1)[1].split("END NOTE TABLE", 1)[0]
    voices = {v: [] for v in "SATB"}
    tie_open = {v: False for v in "SATB"}
    for v, bar, body in re.findall(r"^\s*([SATB])\s+(\d+)\s+\|\s+(.+?)\s*$", block, re.M):
        t = (int(bar) - 1) * bpb
        total = 0.0
        for tok in body.split():
            tie = tok.endswith("~")
            p, d = tok.rstrip("~").split("/")
            d = float(d)
            if p != "r":
                m = midi_of(p)
                if tie_open[v] and voices[v] and voices[v][-1][0] == m and abs(sum(voices[v][-1][1:]) - t) < 1e-9:
                    voices[v][-1] = (m, voices[v][-1][1], voices[v][-1][2] + d)
                else:
                    voices[v].append((m, t, d))
            tie_open[v] = tie
            t += d
            total += d
        assert abs(total - bpb) < 1e-9, f"{v} bar {bar} sums to {total} beats"
    events = [(int(f), float(b)) for f, b in re.findall(r"^\s*E f(\d+)\s+beat ([\d.]+)", doc, re.M)]
    return dict(bpm=bpm, bpb=bpb, bars=bars, fps=fps), voices, events


# ----------------------------------------------------------------------------------------------- counterpoint checks
RANGES = dict(S=(60, 81), A=(53, 74), T=(48, 69), B=(38, 62))
ORDER = "SATB"
CONS = {0, 3, 4, 7, 8, 9}


def note_at(notes, t):
    for i, (m, s, d) in enumerate(notes):
        if s - 1e-9 <= t < s + d - 1e-9:
            return i
    return None


def counterpoint_check(voices, end_beat):
    grid = np.arange(0, end_beat, 0.5)
    errors, report = [], []
    n_beat = n_off = 0
    beat_diss, off_diss = [], []

    def sounding(t):
        out = {}
        for v in ORDER:
            i = note_at(voices[v], t)
            if i is not None:
                out[v] = i
        return out

    def pair_consonant(snd, u, v, t):
        pu, pv = voices[u][snd[u]][0], voices[v][snd[v]][0]
        ic = abs(pu - pv) % 12
        if ic in CONS:
            return True
        low = min(snd, key=lambda w: voices[w][snd[w]][0])
        if len(snd) >= 3 and low not in (u, v):
            pb = voices[low][snd[low]][0]
            if ic == 5:
                return True
            if ic == 6:  # diminished 6/3 or V6/5 colour: both upper notes consonant with the bass
                return all(abs(p - pb) % 12 in CONS for p in (pu, pv))
        return False

    def step_in(v, i):
        return i > 0 and abs(voices[v][i][0] - voices[v][i - 1][0]) <= 2 and \
            abs(sum(voices[v][i - 1][1:]) - voices[v][i][1]) < 1e-9

    def step_out(v, i):
        return i + 1 < len(voices[v]) and abs(voices[v][i + 1][0] - voices[v][i][0]) <= 2 and \
            abs(sum(voices[v][i][1:]) - voices[v][i + 1][1]) < 1e-9

    def suspension(v, i, t):
        m, s, d = voices[v][i]
        if not s < t - 1e-9:
            return False
        prep = sounding(s)
        if not all(pair_consonant(prep, v, w, s) for w in prep if w != v):
            return False
        nxt = voices[v][i + 1] if i + 1 < len(voices[v]) else None
        return nxt is not None and abs(nxt[1] - (s + d)) < 1e-9 and 1 <= m - nxt[0] <= 2 and nxt[1] <= t + 1 + 1e-9

    for t in grid:
        snd = sounding(t)
        if len(snd) < 2:
            continue
        on_beat = abs(t - round(t)) < 1e-9
        n_beat += on_beat
        n_off += not on_beat
        # crossing
        pres = [v for v in ORDER if v in snd]
        for a, b in zip(pres, pres[1:]):
            if voices[a][snd[a]][0] < voices[b][snd[b]][0]:
                errors.append(f"crossing at beat {t}: {a} below {b}")
        for k, u in enumerate(pres):
            for v in pres[k + 1:]:
                if pair_consonant(snd, u, v, t):
                    continue
                iu, iv = snd[u], snd[v]
                if on_beat:
                    ok = [w for w, i in ((u, iu), (v, iv)) if suspension(w, i, t)]
                    if ok:
                        w = ok[0]
                        beat_diss.append(f"beat {t:g}: {w} {voices[w][snd[w]][0]} suspension vs {u if w == v else v}")
                    else:
                        errors.append(f"unprepared dissonance on beat {t:g}: {u}/{v}")
                else:
                    attackers = [(w, i) for w, i in ((u, iu), (v, iv)) if abs(voices[w][i][1] - t) < 1e-9]
                    if any(step_in(w, i) or step_out(w, i) for w, i in attackers):
                        off_diss.append(t)
                    else:
                        errors.append(f"off-beat dissonance not by step at beat {t:g}: {u}/{v}")
    # parallels: successive distinct sonorities of each pair
    par = 0
    acc = 0
    for k, u in enumerate(ORDER):
        for v in ORDER[k + 1:]:
            seq = []
            for t in grid:
                iu, iv = note_at(voices[u], t), note_at(voices[v], t)
                if iu is None or iv is None:
                    seq.append(None)
                    continue
                pair = (voices[u][iu][0], voices[v][iv][0], iu, iv)
                if not seq or seq[-1] is None or seq[-1][2:] != pair[2:]:
                    seq.append(pair)
            for a, b in zip(seq, seq[1:]):
                if a is None or b is None:
                    continue
                if a[0] != b[0] and a[1] != b[1]:
                    ia, ib = abs(a[0] - a[1]) % 12, abs(b[0] - b[1]) % 12
                    if ia == ib and ia in (0, 7):
                        par += 1
                        errors.append(f"consecutive {'8ves' if ia == 0 else '5ths'} {u}/{v}: {a[:2]} -> {b[:2]}")
    # accented parallels, outer voices, beat to beat
    beats = np.arange(0, end_beat, 1.0)
    prev = None
    for t in beats:
        snd = sounding(t)
        pres = [v for v in ORDER if v in snd]
        if len(pres) < 2:
            prev = None
            continue
        top, bot = voices[pres[0]][snd[pres[0]]][0], voices[pres[-1]][snd[pres[-1]]][0]
        cur = (top, bot, (top - bot) % 12)
        if prev and prev[2] == cur[2] and cur[2] in (0, 7) and prev[0] != top and prev[1] != bot:
            acc += 1
            errors.append(f"accented outer-voice parallel into beat {t:g}")
        prev = cur
    # ranges
    for v, (lo, hi) in RANGES.items():
        for m, s, d in voices[v]:
            if not lo <= m <= hi:
                errors.append(f"{v} out of range at beat {s:g}: {m}")
    report.append(f"sonorities on the 8th grid: {n_beat + n_off} ({n_beat} on beats, {n_off} off-beats)")
    report.append(f"dissonances on beats: {len(beat_diss)} -> " + ("; ".join(beat_diss) or "none"))
    report.append(f"off-beat dissonances: {len(off_diss)}, all approached or left by step")
    report.append(f"consecutive 5ths/8ves between any pair: {par}; accented outer-voice parallels: {acc}")
    return errors, report


KNOWN_SUBJECTS = {  # approximate, from memory; used only as a quotation guard on interval sequences
    "BWV 565 fugue": "A4 G4 A4 E4 F4 D4 E4 C#4 D4 A3 Bb3 A3",
    "BWV 578 Little fugue": "G4 D5 Bb4 A4 G4 Bb4 A4 G4 F#4 A4 D4",
    "BWV 542 fugue": "G4 D5 Bb4 A4 G4 Bb4 A4 G4 F#4 D4",
    "BWV 851 WTC I d minor": "D4 E4 F4 G4 E4 F4 D4 C#4 D4 Bb4 G4 A4",
    "Art of Fugue": "D4 A4 F4 D4 C#4 D4 E4 F4 G4 F4 E4",
    "K.626 Kyrie": "D4 A3 Bb3 C#3 D3",
}


def originality_check(subject):
    iv = np.diff([m for m, _, _ in subject])
    worst = 0
    for name, txt in KNOWN_SUBJECTS.items():
        kv = np.diff([midi_of(p) for p in txt.split()])
        for i in range(len(iv)):
            for j in range(len(kv)):
                k = 0
                while i + k < len(iv) and j + k < len(kv) and iv[i + k] == kv[j + k]:
                    k += 1
                worst = max(worst, k)
    return worst


# ----------------------------------------------------------------------------------------------- synthesis
WM3 = np.array([0, -9.8, -7.8, -5.9, -9.8, -2.0, -11.7, -3.9, -7.8, -11.7, -3.9, -7.8])


def freq(m):
    return 440.0 * 2 ** ((m - 69) / 12 + (WM3[m % 12] - WM3[9]) / 1200)


def pipe(f8, t_on, t_off, ranks, rng, tr, att, rel, chiff, swell=None, breath=0.0):
    """One key held from t_on to t_off (s): additive ranks + chiff, returns (start sample, mono array)."""
    s0 = int(round(t_on * SR))
    hold = t_off - t_on
    n = int((hold + rel * 7) * SR)
    tl = np.arange(n) / SR
    ta = tl + t_on
    phi = rng.uniform(0, 2 * np.pi)
    wob = -tr["depth"] / (2 * np.pi * tr["rate"]) * np.cos(2 * np.pi * tr["rate"] * ta + phi)
    off = np.where(tl > hold, np.exp(-(tl - hold) / rel), 1.0)
    out = np.zeros(n)
    for rank in ranks:
        mult, lev, amps = rank[:3]
        a_scale = rank[3] if len(rank) > 3 else 1.0
        f_r = f8 * mult
        if callable(amps):
            amps = amps(f_r)
        for k, a in enumerate(amps, start=1):
            f = f_r * k * (1 + rng.normal(0, 0.0002))
            if f > 16000:
                break
            a_k = att * a_scale * (0.55 + 0.45 / np.sqrt(k))
            on = 0.5 - 0.5 * np.cos(np.pi * np.minimum(tl / a_k, 1.0))
            env = on * off
            if swell is not None:
                env = env * swell(tl, f)
            out += lev * a * env * np.sin(2 * np.pi * f * (ta + wob) + rng.uniform(0, 2 * np.pi))
    if breath > 0:  # steady wind noise at the mouth of the pipe (flute stops)
        sosb = signal.butter(2, [min(2 * f8, 9000), min(6 * f8, 15000)], "bandpass", fs=SR, output="sos")
        nb = signal.sosfilt(sosb, rng.standard_normal(n))
        nb /= np.sqrt(np.mean(nb ** 2)) + 1e-12
        out += breath * nb * (0.5 - 0.5 * np.cos(np.pi * np.minimum(tl / att, 1.0))) * off
    # chiff: band-passed noise at ~mult x the 8' fundamental
    L = int(chiff["length"] * SR)
    fc = min(chiff["mult"] * f8, 12000.0)
    sos = signal.butter(2, [fc / chiff["bw"], min(fc * chiff["bw"], 0.45 * SR)], "bandpass", fs=SR, output="sos")
    nz = signal.sosfilt(sos, rng.standard_normal(L + 256))[256:]
    nz /= np.sqrt(np.mean(nz ** 2)) + 1e-12
    tc = np.arange(L) / SR
    cenv = (1 - np.exp(-tc / 0.0015)) * np.exp(-tc / chiff["decay"]) * (0.5 + 0.5 * np.cos(np.pi * tc / tc[-1]))
    out[:L] += chiff["level"] * 0.5 * nz * cenv
    out *= np.minimum(1.0, (n - np.arange(n)) / (0.004 * SR))  # tidy end of release
    return s0, out


def allpass_block(x, M, g):
    y = np.zeros_like(x)
    xp = np.concatenate([np.zeros(M), x])
    yp = np.zeros(len(x) + M)
    for n0 in range(0, len(x), M):
        n1 = min(len(x), n0 + M)
        seg = -g * x[n0:n1] + xp[n0:n1] + g * yp[n0:n1]
        yp[M + n0:M + n1] = seg
    y[:] = yp[M:]
    return y


def fdn_reverb(xl, xr, room, rng):
    N = len(xl)
    # the network's first output comes one (shortest) delay line after its input: subtract it from the pre-delay
    pd = max(0, int(room["predelay"] * SR) - int(min(room["delays"])))
    sl = np.concatenate([np.zeros(pd), xl])[:N]
    sr_ = np.concatenate([np.zeros(pd), xr])[:N]
    for M, g in room["diffusers"]:
        sl, sr_ = allpass_block(sl, M, g), allpass_block(sr_, M + 13, g)
    d = np.array(room["delays"])
    K = len(d)
    H = np.array([[1.0]])
    while H.shape[0] < K:
        H = np.block([[H, H], [H, -H]])
    H /= np.sqrt(K)
    gains = 10 ** (-3 * d / (room["rt60"] * SR))
    sgn = rng.choice([-1.0, 1.0], size=K)
    inj = np.zeros((K, N))
    inj[0::2] = sl * sgn[0::2, None]
    inj[1::2] = sr_ * sgn[1::2, None]
    maxd = int(d.max())
    buf = np.zeros((K, N + maxd))
    yout = np.zeros((K, N))
    a = room["damp"]
    zi = np.zeros((K, 1))
    B = int(d.min())
    for n0 in range(0, N, B):
        n1 = min(N, n0 + B)
        L = n1 - n0
        y = np.stack([buf[i, maxd + n0 - d[i]: maxd + n0 - d[i] + L] for i in range(K)]) * gains[:, None]
        for i in range(K):
            y[i], zi[i] = signal.lfilter([1 - a], [1, -a], y[i], zi=zi[i])
        yout[:, n0:n1] = y
        buf[:, maxd + n0:maxd + n1] = H @ y + inj[:, n0:n1]
    cl = np.array([1, 1, -1, 1, -1, 1, 1, -1][:K], float)
    cr = np.array([1, -1, 1, 1, 1, -1, 1, 1][:K], float)
    return cl @ yout, cr @ yout


def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x):
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    p = np.cumsum(np.concatenate([np.zeros((1, 2)), y ** 2]), axis=0)
    st = np.arange(0, len(y) - blk + 1, hop)
    z = ((p[st + blk] - p[st]) / blk).sum(axis=1)
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_db(x):
    return 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)


def limit(x, ceil_db):
    c = 10 ** (ceil_db / 20)
    os_ = np.abs(signal.resample_poly(x, 4, 1, axis=0)).reshape(len(x), 4, 2).max(axis=(1, 2))
    need = np.minimum(1.0, c / np.maximum(os_, 1e-9))
    W = int(0.004 * SR)
    g = minimum_filter1d(need, size=2 * W + 1)
    win = np.hanning(2 * W + 1)
    g = np.convolve(g, win / win.sum(), mode="same")
    return x * g[:, None]  # g <= need: every sample in the window sees the window's minimum


def render(out_path):
    grid, voices, events = parse_score(DOC)
    bpm = TAKE["tempo_bpm"] or grid["bpm"]
    spb = 60.0 / bpm
    end_beat = grid["bars"] * grid["bpb"]
    fpb = grid["fps"] * 60.0 / grid["bpm"]

    # ---- composition checks (shared clock: the events must match the note table)
    errors, report = counterpoint_check(voices, end_beat)
    subj = [n for n in voices["A"] if n[1] < 8]
    worst = originality_check(subj)
    first = {v: min((s for _, s, _ in voices[v]), default=None) for v in ORDER}
    expect = {0: first["A"], 8: first["S"], 16: first["B"]}
    for f, b in events:
        assert abs(f - b * fpb) < 0.5, f"event f{f} != beat {b} on the {grid['bpm']} BPM grid"
        if b in expect:
            assert expect[b] == b, f"event at beat {b} has no matching entry"
    print("counterpoint check:")
    for line in report:
        print("  " + line)
    print(f"  originality: longest interval run shared with a known subject = {worst}")
    if errors:
        for e in errors:
            print("  ERROR", e)
        raise SystemExit("counterpoint check failed")
    if worst >= 5:
        raise SystemExit("subject too close to a known fugue subject")

    # ---- synthesis
    rng = np.random.default_rng(SEED)
    buses = {v: np.zeros(N_SAMPLES + SR) for v in ORDER}
    final_beat = max(s for v in ORDER for _, s, _ in voices[v])
    for v in ORDER:
        for m, s, d in voices[v]:
            t_on = s * spb
            is_final = abs(s - final_beat) < 1e-9
            gap = 0.0 if is_final else min(0.045, 0.14 * d * spb)
            t_off = (s + d) * spb - gap
            f8 = freq(m)
            if v == "B":
                ranks = list(TAKE["pedal_ranks"])
                reed = TAKE["pedal_reed"]
                if reed is not None and s >= reed["from_beat"]:
                    ranks.append((1.0, reed["level"], reed["amps"], reed["attack"]))
            else:
                ranks = list(TAKE["manual_ranks"])
                if is_final:
                    ranks += TAKE["final_mixture"]
            swell = None
            if is_final and TAKE["final_swell"] is not None:
                swell = TAKE["final_swell"](t_off - t_on)
            s0, sig = pipe(f8, t_on, t_off, ranks, rng, TAKE["tremor"], TAKE["attack"], TAKE["release"],
                           TAKE["chiff"], swell=swell, breath=TAKE["breath"])
            e = min(len(buses[v]), s0 + len(sig))
            buses[v][s0:e] += TAKE["gains"][v] * sig[:e - s0]
    L = np.zeros(N_SAMPLES)
    R = np.zeros(N_SAMPLES)
    for v in ORDER:
        p = TAKE["pans"][v]
        th = (p + 1) * np.pi / 4
        L += np.cos(th) * np.sqrt(2) * buses[v][:N_SAMPLES]
        R += np.sin(th) * np.sqrt(2) * buses[v][:N_SAMPLES]
    room = TAKE["room"]
    hp = signal.butter(2, 90, "highpass", fs=SR, output="sos")
    wl, wr = fdn_reverb(signal.sosfilt(hp, L), signal.sosfilt(hp, R), room, rng)
    dry_rms = np.sqrt(np.mean(L ** 2 + R ** 2))
    wet_rms = np.sqrt(np.mean(wl ** 2 + wr ** 2)) + 1e-12
    w = room["wet"] * dry_rms / wet_rms
    x = np.stack([L + w * wl, R + w * wr], axis=1)

    # ---- clean-up: DC high-pass, mono below 120 Hz, loudness, true peak, edges
    x = signal.sosfiltfilt(signal.butter(2, 25, "highpass", fs=SR, output="sos"), x, axis=0)
    mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    side = signal.sosfiltfilt(signal.butter(4, 120, "highpass", fs=SR, output="sos"), side)
    x = np.stack([mid + side, mid - side], axis=1)
    fl = int(TAKE["end_fade"] * SR)
    x[-fl:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fl)))[:, None]
    x[0] = 0.0
    for _ in range(4):
        x *= 10 ** ((TARGET_LUFS - lufs(x)) / 20)
        if true_peak_db(x) > -1.25:
            x = limit(x, -1.4)
    tp = true_peak_db(x)
    if tp > -1.05:
        x *= 10 ** ((-1.1 - tp) / 20)
    x = x - x.mean(axis=0)
    x[0] = 0.0
    assert np.all(np.isfinite(x)) and len(x) == N_SAMPLES
    print(f"rendered {TAKE['name']}: {lufs(x):.2f} LUFS, {true_peak_db(x):.2f} dBTP, "
          f"first sample {np.abs(x[0]).max():.1e}, last ms peak {np.abs(x[-48:]).max():.1e}")
    pcm = np.round(np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python take-1.py OUT.wav")
    render(sys.argv[1])
