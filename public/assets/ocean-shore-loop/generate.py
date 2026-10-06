"""ocean-shore-loop: Opus Sound Directory

A 24-second seamless shoreline loop: three synthesised waves of different size
roll in, build and break, about eight seconds apart. Each one is a noise swell
whose low-pass opens as it rises, a feathering hiss along the lip, a bright crash
that travels across the stereo field as the wave breaks along the beach, then a
shhh of white water running up the sand with crackling foam fizz and hundreds of
tiny rising bubble pops, and finally a soft receding backwash. Under them sit a
distant surf roar and a light, gusting wind whose whistle drifts in pitch. Far
off to the right a bell buoy in Eb rocks on the swell: a bronze bell (hum, prime,
minor-third tierce, quint, nominal) whose strikes come in uneven clusters,
blurred by distance and wind. The bell strikes at frame 0, the loop top. The
noise layers are built as spectral envelopes over a circular overlap-add, and
the events are rendered circularly: three identical cycles with tails, reverb
and a wrap-mode limiter running across them, keeping the middle one, so the last
sample flows straight back into the first with no fade. Only the mono surf
rumble sits below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 152406
DURATION_SEC = 24
BPM = None
KEY = "Eb (bell buoy over noise)"
FPS = 30
CUE_FRAMES = (0,)              # loop top: a bell-buoy strike on sample 0
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR          # one loop cycle
CYC = 3                        # cycles rendered; the middle one is kept
L3 = CYC * N
NFFT, HOP = 1024, 256          # spectral-envelope noise synthesis (N is a multiple of HOP)
F = N // HOP
DEBUG = bool(os.environ.get("OCEAN_DEBUG"))

rng = np.random.default_rng(SEED)

FREQ = np.fft.rfftfreq(NFFT, 1 / SR)[None, :]              # (1, K)
FS = np.maximum(FREQ, 1.0)
TK = ((np.arange(F) * HOP + NFFT / 2) / SR)[:, None]       # frame-centre loop times (F, 1)
WIN = np.hanning(NFFT + 1)[:-1]                             # periodic Hann: sum of squares at 75 % overlap = 1.5
OLA_IDX = (np.arange(F)[:, None] * HOP + np.arange(NFFT)[None, :]) % N


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


def pan_gains(p):
    th = (np.asarray(p) + 1) * np.pi / 4
    return np.cos(th) * np.sqrt(2), np.sin(th) * np.sqrt(2)


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a snippet into the 3-cycle bus at loop time t, once per cycle, so every
    event (and its tail) repeats identically and wraps across the loop point."""
    if x.ndim == 1:
        gl, gr = pan_gains(pan)
        x = np.stack([x * gl, x * gr], axis=1)
    t = t % DURATION_SEC
    for k in range(CYC):
        s = int(round(t * SR)) + k * N
        if s >= len(bus):
            continue
        e = min(len(bus), s + len(x))
        bus[s:e] += gain * x[: e - s]


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


# ---------------------------------------------------------------- spectral shapes (vectorised over frames)
def lp(fc, n=2):
    return 1 / np.sqrt(1 + (FS / fc) ** (2 * n))


def hp(fc, n=2):
    return 1 / np.sqrt(1 + (fc / FS) ** (2 * n))


def pink(slope=0.5):
    return (FS / 500.0) ** (-slope) * hp(25, 2)


def bump(fc, octaves, gain):
    return 1 + gain * np.exp(-0.5 * (np.log2(FS / fc) / octaves) ** 2)


def resonant(fc, qf):
    return 1 / np.sqrt(1 + qf ** 2 * (FS / fc - fc / FS) ** 2)


def wrap_dt(t0: float) -> np.ndarray:
    """Circular time since t0, in [-12, 12) s, per frame."""
    h = DURATION_SEC / 2
    return (TK - t0 + h) % DURATION_SEC - h


def lfo(cycles: int, phase: float = 0.0) -> np.ndarray:
    """Per-frame sine with an integer number of cycles per loop."""
    return np.sin(2 * np.pi * cycles * TK / DURATION_SEC + phase)


def crackle(sigma: float) -> np.ndarray:
    """Per-frame random gain (~5 ms grains), unit mean power: granular foam texture."""
    g = np.minimum(rng.lognormal(0.0, sigma, (F, 1)), 3.0)     # cap the rare loud grain
    return g / np.sqrt(np.mean(g ** 2))


