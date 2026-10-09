"""guitar-neo-soul-lick: Opus Sound Directory

A 9-second clean neo-soul electric guitar lick in E major at 72 BPM, played on a glassy single-coil guitar in the "in-between" neck+middle pickup position into a clean tube amp with light compression and a spring reverb. On frame 0 the fretting thumb holds a low A under a fingerpicked double stop whose lower note hammers up a whole step into a bright A-major shape. A second hammered double stop in thirds adds a lydian colour, the thumb walks down to G#, and a pair of sixths slides up the G and high-E strings with a little finger vibrato. One muted ghost "chuck" follows, then a quick pentatonic run that opens with a grace-note pull-off and lands over a thumbed C#. A 4th-to-3rd hammered double stop follows, then a singing whole-step bend over a B bass, held with a finger vibrato that starts slow and quickens before the bend eases back. After a short breath, frame 200 lands on a fast-rolled, lush Emaj9 chord that rings out with a soft chiming 7th-fret natural harmonic on top, and the spring tail fades to silence. Every note is modelled as a real string: an additive waveguide-style string with inharmonic partials, frequency-dependent decay, two polarisations, pluck-position and twin-pickup comb filtering, per-string voice stealing, fretted slides that step across the frets, and humanised timing.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 72009
DURATION_SEC = 9.0
BPM = 72
KEY = "E major"
FPS = 30
CUE_FRAMES = (0, 200)          # frame 0: thumb bass + double stop, frame 200: rolled Emaj9
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
BEAT = 60.0 / BPM              # 0.8333 s
S16 = BEAT / 4
CHORD_T = CUE_FRAMES[1] / FPS  # 6.6667 s = downbeat of bar 3 (exactly 320000 samples)

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- guitar constants
OPEN = np.array([40, 45, 50, 55, 59, 64], float)     # E2 A2 D3 G3 B3 E4, standard tuning
TUNE_CENTS = np.array([0.8, -1.1, 0.5, -0.6, 1.2, -0.4])  # a real guitar is never perfectly in tune
WOUND = [True, True, True, False, False, False]
SCALE = 0.648                                         # 25.5" scale length (m)
NECK_PU, MID_PU, PU_W = 0.162, 0.101, 0.017           # pickup distance from bridge + aperture (m)
B_OPEN = np.array([2.4e-5, 3.0e-5, 4.2e-5, 6.5e-5, 8.5e-5, 1.1e-4])  # inharmonicity per open string
LOSS_B1 = np.array([0.38, 0.42, 0.48, 0.55, 0.62, 0.70])           # frequency-independent loss (1/s)
LOSS_B3 = 4.8e-7                                                    # loss growing with f^2
F_MAX = 8500.0

# excitation kinds: pluck distance from bridge (m), contact low-pass (Hz), contact width (m),
# attack (s), carry-over of the previous vibration, tension-mod depth
EXC = {
    "thumb":  dict(d=0.175, fc=1900, w=0.016, att=0.0005, carry=0.10, tm=0.0022),
    "finger": dict(d=0.140, fc=3600, w=0.010, att=0.0005, carry=0.12, tm=0.0026),
    "pick":   dict(d=0.120, fc=6000, w=0.002, att=0.0003, carry=0.10, tm=0.0030),
    "hammer": dict(d=None,  fc=2300, w=0.012, att=0.0012, carry=0.92, tm=0.0006),
    "pull":   dict(d=None,  fc=3000, w=0.010, att=0.0008, carry=0.55, tm=0.0012),
    "harm3":  dict(d=0.060, fc=5200, w=0.008, att=0.0006, carry=0.10, tm=0.0004),
}


# ---------------------------------------------------------------- utilities
def hz(midi):
    return 440.0 * 2 ** ((np.asarray(midi) - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def biquad(x, kind, f0, gain_db=0.0, q=0.707):
    """RBJ cookbook biquads (peaking / lowpass / highshelf / lowshelf)."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    cw, sw = np.cos(w0), np.sin(w0)
    al = sw / (2 * q)
    if kind == "peak":
        b = [1 + al * a_, -2 * cw, 1 - al * a_]
        a = [1 + al / a_, -2 * cw, 1 - al / a_]
    elif kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(a_) * al
        b = [a_ * ((a_ + 1) + (a_ - 1) * cw + sq), -2 * a_ * ((a_ - 1) + (a_ + 1) * cw),
             a_ * ((a_ + 1) + (a_ - 1) * cw - sq)]
        a = [(a_ + 1) - (a_ - 1) * cw + sq, 2 * ((a_ - 1) - (a_ + 1) * cw), (a_ + 1) - (a_ - 1) * cw - sq]
    elif kind == "lowshelf":
        sq = 2 * np.sqrt(a_) * al
        b = [a_ * ((a_ + 1) - (a_ - 1) * cw + sq), 2 * a_ * ((a_ - 1) - (a_ + 1) * cw),
             a_ * ((a_ + 1) - (a_ - 1) * cw - sq)]
        a = [(a_ + 1) + (a_ - 1) * cw + sq, -2 * ((a_ - 1) + (a_ + 1) * cw), (a_ + 1) + (a_ - 1) * cw - sq]
    else:
        raise ValueError(kind)
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)


