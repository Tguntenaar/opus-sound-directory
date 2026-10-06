"""meditation-bowls-40s: Opus Sound Directory

A 40-second singing-bowl meditation centred on F and C, with no beat. A large F
bowl (F3) is struck with a soft mallet on frame 0. Each of its inharmonic modes
(1, 2.71, 5.15, 8.17 and 11.7 times the fundamental) is a slightly split
doublet, so it beats slowly and turns gently in the stereo field. The same bowl
is then rubbed around the rim: a singing F drone with a slow rotation shimmer
and soft friction grain. The drone swells and settles on a 10-second breathing
cycle (inhale to the peak, exhale to the trough), with a soft re-strike on the
second breath. On frame 600 (20.0 s), at the bottom of an exhale, a smaller and
higher C bowl (C5, a twelfth above the F) is struck. Its rim is rubbed too, and
a brighter layer of slowly drifting high partials opens around it. A soft echo
strike of the C bowl follows at 30 s. The last breaths exhale, the rubbing stops
and the bowls fade into silence by the end. A long, soft room reverb
surrounds everything, and nothing sits below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 400616
DURATION_SEC = 40
BPM = None
KEY = "F / C (bowls)"
FPS = 30
CUE_FRAMES = (0, 600)          # frame 0: F bowl strike, frame 600: higher C bowl strike
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
C_STRIKE_T = CUE_FRAMES[1] / FPS   # 20.0 s
BREATH = 10.0                      # seconds per breath; troughs at 0, 10, 20, 30, 40 s

F_BOWL = 174.61                    # F3
C_BOWL = 523.25                    # C5

rng = np.random.default_rng(SEED)
t_all = np.arange(N) / SR


# ---------------------------------------------------------------- utilities
def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def smoothstep(t: np.ndarray, a: float, b: float) -> np.ndarray:
    u = np.clip((t - a) / (b - a), 0.0, 1.0)
    return u * u * (3 - 2 * u)


def breath(t: np.ndarray) -> np.ndarray:
    """Slow breathing curve: 0 at each exhale trough, 1 at the top of each inhale.
    Inhale rises a little faster than the exhale falls."""
    ph = (t / BREATH) % 1.0
    warped = np.where(ph < 0.45, 0.5 * ph / 0.45, 0.5 + 0.5 * (ph - 0.45) / 0.55)
    return np.sin(np.pi * warped) ** 2


def pan2(x: np.ndarray, pan) -> np.ndarray:
    th = (np.asarray(pan) + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)


# ---------------------------------------------------------------- bowls
def bowl_strike(f0: float, t0: float, vel: float, ratios, amps, decays, splits,
                attack: float = 0.0005) -> np.ndarray:
    """Struck bowl from t0 to the end of the file. Every mode is a doublet (two
    nearly equal frequencies, panned apart) so it beats slowly and moves in stereo.
    The soft mallet also adds a short low-passed felt thump."""
    s0 = int(round(t0 * SR))
    t = t_all[s0:] - t0
    out = np.zeros((len(t), 2))
    for k, (r, a, d, sp) in enumerate(zip(ratios, amps, decays, splits)):
        f = f0 * r
        if f * 1.01 > 15000:
            continue
        bal = rng.uniform(0.35, 0.65)
        for j, (ff, w, pn) in enumerate(((f - sp / 2, bal, -0.35), (f + sp / 2, 1 - bal, 0.35))):
            ph = rng.uniform(0, 2 * np.pi)
            y = a * w * np.sin(2 * np.pi * ff * t + ph) * np.exp(-t / d)
            out += pan2(y, pn * (0.6 + 0.4 * (k > 0)))
    thump_len = int(0.08 * SR)
    th = sos_filter(rng.standard_normal(thump_len), "bandpass", [250, 1800])
    th *= np.exp(-np.arange(thump_len) / SR / 0.010) * 0.5
    out[:thump_len] += th[:, None]
    na = max(1, int(attack * SR))
    out[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na)))[:, None]
    full = np.zeros((N, 2))
    full[s0:] = out * vel
    return full


F_MODES = dict(ratios=(1.0, 2.71, 5.15, 8.17, 11.7), amps=(1.0, 0.50, 0.24, 0.10, 0.04),
               decays=(13.0, 8.0, 4.0, 2.0, 1.0), splits=(0.55, 1.4, 2.3, 3.3, 4.4))
C_MODES = dict(ratios=(1.0, 2.68, 5.05, 8.3, 12.0), amps=(1.0, 0.62, 0.34, 0.16, 0.07),
               decays=(10.0, 6.0, 3.0, 1.6, 0.8), splits=(0.9, 2.0, 3.1, 4.2, 5.5))


def rubbed_rim(f0: float, ratios, env: np.ndarray, rot_hz: float, bright: np.ndarray) -> np.ndarray:
    """Rim-rubbed ('singing') bowl: the fundamental doublet plus the second mode,
    amplitude-modulated by the stick circling the rim (L/R in quadrature so the
    shimmer rotates), with narrow-band friction grain around each mode."""
    out = np.zeros((N, 2))
    rot = 2 * np.pi * rot_hz * t_all + 0.3 * np.sin(2 * np.pi * 0.07 * t_all)
    for k, (r, a) in enumerate(((ratios[0], 1.0), (ratios[1], 0.38))):
        f = f0 * r
        amp = a * (bright if k else 1.0)
        for sp, pn in ((-0.35, -0.4), (0.35, 0.4)):
            y = np.sin(2 * np.pi * (f + sp * (k + 1)) * t_all + rng.uniform(0, 2 * np.pi))
            out += pan2(y * amp * 0.5, pn)
        grain = sos_filter(rng.standard_normal(N), "bandpass", [f * 0.985, f * 1.015], order=2)
        grain /= np.sqrt(np.mean(grain ** 2))
        out += pan2(grain * amp * 0.035, 0.0)
    am = np.stack([1 + 0.22 * np.sin(rot), 1 + 0.22 * np.cos(rot)], axis=1)
    return out * am * env[:, None]


def shimmer(freqs, env: np.ndarray) -> np.ndarray:
    """High bowl partials drifting in and out on slow independent LFOs, panned around."""
    out = np.zeros((N, 2))
    for f in freqs:
        lfo_hz = rng.uniform(0.04, 0.11)
        lfo = 0.5 - 0.5 * np.cos(2 * np.pi * lfo_hz * t_all + rng.uniform(0, 2 * np.pi))
        pan = 0.6 * np.sin(2 * np.pi * rng.uniform(0.02, 0.05) * t_all + rng.uniform(0, 2 * np.pi))
        y = np.sin(2 * np.pi * f * t_all + rng.uniform(0, 2 * np.pi)) * lfo
        out += pan2(y, pan)
    return out * env[:, None] / len(freqs)


def reverb(x: np.ndarray, rt60: float = 4.5, predelay: float = 0.03) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR (large soft room), darker as it decays."""
    t = np.arange(int(rt60 * 1.15 * SR)) / SR
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        bright = sos_filter(rng.standard_normal(len(t)), "bandpass", [220, 7000]) * np.exp(-t / 0.8)
        dark = sos_filter(rng.standard_normal(len(t)), "bandpass", [220, 2500])
        ir = (bright * 0.6 + dark) * env
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
    p = np.cumsum(np.concatenate([[0.0], (y ** 2).sum(axis=1)]))
    starts = np.arange(0, len(y) - blk + 1, hop)
    z = (p[starts + blk] - p[starts]) / blk
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    os = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os)) + 1e-20))