def ola(spec: np.ndarray) -> np.ndarray:
    """Circular overlap-add of random-phase frames: an exactly N-periodic signal whose
    short-time spectrum follows |spec|. Unit-magnitude spectra give unit variance."""
    fr = np.fft.irfft(spec, n=NFFT, axis=1) * WIN * np.sqrt(NFFT / 1.5)
    return np.bincount(OLA_IDX.ravel(), weights=fr.ravel(), minlength=N)


def render_noise(P_L: np.ndarray, P_R: np.ndarray, rho: float = 0.35) -> np.ndarray:
    """Turn per-channel power envelopes (F, K) into one stereo cycle of shaped noise,
    partially correlated between L and R."""
    shape = P_L.shape
    z1 = (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)) / np.sqrt(2)
    z2 = (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)) / np.sqrt(2)
    zr = rho * z1 + np.sqrt(1 - rho ** 2) * z2
    return np.stack([ola(np.sqrt(P_L) * z1), ola(np.sqrt(P_R) * zr)], axis=1)


# ---------------------------------------------------------------- waves, surf, wind
WAVES = (  # break time (s), size, swell time (s), crash pan start -> end
    (3.1, 1.0, 3.4, -0.55, 0.35),
    (11.0, 1.25, 3.9, 0.55, -0.35),
    (18.7, 0.85, 3.0, -0.15, 0.6),
)


def wave_power(tb, A, Ts, p0, p1):
    """Power envelopes (L, R) for one wave: swell, lip hiss, crash, wash, fizz, backwash."""
    dt = wrap_dt(tb)
    pos = dt >= 0
    zero = np.zeros_like(dt)
    PL = np.zeros((F, FREQ.shape[1]))
    PR = np.zeros_like(PL)

    def add(amp, shape, pan):
        gl, gr = pan_gains(pan)
        nonlocal PL, PR
        p = (amp * shape) ** 2
        PL += p * gl ** 2
        PR += p * gr ** 2

    # swell: rises with an opening low-pass, then sinks under the crash
    u = np.clip((dt + Ts) / Ts, 0, 1)
    a_sw = np.where(pos, 0.55 * np.exp(-dt / 0.5), 0.55 * u ** 2)
    fc_sw = np.where(pos, np.maximum(220, 1100 * np.exp(-dt / 0.8)), 160 * (1100 / 160) ** u)
    add(A * a_sw, pink(0.6) * lp(fc_sw, 2), 0.5 * p0)
    # lip feathering just before the break
    a_lip = np.where(pos, np.exp(-dt / 0.15), np.exp(np.maximum(dt, -6) / 0.35)) * 0.16
    add(A * a_lip, hp(2200, 2) * lp(7000, 2), p0)
    # crash: bright, travelling across the stereo field
    a_cr = np.where(pos, (1 - np.exp(-np.maximum(dt, 0) / 0.07)) ** 1.5 * np.exp(-dt / 1.1), zero)
    fc_cr = 900 + 7500 * np.exp(-np.maximum(dt, 0) / 0.7)
    pan_cr = p0 + (p1 - p0) * np.clip(dt / 1.6, 0, 1)
    add(A * a_cr, pink(0.45) * lp(fc_cr, 2) * lp(12000, 3) * hp(60, 1) * bump(500, 0.7, 0.8), pan_cr)
    # white-water wash running up the sand
    a_wa = np.where(pos, 0.6 * (1 - np.exp(-np.maximum(dt, 0) / 0.45)) * np.exp(-dt / 2.0), zero)
    fc_wa = 7000 - 3500 * (1 - np.exp(-np.maximum(dt, 0) / 2.0))
    add(A * a_wa, hp(600, 2) * lp(fc_wa, 2) * pink(0.25), 0.3 * p1)
    # foam fizz: granular high band, independent grain gains per channel
    a_fz = np.where(pos, 0.42 * (1 - np.exp(-np.maximum(dt, 0) / 0.35)) * np.exp(-dt / 2.6), zero)
    shp = hp(3000, 3) * lp(11000, 4)
    PL += (A * a_fz * crackle(0.7) * shp) ** 2
    PR += (A * a_fz * crackle(0.7) * shp) ** 2
    # backwash: soft receding hiss with a pebbly grain
    a_bw = 0.2 * np.exp(-0.5 * ((dt - 4.6) / 1.1) ** 2)
    fc_bw = 6500 - 3000 * np.clip((dt - 3.5) / 2.5, 0, 1)
    add(A * a_bw * crackle(0.5), hp(1400, 2) * lp(fc_bw, 2), -0.4 * p1)
    return PL, PR


