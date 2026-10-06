"""countdown-10-to-0: Opus Sound Directory

An 11-second launch countdown in E minor at 60 BPM, with no speech. Ten clean sine
pips land exactly on each second (frames 0, 30, ... 270), one per count from ten
down to one. Each pip is a semitone higher than the last, climbing from E5 to C#6.
A mono sub thump hits under every pip. The first three seconds are only pips, the
thump and a dark low-passed E minor drone. From 3 s an eighth-note pulse of
band-limited E minor stabs comes in, and its filter slowly opens. In the last three
seconds (7 to 10 s) the pulse tightens to sixteenths. The pips get brighter and
shorter, a tense F tone rubs against the drone, and a noise riser climbs. That
build is cut with a 3 ms fade ending exactly on frame 300 (10.0 s). The launch
hits there: a pitch-dropping low boom, a sharp ignition crack and a roaring,
crackling engine-noise burst. These decay over the final second to silence. All
content below 120 Hz (sub thumps, boom, rumble) is mono.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 1000110
DURATION_SEC = 11
BPM = 60
KEY = "E minor"
FPS = 30
CUE_FRAMES = (0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300)   # ten pips + launch
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM               # 1.0 s, one pip per beat
LAUNCH_T = CUE_FRAMES[-1] / FPS  # 10.0 s
TIGHT_T = 7.0                    # last three seconds tighten

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


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


def svf(x: np.ndarray, fc: np.ndarray, q: float, mode: str = "bp") -> np.ndarray:
    """Zavalishin TPT state-variable filter with per-sample cutoff (lp or bp output)."""
    g = np.tan(np.pi * np.clip(fc, 20, 0.45 * SR) / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    y = np.empty(len(x))
    ic1 = ic2 = 0.0
    lp = mode == "lp"
    for n, (xn, b1, b2, b3) in enumerate(zip(x.tolist(), a1.tolist(), a2.tolist(), a3.tolist())):
        v3 = xn - ic2
        v1 = b1 * ic1 + b2 * v3
        v2 = ic2 + b2 * ic1 + b3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[n] = v2 if lp else v1
    return y


# ---------------------------------------------------------------- voices
def pip(midi: float, bright: float, length: float) -> np.ndarray:
    """Countdown pip: a pure sine with a touch of 2nd/3rd harmonic. The attack is a
    0.5 ms raised cosine, so the onset is sharp but click-free."""
    t = tt(length + 0.05)
    f = hz(midi)
    # cosine phase: the pip is at full level within its first millisecond
    y = np.cos(2 * np.pi * f * t) + 0.10 * bright * np.cos(4 * np.pi * f * t) \
        + 0.04 * bright * np.cos(6 * np.pi * f * t)
    env = np.ones_like(t)
    env *= 1.0 - 0.25 * (1 - np.exp(-t / 0.05))          # slight sag after the strike
    na = int(0.0005 * SR)
    env[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    nr = int(0.05 * SR)
    env[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    y = y * env * 0.5
    # tiny band-limited "relay tick" (3 ms) that gives the strike its edge
    tick = sos_filter(noise(0.012), "bandpass", [2500, 11000], order=2) * np.exp(-tt(0.012) / 0.0015)
    y[: len(tick)] += fade(tick, a=0.0005, r=0.003) * 0.12
    return y


def sub_thump(level_hz: float = 41.2, dur: float = 0.42) -> np.ndarray:
    """Mono sub thump on each count: sine falling from ~2x to E1, cosine phase."""
    t = tt(dur)
    f = level_hz + level_hz * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / 0.13)
    return fade(y, a=0.0005, r=0.04)


def saw_stab(midi: float, dur: float, cutoff: float, decay: float) -> np.ndarray:
    """Band-limited saw (additive, partials < 12 kHz) through a static 2-pole roll-off,
    with a fast-decaying amplitude: one pulse of the E minor engine."""
    t = tt(dur)
    f = hz(midi)
    y = np.zeros_like(t)
    for k in range(1, int(12000 // f) + 1):
        a = (1 / k) / (1 + (k * f / cutoff) ** 2)
        if a < 2e-4:
            break
        y += a * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    y *= np.exp(-t / decay)
    return fade(y, a=0.002, r=0.01)


def drone(midis, dur: float, cutoff: float) -> np.ndarray:
    """Dark, slowly-beating saw drone (stereo detune), low-passed hard."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for m in midis:
        for ch, cents in ((0, -6), (1, 6), (0, 2), (1, -2)):
            f = hz(m) * 2 ** (cents / 1200)
            for k in range(1, int(4000 // f) + 1):
                a = (1 / k) / (1 + (k * f / cutoff) ** 4)
                out[:, ch] += a * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    return out


def reverb(x: np.ndarray, rt60: float = 1.2, predelay: float = 0.015) -> np.ndarray:
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [300, 7000]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


# ---------------------------------------------------------------- launch
def launch_boom() -> np.ndarray:
    t = tt(1.0)
    f = 34 + (120 - 34) * np.exp(-t / 0.09)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR + np.pi / 2) * np.exp(-t / 0.38)
    y = np.tanh(1.4 * y) / np.tanh(1.4)
    return fade(y, a=0.0005, r=0.2)


def ignition_crack() -> np.ndarray:
    t = tt(0.12)
    y = sos_filter(noise(0.12), "bandpass", [700, 7000], order=2)
    y *= np.exp(-t / 0.018)
    return fade(y, a=0.0005, r=0.02)


def engine_roar(dur: float) -> np.ndarray:
    """Wide roaring noise burst: decorrelated noise through a low-pass that falls from
    ~6 kHz to ~700 Hz, a slow growl modulation, and sparse band-passed crackle grains."""
    t = tt(dur)
    fc = 700 + 5300 * np.exp(-t / 0.28)
    swell = (1 - np.exp(-t / 0.012)) * np.exp(-t / 0.42)
    growl = 1 + 0.25 * np.sin(2 * np.pi * 9 * t) * np.sin(2 * np.pi * 2.3 * t + 1)
    out = np.zeros((len(t), 2))
    for ch in range(2):
        y = svf(noise(dur), fc * (1.0 + 0.04 * ch), 0.8, mode="lp")
        # crackle: short soft grains, band-limited, Poisson-scattered
        cr = np.zeros(len(t))
        n_gr = 140
        pos = np.sort(rng.integers(0, int(0.8 * len(t)), n_gr))
        gl = int(0.003 * SR)
        gw = np.hanning(gl)
        for p in pos:
            cr[p:p + gl] += gw * rng.uniform(0.3, 1.0) * (1 if rng.uniform() < 0.5 else -1)
        cr = sos_filter(cr, "bandpass", [900, 6000], order=2) * np.exp(-t / 0.35)
        out[:, ch] = y * swell * growl + 0.9 * cr
    return fade(out, a=0.002, r=0.1)


def rumble(dur: float) -> np.ndarray:
    t = tt(dur)
    y = sos_filter(noise(dur), "lowpass", 90, order=4)
    y = sos_filter(y, "highpass", 25, order=2)
    y /= np.sqrt(np.mean(y ** 2)) + 1e-12
    env = (1 - np.exp(-t / 0.03)) * np.exp(-t / 0.4)
    return fade(y * env, a=0.002, r=0.1)


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 120.0) -> np.ndarray:
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
    return y - y.mean(axis=0)


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    pre = np.zeros((N, 2))      # count layer: pips, echoes (cut on the launch frame)
    bed = np.zeros((N, 2))      # drone, pulse, ticks, riser: ducked into every count
    pre_low = np.zeros((N, 2))  # mono sub thumps (also cut at launch)
    send = np.zeros((N, 2))
    post = np.zeros((N, 2))     # launch
    post_low = np.zeros((N, 2))

    ls = int(LAUNCH_T * SR)

    # --- pips: E5 rising a semitone per count -> C#6
    for i in range(10):
        t = i * BEAT
        tight = t >= TIGHT_T
        bright = 0.6 + 0.12 * i + (0.8 if tight else 0.0)
        length = 0.16 if not tight else 0.11
        p = pip(76 + i, bright, length)
        g = 0.55 + 0.02 * i
        place(pre, p, t, g)
        place(send, p, t, g * 0.35)
        # quiet ping-pong echoes, well clear of the next cue window
        place(pre, p, t + 0.375, g * 0.16, pan=-0.6)
        place(pre, p, t + 0.75, g * 0.07, pan=0.6)

    # --- sub thump under every count, growing
    for i in range(10):
        place(pre_low, sub_thump(), i * BEAT, 0.45 + 0.05 * i)

    # --- drone: E2 + B2 throughout, F3 rub in the last three seconds
    dr = drone((40, 47, 52), LAUNCH_T, 260)
    t = np.arange(len(dr)) / SR
    env = np.clip(t / 1.5, 0, 1) ** 2 * (0.5 + 0.5 * t / LAUNCH_T)
    dr *= env[:, None] * 0.035
    bed[: len(dr)] += dr
    rub = drone((53, 55), LAUNCH_T - TIGHT_T, 700)        # F3 + G3 against the E
    tr = np.arange(len(rub)) / SR
    rub *= ((tr / (LAUNCH_T - TIGHT_T)) ** 1.5 * 0.025)[:, None]
    place(bed, rub, TIGHT_T)

    # --- pulse engine: E minor stabs, eighths from 3 s, sixteenths from 7 s
    chord = (52, 55, 59, 64)
    step8, step16 = BEAT / 2, BEAT / 4
    times = []
    tp = 3.0
    while tp < LAUNCH_T - 1e-9:
        times.append(tp)
        tp += step8 if tp < TIGHT_T - 1e-9 else step16
    for tp in times:
        if abs(tp - round(tp)) < 1e-9:      # the count itself belongs to the pip + thump
            continue
        prog = (tp - 3.0) / (LAUNCH_T - 3.0)
        cutoff = 500 * (4500 / 500) ** prog
        dec = 0.07 if tp < TIGHT_T else 0.045
        vel = 0.10 + 0.10 * prog
        accent = 1.0 if abs((tp % 1.0) - 0.5) < 1e-9 else 0.7
        for j, m in enumerate(chord):
            st = saw_stab(m, 0.2, cutoff, dec)
            place(bed, st, tp, vel * accent * 0.5, pan=(-0.35, 0.35, -0.15, 0.15)[j])
        place(send, np.stack([st, st], 1), tp, vel * 0.1)
        # a soft off-beat E1 bass pulse (mono)
        if accent == 1.0:
            place(pre_low, saw_stab(28, 0.25, 260, 0.08), tp, 0.18 + 0.2 * prog)

    # --- tick on the off-beat sixteenth grid in the tight section (filtered noise)
    for k in range(12):
        tk = TIGHT_T + 0.125 + k * 0.25
        if tk >= LAUNCH_T - 0.05:
            break
        hh = sos_filter(noise(0.04), "bandpass", [6000, 12000], order=2) * np.exp(-tt(0.04) / 0.008)
        place(bed, fade(hh, 0.0005, 0.005), tk, 0.12 + 0.02 * k, pan=0.4 * (-1) ** k)

    # --- noise riser 7 -> 10 s
    rd = LAUNCH_T - TIGHT_T
    tr = tt(rd)
    fc = 400 * (7000 / 400) ** (tr / rd) ** 1.3
    amp = (tr / rd) ** 2.0
    rl = svf(noise(rd), fc, 3.0) * amp
    rr = svf(noise(rd), fc * 1.05, 3.0) * amp
    place(bed, np.stack([rl, rr], 1), TIGHT_T, 0.15)

    # --- sidechain duck: the bed dips in the 50 ms before every count (and pumps back
    # after it), so each pip strikes into a pocket. Deeper pre-suck into the launch.
    duck = np.ones(N)
    for i in range(1, 11):
        c = int(i * BEAT * SR)
        depth, pre_s, rec = (0.65, 0.05, 0.16) if i < 10 else (0.85, 0.09, 0.0)
        a = int(pre_s * SR)
        duck[c - a:c] = np.minimum(duck[c - a:c], 1 - depth * (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))))
        if rec:
            r = int(rec * SR)
            duck[c:c + r] = np.minimum(duck[c:c + r], 1 - depth * (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, r))))
    bed *= duck[:, None]

    # --- pre-launch bus: filter, then the cut fade that ends exactly on frame 300
    pre = sos_filter(pre + bed, "highpass", 120, order=4)
    pre = pre + sos_filter(reverb(send, rt60=1.1), "highpass", 250, order=4) * 0.5
    pre_low = np.repeat(pre_low.mean(axis=1, keepdims=True), 2, axis=1)
    pre_low = sos_filter(pre_low, "highpass", 22, order=2)
    cutf = int(0.003 * SR)
    cut = np.ones(N)
    cut[ls - cutf:ls] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, cutf))
    cut[ls:] = 0.0
    pre *= cut[:, None]
    pre_low *= cut[:, None]

    # --- launch at frame 300
    place(post_low, launch_boom(), LAUNCH_T, 1.0)
    place(post_low, rumble(1.0), LAUNCH_T, 0.35)
    place(post, ignition_crack(), LAUNCH_T, 0.8)
    place(post, engine_roar(1.0), LAUNCH_T, 1.7)
    post = sos_filter(post, "highpass", 120, order=4)
    post_low = np.repeat(post_low.mean(axis=1, keepdims=True), 2, axis=1)
    post_low = sos_filter(post_low, "highpass", 22, order=2)

    mix = pre + pre_low + post + post_low
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "lowpass", 16500, order=4)

    nf = int(0.3 * SR)
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