def limiter_gain(x: np.ndarray, ceiling_db: float, look_ms: float = 3.0, rel_ms: float = 250.0) -> np.ndarray:
    """Gain curve of a look-ahead limiter driven by the 4x-oversampled (true) peak.
    Held over the look-ahead window, one-pole release, edge-safe box smoothing."""
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
    return uniform_filter1d(g, size=L + 1, mode="nearest")


def master(mix: np.ndarray) -> np.ndarray:
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3
    for _ in range(12):
        z = mix * 10 ** (gain_db / 20)
        y = z * limiter_gain(z, ceiling)[:, None]
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    br = breath(t_all)

    # --- struck bowls
    strikes = bowl_strike(F_BOWL, 0.0, 1.0, attack=0.001, **F_MODES)           # frame 0
    strikes += bowl_strike(F_BOWL, 10.0, 0.30, **F_MODES)                      # soft re-strike
    c_hit = bowl_strike(C_BOWL, C_STRIKE_T, 0.95, **C_MODES)                   # frame 600
    c_hit += bowl_strike(C_BOWL, 30.0, 0.28, **C_MODES)                        # soft echo
    strikes += c_hit

    # --- rubbed rims, breathing
    rub_f_env = smoothstep(t_all, 1.5, 7.0) * (1 - smoothstep(t_all, 31.0, 38.0))
    rub_f_env *= 0.30 + 0.70 * br
    rub_f = rubbed_rim(F_BOWL, F_MODES["ratios"], rub_f_env, 0.75, 0.35 + 0.65 * br)
    rub_c_env = smoothstep(t_all, 21.0, 26.0) * (1 - smoothstep(t_all, 32.0, 38.5))
    rub_c_env *= 0.30 + 0.70 * br
    rub_c = rubbed_rim(C_BOWL, C_MODES["ratios"], rub_c_env, 1.1, 0.40 + 0.60 * br)

    # --- brighter layer after frame 600: high partial shimmer of both bowls
    shim_env = smoothstep(t_all, 20.5, 27.0) * (1 - smoothstep(t_all, 33.0, 38.5)) * (0.45 + 0.55 * br)
    shim = shimmer((C_BOWL * 2.68, C_BOWL * 5.05, F_BOWL * 8.17, F_BOWL * 11.7,
                    C_BOWL * 2.68 * 2.0 * 1.003, C_BOWL * 8.3), shim_env)

    dry = strikes * 0.55 + rub_f * 0.42 + rub_c * 0.30 + shim * 0.16
    wet = reverb(dry * np.array([1.0, 1.0]), rt60=4.5) * 0.55
    mix = dry + wet
    mix = sos_filter(mix, "highpass", 130, order=8)

    # nothing below 120 Hz; stereo width (doublets, reverb) kept above ~320 Hz
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 320, order=10)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "lowpass", 15000, order=4)

    # the last exhale: bowls are gently damped into silence
    tail = 1 - smoothstep(t_all, 33.5, 39.4)
    return mix * tail[:, None]


def main() -> None:
    mix = render()
    y = master(mix)
    y = y - y.mean(axis=0, keepdims=True)                 # constant per-channel DC trim
    tail = 1 - smoothstep(t_all, 39.0, 39.6)              # re-silence the trimmed end
    y = y * tail[:, None]
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    pcm[0] = 0
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