def bed_power():
    """Distant surf roar, far shore hiss and a light gusting wind."""
    PL = np.zeros((F, FREQ.shape[1]))
    PR = np.zeros_like(PL)
    roar = 0.2 * (1 + 0.15 * lfo(3, 0.4)) * pink(0.7) * lp(450, 2) * hp(40, 2)
    PL += roar ** 2
    PR += roar ** 2
    far = 0.045 * (1 + 0.2 * lfo(2, 2.0)) * hp(1000, 2) * lp(6000, 2)
    PL += far ** 2
    PR += far ** 2
    gust = np.maximum(0.2, 1 + 0.45 * lfo(2, 0.3) + 0.25 * lfo(5, 2.0))
    fcw = 650 * 2 ** (0.5 * lfo(2, 0.6) + 0.25 * lfo(7, 0.0))
    wind = 0.06 * gust * (resonant(fcw, 3.0) + 0.25 * hp(300, 2) * lp(3000, 2)) * hp(150, 2)
    gl, gr = pan_gains(0.45 * lfo(1, 0.9))
    PL += wind ** 2 * gl ** 2
    PR += wind ** 2 * gr ** 2
    return PL, PR


# ---------------------------------------------------------------- foam bubbles
def bubble(f0: float, dur: float, rise: float) -> np.ndarray:
    """A Minnaert-style bubble: a damped sine whose pitch rises as it decays."""
    t = tt(dur)
    f = f0 * (1 + rise * t / dur)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (dur / 4))
    return fade(y, a=0.0005, r=0.002)


# ---------------------------------------------------------------- bell buoy
BELL = ((0.25, 0.12, 4.5), (0.5, 0.35, 3.2), (0.6, 0.5, 2.4), (0.75, 0.2, 1.8), (1.0, 1.0, 2.6),
        (1.5, 0.32, 1.2), (2.0, 0.22, 0.8), (2.5, 0.12, 0.5), (3.0, 0.07, 0.35))


def bell(nominal: float, vel: float) -> np.ndarray:
    """Bronze bell: hum, prime, tierce (minor third), quint, nominal and upper partials,
    the prime and nominal doubled 0.5 Hz apart for a slow warble, plus a clapper tink."""
    dur = 5.5
    t = tt(dur)
    y = np.zeros(len(t))
    for r, a, tau in BELL:
        f = nominal * r
        ph = rng.uniform(0, 2 * np.pi)
        tau_v = tau * (0.85 + 0.15 * vel)
        y += a * np.sin(2 * np.pi * f * t + ph) * np.exp(-t / tau_v)
        if r in (0.5, 1.0):
            y += 0.5 * a * np.sin(2 * np.pi * (f + 0.5) * t + ph + 1.0) * np.exp(-t / tau_v)
    tink = sos_filter(noise(dur), "bandpass", [1500, 5000]) * np.exp(-t / 0.004) * 0.6
    y = fade((y * (0.6 + 0.4 * vel) + tink * vel), a=0.001, r=0.4)
    return sos_filter(y, "lowpass", 3200, order=2)


def open_air_ir(length: float = 1.6) -> np.ndarray:
    """Outdoor diffusion: a few water/shore reflections and a thin, fast tail."""
    t = tt(length)
    irs = []
    for c in range(2):
        tail = sos_filter(rng.standard_normal(len(t)), "bandpass", [300, 3000]) * np.exp(-6.9 * t / 1.3)
        tail *= (1 - np.exp(-t / 0.05)) * 0.25
        ir = tail.copy()
        ir[0] += 1.0
        for d, g in ((0.11, 0.45), (0.23, 0.3), (0.41, 0.2), (0.63, 0.12)):
            ir[int((d + 0.013 * c) * SR)] += g
        irs.append(ir)
    nrm = np.sqrt(np.sum(irs[0] ** 2))
    return np.stack([ir / nrm for ir in irs], 1)


