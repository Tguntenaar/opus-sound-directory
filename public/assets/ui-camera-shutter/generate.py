"""ui-camera-shutter: Opus Sound Directory

A 0.5-second synthesised DSLR shutter, crisp and mechanical with no musical tone. On frame 0 the
mirror flips up with a hard clack: a sharp grit transient over damped, inharmonic metal-and-polymer
body modes, a small mono thud and a tiny mirror bounce 6 ms later. The focal-plane curtains then
run as a short whirr: two quick, grainy swipes of band-passed noise, chopped by an irregular gear
ratchet whose filter sweeps upward as each curtain crosses the frame. At 125 ms the mirror drops
back with a second clack, a little lower and heavier than the first. A tiny return spring then
rattles: six to seven quick metallic ticks that bounce closer together and quieter, each ringing
for only a few milliseconds so no pitch forms. A small, close room keeps it tight. Everything has
settled by about 0.33 s, and the last 60 ms fade to silence.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 50502
DURATION_SEC = 0.5
BPM = None
KEY = "atonal"
FPS = 30
CUE_FRAMES = (0,)               # frame 0: mirror-up clack
TARGET_LUFS = -17.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
CURTAIN_1 = 0.024               # first curtain starts after the mirror has settled
CURTAIN_2 = 0.068               # second curtain closes the exposure
MIRROR_DOWN = 0.125             # mirror return clack
SPRING_T = 0.147                # return spring starts to rattle

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Short raised-cosine attack/release so nothing starts or stops with a click."""
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    x[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
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


def svf_bandpass(x: np.ndarray, fc: np.ndarray, q: float) -> np.ndarray:
    """TPT state-variable band-pass with a per-sample cutoff (short segments only)."""
    g = np.tan(np.pi * np.clip(fc, 20, 0.45 * SR) / SR)
    k = 1.0 / q
    ic1 = ic2 = 0.0
    out = np.empty_like(x)
    for n in range(len(x)):
        gn = g[n]
        a1 = 1.0 / (1.0 + gn * (gn + k))
        v1 = a1 * ic1 + gn * a1 * (x[n] - ic2)
        v2 = ic2 + gn * v1
        ic1, ic2 = 2 * v1 - ic1, 2 * v2 - ic2
        out[n] = v1
    return out * k


def soft_sat(x: np.ndarray, drive: float) -> np.ndarray:
    """Band-limited tanh saturation (4x oversampled, then decimated with scipy's anti-alias
    FIR). Used to round off the coincident peak of a clack's modes so it reads hard and dense
    without the limiter having to squash it."""
    up = signal.resample_poly(x, 4, 1)
    return signal.resample_poly(np.tanh(drive * up) / drive, 1, 4)[: len(x)]


# ---------------------------------------------------------------- voices
def clack(modes, grit_band, grit_decay: float, thud_hz: float, thud_amp: float,
          bounce_t: float = 0.006, dur: float = 0.06):
    """Mirror slap: a 0.5 ms raised-cosine onset into band-passed grit, damped inharmonic body
    modes, and a tiny mirror bounce. Returns (high part, mono thud) so the thud can stay centred."""
    t = tt(dur)
    grit = sos_filter(noise(dur), "bandpass", grit_band, order=2)
    grit /= np.std(grit[:240]) * 3 + 1e-9
    hi = grit * np.exp(-t / grit_decay)
    for f, amp, dec in modes:
        hi += amp * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / dec)
    # bounce: the same grit, quieter and shorter, a few ms later
    nb = int(bounce_t * SR)
    tb = t[: len(t) - nb]
    bounce = sos_filter(noise(dur)[: len(tb)], "bandpass", grit_band, order=2)
    bounce /= np.std(bounce[:240]) * 3 + 1e-9
    bounce *= 0.35 * np.exp(-tb / (grit_decay * 0.6)) * (1 - np.exp(-tb / 0.0004))
    hi[nb:] += bounce
    hi = soft_sat(hi, 1.6)
    na = int(0.0005 * SR)
    hi[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    hi = fade(hi, a=0.0005, r=0.008)
    f = thud_hz * (1 + 0.25 * np.exp(-t / 0.004))
    thud = thud_amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.011) * (1 - np.exp(-t / 0.0008))
    return hi, fade(thud, a=0.0005, r=0.01)


