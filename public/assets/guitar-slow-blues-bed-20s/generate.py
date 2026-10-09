"""guitar-slow-blues-bed-20s: Opus Sound Directory

A 20-second slow-burn blues-ballad bed in G, 12/8 at 60 dotted-quarter beats per
minute (one beat = one second = 30 frames). The star is an electric lead guitar on
the edge of breakup: a single-coil neck pickup into a 4x-oversampled two-stage tube
preamp and a 1x12 open-back cab, mic'd in a small room with a warm plate. It plays
an original call-and-response solo. High, singing calls on the top strings use
continuous half- and whole-step bends, finger vibrato that starts slow and speeds
up, and pick rakes. Lower answers use double stops sliding chromatically, a blue
curl and a hammer-on trill between the minor and major third. Under it sit a soft
drawbar organ through a slow rotary speaker, a round finger-style electric bass
walking in triplets, and a brushed 12/8 shuffle kit (felt kick, brush taps on 2
and 4 with a circular sweep, triplet ride, hi-hat foot). The form is a two-beat
pickup on the V chord, then four bars (G9 C9 | G9 Dm7 G7 | C9 C#dim7 | G/D E7#9
Am7 D7) with the last bar as the turnaround. The band enters with the first guitar
bend on frame 0, swells bar by bar to the high bent cry in bar 3, and stops dead
on a G9 hit on frame 540 (guitar chord, bass, kick, organ, brush cymbal). The hit
rings for 2 s to silence. Only the mono kick and bass sit below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 60540
DURATION_SEC = 20
BPM = 60                       # dotted-quarter pulse of the 12/8 bar
KEY = "G (12/8 blues)"
FPS = 30
CUE_FRAMES = (0, 540)          # frame 0: first bend + band, frame 540: G9 stop hit
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 1.0 s; triplet eighth = 1/3 s
TRIP = BEAT / 3
HIT_T = CUE_FRAMES[1] / FPS    # 18.0 s
STOP_T = HIT_T - 0.08          # the band is silent for the last 80 ms before the hit

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi):
    return 440.0 * 2 ** ((np.asarray(midi, dtype=float) - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    x = x.copy()
    na, nr = min(len(x), max(1, int(a * SR))), min(len(x), max(1, int(r * SR)))
    shp = (-1,) + (1,) * (x.ndim - 1)
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))).reshape(shp)
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))).reshape(shp)
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a mono (L,) or stereo (L,2) snippet into a bus at time t (equal-power pan)."""
    s = int(round(t * SR))
    if s >= len(bus):
        return
    if bus.ndim == 1:
        e = min(len(bus), s + len(x))
        bus[s:e] += gain * x[: e - s]
        return
    if x.ndim == 1:
        th = (pan + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)
    e = min(len(bus), s + len(x))
    bus[s:e] += gain * x[: e - s]


