"""drop-whoosh-stinger: Opus Sound Directory

A light, fast 2-second edit-transition stinger that goes from atonal air to a
clean A. A flanged band-pass noise whoosh flies across the stereo field from
hard left towards the right, like something passing the camera. Its filter
climbs from 250 Hz to about 7 kHz, its comb notches sweep upward and its far
side darkens, so it reads as a doppler pass-by. A thin layer of high air
thickens it in the last third of a second. The whoosh takes a 25 ms breath and
then lands a tight, punchy impact exactly on frame 30 (1.0 s). The impact is a
short mono kick dropping to A1, a snappy noise crack and a bright, fast-decaying
A power-chord stab, with a quick splash. A short 0.7 s room tail fades to
silence by 2 s. The kick is the only content below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 503030
DURATION_SEC = 2
BPM = 120
KEY = "atonal -> A"
FPS = 30
CUE_FRAMES = (30,)             # frame 30 (1.0 s): the impact
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
HIT_T = CUE_FRAMES[0] / FPS    # 1.0 s = sample 48000

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
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))).reshape((-1,) + (1,) * (x.ndim - 1))
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))).reshape((-1,) + (1,) * (x.ndim - 1))
    return x


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a mono (L,) or stereo (L,2) snippet into a stereo bus at time t (equal-power pan)."""
    s = int(round(t * SR))
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


def svf(x: np.ndarray, fc: np.ndarray, q: np.ndarray | float, mode: str = "bp") -> np.ndarray:
    """Zavalishin TPT state-variable filter with per-sample cutoff and Q (for sweeps)."""
    g = np.tan(np.pi * np.clip(fc, 20, 0.45 * SR) / SR)
    k = 1.0 / np.broadcast_to(np.asarray(q, dtype=float), g.shape)
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    bp = np.empty(len(x))
    lp = np.empty(len(x))
    ic1 = ic2 = 0.0
    for n, (xn, b1, b2, b3) in enumerate(zip(x.tolist(), a1.tolist(), a2.tolist(), a3.tolist())):
        v3 = xn - ic2
        v1 = b1 * ic1 + b2 * v3
        v2 = ic2 + b2 * ic1 + b3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        bp[n] = v1
        lp[n] = v2
    return bp * k if mode == "bp" else lp     # bp normalised to unity peak gain


