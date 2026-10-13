"""game-loot-reward-6s -- take 1 (faithful)

CREATIVE BRIEF
The whole mobile-game "you got a reward" moment in one 6.0 s file, built from a named SFX vocabulary:
wooden chest knocks that speed up with creaks, a rising detuned-saw charge with an opening band-pass,
accelerating tremolo and a pentatonic sparkle bed, 0.1 s of true silence, a burst (sub thump + noise
crack + glassy inharmonic "shing"), a coin shower of two-operator FM bells over a rising score-counter
tick, a 5-frame duck, and a brassy saw+square victory fanfare (Bb-D-F-Bb, top voice C -> D) with an
octave-up sine-chorus shimmer that rings out to true silence. Take angle: implement the brief exactly.
Everything is synthesized here; no samples, no melody borrowed from any game.

GRID / CLOCK
48 kHz, 288000 samples = 6.0 s = 180 frames @ 30 fps. 120 BPM -> 1 beat = 15 frames = 0.5 s,
1 bar = 60 frames, 1 sixteenth = 3.75 frames. sample = round(frame / 30 * 48000). Key Bb major.
Harmony under the bars:  bar 1 (f0-60)  F  (dominant: knocks + charge on F)
                         bar 2 (f60-120) F -> Bb (burst at f75, coins on the Bb triad)
                         bar 3 (f120-180) Bb (fanfare Bb-D-F-Bb, top C -> D)

CUE SHEET  (the code parses every '@' row below; it is the only timing table)
  frame   event    params
@   0.00  knock    n=0 creak=0                 CUE f0: chest tap (peak at +1..3 ms, file starts silent)
@  10.00  knock    n=1 creak=1                 knocks accelerate 2 -> 8 per second: phase = 2t + 3t^2
@  16.46  knock    n=2 creak=0
@  21.62  knock    n=3 creak=1
@  26.06  knock    n=4 creak=0
@  30.00  knock    n=5 creak=1
@  30.00  charge   end=72 f0=F3 f1=F4 bp0=500 bp1=5000 trem0=4 trem1=16
@  32.85  ping     note=D6 pan=+0.17           sparkle bed, Bb pentatonic, density rising
@  36.52  ping     note=Bb5 pan=+0.43
@  41.28  ping     note=D6 pan=-0.72
@  43.09  ping     note=F6 pan=+0.56
@  45.37  ping     note=F6 pan=+0.52
@  47.06  ping     note=G6 pan=+0.32
@  52.23  ping     note=C6 pan=+0.57
@  53.41  ping     note=G6 pan=+0.05
@  56.86  ping     note=D6 pan=-0.65
@  60.99  ping     note=G6 pan=+0.55
@  64.82  ping     note=F6 pan=-0.27
@  67.02  ping     note=Bb6 pan=-0.53
@  67.53  ping     note=F6 pan=-0.55
@  68.14  ping     note=C7 pan=+0.70
@  68.24  ping     note=G6 pan=-0.47
@  70.26  ping     note=Bb6 pan=-0.71
@  70.63  ping     note=G6 pan=-0.34
@  70.96  ping     note=C7 pan=-0.00
@  72.00  silence  end=75                      0.1 s of digital zero
@  75.00  burst    sub0=90 sub1=45 shing=1200  CUE f75: chest bursts open
@  78.00  ticks    end=130 rate=20 f0=1500 f1=3000   score counter, 1 ms clicks
@  78.00  coin     note=F6 pan=+0.41 vel=0.96  coin shower, Bb major triad above Bb5
@  79.02  coin     note=D6 pan=+0.72 vel=0.93
@  79.10  coin     note=Bb5 pan=-0.03 vel=0.94
@  79.54  coin     note=D6 pan=+0.76 vel=0.90
@  81.04  coin     note=D6 pan=-0.53 vel=0.98
@  81.20  coin     note=D7 pan=-0.50 vel=0.97
@  81.39  coin     note=D6 pan=+0.09 vel=0.94
@  82.50  coin     note=Bb6 pan=-0.00 vel=0.91
@  86.28  coin     note=D6 pan=+0.06 vel=0.86
@  89.62  coin     note=Bb5 pan=+0.84 vel=0.83
@  94.37  coin     note=Bb5 pan=+0.52 vel=0.85
@  95.19  coin     note=F6 pan=-0.51 vel=0.82
@  97.67  coin     note=D6 pan=-0.84 vel=0.83
@  98.04  coin     note=F6 pan=-0.58 vel=0.81
@  99.00  coin     note=Bb6 pan=-0.01 vel=0.79
@  99.05  coin     note=Bb6 pan=+0.59 vel=0.83
@  99.07  coin     note=Bb5 pan=+0.06 vel=0.80
@  99.41  coin     note=D6 pan=-0.41 vel=0.81
@ 101.87  coin     note=D7 pan=-0.40 vel=0.76
@ 107.69  coin     note=F6 pan=-0.79 vel=0.78
@ 111.18  coin     note=D7 pan=+0.10 vel=0.70
@ 116.99  coin     note=F6 pan=-0.84 vel=0.71
@ 118.95  coin     note=D7 pan=-0.22 vel=0.62
@ 121.73  coin     note=Bb6 pan=+0.57 vel=0.65
@ 130.00  duck     end=135 depth=-24           shower bus ducks out of the way
@ 135.00  brass    len=0.10 chord=Bb2,Bb3,D4,F4,Bb4,C5 vel=0.95   CUE f135: fanfare, 16th #1
@ 138.75  brass    len=0.10 chord=Bb2,Bb3,D4,F4,Bb4,C5 vel=0.90   16th #2
@ 142.50  brass    len=0.85 chord=Bb2,Bb3,D4,F4,Bb4,D5 vel=1.00   held chord, top voice C -> D
@ 142.50  shimmer  len=0.85 chord=Bb4,D5,F5,Bb5,D6               octave-up sine chorus, wide
@ 168.00  fade     end=179.4                    master fade, digital zero after f179.4
"""
import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 48000
N = 288000
FPS = 30
SEED = 42
TARGET_LUFS = -14.0
rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- cue sheet
def parse_cues(doc):
    rows = []
    for line in doc.splitlines():
        s = line.strip()
        if not s.startswith("@"):
            continue
        tok = s[1:].split()
        kw = {}
        for t in tok[2:]:
            if "=" not in t:
                break
            k, v = t.split("=", 1)
            try:
                v = float(v)
            except ValueError:
                pass
            kw[k] = v
        rows.append((float(tok[0]), tok[1], kw))
    return rows


