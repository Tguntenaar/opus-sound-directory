"""logo-sting-dark-cinematic: Opus Sound Directory

A 4-second ominous logo reveal centred on low D. On frame 0 a dull low knock opens
a mono sub rumble on D1 that slowly swells, while a metallic scrape (stick-slip
friction exciting an inharmonic resonator bank, sliding across the stereo field)
grinds and squeals above it, with a second, harder scrape taking over at 1.0 s.
From 1.05 s a reverse cymbal pulls the air in, rising to a sharp stop 45 ms before
the hit and leaving a short vacuum. On frame 75 (2.5 s) a massive low brass-like
braam lands: a D minor stack (D1 D2 A2 D3 F3 A3) of detuned band-limited saws whose
resonant low-pass snaps open and slowly closes, with a pitch bend up into the note,
a sub knock and a short crack on the attack. A long, dark hall tail then rolls the
braam down to silence. Only the sub, the knocks and the braam's low partials sit
below 120 Hz, and they are mono.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 620075
DURATION_SEC = 4
BPM = None
KEY = "D minor (low D1 braam)"
FPS = 30
CUE_FRAMES = (0, 75)           # frame 0: rumble + scrape in; frame 75 (2.5 s): braam reveal
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
HIT_T = CUE_FRAMES[1] / FPS    # 2.5 s
HIT_S = int(round(HIT_T * SR)) # 120000
VACUUM = 0.045                 # gap between the reverse-cymbal stop and the braam

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Raised-cosine attack/release so nothing starts or stops with a click."""
    x = x.copy()
    sh = (-1,) + (1,) * (x.ndim - 1)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))).reshape(sh)
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))).reshape(sh)
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


def noise(n: int) -> np.ndarray:
    return rng.standard_normal(n)


def smooth_random(n: int, rate_hz: float) -> np.ndarray:
    """Band-limited random wander in roughly [-1, 1] (low-passed noise, normalised)."""
    y = sos_filter(noise(n + SR), "lowpass", rate_hz, order=2)[SR:]
    return y / (np.abs(y).max() + 1e-12)


def reverb(x: np.ndarray, rt60: float, predelay: float, band=(120, 3500)) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (dark hall)."""
    t = tt(rt60 * 1.15)
    env = np.exp(-6.9 * t / rt60) * (1 - np.exp(-t / 0.03))
    irs = []
    for _ in range(2):
        ir = sos_filter(noise(len(t)), "bandpass", list(band)) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


# ---------------------------------------------------------------- intro voices
def sub_rumble(dur: float) -> np.ndarray:
    """Mono D1 sub: two slightly detuned sines (slow beating) + low-passed noise, swelling."""
    t = tt(dur)
    f = hz(26)
    drift = 1 + 0.004 * smooth_random(len(t), 0.7)
    ph = 2 * np.pi * np.cumsum(f * drift) / SR
    tone = np.sin(ph) + 0.6 * np.sin(ph * 1.0075 + 1.1) + 0.22 * np.sin(2 * ph + 0.4)
    nz = sos_filter(noise(len(t)), "bandpass", [24, 70], order=2)
    nz /= np.abs(nz).max()
    swell = 0.25 + 0.75 * (t / dur) ** 1.5
    wob = 1 + 0.18 * smooth_random(len(t), 2.5)
    y = (0.55 * tone + 0.9 * nz) * swell * wob
    return fade(y, a=0.001, r=0.04)


def growl(dur: float) -> np.ndarray:
    """Stereo low-mid grit (130-420 Hz noise) with an uneven, grinding amplitude."""
    t = tt(dur)
    out = np.stack([sos_filter(noise(len(t)), "bandpass", [130, 420], order=2) for _ in range(2)], 1)
    grind = np.clip(0.55 + 0.6 * smooth_random(len(t), 9.0), 0.1, None)
    env = (0.25 + 0.75 * (t / dur) ** 2)[:, None] * grind[:, None]
    return fade(out * env, a=0.001, r=0.04)


def knock(dur: float = 0.6) -> np.ndarray:
    """Dull low knock: pitch-dropping sine 85 Hz -> D1 plus a felt-like low noise burst."""
    t = tt(dur)
    f = hz(26) + (85 - hz(26)) * np.exp(-t / 0.05)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / 0.22)
    y += 0.5 * sos_filter(noise(len(t)), "lowpass", 600, order=2) * np.exp(-t / 0.02)
    return fade(y, a=0.001, r=0.1)


def metal_modes(f0: float):
    """Inharmonic free-bar / plate-like mode ratios with falling gain and rising Q."""
    ratios = (1.0, 2.32, 3.87, 5.41, 6.93, 8.79, 11.04, 13.6)
    return [(f0 * r, 1.0 / (1 + 0.35 * i), 60 + 25 * i) for i, r in enumerate(ratios) if f0 * r < 12000]


def scrape(dur: float, f0: float, rate0: float, rate1: float, pressure: np.ndarray,
           pan_from: float, pan_to: float) -> np.ndarray:
    """Metal scrape: jittered stick-slip noise bursts through a resonant inharmonic mode bank,
    swept across the stereo field."""
    n = int(round(dur * SR))
    t = np.arange(n) / SR
    rate = (rate0 + (rate1 - rate0) * t / dur) * (1 + 0.3 * smooth_random(n, 6.0))
    frac = np.cumsum(rate) / SR % 1.0
    slip = np.exp(-frac / 0.18)                       # burst at each slip, decays until the next stick
    slip = sos_filter(slip, "lowpass", 900, order=2)  # soften the per-cycle edges
    exc = noise(n) * (0.25 + slip) * pressure
    exc = sos_filter(exc, "highpass", 300, order=2)
    y = np.zeros(n)
    for f, g, q in metal_modes(f0):
        f_glide = f * (1 + 0.004 * smooth_random(1, 1.0)[0])
        b, a = signal.iirpeak(f_glide, q, fs=SR)
        y += g * signal.lfilter(b, a, exc)
    grit = sos_filter(exc, "bandpass", [1800, 7000], order=2) * 0.05
    y = y + grit
    y = fade(y / (np.abs(y).max() + 1e-12), a=0.001, r=0.06)
    pan = np.linspace(pan_from, pan_to, n)
    th = (pan + 1) * np.pi / 4
    return np.stack([y * np.cos(th), y * np.sin(th)], axis=1) * np.sqrt(2)


def cymbal(dur: float) -> np.ndarray:
    """Forward crash: dense inharmonic partials + bright noise, both decaying (stereo)."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for ch in range(2):
        freqs = np.exp(rng.uniform(np.log(2800), np.log(11000), 70))
        y = np.zeros(len(t))
        for f in freqs:
            dec = 0.25 + 0.9 * rng.uniform() * (3000 / f)
            y += np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / dec)
        y /= np.sqrt(len(freqs))
        nz = sos_filter(noise(len(t)), "bandpass", [3500, 13000], order=2) * np.exp(-t / 0.45)
        y = 0.6 * y + 1.1 * nz
        y = sos_filter(y, "lowpass", 12500, order=4)
        out[:, ch] = y * (1 - np.exp(-t / 0.002))
    return out