def curtain(dur: float, f_lo: float, f_hi: float) -> np.ndarray:
    """One curtain swipe: noise through a band-pass sweeping f_lo -> f_hi, chopped by an
    irregular gear ratchet (jittered tick train ~1.1-1.6 kHz, so it never forms a pitch)."""
    t = tt(dur)
    n = len(t)
    # irregular ratchet: tick times with +-40 % jitter on a rate that speeds up through the swipe
    ticks = np.zeros(n)
    pos = 0.0
    while pos < dur:
        rate = 1100 + 500 * pos / dur
        pos += (1.0 / rate) * rng.uniform(0.6, 1.4)
        i = int(pos * SR)
        if i < n:
            ticks[i] = rng.uniform(0.5, 1.0)
    # each ratchet tick opens a ~0.35 ms grain
    grain = np.exp(-np.arange(int(0.0018 * SR)) / (0.00035 * SR))
    chop = np.convolve(ticks, grain)[:n]
    fc = f_lo * (f_hi / f_lo) ** (t / dur)
    swish = svf_bandpass(noise(dur), fc, q=1.4)
    grains = svf_bandpass(noise(dur), fc * 1.3, q=2.0) * chop
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    y = (0.45 * swish / (np.std(swish) + 1e-9) + 0.8 * grains / (np.std(grains) + 1e-9)) * env
    return fade(y, a=0.002, r=0.004)


def spring_tick(dur: float = 0.03) -> np.ndarray:
    """One rattle of a tiny steel return spring: a short grit tick and a few damped inharmonic
    modes (a few ms each, randomly detuned per hit) so the rattle reads as metal, not as a note."""
    t = tt(dur)
    y = sos_filter(noise(dur), "bandpass", [2500, 9000], order=2)
    y = y / (np.std(y[:96]) * 3 + 1e-9) * np.exp(-t / 0.0008)
    for f, amp, dec in ((3310, 0.55, 0.006), (5140, 0.40, 0.0045), (7420, 0.25, 0.003), (8930, 0.15, 0.002)):
        f *= rng.uniform(0.94, 1.06)
        y += amp * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / dec)
    y *= 1 - np.exp(-t / 0.00025)
    return fade(y, a=0.0003, r=0.005)


def room(x: np.ndarray, rt60: float = 0.14, predelay: float = 0.002) -> np.ndarray:
    """Small, close room: decorrelated stereo exponential-noise IR, band-limited."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [300, 6500]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


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
    starts = range(0, len(y) - blk + 1, hop)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in starts])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    os = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os)) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 1.5, rel_ms: float = 12.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. Held over the
    look-ahead window, one-pole release, edge-safe box smoothing; it never clips the waveform."""
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
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3          # margin for dither + inter-sample
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    mech = np.zeros((N, 2))
    low = np.zeros((N, 2))
    send = np.zeros((N, 2))

    # mirror up (frame 0): the loudest, brightest event
    up_hi, up_thud = clack([(1180, 0.50, 0.008), (2730, 0.40, 0.007), (4310, 0.30, 0.0048),
                            (6870, 0.18, 0.0028)], [900, 9000], 0.0032, 175, 0.40)
    place(mech, up_hi, 0.0, 1.0, pan=-0.06)
    place(send, up_hi, 0.0, 0.30, pan=-0.06)
    place(low, up_thud, 0.0, 1.0)

    # curtains: two grainy swipes, the second one starting a touch higher and panned the other way
    c1 = curtain(0.040, 2600, 5200)
    c2 = curtain(0.044, 3000, 6200)
    place(mech, c1, CURTAIN_1, 0.13, pan=-0.20)
    place(mech, c2, CURTAIN_2, 0.14, pan=0.20)
    place(send, c1, CURTAIN_1, 0.06, pan=-0.20)
    place(send, c2, CURTAIN_2, 0.06, pan=0.20)

    # mirror down: lower, heavier, a little less bright
    dn_hi, dn_thud = clack([(1010, 0.55, 0.009), (2390, 0.40, 0.008), (3720, 0.28, 0.005),
                            (5910, 0.15, 0.003)], [700, 7500], 0.0036, 150, 0.38)
    place(mech, dn_hi, MIRROR_DOWN, 0.50, pan=0.05)
    place(send, dn_hi, MIRROR_DOWN, 0.28, pan=0.05)
    place(low, dn_thud, MIRROR_DOWN, 1.0)

    # return spring: bouncing ticks, intervals and levels shrinking
    t = SPRING_T
    gaps = (0.021, 0.016, 0.0125, 0.010, 0.008, 0.0065)
    amp = 0.26
    for i in range(len(gaps) + 1):
        place(mech, spring_tick(), t, amp, pan=0.25 * rng.uniform(-1, 1))
        place(send, spring_tick(), t, amp * 0.3)
        if i < len(gaps):
            t += gaps[i] * rng.uniform(0.92, 1.08)
            amp *= 0.72

    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    wet = room(send) * 0.30
    mix = mech + low + wet
    mix = sos_filter(mix, "lowpass", 11000, order=4)             # crisp, never fizzy
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 300, order=6)            # low end strictly centred
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 90, order=4)               # DC / sub: a shutter has no low end

    # 60 ms cosine tail-out so the last sample is exactly silent
    nf = int(0.06 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    y -= y.mean(axis=0)            # constant per-channel offset left by the limiter on the thuds
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