CUES = parse_cues(__doc__)


def fs(frame):
    return int(round(frame / FPS * SR))


NOTE_IDX = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def hz(name):
    p, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE_IDX[p] + 12 * (o + 1) - 69) / 12)


# ---------------------------------------------------------------- dsp helpers
def tt(dur):
    return np.arange(int(round(dur * SR))) / SR


def polyblep(t, dt):
    out = np.zeros_like(t)
    m = t < dt
    x = t[m] / dt[m]
    out[m] = x + x - x * x - 1.0
    m = t > 1.0 - dt
    x = (t[m] - 1.0) / dt[m]
    out[m] = x * x + x + x + 1.0
    return out


def saw(freq, ph0=0.0):
    dt = np.broadcast_to(freq, freq.shape) / SR
    ph = (ph0 + np.cumsum(dt)) % 1.0
    return 2.0 * ph - 1.0 - polyblep(ph, dt)


def square(freq, ph0=0.0):
    dt = freq / SR
    ph = (ph0 + np.cumsum(dt)) % 1.0
    sq = np.where(ph < 0.5, 1.0, -1.0)
    return sq + polyblep(ph, dt) - polyblep((ph + 0.5) % 1.0, dt)


def svf(x, fc, q):
    """TPT state-variable filter (short recursive filter); returns lp, bp, hp."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    g = np.tan(np.pi * np.clip(fc, 20, 20000) / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    lp = np.empty(len(x))
    bp = np.empty(len(x))
    ic1 = ic2 = 0.0
    xs, A1, A2, A3 = x.tolist(), a1.tolist(), a2.tolist(), a3.tolist()
    for n in range(len(xs)):
        v3 = xs[n] - ic2
        v1 = A1[n] * ic1 + A2[n] * v3
        v2 = ic2 + A2[n] * ic1 + A3[n] * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        lp[n] = v2
        bp[n] = v1
    return lp, bp, x - k * bp - lp


def peak(x, f, q):
    b, a = signal.iirpeak(f, q, fs=SR)
    return signal.lfilter(b, a, x, axis=0)


def sos(x, kind, f, order=2):
    return signal.sosfilt(signal.butter(order, f, kind, fs=SR, output="sos"), x, axis=0)


def pan2(sig, pan):
    if sig.ndim == 2:
        return sig
    a = (pan + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], axis=1) * np.sqrt(2)


def place(buf, sig, frame, pan=0.0, align="onset", min_start=0):
    st = pan2(sig, pan)
    s = fs(frame)
    if align == "peak":
        s -= int(np.argmax(np.abs(st).max(axis=1)))
    s = max(s, min_start)
    e = min(N, s + len(st))
    buf[s:e] += st[: e - s]


def make_ir(rt60, dur, damp=3500.0, pre=0.015):
    t = tt(dur)
    n = rng.standard_normal((len(t), 2))
    lo = sos(n, "low", damp)
    hi = n - lo
    ir = lo * (10 ** (-3 * t / rt60))[:, None] + hi * (10 ** (-3 * t / (rt60 * 0.35)))[:, None]
    ir *= (1 - np.exp(-t / 0.004))[:, None]
    ir = sos(ir, "high", 180)
    ir = np.vstack([np.zeros((int(pre * SR), 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def reverb(x, ir):
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)


# ---------------------------------------------------------------- loudness / mastering
def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x):
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def tp_env(x):
    up = signal.resample_poly(x, 4, 1, axis=0)
    return np.abs(up).reshape(-1, 4, 2).max(axis=(1, 2))


def true_peak_db(x):
    return 20 * np.log10(tp_env(x).max() + 1e-12)


def limiter(x, ceil_db=-1.4, look_ms=1.5, rel_ms=80.0):
    c = 10 ** (ceil_db / 20)
    g = np.minimum(1.0, c / np.maximum(tp_env(x), 1e-9))
    L = int(look_ms * SR / 1000)
    g1 = minimum_filter1d(g, 2 * L + 1)
    if (g1 < 1).any():
        a = 1 - np.exp(-1 / (rel_ms * SR / 1000))
        y = g1.tolist()
        prev = 1.0
        for i in range(len(y)):
            v = prev + (1 - prev) * a
            if y[i] < v:
                v = y[i]
            y[i] = prev = v
        g1 = np.array(y)
    return x * uniform_filter1d(g1, 2 * L + 1)[:, None]


def master(x, gates, fade):
    x = sos(x, "high", 25)                                    # DC / rumble high-pass
    m, s = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    s = sos(s, "high", 120, order=4)                          # mono below 120 Hz
    x = np.stack([m + s, m - s], axis=1)
    for _ in range(5):
        x *= 10 ** ((TARGET_LUFS - lufs(x)) / 20)
        x = limiter(x)
    for a, b in gates:                                        # true digital silence
        sa, sb = fs(a), fs(b)
        f = int(0.003 * SR)
        x[sa - f:sa] *= np.cos(np.linspace(0, np.pi / 2, f))[:, None] ** 2
        x[sa:sb] = 0.0
    fa, fb = fs(fade[0]), fs(fade[1])
    x[fa:fb] *= np.cos(np.linspace(0, np.pi / 2, fb - fa))[:, None] ** 2
    x[fb:] = 0.0
    tp = true_peak_db(x)
    if tp > -1.1:
        x *= 10 ** ((-1.1 - tp) / 20)
    return x


def write_wav(path, x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- instruments
def knock(n, creak):
    t = tt(0.25)
    burst = np.zeros(len(t))
    b = int(0.003 * SR)
    eb = np.minimum(np.arange(b) / 10.0, 1.0) * np.exp(-np.arange(b) / (0.0009 * SR))
    burst[:b] = rng.standard_normal(b) * eb
    wood = 1.0 * peak(burst, 600, 9) + 0.75 * peak(burst, 1400, 12) + 0.12 * burst
    body = (np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.028) + 0.35 * np.sin(2 * np.pi * 360 * t) * np.exp(-t / 0.016))
    body *= np.minimum(t / 0.0008, 1.0)
    k = wood / np.abs(wood).max() + 0.8 * body
    k /= np.abs(k).max()
    if creak:
        tc = tt(0.17)
        f_ss = 42 + 14 * tc / tc[-1] + 3 * rng.standard_normal(len(tc)).cumsum() / np.sqrt(len(tc))
        ss = np.cumsum(f_ss) / SR
        grains = np.exp(-((ss % 1.0) / 0.12))                 # stick-slip bow pulses
        exc = rng.standard_normal(len(tc)) * (0.25 + grains)
        _, bp1, _ = svf(exc, 880 + 70 * tc / tc[-1], 28)
        _, bp2, _ = svf(exc, 1790 + 120 * tc / tc[-1], 34)
        cr = (bp1 + 0.35 * bp2) * np.sin(np.pi * tc / tc[-1]) ** 1.5
        cr = sos(cr, "low", 4000, order=4)
        cr = 0.42 * cr / np.abs(cr).max()
        st = int(0.022 * SR)
        k[st:st + len(cr)] += cr[: len(k) - st]
    return k * (0.85 if n == 0 else 0.62 + 0.38 * n / 5)              # f0 tap is decisive


def charge(a, b, kw):
    d = (b - a) / FPS
    t = tt(d)
    tau = t / d
    f = hz(kw["f0"]) * (hz(kw["f1"]) / hz(kw["f0"])) ** (tau ** 1.25)
    det = 2 ** (8 / 1200)
    s1 = saw(f * det, 0.13)
    s2 = saw(f / det, 0.61)
    fc = kw["bp0"] * (kw["bp1"] / kw["bp0"]) ** tau
    out = []
    for s in (0.75 * s1 + 0.45 * s2, 0.45 * s1 + 0.75 * s2):
        lp, bp, _ = svf(s, fc, 2.6)
        out.append(bp + 0.22 * lp)
    x = np.stack(out, axis=1)
    rate = kw["trem0"] * (kw["trem1"] / kw["trem0"]) ** tau
    trem = 1 - 0.5 * (0.5 - 0.5 * np.cos(2 * np.pi * np.cumsum(rate) / SR))
    env = (0.3 + 0.7 * tau ** 1.6) * np.minimum(t / 0.03, 1)
    return x * (trem * env)[:, None]


def ping(note):
    f = hz(note)
    t = tt(0.4)
    p = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.11) + 0.18 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.04)
    return p * np.minimum(t / 0.0015, 1)


def burst(kw):
    t = tt(0.6)
    f = kw["sub0"] * (kw["sub1"] / kw["sub0"]) ** (np.minimum(t, 0.1) / 0.1)   # 90 -> 45 Hz in 100 ms
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) + 0.45 * np.sin(2 * ph)                                   # 2nd harmonic
    sub = np.tanh(2.6 * sub) / np.tanh(2.6) * np.exp(-t / 0.17) * np.minimum(t / 0.0004, 1)
    sub *= 1 + 0.6 * np.exp(-t / 0.004)                                       # first cycle = the peak
    crack = rng.standard_normal((len(t), 2)) * np.exp(-t / 0.011)[:, None]
    crack = sos(crack, "high", 1800) + 0.6 * peak(crack, 4200, 2.0)
    crack /= np.abs(crack).max()
    tsh = tt(1.9)
    sh = np.zeros((len(tsh), 2))
    for ratio, amp, dec in ((1.0, 1.0, 1.25), (2.76, 0.6, 0.8), (5.4, 0.38, 0.45)):
        for c, dt in ((0, 0.9985), (1, 1.0015)):
            sh[:, c] += amp * np.sin(2 * np.pi * kw["shing"] * ratio * dt * tsh + c) * np.exp(-tsh / dec)
    sh *= np.minimum(tsh / 0.0015, 1)[:, None]
    return sub, crack, sh / np.abs(sh).max()


def coin(note, vel):
    f = hz(note)
    t = tt(0.75)
    idx = 1.9 * np.exp(-t / 0.035) + 0.35
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * 1.4 * f * t))      # 2-op FM bell
    return vel * y * np.exp(-t / 0.2) * np.minimum(t / 0.0007, 1)


def tick(f):
    n = int(0.001 * SR)
    return np.sin(2 * np.pi * f * np.arange(n) / SR) * np.hanning(n)


def brass(chord, length, vel):
    tail = 1.25
    t = tt(length + tail)
    out = np.zeros((len(t), 2))
    voices = chord.split(",")
    tau_acc = 0.006 if length < 0.2 else 0.03                                # tongued accent
    sus = lambda u: 0.5 + 0.5 * np.exp(-np.maximum(u - 0.002, 0) / tau_acc)
    rel = np.exp(-np.maximum(t - length, 0) / (0.022 if length < 0.2 else 0.24))
    bright = np.where(t < length, sus(t), sus(length) * rel)                # filter opens at the tongue
    env = np.minimum(t / 0.0015, 1) * bright
    for i, v in enumerate(voices):
        f0 = hz(v) * 2 ** (rng.uniform(-4, 4) / 1200)
        scoop = 2 ** (-35 / 1200 * np.exp(-t / 0.018))
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.25) / 0.2, 0, 1)
        f = f0 * scoop * vib
        w = 0.62 * saw(f, 0.5) + 0.38 * square(f, 0.0)                     # phase-locked attack
        pan = 0.0 if i == 0 else -0.55 + 1.1 * (i - 1) / max(len(voices) - 2, 1)
        g = 1.0 if i == 0 else 0.62
        out += pan2(w * g, pan)
    fc = 650 + 4200 * bright ** 1.3
    for c in range(2):
        out[:, c] = svf(out[:, c], fc, 1.1)[0]
    out *= env[:, None]
    tg = sos(rng.standard_normal((len(t), 2)), "bandpass", [1500, 4500]) * np.exp(-t / 0.0012)[:, None]
    tg *= 1.15 * np.abs(out[:int(0.02 * SR)]).max() / np.abs(tg).max()       # tongue "t" transient
    return (out + tg) * vel


def shimmer(chord, length):
    t = tt(length + 1.3)
    out = np.zeros((len(t), 2))
    for v in chord.split(","):
        f = hz(v)
        for cents, pan in ((-7, -0.95), (0, 0.0), (7, 0.95)):
            out += pan2(np.sin(2 * np.pi * f * 2 ** (cents / 1200) * t + rng.random() * 6.28), pan)
    env = np.minimum(t / 0.18, 1) * np.where(t < length, 1.0, np.exp(-(t - length) / 0.3))
    return out * env[:, None]


# ---------------------------------------------------------------- render
def render():
    main = np.zeros((N, 2))
    shower = np.zeros((N, 2))
    gates = []
    fade = (170.0, 179.4)
    duck = np.ones(N)
    for fr, ev, kw in CUES:
        if ev == "knock":
            k = knock(int(kw["n"]), int(kw["creak"]))
            place(main, 1.1 * k, fr, pan=(-0.18 if int(kw["n"]) % 2 else 0.18), align="peak", min_start=48)
        elif ev == "charge":
            main[fs(fr):fs(fr) + fs(kw["end"] - fr)] += 0.55 * charge(fr, kw["end"], kw)
        elif ev == "ping":
            place(main, 0.16 * ping(kw["note"]), fr, pan=kw["pan"])
        elif ev == "silence":
            gates.append((fr, kw["end"]))
        elif ev == "burst":
            sub, crack, sh = burst(kw)
            place(main, 0.6 * sub, fr)
            place(main, 0.55 * crack, fr)
            place(shower, 0.30 * sh, fr)
        elif ev == "ticks":
            n_t = int((kw["end"] - fr) * kw["rate"] / FPS)
            for i in range(n_t):
                f = kw["f0"] * (kw["f1"] / kw["f0"]) ** (i / (n_t - 1))
                place(shower, 0.24 * tick(f), fr + i * FPS / kw["rate"], pan=0.0)
        elif ev == "coin":
            place(shower, 0.17 * coin(kw["note"], kw["vel"]), fr, pan=kw["pan"])
        elif ev == "duck":
            a, b = fs(fr), fs(fr) + int(0.05 * SR)
            lo = 10 ** (kw["depth"] / 20)
            duck[a:b] = 1 - (1 - lo) * np.sin(np.linspace(0, np.pi / 2, b - a)) ** 2
            duck[b:] = lo
        elif ev == "brass":
            place(main, 0.42 * brass(kw["chord"], kw["len"], kw["vel"]), fr)
        elif ev == "shimmer":
            place(main, 0.035 * shimmer(kw["chord"], kw["len"]), fr)
        elif ev == "fade":
            fade = (fr, kw["end"])
    shower *= duck[:, None]
    mix = main + shower
    wet = reverb(mix, make_ir(0.9, 1.4))
    mix = mix + 0.12 * wet
    return master(mix, gates, fade)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "take-1.wav"
    x = render()
    assert x.shape == (N, 2) and np.all(np.isfinite(x))
    write_wav(out, x)
    print(f"{out}: {len(x)} samples, {lufs(x):.2f} LUFS, {true_peak_db(x):.2f} dBTP")
    for fr in (0, 75, 135):
        s = fs(fr)
        seg = np.abs(x[s:s + int(0.05 * SR)]).max(axis=1)
        print(f"  cue f{fr}: local peak at +{np.argmax(seg) / SR * 1000:.1f} ms")