def reverse_cymbal(dur: float) -> np.ndarray:
    y = cymbal(dur)[::-1].copy()
    y = sos_filter(y, "highpass", 900, order=2)
    return fade(y, a=0.05, r=0.003)                    # <=3 ms stop into the vacuum


# ---------------------------------------------------------------- the braam
BRAAM_NOTES = ((26, 1.00, 0.0), (38, 0.85, 0.0), (45, 0.55, -0.35), (50, 0.55, 0.35),
               (53, 0.32, -0.5), (57, 0.30, 0.5))     # (midi, amp, pan): D1 D2 A2 D3 F3 A3
DETUNE_CENTS = (-11.0, 0.0, 10.0)


def lp_mag(f: np.ndarray, fc: np.ndarray, q: float) -> np.ndarray:
    """Magnitude of a 2-pole resonant low-pass (analytic), used to weight additive partials."""
    r = f / fc
    return 1.0 / np.sqrt((1 - r * r) ** 2 + (r / q) ** 2)


def braam(dur: float) -> np.ndarray:
    """Brass-like braam: band-limited (additive) detuned saws with a resonant filter swell."""
    t = tt(dur)
    n = len(t)
    # filter envelope: snaps open in ~70 ms, blooms, then slowly closes (dark)
    fc = (140 + 2100 * (1 - np.exp(-t / 0.035)) * np.exp(-t / 0.55) + 260 * np.exp(-t / 2.0))
    bend = 2 ** ((-45 * np.exp(-t / 0.06)) / 1200)    # pitch scoops up into the note
    amp = (1 - np.exp(-t / 0.006)) * (0.55 + 0.45 * np.exp(-t / 0.35)) * np.exp(-t / 0.8)
    growl_am = 1 + 0.07 * np.sin(2 * np.pi * 31 * t) * np.exp(-t / 0.4)
    out = np.zeros((n, 2))
    for midi, a_note, pan in BRAAM_NOTES:
        for j, cents in enumerate(DETUNE_CENTS):
            f0 = hz(midi) * 2 ** (cents / 1200)
            drift = 1 + 0.0015 * smooth_random(n, 1.5)
            ph = 2 * np.pi * np.cumsum(f0 * bend * drift) / SR + rng.uniform(0, 2 * np.pi)
            y = np.zeros(n)
            kmax = int(7500 // f0)
            for k in range(1, kmax + 1):
                y += np.sin(k * ph) / k * lp_mag(k * f0, fc, 2.2)
            p = np.clip(pan + (j - 1) * 0.45, -1, 1)
            th = (p + 1) * np.pi / 4
            out[:, 0] += a_note * y * np.cos(th)
            out[:, 1] += a_note * y * np.sin(th)
    out *= (amp * growl_am)[:, None] / len(DETUNE_CENTS)
    return fade(out, a=0.0005, r=0.3)


def braam_sub(dur: float) -> np.ndarray:
    """Mono D1 sine under the braam with a short pitch-dropping knock on the attack."""
    t = tt(dur)
    f = hz(26) * (1 + 1.2 * np.exp(-t / 0.03))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.65)
    return fade(y, a=0.0005, r=0.3)