def frac_delay(x: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Read x at (n - d[n]) with linear interpolation (d in samples, smooth)."""
    n = np.arange(len(x), dtype=float)
    return np.interp(n - d, n, x, left=0.0)


def reverb(x: np.ndarray, rt60: float, predelay: float, band=(300, 9000)) -> np.ndarray:
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


# ---------------------------------------------------------------- voices
def whoosh(dur: float) -> np.ndarray:
    """Flanged band-pass noise pass-by: rising centre, rising comb notches,
    accelerating left-to-right pan, far channel darker (doppler/air-absorption cue)."""
    t = tt(dur)
    u = t / dur
    fc = 250 * (7000 / 250) ** (u ** 1.7)
    q = 1.1 + 2.4 * u ** 2
    # pan position: slow drift on the left, then whips across late (accelerating)
    pos = -0.9 + 1.55 * u ** 3.2
    th = (np.clip(pos, -1, 1) + 1) * np.pi / 4
    # amplitude: swells hard into the hit; 25 ms breath before it
    amp = (0.06 + 0.94 * u ** 2.0) * (1 - np.exp(-t / 0.08))
    breath = 0.025
    out = np.zeros((len(t), 2))
    for ch in range(2):
        src = noise(dur)
        b = svf(src, fc * (1.0 if ch == 0 else 1.035), q)
        # flanger: delay sweeps 3.2 ms -> 0.25 ms so the notches rise with the filter
        d = (3.2e-3 * (0.25 / 3.2) ** (u ** 1.3)) * SR * (1.0 if ch == 0 else 1.07)
        out[:, ch] = 0.6 * b + 0.4 * frac_delay(b, d)
    # air layer in the last ~0.35 s
    air_env = np.clip((t - (dur - 0.35)) / 0.35, 0, 1) ** 2
    air = np.stack([sos_filter(noise(dur), "bandpass", [6000, 13000]) for _ in range(2)], axis=1)
    out += 0.35 * air * air_env[:, None]
    out *= amp[:, None]
    # doppler-ish: the side the source is moving away from is panned down and darkened
    far_dark = np.stack([sos_filter(out[:, 0], "lowpass", 2500), sos_filter(out[:, 1], "lowpass", 2500)], 1)
    w_far = np.stack([np.clip(pos, 0, 1), np.clip(-pos, 0, 1)], 1)        # L is "far" once pos > 0
    out = out * (1 - 0.6 * w_far) + far_dark * 0.6 * w_far
    out *= np.stack([np.cos(th), np.sin(th)], 1) * np.sqrt(2)
    # the breath: 25 ms dip right before the hit, ending exactly on the cue sample
    nb = int(breath * SR)
    dip = np.ones(len(t))
    dip[-nb:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nb))
    dip[-nb:] = 0.12 + 0.88 * dip[-nb:]
    out *= dip[:, None]
    return fade(out, a=0.004, r=0.002)


def punch_kick() -> np.ndarray:
    """Tight kick: 240 Hz -> A1 (55 Hz) sweep, short body."""
    t = tt(0.32)
    f = hz(33) + (240 - hz(33)) * np.exp(-t / 0.020)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.068)
    y = np.tanh(1.6 * body) / np.tanh(1.6)
    return fade(y, a=0.0008, r=0.08)


def crack() -> np.ndarray:
    t = tt(0.12)
    y = sos_filter(noise(0.12), "bandpass", [1400, 9000], order=2)
    env = np.exp(-t / 0.011) + 0.25 * np.exp(-t / 0.035)
    return fade(y * env * 0.9, a=0.0006, r=0.01)


def stab(midi: float, dur: float, detune: float) -> np.ndarray:
    """Bright band-limited saw stab whose upper partials decay fastest."""
    t = tt(dur)
    f = hz(midi) * 2 ** (detune / 1200)
    y = np.zeros_like(t)
    for k in range(1, int(15500 // f) + 1):
        env = np.exp(-t * (9 + 2.2 * (k - 1)))
        y += (1 / k) * env * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    return fade(y * 0.5, a=0.0008, r=0.03)


def splash(dur: float) -> np.ndarray:
    t = tt(dur)
    env = np.exp(-t / 0.16)
    return np.stack([fade(sos_filter(noise(dur), "bandpass", [2500, 11000]) * env, 0.0006, 0.05)
                     for _ in range(2)], axis=1)


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 1.5, rel_ms: float = 60.0) -> np.ndarray:
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
    g = uniform_filter1d(g, size=L + 1, mode="nearest")  # edge-safe (no ramp at file start/end)
    return x * g[:, None]


def master(mix: np.ndarray) -> np.ndarray:
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.4
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        # gain riding on the asymmetric kick lobe leaves a little DC: block it after the limiter
        y = sos_filter(y, "highpass", 20, order=2)
        y = soft_limiter(y, ceiling)                 # re-catch the filter's small overshoot
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    low = np.zeros((N, 2))      # kick: the only content below 120 Hz
    fx = np.zeros((N, 2))       # whoosh + splash
    hit = np.zeros((N, 2))      # crack + stab
    send = np.zeros((N, 2))

    # --- intro/body: the pass-by whoosh, sample 0 -> cue sample
    w = whoosh(HIT_T)
    place(fx, w, 0.0, 0.55)
    place(send, w, 0.0, 0.10)

    # --- payoff: tight impact on frame 30
    place(low, punch_kick(), HIT_T, 0.8)
    c = crack()
    place(hit, c, HIT_T, 0.55, pan=0.15)
    place(send, np.stack([c, c], 1), HIT_T, 0.25)
    for i, (m, g) in enumerate(((57, 0.30), (64, 0.24), (69, 0.22), (76, 0.14))):   # A3 E4 A4 E5
        for side, det in ((-1, -6), (1, 6)):
            s = stab(m, 0.55, det)
            place(hit, s, HIT_T, g, pan=0.5 * side)
            place(send, s, HIT_T, g * 0.35, pan=0.5 * side)
    sp = splash(0.7)
    place(fx, sp, HIT_T, 0.22)
    place(send, sp, HIT_T, 0.10)

    hp = lambda x, f=160: sos_filter(x, "highpass", f, order=4)
    fx, hit = hp(fx, 200), hp(hit)
    wet = hp(reverb(send, rt60=0.7, predelay=0.012), 220) * 0.6
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)

    mix = low * 1.0 + fx + hit + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 120, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 25, order=2)
    mix = sos_filter(mix, "lowpass", 16500, order=4)

    nf = int(0.25 * SR)
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