def sosf(x, kind, freq, order=2, fs=SR):
    sos = signal.butter(order, freq, btype=kind, fs=fs, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def peak(x, f0, gain_db, q, fs=SR):
    """Peaking-EQ biquad."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / fs
    al = np.sin(w0) / (2 * q)
    b = [1 + al * a_, -2 * np.cos(w0), 1 - al * a_]
    a = [1 + al / a_, -2 * np.cos(w0), 1 - al / a_]
    return signal.lfilter(b, a, x, axis=0)


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


def smooth_ramp(n: int) -> np.ndarray:
    return 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, max(2, n)))


# ---------------------------------------------------------------- the electric guitar
# Standard tuning, string 1 = high E. A 648 mm scale; the neck single-coil sits 155 mm
# from the bridge and the player picks about 118 mm from the bridge.
OPEN = {1: 64, 2: 59, 3: 55, 4: 50, 5: 45, 6: 40}
SCALE_MM, PICKUP_MM, PICK_MM, APERTURE_MM = 648.0, 155.0, 118.0, 12.0


def vib_len(fret: float) -> float:
    return SCALE_MM * 2 ** (-fret / 12)


def loss(fn):
    """String loss per partial (1/s): air + internal friction, rising with frequency."""
    return 0.6 + 2.5e-4 * fn + 1.0e-6 * fn ** 2


def slow_jitter(L: int, step: float, amt: float) -> np.ndarray:
    """Smooth random wobble (for human vibrato depth/rate)."""
    k = int(L / (step * SR)) + 3
    pts = rng.uniform(-1, 1, k)
    return 1 + amt * np.interp(np.arange(L) / SR, np.arange(k) * step, pts)


def gtr(string: int, fret: float, vel: float, hold: float, ops=(), tick: bool = False,
        bright: float = 1.0, mute_rate: float = 26.0) -> np.ndarray:
    """One string vibration from pick to mute, as a DI (pickup) signal.

    Additive string with integrated phase so bends, slides, hammer-ons and vibrato are
    continuous: partials f_n = n f0(t) sqrt(1 + B n^2), plucking-position comb
    |sin(n pi p)|, magnetic-pickup comb sin(n pi q) with aperture loss, pick hardness
    low-pass, per-partial loss that rises with frequency, a tension-modulation pitch
    sag on the attack, slow two-polarisation beating, and re-excitation on hammer-ons
    / pull-offs. ops (times relative to the pick):
      ('bend', t0, semis, dur)  continuous bend to `semis` above the fret (0 = release)
      ('vib', t0, t1, cents, rate0, rate1, sign)  finger vibrato, +1 sharp-ward, -1 flat
      ('ham'|'pull', t0, fret)  ('slide', t0, fret, dur)
    """
    tail = 0.03 if tick else 0.32
    L = int(round((hold + tail) * SR))
    t = np.arange(L) / SR
    fret_c = np.full(L, float(fret))
    bend = np.zeros(L)
    vib = np.zeros(L)
    events = [(0.0, "pick", float(fret))]
    cur = 0.0
    for op in sorted(ops, key=lambda o: o[1]):
        k = op[0]
        if k == "bend":
            _, t0, amt, d = op
            amt = amt + (rng.normal(0, 0.035) if amt else 0.0)       # human intonation
            s = np.clip((t - t0) / d, 0, 1)
            shape = 0.5 * (1 - (1 - s) ** 3) + 0.5 * (s * s * (3 - 2 * s))
            bend += (amt - cur) * shape
            cur = amt
        elif k == "vib":
            _, t0, t1, cents, r0, r1, sign = op
            rate = (r0 + (r1 - r0) * np.clip((t - t0) / max(1e-3, t1 - t0), 0, 1)) * slow_jitter(L, 0.2, 0.05)
            ph = 2 * np.pi * np.cumsum(np.where(t >= t0, rate, 0.0)) / SR
            depth = (cents / 100) * np.clip((t - t0) / 0.22, 0, 1) * np.clip((t1 - t) / 0.12, 0, 1)
            depth = depth * slow_jitter(L, 0.15, 0.18)
            vib += sign * depth * (0.5 - 0.5 * np.cos(ph))
        elif k in ("ham", "pull"):
            _, t0, nf = op
            fret_c[t >= t0] = nf
            events.append((t0, k, float(nf)))
        elif k == "slide":
            _, t0, nf, d = op
            i0 = min(L - 1, int(t0 * SR))
            a = fret_c[i0]
            s = np.clip((t - t0) / d, 0, 1)
            s = s * s * (3 - 2 * s)
            nst = max(1, int(abs(nf - a)))
            stair = a + (nf - a) * np.floor(s * nst + 0.5) / nst      # crossing the frets
            fret_c = np.where(t >= t0, 0.4 * (a + (nf - a) * s) + 0.6 * stair, fret_c)
            events.append((t0 + d, "slide", float(nf)))
    fret_s = uniform_filter1d(fret_c, size=int(0.0025 * SR), mode="nearest")
    midi = OPEN[string] + fret_s + bend + vib + 0.06 * vel ** 2 * np.exp(-t / 0.03)
    f0 = hz(midi)
    base = 2 * np.pi * (np.cumsum(f0) - f0[0]) / SR

    Lv = vib_len(fret)
    q = PICKUP_MM / Lv
    Bc = (3e-5 if string <= 3 else 1.2e-4) * (SCALE_MM / Lv) ** 2
    fmax = f0.max()
    K = max(1, min(40, int(9000 / fmax)))
    amp = 0.5 * vel ** 1.4
    sign0 = None
    y = np.zeros(L)
    tm = np.clip(t - hold, 0, None)
    grow = np.clip(t / 0.45, 0, 1)
    n_all = np.arange(1, K + 1)
    pk_exc = np.sin(n_all * np.pi * (PICK_MM / Lv))
    sign0 = np.where(pk_exc >= 0, 1.0, -1.0)
    for n in n_all:
        st = np.sqrt(1 + Bc * n * n)
        if n * fmax * st > 9500:
            break
        A = np.zeros(L)
        for (te, kind, fe) in events:
            ie = int(round(te * SR))
            if ie >= L:
                continue
            Le = vib_len(fe)
            fe_hz = float(hz(OPEN[string] + fe))
            if kind == "pick":
                fc = 700.0 if tick else (900 + 3800 * vel ** 1.5) * bright
                pe, g, keep, rr = PICK_MM / Le, 1.0, 1.0, 0.0004
            elif kind == "ham":
                fc, pe, g, keep, rr = 1300.0, 6.0 / Le, 0.42, 0.72, 0.0012
            elif kind == "pull":
                fc, pe, g, keep, rr = 1900.0, 6.0 / Le, 0.5, 0.55, 0.0010
            else:                                                     # slide arrival
                fc, pe, g, keep, rr = 1500.0, 6.0 / Le, 0.12, 0.95, 0.002
            if ie > 0 and keep < 1.0:
                nk = int(0.0015 * SR)
                kc = np.ones(L - ie)
                kc[:nk] = 1 - (1 - keep) * smooth_ramp(nk)
                kc[nk:] = keep
                A[ie:] *= kc
            exc = abs(np.sin(n * np.pi * pe)) / n * sign0[n - 1] / np.sqrt(1 + (n * fe_hz / fc) ** 2)
            seg = np.exp(-loss(n * fe_hz) * (t[ie:] - te))
            nr = max(2, int(rr * SR))
            seg[:nr] *= smooth_ramp(nr)
            A[ie:] += g * exc * seg
        mr = (120 + 10 * n) if tick else (mute_rate + 3.5 * n)
        A *= np.exp(-tm * mr)
        P = np.sin(n * np.pi * q) * np.sinc(n * APERTURE_MM / (2 * Lv))
        beat = 1 + 0.07 * grow * np.cos(2 * np.pi * (0.35 + 0.12 * n) * t + rng.uniform(0, 2 * np.pi))
        y += P * A * beat * np.sin(n * st * base)
    if not tick:
        pn = sosf(noise(0.02), "bandpass", [1200, 6000])
        te = np.arange(len(pn)) / SR
        y[: len(pn)] += pn * (1 - np.exp(-te / 0.0002)) * np.exp(-te / 0.0022) * 0.035 * vel * bright
    return fade(y * amp, a=0.0003, r=0.01)


def leveler(x: np.ndarray, thresh: float, ratio: float = 3.0, att: float = 0.012, rel: float = 0.28) -> np.ndarray:
    """Slow optical-style leveller in front of the amp: lets the pick attack through,
    then holds sustaining notes up so they keep pushing the amp (more singing)."""
    det = np.sqrt(np.maximum(uniform_filter1d(x ** 2, size=int(0.006 * SR), mode="nearest"), 0)) + 1e-9
    want = np.minimum(0.0, (20 * np.log10(det / thresh)) * (1 / ratio - 1))
    want = np.where(det > thresh, want, 0.0)
    ca, cr = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    g = np.empty_like(want)
    prev = 0.0
    for n, w in enumerate(want.tolist()):
        c = ca if w < prev else cr
        prev = c * prev + (1 - c) * w
        g[n] = prev
    return x * 10 ** (g / 20)


def amp_and_cab(di: np.ndarray, drive: float = 2.8) -> np.ndarray:
    """Edge-of-breakup tube amp at 4x oversampling: coupling high-pass, mid push into an
    asymmetric triode stage, tone stack, a second milder stage, soft power-amp
    saturation; then a 1x12 open-back cab (low thump, presence peak, steep low-pass
    with nothing left above ~7 kHz)."""
    fs4 = 4 * SR
    x = signal.resample_poly(di, 4, 1)
    x = sosf(x, "highpass", 90, 1, fs4)
    x = peak(x, 800, 4.0, 0.8, fs4)
    x = sosf(x, "lowpass", 6500, 1, fs4)
    b1 = 0.25
    y = np.tanh(drive * x + b1) - np.tanh(b1)
    y = sosf(y, "highpass", 25, 1, fs4)
    y = peak(y, 450, -3.0, 0.7, fs4)            # tone stack: mid scoop, treble lift
    y = peak(y, 2600, 2.5, 0.6, fs4)
    b2 = -0.12
    y = np.tanh(1.4 * y + b2) - np.tanh(b2)
    y = sosf(y, "highpass", 25, 1, fs4)
    y = y / (1 + np.abs(y) ** 2.5) ** 0.4        # power amp
    y = signal.resample_poly(y, 1, 4)
    y = sosf(y, "highpass", 80, 2)
    y = peak(y, 115, 2.5, 1.4)
    y = peak(y, 650, -2.0, 1.0)
    y = peak(y, 2300, 3.0, 1.3)
    y = peak(y, 3900, -2.5, 3.0)
    y = sosf(y, "lowpass", 5200, 8)
    y = sosf(y, "lowpass", 7000, 2)
    return y


# ---------------------------------------------------------------- the band
DRAWBARS = (1.0, 1.5, 2.0, 3.0, 4.0)            # 8', 5 1/3', 4', 2 2/3', 2'


def organ(timeline, levels_t, levels, expr_t, expr) -> np.ndarray:
    """Drawbar organ: free-running tonewheel sines gated per key (common tones hold
    across chord changes), a quiet key click on each key-down, drawbar registration
    and swell pedal drawn over time. Mono, before the rotary."""
    out = np.zeros(N)
    gates: dict[int, list] = {}
    for t0, t1, notes in timeline:
        for m in notes:
            gates.setdefault(m, []).append([t0, t1])
    lv = np.stack([np.interp(np.arange(N) / SR, levels_t, [l[k] for l in levels]) for k in range(5)])
    for m in sorted(gates):
        segs = []
        for a, b in sorted(gates[m]):
            if segs and abs(segs[-1][1] - a) < 1e-6:
                segs[-1][1] = b
            else:
                segs.append([a, b])
        for a, b in segs:
            s0, s1 = int(round(a * SR)), int(round(b * SR))
            rel = int(0.03 * SR)
            e = min(N, s1 + rel)
            t = np.arange(s0, e) / SR
            g = np.ones(e - s0)
            na = int(0.012 * SR)
            g[:na] = smooth_ramp(na)
            g[s1 - s0:] = np.cos(np.linspace(0, np.pi / 2, e - s1)) ** 2
            tone = np.zeros(e - s0)
            for k, r in enumerate(DRAWBARS):
                f = float(hz(m)) * r
                if f > 6000:
                    continue
                ph = rng.uniform(0, 2 * np.pi)
                w = np.sin(2 * np.pi * f * t + ph)
                tone += lv[k, s0:e] * (w + 0.03 * w * w)            # slight wheel asymmetry
            out[s0:e] += tone * g
            ck = sosf(noise(0.006), "bandpass", [1200, 5000]) * np.exp(-np.arange(int(0.006 * SR)) / (0.0012 * SR))
            place(out, ck * 0.05, a)
    out *= 0.12 * np.interp(np.arange(N) / SR, expr_t, expr)
    out = np.tanh(1.3 * out) / 1.3                                   # warm tube preamp
    return out


def rotary(x: np.ndarray) -> np.ndarray:
    """Slow (chorale) rotary speaker: horn above 800 Hz gets doppler (modulated delay)
    plus amplitude rotation; the drum below gets a gentler rotation. Two mics."""
    t = np.arange(N) / SR
    lo = sosf(x, "lowpass", 800, 4)
    hi = x - lo
    hp_ = 2 * np.pi * 0.83 * t
    dp_ = 2 * np.pi * 0.67 * t + 1.1
    out = np.zeros((N, 2))
    idx = np.arange(N, dtype=float)
    for ch, off in ((0, 0.0), (1, 0.62 * np.pi)):
        d = (0.0007 + 0.0004 * np.sin(hp_ + off)) * SR
        h = np.interp(idx - d, idx, hi) * (1 + 0.22 * np.sin(hp_ + off + np.pi / 2))
        out[:, ch] = h + lo * (1 + 0.05 * np.sin(dp_ + off))
    return out


def bass(midi: float, dur: float, vel: float = 1.0, att: float = 0.003, rel: float = 0.04) -> np.ndarray:
    """Round finger-style electric bass: additive string (plucked over the neck end,
    neck pickup), partials < 2.4 kHz with frequency-dependent loss, small pitch settle
    and a flesh thump. Released with a finger mute."""
    t = tt(dur + rel)
    f = float(hz(midi)) * (1 + 0.004 * vel * np.exp(-t / 0.03))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros_like(t)
    f1 = float(hz(midi))
    for n in range(1, 15):
        if n * f1 > 2400:
            break
        a = np.sin(n * np.pi * 0.19) * np.sin(n * np.pi * 0.24) / n
        sig = 1.0 + 1.2e-5 * (n * f1) ** 2 + 0.002 * n * f1
        y += a * np.exp(-sig * t) * np.sin(n * ph)
    th = sosf(noise(dur + rel), "bandpass", [150, 700]) * np.exp(-t / 0.006) * 0.06
    y = (y / 0.4 + th) * (0.75 + 0.25 * vel)
    nr = int(rel * SR)
    y[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return fade(y * 0.5 * vel, a=att, r=0.004)


def kick(vel: float = 1.0, att: float = 0.0005) -> np.ndarray:
    """Soft felt-beater kick."""
    t = tt(0.45)
    f = 52 + 40 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.17)
    beater = sosf(noise(0.45), "bandpass", [400, 2500]) * np.exp(-t / 0.004) * 0.08
    y = np.tanh(1.3 * body) / np.tanh(1.3) + beater
    return fade(y * 0.8 * vel, a=att, r=0.05)


def brush_tap(vel: float = 1.0, att: float = 0.002, on_tau: float = 0.0025) -> np.ndarray:
    """Brush slap on the snare: bristle spray, wire buzz, a little head tone."""
    d = 0.4
    t = tt(d)
    on = 1 - np.exp(-t / on_tau)
    br = sosf(noise(d), "bandpass", [700, 9000]) * on * (0.65 * np.exp(-t / 0.035) + 0.35 * np.exp(-t / 0.14))
    wires = sosf(noise(d), "bandpass", [2500, 7500]) * np.exp(-t / 0.11) * (1 - np.exp(-t / 0.006)) * 0.35
    head = np.sin(2 * np.pi * 192 * t) * np.exp(-t / 0.05) * 0.22 * on
    return fade((br + wires + head) * 0.3 * vel, a=att, r=0.05)


def hat_foot(vel: float = 1.0) -> np.ndarray:
    d = 0.09
    t = tt(d)
    y = sosf(noise(d), "bandpass", [600, 7000]) * np.exp(-t / 0.012) * (1 - np.exp(-t / 0.0008))
    ring = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.3)) for f in (3400, 5150, 6900)) * 0.04 * np.exp(-t / 0.02)
    return fade((y + ring) * 0.12 * vel, a=0.0008, r=0.02)


def ride_template(d: float = 2.4) -> np.ndarray:
    """Stick-on-ride stroke: many inharmonic partials (lower ones ring longer), a short
    stick ping and a slowly blooming noise wash."""
    t = tt(d)
    y = np.zeros_like(t)
    fr = np.exp(rng.uniform(np.log(2300), np.log(9800), 34))
    for f in fr:
        tau = 0.25 + 1.4 * (2300 / f) ** 1.2
        y += rng.uniform(0.3, 1.0) / np.sqrt(f / 2300) * np.exp(-t / tau) * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.3))
    y *= 0.05
    stick = sosf(noise(d), "bandpass", [2000, 8000]) * np.exp(-t / 0.004) * 0.5
    wash = sosf(noise(d), "bandpass", [3500, 12000]) * np.exp(-t / 0.9) * (1 - np.exp(-t / 0.012)) * 0.18
    return fade(y + stick + wash, a=0.0006, r=0.1)


def cymbal_hit(d: float = 2.0, att: float = 0.003) -> np.ndarray:
    """Soft brushed/mallet cymbal for the stop hit (stereo)."""
    t = tt(d)
    out = []
    for _ in range(2):
        wash = sosf(noise(d), "bandpass", [2500, 11000]) * np.exp(-t / 0.7)
        bell = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.3)) * np.exp(-t / 1.1)
                   for f in rng.uniform(2800, 7000, 8)) * 0.03
        out.append(fade((wash + bell) * (1 - np.exp(-t / 0.02)), a=att, r=0.3))
    return np.stack(out, axis=1) * 0.2


def reverb(x: np.ndarray, rt_lo: float, rt_hi: float, predelay: float, band=(250, 7000)) -> np.ndarray:
    """Decorrelated stereo noise-IR reverb whose highs die faster than its lows."""
    t = tt(rt_lo * 1.2)
    irs = []
    for _ in range(2):
        lo = sosf(rng.standard_normal(len(t)), "bandpass", [band[0], 1800]) * np.exp(-6.9 * t / rt_lo)
        hi = sosf(rng.standard_normal(len(t)), "bandpass", [1800, band[1]]) * np.exp(-6.9 * t / rt_hi)
        ir = np.concatenate([np.zeros(int(predelay * SR)), (lo + 0.7 * hi) * (1 - np.exp(-t / 0.01))])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


def room_reflections(x: np.ndarray) -> np.ndarray:
    """Amp-in-a-small-room early reflections around a mono close mic (stereo out)."""
    out = np.stack([x, x], axis=1)
    taps = ((0.0071, 0.30, 0), (0.0093, 0.27, 1), (0.0128, 0.22, 0), (0.0167, 0.20, 1),
            (0.0219, 0.15, 0), (0.0254, 0.14, 1), (0.0313, 0.10, 0), (0.0361, 0.09, 1))
    refl = np.zeros_like(out)
    for d, g, ch in taps:
        s = int(d * SR)
        refl[s:, ch] += g * x[:-s]
    return out + sosf(refl, "lowpass", 3800, 2)


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 110.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak; gain held over
    the look-ahead, one-pole release, edge-safe box smoothing. Never clips."""
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


def glue(x: np.ndarray, thresh_db: float, ratio: float = 2.0, rel: float = 0.18) -> np.ndarray:
    """Gentle RMS bus compressor (~10 ms detector, 180 ms release)."""
    det = uniform_filter1d((x ** 2).mean(axis=1), size=int(0.01 * SR), mode="nearest")
    lvl = 10 * np.log10(det + 1e-12)
    gr = np.maximum(0, lvl - thresh_db) * (1 - 1 / ratio)
    rc = np.exp(-1.0 / (rel * SR))
    g = np.empty_like(gr)
    prev = 0.0
    for n, v in enumerate(gr.tolist()):
        prev = v if v > prev else prev * rc + v * (1 - rc)
        g[n] = prev
    g = uniform_filter1d(g, size=int(0.003 * SR), mode="nearest")
    return x * (10 ** (-g / 20))[:, None]


def master(mix: np.ndarray) -> np.ndarray:
    mix = glue(mix, thresh_db=10 * np.log10(np.mean(mix ** 2) * 2) + 4.0)
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


# ---------------------------------------------------------------- the score
# Lead: (t, string, fret, vel, off, ops with ABSOLUTE times, flags). All phrases original.
def V(t, s, f, v, off, ops=(), cue=False, rake=False, pair=None):
    return dict(t=t, s=s, f=f, v=v, off=off, ops=list(ops), cue=cue, rake=rake, pair=pair)


LEAD = [
    # pickup on D9: struck whole-step bend that sings, released, a pull-off and a blue curl
    V(0.000, 3, 14, 1.00, 1.10, [("bend", 0.02, 2, 0.21), ("vib", 0.30, 0.86, 26, 4.6, 6.0, -1),
                                 ("bend", 0.90, 0, 0.17)], cue=True),
    V(1.000, 2, 15, 0.80, 1.32, [("pull", 1.167, 13)]),
    V(1.333, 3, 14, 0.70, 1.62),
    V(1.667, 3, 15, 0.74, 1.96, [("bend", 1.70, 0.45, 0.14)]),
    # bar 1 call: the major third, sung with slow-to-fast vibrato
    V(2.000, 2, 12, 0.92, 3.22, [("vib", 2.28, 3.15, 30, 4.4, 6.3, +1)]),
    # bar 1 answer, low: curl, root, then double stops over C9 (slide in, blue-third hammer)
    V(3.333, 3, 3, 0.74, 3.62, [("bend", 3.37, 1, 0.10)]),
    V(3.667, 4, 5, 0.70, 3.96, [("vib", 3.75, 3.95, 12, 5.5, 6.0, +1)]),
    V(4.000, 3, 8, 0.84, 4.62, [("slide", 0.0 + 4.000, 9, 0.06), ("vib", 4.25, 4.60, 14, 5.4, 6.0, +1)],
      pair=(2, 7, [("slide", 4.000, 8, 0.06), ("vib", 4.25, 4.60, 14, 5.4, 6.0, +1)])),
    V(4.667, 3, 8, 0.78, 5.28, [("ham", 4.75, 9), ("vib", 4.95, 5.25, 12, 5.6, 6.2, +1)],
      pair=(2, 8, [("vib", 4.95, 5.25, 12, 5.6, 6.2, +1)])),
    V(5.333, 3, 5, 0.70, 5.63),
    V(5.667, 3, 3, 0.72, 5.97, [("bend", 5.70, 0.35, 0.12)]),
    # bar 2 call: raked high G with wide vibrato, then a slow whole-step bend and release
    V(6.000, 1, 15, 1.00, 7.28, [("vib", 6.32, 7.20, 34, 4.5, 6.4, +1)], rake=True),
    V(7.333, 2, 15, 0.90, 8.95, [("bend", 7.36, 2, 0.30), ("vib", 7.72, 8.30, 24, 4.8, 6.2, -1),
                                 ("bend", 8.33, 0, 0.22), ("pull", 8.667, 13)]),
    # bar 2 answer: minor/major-third hammer-on trill resolving on B over G7
    V(9.000, 3, 15, 0.82, 9.98, [("ham", 9.09, 16), ("pull", 9.18, 15), ("ham", 9.27, 16),
                                 ("pull", 9.36, 15), ("ham", 9.45, 16),
                                 ("vib", 9.60, 9.96, 20, 5.6, 6.4, +1)]),
    # bar 3 call (the peak): raked high G bent a whole step to A, wide accelerating vibrato
    V(10.000, 1, 15, 1.00, 11.97, [("bend", 10.03, 2, 0.20), ("vib", 10.36, 11.30, 38, 4.3, 6.6, -1),
                                   ("bend", 11.33, 0, 0.25), ("pull", 11.667, 12)], rake=True),
    # bar 3 answer over C#dim7: tritone double stop sliding down chromatically, then G/B
    V(12.000, 3, 15, 0.86, 13.30, [("slide", 12.667, 14, 0.05), ("slide", 13.000, 13, 0.05),
                                   ("vib", 12.25, 12.62, 10, 5.5, 6.0, +1)],
      pair=(2, 14, [("slide", 12.667, 13, 0.05), ("slide", 13.000, 12, 0.05)])),
    V(13.333, 3, 12, 0.80, 13.95, [("vib", 13.55, 13.92, 14, 5.4, 6.2, +1)],
      pair=(2, 12, [("vib", 13.55, 13.92, 14, 5.4, 6.2, +1)])),
    # bar 4 turnaround
    V(14.000, 1, 15, 0.90, 14.31, [("vib", 14.10, 14.30, 14, 6.0, 6.0, +1)]),
    V(14.333, 2, 15, 0.86, 16.64, [("bend", 14.62, 2, 0.36), ("vib", 15.08, 15.60, 28, 4.8, 6.3, -1),
                                   ("bend", 15.62, 0, 0.20), ("pull", 15.90, 13),
                                   ("vib", 16.15, 16.60, 22, 5.0, 6.2, +1)]),
    V(16.667, 3, 14, 0.72, 16.97),
    V(17.000, 3, 11, 0.80, 17.32, [("vib", 17.12, 17.30, 14, 6.0, 6.0, +1)]),
    V(17.333, 3, 12, 0.72, 17.64, [("ham", 17.50, 14)]),
    V(17.667, 3, 15, 0.74, 17.90, [("bend", 17.70, 0.5, 0.12)]),
]

# the stop hit: G9 (x-10-9-10-10-10), fast down-strum
HIT_CHORD = [(5, 10), (4, 9), (3, 10), (2, 10), (1, 10)]

D9 = (54, 57, 60, 64)
G9 = (53, 57, 59, 62)
C9 = (52, 55, 58, 62)
DM7 = (53, 57, 60, 62)
G7 = (53, 55, 59, 62)
CSDIM7 = (52, 55, 58, 61)
GD = (50, 55, 59, 62)
E7S9 = (52, 56, 62, 67)
AM7 = (52, 55, 57, 60)
D7 = (54, 57, 60, 62)
G9H = (53, 57, 59, 62, 67)
ORGAN = [(0.0, 2.0, D9), (2.0, 4.0, G9), (4.0, 6.0, C9), (6.0, 8.0, G9), (8.0, 9.0, DM7),
         (9.0, 10.0, G7), (10.0, 12.0, C9), (12.0, 14.0, CSDIM7), (14.0, 15.0, GD),
         (15.0, 16.0, E7S9), (16.0, 17.0, AM7), (17.0, STOP_T, D7), (HIT_T, 19.65, G9H)]

# bass (t, midi, beats): long on the beat, short pickup on the third triplet
BASS = [(0.0, 38, 0.62), (0.667, 33, 0.3), (1.0, 36, 0.62), (1.667, 30, 0.3),
        (2.0, 31, 0.62), (2.667, 38, 0.3), (3.0, 40, 0.62), (3.667, 35, 0.3),
        (4.0, 36, 0.62), (4.667, 43, 0.3), (5.0, 34, 0.62), (5.667, 30, 0.3),
        (6.0, 31, 0.62), (6.667, 38, 0.3), (7.0, 35, 0.62), (7.667, 37, 0.3),
        (8.0, 38, 0.62), (8.667, 33, 0.3), (9.0, 31, 0.62), (9.667, 35, 0.3),
        (10.0, 36, 0.62), (10.667, 43, 0.3), (11.0, 34, 0.62), (11.667, 36, 0.3),
        (12.0, 37, 0.62), (12.667, 40, 0.3), (13.0, 43, 0.62), (13.667, 37, 0.3),
        (14.0, 38, 0.62), (14.667, 35, 0.3), (15.0, 40, 0.62), (15.667, 32, 0.3),
        (16.0, 33, 0.62), (16.667, 40, 0.3), (17.0, 38, 0.62), (17.667, 30, 0.23)]


def render() -> np.ndarray:
    di = np.zeros(N + SR)          # lead guitar DI (mono)
    org_in = np.zeros(N)
    low = np.zeros(N)              # kick + bass, mono
    drums = np.zeros((N, 2))
    drum_send = np.zeros((N, 2))

    def lay():                     # the soloist sits a hair behind the beat
        return 0.008 + float(rng.uniform(-0.007, 0.007))

    # ---- lead guitar
    for nv in LEAD:
        t0 = nv["t"] + (0.0 if nv["cue"] else lay())
        rel_ops = [(o[0], o[1] - nv["t"]) + tuple(o[2:]) for o in nv["ops"]]
        rel_ops = [o if o[0] != "vib" else (o[0], o[1], o[2] - nv["t"]) + tuple(o[3:]) for o in rel_ops]
        hold = nv["off"] - nv["t"]
        if nv["rake"]:                                        # muted strings dragged into the note
            for k, st in enumerate(range(nv["s"] + 2, nv["s"], -1)):
                place(di, gtr(st, nv["f"], 0.55, 0.006, tick=True), t0 - 0.030 + 0.014 * k)
        place(di, gtr(nv["s"], nv["f"], nv["v"], hold, rel_ops), t0)
        if nv["pair"]:
            s2, f2, ops2 = nv["pair"]
            ops2 = [(o[0], o[1] - nv["t"]) + tuple(o[2:]) for o in ops2]
            ops2 = [o if o[0] != "vib" else (o[0], o[1], o[2] - nv["t"]) + tuple(o[3:]) for o in ops2]
            place(di, gtr(s2, f2, nv["v"] * 0.92, hold, ops2), t0 + float(rng.uniform(0.004, 0.009)))

    # the G9 stop hit (first string exactly on the cue), shaken a little, damped at 19.6 s
    for k, (s, f) in enumerate(HIT_CHORD):
        hold = 19.58 - HIT_T - 0.006 * k
        ops = [("vib", 0.70, 1.55, 11, 5.2, 5.6, +1)]
        place(di, gtr(s, f, 0.70, hold, ops, mute_rate=9.0), HIT_T + 0.003 * k)

    di = di[:N]
    # volume knob rolled back for the G9 hit so the 9th chord stays clear instead of mushy
    knob = np.interp(np.arange(N) / SR, [0, STOP_T, STOP_T + 0.04, 20], [1.0, 1.0, 0.62, 0.62])
    lead = amp_and_cab(leveler(di, thresh=0.06) * 1.6 * knob)
    lead = sosf(lead, "highpass", 110, 2)
    ride_db = np.interp(np.arange(N) / SR, [0, 5.8, 6.2, 9.8, 10.0, 13.8, 14.0, 17.9, HIT_T, 20],
                        [-1.0, -1.0, -0.3, -0.3, 0.6, 0.6, 0.0, 0.0, 3.0, 3.0])
    lead = lead * 10 ** (ride_db / 20)                                # mix-engineer fader ride
    lead_st = room_reflections(lead)

    # ---- organ
    lv_t = [0.0, 6.0, 10.0, 14.0, 18.0, 20.0]
    lv = [(1.0, 0.5, 0.35, 0.0, 0.0), (1.0, 0.6, 0.45, 0.08, 0.05), (1.0, 0.65, 0.55, 0.15, 0.10),
          (1.0, 0.7, 0.6, 0.18, 0.12), (1.0, 0.7, 0.6, 0.2, 0.15), (1.0, 0.7, 0.6, 0.2, 0.15)]
    ex_t = [0.0, 2.0, 6.0, 10.0, 14.0, 17.9, HIT_T, 18.4, 19.6, 20.0]
    ex = [0.42, 0.50, 0.62, 0.78, 0.86, 0.95, 1.0, 0.92, 0.0, 0.0]
    org_in += organ(ORGAN, lv_t, lv, ex_t, ex)
    org = rotary(sosf(org_in, "highpass", 150, 4))
    org = sosf(org, "lowpass", 4200, 2)

    # ---- bass + kick
    for t0, m, ln in BASS:
        on_beat = abs(t0 - round(t0)) < 1e-6
        tt0 = t0 + (0.0 if t0 == 0.0 else float(rng.uniform(-0.004, 0.004)))
        place(low, bass(m, ln, 0.92 if on_beat else 0.62, att=0.0005 if t0 == 0.0 else 0.003), tt0)
    place(low, bass(31, 1.55, 1.0, att=0.0004, rel=0.3), HIT_T)
    kicks = [0.0, 2, 4, 6, 8, 10, 12, 14, 16]
    for k in kicks:
        place(low, kick(0.85 if k else 0.8, att=0.0005), k + (0.0 if k == 0 else float(rng.uniform(-0.003, 0.003))))
    for k in (13.667, 17.667):
        place(low, kick(0.42), k)
    place(low, kick(1.15, att=0.0004), HIT_T)

    # ---- drums: brushes, ride, hat foot
    bar_lvl = lambda t: 0.55 if t < 2 else 0.72 if t < 6 else 0.86 if t < 10 else 1.0 if t < 14 else 1.12
    for t0 in (1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0, 17.0):
        v = 0.85 * bar_lvl(t0) * float(rng.uniform(0.92, 1.05))
        x = brush_tap(v)
        tj = t0 + float(rng.uniform(-0.005, 0.006))
        place(drums, x, tj, 1.0, 0.05)
        place(drum_send, x, tj, 0.4, 0.05)
        place(drums, hat_foot(0.8), t0 + float(rng.uniform(-0.004, 0.004)), 1.0, 0.3)
    for t0 in (5.667, 7.667, 9.667, 11.667, 13.667, 15.667, 17.333, 17.667, 17.80):
        v = {17.333: 0.42, 17.667: 0.55, 17.80: 0.5}.get(t0, 0.22)
        place(drums, brush_tap(v), t0 + float(rng.uniform(-0.004, 0.004)), 1.0, 0.0)
    rides = [ride_template() for _ in range(3)]
    k = 0
    t0 = 1.0
    while t0 < 17.70:
        pos = k % 3
        v = (0.80, 0.42, 0.62)[pos] * bar_lvl(t0) * float(rng.uniform(0.9, 1.08))
        tj = t0 + float(rng.uniform(-0.004, 0.004))
        x = rides[k % 3] * v
        place(drums, x, tj, 0.55, 0.38)
        place(drum_send, x, tj, 0.12, 0.38)
        k += 1
        t0 = 1.0 + k * TRIP
    # circular brush sweep: one stir per beat, swelling toward the back-beat
    tsw = np.arange(N) / SR
    sweep = sosf(noise(DURATION_SEC), "bandpass", [900, 6500])
    stir = (0.5 - 0.5 * np.cos(2 * np.pi * (tsw - 0.2))) ** 1.5
    win = np.clip((tsw - 0.8) / 0.6, 0, 1) * np.clip((STOP_T - tsw) / 0.05, 0, 1)
    sw = sweep * stir * win * 0.022 * np.interp(tsw, [0, 6, 10, 14, 18], [0.8, 0.9, 1.0, 1.1, 1.1])
    drums[:, 0] += sw * 0.8
    drums[:, 1] += sw * 1.1

    # ---- the stop: everything the band is playing is choked just before the hit
    g = np.ones(N)
    s0, s1 = int(round(STOP_T * SR)), int(round(HIT_T * SR))
    nf = int(0.025 * SR)
    g[s0 - nf:s0] = np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
    g[s0:s1] = 0.0
    low *= g
    drums *= g[:, None]
    # (organ gates already stop at STOP_T; the lead's last note is damped at 17.90 s)

    # ---- the hit's cymbal and brush slap
    cy = cymbal_hit(2.0)
    place(drums, cy, HIT_T, 1.3)
    place(drum_send, cy, HIT_T, 0.25)
    place(drums, brush_tap(1.0, att=0.0004, on_tau=0.0003), HIT_T, 0.9, 0.05)

    # ---- buses
    lead_wet = reverb(lead_st, rt_lo=2.0, rt_hi=1.2, predelay=0.028, band=(300, 6000))
    lead_wet = sosf(lead_wet, "highpass", 300, 2)
    org_wet = reverb(org, rt_lo=1.4, rt_hi=0.9, predelay=0.02, band=(250, 5000))
    drum_wet = reverb(drum_send, rt_lo=0.8, rt_hi=0.5, predelay=0.012, band=(300, 8000))
    drums = sosf(drums, "highpass", 160, 2)

    lowb = sosf(low, "highpass", 32, 2)
    lowb = sosf(lowb, "lowpass", 2600, 2)
    lowst = np.stack([lowb, lowb], axis=1)

    mix = (lead_st * 1.0 + lead_wet * 0.13 + org * 0.42 + org_wet * 0.08 + lowst * 0.48
           + drums * 1.1 + sosf(drum_wet, "highpass", 250, 2) * 0.3)
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sosf(side, "highpass", 250, 8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sosf(mix, "highpass", 20, 2)
    mix = sosf(mix, "lowpass", 16000, 4)

    nf = int(0.35 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    y = y - y.mean(axis=0, keepdims=True)
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