def crack(dur: float = 0.12) -> np.ndarray:
    t = tt(dur)
    y = sos_filter(noise(len(t)), "bandpass", [700, 7000], order=2) * np.exp(-t / 0.007)
    y += 0.8 * sos_filter(noise(len(t)), "bandpass", [150, 600], order=2) * np.exp(-t / 0.04)
    return fade(y, a=0.0004, r=0.02)


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 60.0) -> np.ndarray:
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
    g = uniform_filter1d(g, size=L + 1, mode="nearest")  # edge-safe smoothing
    return x * g[:, None]


def master(mix: np.ndarray) -> np.ndarray:
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.4
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        y = sos_filter(y, "highpass", 18, order=2)      # block limiter DC on the asymmetric sub
        y = soft_limiter(y, ceiling)
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y - y.mean(axis=0, keepdims=True)             # constant per-channel DC trim


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    low = np.zeros((N, 2))      # mono sub material (rumble, knocks, braam sub)
    intro = np.zeros((N, 2))    # growl, scrapes, reverse cymbal
    hit = np.zeros((N, 2))      # braam + crack
    send = np.zeros((N, 2))     # hall send for the hit
    isend = np.zeros((N, 2))    # hall send for the intro (ducked out before the vacuum)

    # --- frame 0: knock + rumble + first scrape, all starting on sample 0
    pre_end = HIT_T - VACUUM
    place(low, knock(), 0.0, 0.5)
    place(low, sub_rumble(pre_end), 0.0, 0.36)
    place(intro, growl(pre_end), 0.0, 0.10)

    n1 = int(1.55 * SR)
    t1 = np.arange(n1) / SR
    p1 = (np.exp(-t1 / 0.08) * 0.45 + 0.55 * (1 - np.exp(-t1 / 0.3))) * np.exp(-np.clip(t1 - 0.9, 0, None) / 0.25)
    s1 = scrape(1.55, 610.0, 38.0, 70.0, p1, -0.7, 0.2)
    place(intro, s1, 0.0, 0.2)
    place(isend, s1, 0.0, 0.22)

    n2 = int((pre_end - 1.0) * SR)
    t2 = np.arange(n2) / SR
    p2 = (1 - np.exp(-t2 / 0.12)) * (0.5 + 0.5 * (t2 / t2[-1]) ** 1.5) * np.exp(-np.clip(t2 - 1.15, 0, None) / 0.12)
    s2 = scrape(pre_end - 1.0, 870.0, 60.0, 130.0, p2, 0.6, -0.3)
    place(intro, s2, 1.0, 0.17)
    place(isend, s2, 1.0, 0.25)

    # --- reverse cymbal pull, stopping 45 ms before the hit
    rc_start = 1.05
    place(intro, reverse_cymbal(pre_end - rc_start), rc_start, 0.1)

    # --- frame 75: braam
    tail = DURATION_SEC - HIT_T
    b = braam(tail)
    place(hit, b, HIT_T, 1.0)
    place(send, b, HIT_T, 0.7)
    place(low, braam_sub(tail), HIT_T, 0.8)
    c = crack()
    place(hit, np.stack([c, c], 1), HIT_T, 0.45)
    place(send, np.stack([c, c], 1), HIT_T, 0.3)

    intro = sos_filter(intro, "highpass", 140, order=4)
    wet = sos_filter(reverb(send, rt60=3.0, predelay=0.03), "highpass", 150, order=4)
    iwet = sos_filter(reverb(isend, rt60=1.8, predelay=0.02), "highpass", 150, order=4)
    t = np.arange(N) / SR
    d0, d1 = HIT_T - 0.25, HIT_T - VACUUM - 0.005      # intro hall pulled out into the vacuum
    duck = np.where(t < d0, 1.0, np.where(t > d1, 0.0, 0.5 + 0.5 * np.cos(np.pi * (t - d0) / (d1 - d0))))
    wet = wet + iwet * duck[:, None]
    wet = sos_filter(wet, "lowpass", 3800, order=2) * 0.7
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    low = sos_filter(low, "lowpass", 220, order=2)

    mix = low + 0.8 * intro + hit + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 20, order=2)
    mix = sos_filter(mix, "lowpass", 15000, order=4)

    nf = int(0.45 * SR)
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