def one_pole_lp(x, tau):
    a = np.exp(-1.0 / (tau * SR))
    return signal.lfilter([1 - a], [1, -a], x, axis=0)


# ---------------------------------------------------------------- string model
def fret_contour(t, keys):
    """keys: list of (time, fret, glide). glide 0 = hammer/pull/fret change (1.2 ms
    smoothing); glide > 0 = finger slide lasting `glide` s. A slide crosses the frets
    as a smoothed staircase (the string snaps from fret to fret) mixed with a little
    continuous glide, eased in and out."""
    fr = np.full_like(t, float(keys[0][1]))
    prev = float(keys[0][1])
    for (tk, fk, g) in keys[1:]:
        fk = float(fk)
        if g <= 0:
            fr = fr + (fk - prev) * smoothstep((t - tk) / 0.0012)
        else:
            u = 0.5 - 0.5 * np.cos(np.pi * np.clip((t - tk) / g, 0, 1))
            span = fk - prev
            x = abs(span) * u
            fl = np.floor(x)
            stair = fl + smoothstep((x - fl - 0.62) / 0.38)
            path = 0.78 * np.minimum(stair, abs(span)) + 0.22 * x
            fr = fr + np.sign(span) * path
        prev = fk
    return fr


def bend_contour(t, bends):
    """bends: (t_start, t_end, target semitones). Fast rise that settles (ease-out)."""
    b = np.zeros_like(t)
    prev = 0.0
    for (ts, te, tgt) in bends:
        u = np.clip((t - ts) / (te - ts), 0, 1)
        shape = 1 - (1 - u) ** 2.4
        b = b + (tgt - prev) * shape
        prev = tgt
    return b


def vib_contour(t, vibs):
    """Finger vibrato is a bend: it only ever raises the pitch (cents)."""
    v = np.zeros_like(t)
    for (ts, te, r0, r1, depth) in vibs:
        m = (t >= ts)
        u = np.clip((t - ts) / (te - ts), 0, 1)
        rate = r0 + (r1 - r0) * u
        ph = 2 * np.pi * np.cumsum(rate * m) / SR
        env = smoothstep((t - ts) / 0.35) * (1 - smoothstep((t - te + 0.12) / 0.12))
        v += depth * env * (0.5 - 0.5 * np.cos(ph))
    return v


