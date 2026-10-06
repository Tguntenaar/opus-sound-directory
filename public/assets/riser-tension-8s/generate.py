"""riser-tension-8s: Opus Sound Directory

An 8-second tension riser in Bb at 120 BPM that climbs on three fronts at once and then
stops dead. A Shepard-Risset glissando (octave-spaced sines on Bb under a raised-cosine
spectral window, so it seems to rise forever) speeds up and brightens, and a second stack
a fifth above (F) joins halfway. A band-pass noise sweep opens from 250 Hz to 9 kHz. A
heartbeat-like low pulse on Bb1 accelerates smoothly from quarter notes to a roughly
18 Hz flutter, and a Bb/F drone tremolos in sync with it. At frame 210 (7.0 s)
everything, reverb included, cuts to true silence through a 1.5 ms fade that ends on
the cue sample. A quarter of a second later a single soft, low felt-mallet hit on Bb1
blooms in a small dark room and decays to silence. Below 120 Hz there is only the mono
pulse and the hit.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 72100
DURATION_SEC = 8
BPM = 120
KEY = "Bb"
FPS = 30
CUE_FRAMES = (210,)            # frame 210: hard cut to silence
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
CUT_T = CUE_FRAMES[0] / FPS    # 7.0 s
CUT_S = int(round(CUT_T * SR)) # 336000
HIT_T = CUT_T + 0.25           # soft low hit, an eighth note after the cut
BB1 = 58.270470189761          # Bb1

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na)))[:, None] if x.ndim == 2 else \
        0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr)))[:, None] if x.ndim == 2 else \
        0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
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


def noise(n: int) -> np.ndarray:
    return rng.standard_normal(n)


def svf_bandpass(x: np.ndarray, fc: np.ndarray, q: np.ndarray | float) -> np.ndarray:
    """Zavalishin TPT state-variable band-pass with per-sample cutoff and Q (for sweeps)."""
    g = np.tan(np.pi * np.clip(fc, 20, 0.45 * SR) / SR)
    k = 1.0 / np.broadcast_to(q, g.shape)
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


def reverb(x: np.ndarray, rt60: float, band=(200, 6000), predelay: float = 0.015) -> np.ndarray:
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


# ---------------------------------------------------------------- riser voices
T = CUT_T
t_r = np.arange(CUT_S) / SR    # riser timeline 0 .. 7.0 s
u = t_r / T                     # normalised 0 .. 1


def pulse_phase() -> np.ndarray:
    """Exponential acceleration from 2 Hz (quarters at 120 BPM) to 18 Hz: phi(t) = int r dt."""
    r0, k = 2.0, 9.0
    return r0 * T / np.log(k) * (k ** u - 1)


def shepard_stack(offset_oct: float, detune_cents: float, climb: np.ndarray, tilt: np.ndarray) -> np.ndarray:
    """Shepard-Risset glissando: K octave-spaced sines on Bb2, raised-cosine window in
    log-frequency (exactly zero where a partial wraps from top to bottom)."""
    K = 7                                    # 116.5 Hz .. 14.9 kHz
    fb = 2 * BB1 * 2 ** (offset_oct + detune_cents / 1200)
    y = np.zeros(CUT_S)
    for i in range(K):
        p = np.mod(i + climb, K)
        w = np.sin(np.pi * p / K) ** 2 * np.exp(tilt * (p - K / 2))
        f = fb * 2 ** p
        w = np.where(f < 15500, w, 0.0)
        ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 2 * np.pi)
        y += w * np.sin(ph)
    return y / 2.2


def shepard_layer() -> np.ndarray:
    rate = 0.10 + 0.62 * u ** 2.2                   # octaves per second, accelerating
    climb = np.cumsum(rate) / SR
    tilt = 0.05 + 0.40 * u ** 1.5                   # brightens as it climbs
    out = np.zeros((CUT_S, 2))
    for ch, dc in enumerate((-4.0, 4.0)):
        out[:, ch] += shepard_stack(0.0, dc, climb, tilt)
    fifth = np.zeros((CUT_S, 2))
    for ch, dc in enumerate((5.0, -5.0)):
        fifth[:, ch] += shepard_stack(7 / 12, dc, climb, tilt)
    fifth_env = np.clip((t_r - 3.4) / 1.6, 0, 1) ** 2
    env = 0.25 + 0.75 * u ** 1.6
    return (out + 0.6 * fifth * fifth_env[:, None]) * env[:, None]


def noise_sweep() -> np.ndarray:
    fc = 250 * (9000 / 250) ** (u ** 1.5)
    q = 1.6 + 2.0 * u
    amp = u ** 2.4
    out = np.stack([svf_bandpass(noise(CUT_S), fc, q), svf_bandpass(noise(CUT_S), fc * 1.05, q)], axis=1)
    air = sos_filter(noise(CUT_S * 2).reshape(CUT_S, 2), "highpass", 6500, order=4)
    air = sos_filter(air, "lowpass", 15000, order=4) * (np.clip((t_r - 4.5) / 2.5, 0, 1) ** 3)[:, None]
    return out * amp[:, None] * 0.9 + air * 0.35


def drone_layer(phi: np.ndarray) -> np.ndarray:
    """Bb3 / F4 / Bb4 additive drone, harmonic roll-off opening with time, tremolo locked to
    the accelerating pulse."""
    fc = 500 * (4500 / 500) ** u                     # time-varying spectral roll-off
    out = np.zeros((CUT_S, 2))
    for j, (m, pan) in enumerate(((58, -0.3), (65, 0.3), (70, 0.0))):
        for cents in (-6, 6):
            f = hz(m) * 2 ** (cents / 1200)
            y = np.zeros(CUT_S)
            for k in range(1, int(14000 // f) + 1):
                a = (1 / k) / (1 + (k * f / fc) ** 2)
                y += a * np.sin(2 * np.pi * k * f * t_r + rng.uniform(0, 2 * np.pi))
            th = (pan + (0.15 if cents > 0 else -0.15) + 1) * np.pi / 4
            out[:, 0] += y * np.cos(th)
            out[:, 1] += y * np.sin(th)
    depth = 0.15 + 0.6 * u
    trem = 1 - depth * (0.5 - 0.5 * np.cos(2 * np.pi * (phi + 0.5)))   # dips between pulses
    env = 0.35 + 0.65 * u ** 1.2
    return out * (trem * env)[:, None] * 0.22


def pulse_hit(rate: float, level: float) -> tuple[np.ndarray, np.ndarray]:
    """One heartbeat pulse: mono low thump on Bb1 (+ octave) and a mid noise chuff."""
    d = min(0.28, 1.2 / rate)
    t = tt(d)
    dec = min(0.06, 0.28 / rate)
    f = BB1 * (1 + 0.9 * np.exp(-t / 0.018))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.35 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    body *= np.exp(-t / dec)
    body = fade(body, a=0.0015, r=min(0.02, d / 4)) * level
    ch = sos_filter(noise(len(t)), "bandpass", [700, 3200], order=2)
    ch *= np.exp(-t / 0.012) * (1 - np.exp(-t / 0.0006))
    ch = fade(ch, a=0.001, r=min(0.02, d / 4)) * level * 0.22
    return body, ch


# ---------------------------------------------------------------- soft low hit
def soft_low_hit() -> np.ndarray:
    d = N / SR - HIT_T
    t = tt(d)
    f = BB1 * (1 + 0.12 * np.exp(-t / 0.05))
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-t / 0.32)
    body = (0.45 * np.sin(2 * ph) * np.exp(-t / 0.22) + 0.18 * np.sin(3 * ph) * np.exp(-t / 0.14)
            + 0.07 * np.sin(5 * ph) * np.exp(-t / 0.08))
    felt = sos_filter(noise(len(t)), "lowpass", 420, order=2) * np.exp(-t / 0.035) * 0.5
    y = sub + body + felt
    att = int(0.006 * SR)
    y[:att] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, att))
    return y * 0.9


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
def render() -> np.ndarray:
    phi = pulse_phase()

    # --- riser buses (0 .. cut)
    tones = shepard_layer()
    nz = noise_sweep()
    drone = drone_layer(phi)

    low = np.zeros((CUT_S, 2))
    mid = np.zeros((CUT_S, 2))
    r0, k = 2.0, 9.0
    n = 0
    while True:
        tn = T * np.log(1 + n * np.log(k) / (r0 * T)) / np.log(k)   # phi(tn) = n
        if tn >= T - 0.004:
            break
        rate = r0 * k ** (tn / T)
        lev = 0.45 + 0.55 * (tn / T) ** 1.3
        body, ch = pulse_hit(rate, lev)
        place(low, body, tn, 0.85)
        place(mid, ch, tn, 1.0, pan=0.25 * (-1) ** n)
        n += 1

    hp = lambda x, f=130: sos_filter(x, "highpass", f, order=4)
    tones = hp(tones, 125)
    nz = hp(nz, 180)
    drone = hp(drone, 140)
    mid = hp(mid, 300)
    send = tones * 0.5 + drone * 0.6 + nz * 0.25
    wet = hp(reverb(send, rt60=1.6, band=(250, 7000)), 200) * 0.32
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    low = sos_filter(low, "lowpass", 400, order=2)

    riser = low * 0.9 + tones * 0.85 + nz * 0.55 + drone * 1.0 + mid * 0.9 + wet
    riser = sos_filter(riser, "highpass", 25, order=2)
    riser = sos_filter(riser, "lowpass", 16500, order=4)

    # final pre-cut push: +3 dB over the last half second
    push = 1 + 0.4 * np.clip((t_r - 6.5) / 0.5, 0, 1) ** 2
    riser *= push[:, None]
    # the cut: 1.5 ms raised-cosine ending exactly on the cue sample; fade-in at the start
    nf = int(0.0015 * SR)
    riser[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf + 1)[1:]))[:, None]
    ni = int(0.25 * SR)
    riser[:ni] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, ni)))[:, None]

    # --- after the cut: silence, then the soft low hit (mono below 120 Hz) in a small dark room
    hit = soft_low_hit()
    hit_bus = np.zeros((N, 2))
    place(hit_bus, hit, HIT_T)
    hit_hi = sos_filter(hit_bus, "highpass", 140, order=2)
    room = sos_filter(reverb(hit_hi, rt60=0.9, band=(150, 1800), predelay=0.01), "lowpass", 2500, order=2) * 0.35
    room[: int(HIT_T * SR)] = 0.0
    post = hit_bus + room
    post = sos_filter(post, "highpass", 25, order=2)
    post[: int(HIT_T * SR)] = 0.0                 # filters are causal; nothing before the hit

    mix = np.zeros((N, 2))
    mix[:CUT_S] = riser
    mix += post

    # mono-ize below 120 Hz (M/S high-pass on the side channel), per section so nothing leaks over the cut
    for a, b in ((0, CUT_S), (CUT_S, N)):
        m_, s_ = (mix[a:b, 0] + mix[a:b, 1]) / 2, (mix[a:b, 0] - mix[a:b, 1]) / 2
        s_ = sos_filter(s_, "highpass", 120, order=4)
        mix[a:b] = np.stack([m_ + s_, m_ - s_], axis=1)
    mix[CUT_S:int(HIT_T * SR)] = 0.0

    # last 0.25 s cosine tail-out so the final sample is silent
    nt = int(0.25 * SR)
    mix[-nt:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nt)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    y[CUT_S:int(HIT_T * SR)] = 0.0                # the limiter's smoothing must not smear the cut
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