def convolve(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)


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
    os_ = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os_)) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 200.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak, on the
    periodic 3-cycle buffer with wrap-mode hold and smoothing windows. The release
    recursion runs on 8-sample blocks of the held gain (block minimum, so it never
    under-limits), then the step curve is smoothed with an L+1 wrap window."""
    ceil = 10 ** (ceiling_db / 20)
    os_ = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = os_[: len(x) * 4].reshape(len(x), 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    L = int(look_ms * 1e-3 * SR)
    held = minimum_filter1d(need, size=2 * L + 1, mode="wrap")
    B = 8
    hb = held.reshape(-1, B).min(axis=1)
    rc = np.exp(-B / (rel_ms * 1e-3 * SR))
    g = np.empty_like(hb)
    prev = 1.0
    for n, h in enumerate(hb.tolist()):
        prev = min(h, prev * rc + (1 - rc))
        g[n] = prev
    g = np.repeat(g, B)
    g = uniform_filter1d(g, size=L + 1, mode="wrap")
    return x * g[:, None]


def mid_cycle(x: np.ndarray) -> np.ndarray:
    return x[N:2 * N]


def master(mix: np.ndarray) -> np.ndarray:
    """Normalise the kept cycle to TARGET_LUFS; limit the whole periodic buffer."""
    gain_db = TARGET_LUFS - integrated_lufs(mid_cycle(mix))
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(mid_cycle(y))
        if abs(err) < 0.03:
            break
        gain_db += err
    y = mid_cycle(y)
    return y - y.mean(axis=0)          # constant offset only, so the loop seam is untouched


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    # ---- noise layers: one exactly periodic cycle each, tiled over the three cycles
    PL, PR = np.zeros((F, FREQ.shape[1])), np.zeros((F, FREQ.shape[1]))
    for w in WAVES:
        a, b = wave_power(*w)
        PL += a
        PR += b
    waves = np.tile(render_noise(PL, PR), (CYC, 1))
    bl, br = bed_power()
    bed = np.tile(render_noise(bl, br, rho=0.2), (CYC, 1))

    # ---- foam bubbles, denser early in each wash
    bub = np.zeros((L3, 2))
    for tb, A, *_ in WAVES:
        for _ in range(int(230 * A)):
            dt = 0.12 + rng.gamma(1.6, 0.9)
            if dt > 5.5:
                continue
            f0 = np.exp(rng.uniform(np.log(1300), np.log(4800)))
            dur = rng.uniform(0.008, 0.03) * (2200 / f0) ** 0.5
            env = np.exp(-dt / 2.4)
            amp = 0.1 * rng.lognormal(0, 0.5) * env
            place(bub, bubble(f0, max(dur, 0.006), rng.uniform(0.15, 0.45)), tb + dt, amp, rng.uniform(-0.8, 0.8))

    # ---- bell buoy, far right, in uneven clusters as it rocks
    bells = np.zeros((L3, 2))
    nominal = hz(75)                                   # Eb5
    for t0, v in ((0.0, 0.9), (0.62, 0.45), (8.3, 0.7), (15.1, 0.85), (15.68, 0.4), (20.9, 0.6)):
        place(bells, bell(nominal, v), t0, v, 0.62)
    bells = convolve(bells, open_air_ir())
    sway = 1 + 0.25 * np.sin(2 * np.pi * 4 * np.arange(L3) / N + 1.0)    # wind blur, 4 cycles per loop
    bells *= sway[:, None]
    bells = sos_filter(bells, "highpass", 140, order=2)

    stems = {"waves": waves, "bed": bed, "bubbles": bub, "bell": 0.03 * bells}
    if DEBUG:
        for k, v in stems.items():
            print(f"  stem {k:8s} {integrated_lufs(mid_cycle(v)):6.1f} LUFS (pre-master)")
    mix = sum(stems.values())
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 20, order=2)
    mix = sos_filter(mix, "lowpass", 15000, order=4)
    return mix


def main() -> None:
    y = master(render())
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP  "
          f"seam step {np.abs(f[0] - f[-1]).max():.4f}")


if __name__ == "__main__":
    main()