def pickup_gain(n, L):
    """Neck + middle pickups in parallel: signed sum of two aperture-averaged
    position combs (the hollow 'in-between' sound)."""
    g = np.zeros(np.broadcast(n, L).shape)
    for d, w in ((NECK_PU, 1.0), (MID_PU, 0.92)):
        g = g + w * np.sin(np.pi * n * d / L) * np.sinc(n * PU_W / (2 * L))
    return g


def excitation_spectrum(n, kind, L, f0):
    p = EXC[kind]
    d = p["d"] if p["d"] is not None else 0.035 + 0.25 * L  # hammer/pull: struck near the fretting finger
    e = (1.0 / n) * np.sin(np.pi * n * d / L) * np.sinc(n * p["w"] / (2 * L))
    e = e * (1 + (n * f0 / p["fc"]) ** 2) ** -0.75   # ~9 dB/oct above the contact corner
    if kind == "harm3":   # finger lightly on the 7th-fret node: only every 3rd mode survives
        e = e * np.where(n % 3 == 0, 1.0, 0.012)
    return e


def render_string(ev) -> tuple[int, np.ndarray]:
    """One continuous vibration of one string: a pick/finger/thumb attack plus any
    legato articulations (hammer-on, pull-off, slide, bend, vibrato) until the next
    attack on the same string or a release. Returns (start sample, mono signal)."""
    s = ev["s"]
    t0 = ev["t0"]
    s0 = int(round(t0 * SR))
    end = ev.get("end")
    damp = ev.get("damp", 0.03)
    stop = DURATION_SEC if end is None else min(DURATION_SEC, end + 9 * damp + 0.01)
    n_s = max(16, int(round(stop * SR)) - s0)
    t = s0 / SR + np.arange(n_s) / SR

    fret = fret_contour(t, ev["frets"])
    L = SCALE * 2 ** (-fret / 12)
    semis = OPEN[s] + fret + bend_contour(t, ev.get("bends", [])) \
        + (vib_contour(t, ev.get("vibs", [])) + TUNE_CENTS[s]) / 100
    excs = ev["exc"]
    tm = np.zeros_like(t)
    for (te_, kind, g) in excs:
        m = t >= te_
        tm[m] += EXC[kind]["tm"] * g * np.exp(-(t[m] - te_) / 0.11)   # pitch glide from string stretch
    f0 = hz(semis) * (1 + tm)
    Bc = B_OPEN[s] * (SCALE / L) ** 2

    # extra damping: release (finger lifts / palm), mute, friction while sliding
    extra = np.zeros_like(t)
    if end is not None:
        extra += smoothstep((t - end) / 0.004) / damp
    if ev.get("mute"):
        extra += 1.0 / ev["mute"]
    for (tk, fk, g) in ev["frets"][1:]:
        if g > 0:
            extra += 2.5 * ((t >= tk) & (t <= tk + g))
    hf_damp = 1.0 if end is None else 1 + 0.8 * smoothstep((t - end) / 0.004)

    idx = [max(0, int(round((te_ - t0) * SR))) for (te_, _, _) in excs]
    n_max = int(min(90, F_MAX // f0.max()))
    n = np.arange(1, n_max + 1)
    specs = [excitation_spectrum(n, kind, L[i], f0[i]) * g for (i, (_, kind, g)) in zip(idx, excs)]
    p0 = pickup_gain(n, L[idx[0]])
    norm = np.sqrt(np.sum((specs[0] / excs[0][2] * p0) ** 2)) + 1e-9
    sign = np.sign(specs[0] * p0 + 1e-12)
    # carry-over envelopes: an attack on a vibrating string keeps only part of it
    carry = []
    for j, (i, (_, kind, _)) in enumerate(zip(idx, excs)):
        c = EXC[kind]["carry"]
        k = np.ones(n_s)
        k[i:] = c + (1 - c) * (1 - smoothstep(np.arange(n_s - i) / (0.003 * SR)))
        carry.append(k)
    ramps = []
    for i, (_, kind, _) in zip(idx, excs):
        r = np.zeros(n_s)
        na = max(1, int(EXC[kind]["att"] * SR))
        r[i:] = smoothstep(np.arange(n_s - i) / na)
        ramps.append(r)
    later = []
    for j in range(len(excs)):
        k = np.ones(n_s)
        for jj in range(j + 1, len(excs)):
            k = k * carry[jj]
        later.append(k * ramps[j])

    out = np.zeros(n_s)
    det = rng.uniform(0.08, 0.35, n_max) * np.sqrt(n)   # 2nd polarisation detune (Hz): slow beating
    w2 = rng.uniform(0.35, 0.55)
    for k_i, k in enumerate(n):
        fk = k * f0 * np.sqrt(1 + Bc * k * k)
        if fk.max() > F_MAX:
            break
        alpha = LOSS_B1[s] + LOSS_B3 * fk ** 2 + extra * (1 + hf_damp * (fk / 1800.0))
        lam = np.cumsum(alpha) / SR
        e1 = np.zeros(n_s)
        e2 = np.zeros(n_s)
        for j, i in enumerate(idx):
            a = specs[j][k_i]
            if a == 0:
                continue
            dl = lam[i:] - lam[i]
            e1[i:] += (a * np.exp(-dl) * later[j][i:]) ** 2
            e2[i:] += (a * np.exp(-2.3 * dl) * later[j][i:]) ** 2
        pu = pickup_gain(k, L)
        ph = 2 * np.pi * (np.cumsum(fk) - fk[0]) / SR
        ph2 = ph + 2 * np.pi * det[k_i] * (t - t0)
        out += sign[k_i] * np.abs(pu) * (np.sqrt(e1) * np.sin(ph) + w2 * np.sqrt(e2) * np.sin(ph2))
    out /= norm
    nf = min(n_s, int(0.002 * SR))
    out[-nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
    return s0, out


def pick_noise(kind: str, g: float) -> np.ndarray:
    """Tiny contact noise of nail/flesh/pick leaving the string."""
    t = tt(0.012)
    band = {"pick": [1800, 7000], "finger": [700, 4000], "thumb": [300, 2200]}.get(kind, [500, 3000])
    y = sos_filter(rng.standard_normal(len(t)), "bandpass", band) * np.exp(-t / 0.0016)
    y[: 12] *= smoothstep(np.arange(12) / 12)
    return y * g * 0.035


def squeak(dur: float, f_a: float, f_b: float) -> np.ndarray:
    """Finger sliding along a wound string: a swept, rough resonance."""
    t = tt(dur)
    f = f_a * (f_b / f_a) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    rough = 1 + 0.6 * one_pole_lp(rng.standard_normal(len(t)), 0.002)
    tone = np.sin(ph) * rough + 0.5 * np.sin(2 * ph + 0.3) * rough
    nz = sos_filter(rng.standard_normal(len(t)), "bandpass", [1200, 4200]) * 0.6
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return (tone * 0.5 + nz) * env


# ---------------------------------------------------------------- amp / effects
def compressor(x, thr_db, ratio=2.6, tau=0.012, rel=0.09):
    env = np.sqrt(one_pole_lp(x ** 2, tau) + 1e-12)
    lev = 20 * np.log10(env)
    gr = -(1 - 1 / ratio) * np.maximum(0.0, lev - thr_db)
    gr = one_pole_lp(gr, rel)
    return x * 10 ** (gr / 20)


def preamp(x, drive=1.25, bias=0.14):
    """Clean tube stage, 4x oversampled, slightly asymmetric (warm, not dirty)."""
    up = signal.resample_poly(x, 4, 1)
    y = (np.tanh(drive * (up + bias)) - np.tanh(drive * bias)) / (drive * (1 - np.tanh(drive * bias) ** 2))
    return signal.resample_poly(y, 1, 4)[: len(x)]


def tone_and_cab(x):
    y = biquad(x, "lowshelf", 160, -2.0, 0.7)
    y = biquad(y, "peak", 520, -3.0, 0.7)          # scooped clean-amp mids
    y = biquad(y, "highshelf", 2200, 2.5, 0.7)     # bright cap on the volume pot
    y = biquad(y, "peak", 3200, 3.0, 1.1)          # glassy presence
    # 1x12 open-back cab + mic: thin lows, cone peak, steep top roll-off
    y = sos_filter(y, "highpass", 85, order=2)
    y = biquad(y, "peak", 120, 1.5, 1.3)
    y = biquad(y, "peak", 2300, 1.6, 2.0)
    y = sos_filter(y, "lowpass", 6000, order=4)
    y = sos_filter(y, "lowpass", 7800, order=4)
    return y


def spring_ir(delay: float, disp: float, rt_lo: float, seconds_fft: int = 2 ** 19) -> np.ndarray:
    """Spring tank, built in the frequency domain: each round trip is a delay, a
    dispersive phase (group delay rising with frequency, the 'drip' chirp), a narrow
    transducer band and frequency-dependent loss. IR = H_in * H_loop / (1 - H_loop)."""
    f = np.fft.rfftfreq(seconds_fft, 1 / SR)
    df = f[1] - f[0]
    gd = disp * (np.minimum(f, 5000.0) / 4000.0) ** 1.15
    phi = 2 * np.pi * np.cumsum(gd) * df
    rt = rt_lo / (1 + (f / 2800.0) ** 2) + 0.12
    g = 10 ** (-3 * delay / rt)
    _, hb = signal.sosfreqz(signal.butter(2, [180, 4600], "bandpass", fs=SR, output="sos"), worN=f, fs=SR)
    loop = g * np.abs(hb) * np.exp(-1j * (2 * np.pi * f * delay + phi))
    _, hin = signal.sosfreqz(signal.butter(2, [300, 4200], "bandpass", fs=SR, output="sos"), worN=f, fs=SR)
    H = hin * loop / (1 - loop)
    ir = np.fft.irfft(H, n=seconds_fft)[: int(4.0 * SR)]
    ir *= 1 - smoothstep((np.arange(len(ir)) / SR - 3.2) / 0.8)
    return ir / np.sqrt(np.sum(ir ** 2))


def room_ir(rt60=0.45, predelay=0.006):
    t = tt(rt60 * 1.2)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [250, 6000]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return irs


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
    return float(20 * np.log10(np.max(np.abs(signal.resample_poly(x, 4, 1, axis=0))) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 110.0) -> np.ndarray:
    ceil = 10 ** (ceiling_db / 20)
    os_ = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = os_[: len(x) * 4].reshape(len(x), 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    L = int(look_ms * 1e-3 * SR)
    held = minimum_filter1d(need, size=2 * L + 1, mode="nearest")
    rc = np.exp(-1.0 / (rel_ms * 1e-3 * SR))
    g = np.empty_like(held)
    prev = 1.0
    for i, h in enumerate(held.tolist()):
        prev = min(h, prev * rc + (1 - rc))
        g[i] = prev
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


# ---------------------------------------------------------------- the phrase
def score():
    """Every note on a real string/fret (strings 0..5 = low E..high E). Bar 1 over an
    A bass (IV), bar 2 over C# then B (vi -> V), bar 3 = Emaj9 on frame 200."""
    lay = 0.007                                  # lazy, behind-the-beat feel

    def h(t, ms=7.0):
        return t + lay + rng.uniform(-ms, ms) / 1000

    b = lambda bar, beat: bar * 4 * BEAT + beat * BEAT     # 0-based bar, fractional beat
    ev = []
    E = lambda **k: ev.append(k)

    # bar 1, beat 1 (cue f0): thumb-fretted A2 + fingers pinch B3/E4, G string hammers B->C#
    E(s=0, t0=0.0, frets=[(0.0, 5, 0)], exc=[(0.0, "thumb", 0.72)], end=h(b(0, 1.95)), damp=0.05)
    E(s=3, t0=0.0, frets=[(0.0, 4, 0), (h(b(0, 0.22)), 6, 0)],
      exc=[(0.0, "finger", 0.62), (h(b(0, 0.22)), "hammer", 0.55)], end=h(b(0, 0.93)), damp=0.035)
    E(s=4, t0=0.0, frets=[(0.0, 5, 0)], exc=[(0.0, "finger", 0.58)], end=h(b(0, 0.93)), damp=0.035)
    # beat 2: D#4/G#4 (4th) hammers to E4/G#4 (major 3rd)
    t = h(b(0, 1.0))
    E(s=3, t0=t, frets=[(t, 8, 0), (t + 0.115, 9, 0)], exc=[(t, "finger", 0.6), (t + 0.115, "hammer", 0.5)],
      end=h(b(0, 1.88)), damp=0.04)
    E(s=4, t0=t + 0.004, frets=[(t, 9, 0)], exc=[(t + 0.004, "finger", 0.6)], end=h(b(0, 1.88)), damp=0.04)
    # beat 3: thumb walks to G#2; sixths D#4/C5 slide up a fret to E4/C#5, re-pluck, slide to F#4/D#5
    tb = h(b(0, 2.0))
    E(s=0, t0=tb, frets=[(tb, 4, 0)], exc=[(tb, "thumb", 0.62)], end=h(b(0, 2.98)), damp=0.03)
    t = tb + 0.006
    E(s=3, t0=t, frets=[(t, 8, 0), (t + 0.045, 9, 0.075)], exc=[(t, "finger", 0.6)], end=h(b(0, 2.5)) - 0.012,
      damp=0.012)
    E(s=5, t0=t + 0.003, frets=[(t, 8, 0), (t + 0.045, 9, 0.075)], exc=[(t + 0.003, "finger", 0.6)],
      end=h(b(0, 2.5)) - 0.012, damp=0.012)
    t = h(b(0, 2.5))
    E(s=3, t0=t, frets=[(t, 9, 0), (t + 0.05, 11, 0.11)], exc=[(t, "finger", 0.62)],
      vibs=[(t + 0.22, b(0, 3.0) - 0.02, 4.8, 5.6, 14.0)], end=h(b(0, 2.94)), damp=0.025)
    E(s=5, t0=t + 0.004, frets=[(t, 9, 0), (t + 0.05, 11, 0.11)], exc=[(t + 0.004, "finger", 0.6)],
      vibs=[(t + 0.22, b(0, 3.0) - 0.02, 4.8, 5.6, 14.0)], end=h(b(0, 2.94)), damp=0.025)
    # beat 4: one muted ghost "chuck" across D-G-B-E, fretting hand resting on the strings
    tc = b(0, 3.0) + 0.012
    for i, (s, fr) in enumerate(((2, 9), (3, 9), (4, 10), (5, 9))):
        E(s=s, t0=tc + 0.007 * i, frets=[(tc, fr, 0)], exc=[(tc + 0.007 * i, "pick", 0.5 - 0.04 * i)],
          mute=0.016, end=tc + 0.08, damp=0.02)
    # beat 4.5: pentatonic pickup run (16th triplets) with a grace-note pull-off E5 -> C#5
    tr = h(b(0, 3.5), 4)
    st = BEAT / 6
    E(s=5, t0=tr, frets=[(tr, 12, 0), (tr + 0.048, 9, 0)], exc=[(tr, "finger", 0.66), (tr + 0.048, "pull", 0.62)],
      end=tr + 1.6 * st, damp=0.03)
    t = tr + st + rng.uniform(-0.004, 0.004)
    E(s=4, t0=t, frets=[(t, 12, 0)], exc=[(t, "finger", 0.6)], end=t + 1.15 * st, damp=0.03)
    t = tr + 2 * st + rng.uniform(-0.004, 0.004)
    E(s=4, t0=t, frets=[(t, 9, 0)], exc=[(t, "finger", 0.58)], end=b(1, 0.0) + 0.06, damp=0.03)
    # thumb shifts up the wound low E to fret 9 (a soft squeak), lands C#3 on bar 2
    # bar 2, beat 1: C#3 bass + E4/G#4 double stop (a 3rd)
    tb = h(b(1, 0.0))
    E(s=0, t0=tb, frets=[(tb, 9, 0)], exc=[(tb, "thumb", 0.68)], end=h(b(1, 1.5)), damp=0.04)
    E(s=3, t0=tb + 0.005, frets=[(tb, 9, 0)], exc=[(tb + 0.005, "finger", 0.58)], end=h(b(1, 0.92)), damp=0.03)
    E(s=4, t0=tb + 0.009, frets=[(tb, 9, 0)], exc=[(tb + 0.009, "finger", 0.6)], end=h(b(1, 0.92)), damp=0.03)
    # beat 2: G#4/C#5 (4th) hammers to A4/C#5 (3rd)
    t = h(b(1, 1.0))
    E(s=4, t0=t, frets=[(t, 9, 0), (t + 0.10, 10, 0)], exc=[(t, "finger", 0.6), (t + 0.10, "hammer", 0.5)],
      end=h(b(1, 1.92)), damp=0.03)
    E(s=5, t0=t + 0.004, frets=[(t, 9, 0)], exc=[(t + 0.004, "finger", 0.62)], end=h(b(1, 1.92)), damp=0.03)
    # beat 2.5: thumb B2, G string F#4 bent a whole step to G#4, slow-then-faster finger vibrato
    tb = h(b(1, 1.5))
    E(s=0, t0=tb, frets=[(tb, 7, 0)], exc=[(tb, "thumb", 0.64)], end=h(b(1, 3.85)), damp=0.05)
    t = h(b(1, 2.0))
    E(s=3, t0=t, frets=[(t, 11, 0)], exc=[(t, "finger", 0.72)],
      bends=[(t + 0.05, t + 0.21, 2.0), (b(1, 3.55), b(1, 3.85), 1.55)],
      vibs=[(t + 0.32, b(1, 3.6), 4.2, 6.0, 22.0)], end=h(b(1, 3.86)), damp=0.03)
    # beat 4: a soft B3 on the D string (9th fret) under the held bend
    t = h(b(1, 3.0))
    E(s=2, t0=t, frets=[(t, 9, 0)], exc=[(t, "finger", 0.36)], end=h(b(1, 3.86)), damp=0.03)

    # bar 3, beat 1 (cue f200): fast-rolled Emaj9 = E2 E3 G#3 D#4 F#4 (0 7 6 8 7 x)
    roll = [(0, 0, "thumb", 0.70), (1, 7, "finger", 0.70), (2, 6, "finger", 0.70),
            (3, 8, "finger", 0.74), (4, 7, "finger", 0.78)]
    for i, (s, fr, kind, g) in enumerate(roll):
        t = CHORD_T + (0.0 if i == 0 else 0.015 * i + rng.uniform(-0.002, 0.002))
        E(s=s, t0=t, frets=[(t, fr, 0)], exc=[(t, kind, g)],
          vibs=[(CHORD_T + 0.6, DURATION_SEC, 3.2, 3.6, 4.0)] if s >= 3 else [])
    # natural harmonic on the open high E at the 7th fret (B5) floats on top
    t = CHORD_T + 0.31
    E(s=5, t0=t, frets=[(t, 0, 0)], exc=[(t, "harm3", 0.5)])
    return ev


def render() -> np.ndarray:
    ev = score()
    # per-string voice stealing: a new attack on a string stops the old vibration
    by_s = {}
    for e in ev:
        by_s.setdefault(e["s"], []).append(e)
    for lst in by_s.values():
        lst.sort(key=lambda e: e["t0"])
        for a, b_ in zip(lst, lst[1:]):
            if a.get("end") is None or a["end"] > b_["t0"] - 0.004:
                a["end"] = b_["t0"] - 0.004
                a["damp"] = min(a.get("damp", 0.03), 0.006)

    gtr = np.zeros(N)
    for e in ev:
        s0, y = render_string(e)
        if e["t0"] < CHORD_T - 0.01:
            y = y * 0.86          # the phrase sits a touch under the resolving chord
        nn = min(len(y), N - s0)
        gtr[s0:s0 + nn] += y[:nn]
        for (te_, kind, g) in e["exc"]:
            if kind in ("pick", "finger", "thumb"):
                pn = pick_noise(kind, g)
                i0 = int(round(te_ * SR))
                m = min(len(pn), N - i0)
                gtr[i0:i0 + m] += pn[:m]
    # thumb squeak on the wound low E during the position shift into bar 2
    sq = squeak(0.11, 1100, 2300)
    i0 = int(round((4 * BEAT - 0.17) * SR))
    gtr[i0:i0 + len(sq)] += sq * 0.012
    # muted chuck body thump (fretting hand + pick against damped strings)
    tc = 3 * BEAT + 0.012
    th = sos_filter(rng.standard_normal(int(0.05 * SR)), "bandpass", [150, 1800]) \
        * np.exp(-tt(0.05) / 0.009)
    th[:24] *= smoothstep(np.arange(24) / 24)
    i0 = int(round(tc * SR))
    gtr[i0:i0 + len(th)] += th * 0.10

    # electronics: pickup inductance/cable resonance, then compression and the amp
    gtr = biquad(gtr, "lowpass", 4100, 0.0, 2.1)
    gtr = gtr / (np.abs(gtr).max() + 1e-9)
    act = np.abs(gtr) > 1e-4
    thr = 20 * np.log10(np.percentile(np.sqrt(one_pole_lp(gtr ** 2, 0.012))[act], 90) + 1e-9) - 3
    gtr = compressor(gtr, thr)
    gtr = 0.55 * gtr / (np.abs(gtr).max() + 1e-9)
    pre = preamp(gtr)
    pre = sos_filter(pre, "highpass", 30, order=2)

    # spring tank (two springs per side), driven from the preamp like a real amp
    send = sos_filter(pre, "highpass", 220, order=2)
    ir_l = spring_ir(0.0335, 0.026, 2.4) + 0.7 * spring_ir(0.0412, 0.031, 2.1)
    ir_r = spring_ir(0.0368, 0.028, 2.3) + 0.7 * spring_ir(0.0447, 0.024, 2.2)
    wet = np.stack([signal.fftconvolve(send, ir_l)[:N], signal.fftconvolve(send, ir_r)[:N]], axis=1)
    wet /= np.sqrt(np.mean(wet ** 2)) / np.sqrt(np.mean(send ** 2))

    dry = tone_and_cab(pre)
    wet = tone_and_cab(wet)
    mix = np.stack([dry, dry], axis=1) + 0.26 * wet
    # the cab in a small room
    rl, rr = room_ir()
    room = np.stack([signal.fftconvolve(dry, rl)[:N], signal.fftconvolve(dry, rr)[:N]], axis=1)
    mix += 0.10 * room

    # mono low end: the side channel is high-passed steeply at 250 Hz
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)

    # the player eases the volume knob down as the chord rings out: silent by the end
    tl = np.arange(N) / SR
    knob = 1 - smoothstep((tl - 7.9) / 1.06)
    mix *= knob[:, None]
    nf = int(0.03 * SR)
    mix[-nf:] *= np.linspace(1, 0, nf)[:, None] ** 2
    mix[:3] *= np.array([0.0, 0.33, 0.67])[:, None]
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
