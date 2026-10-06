"""logo-sting-organic: Opus Sound Directory

A 3-second warm, earthy brand motif in G major at 96 BPM. On frame 0 a thumb-plucked
kalimba G4 sounds together with a deep hand-drum bass tone. The kalimba then walks up
B4, D5 and E5 in eighth notes and sighs back down to D5. Each note is a steel tine with
inharmonic overtones (about 5.9x and 17x the fundamental), a slow coupling beat, a
soft thumb click and a hollow wooden body. Under it, a hand drum plays open tones and
a light slap, and a seed shaker swishes in sixteenths with off-beat accents. The
groove breathes out just before frame 48 (1.6 s). There the motif resolves on a soft
drum (bass plus open tone) and a five-tine G major chord (G3 D4 G4 B4 G5). The chord
rings in a small wooden room and decays to silence. Only the hand-drum bass tone sits
below 120 Hz, and it is mono.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 96048
DURATION_SEC = 3
BPM = 96
KEY = "G major"
FPS = 30
CUE_FRAMES = (0, 48)           # frame 0: first tine + drum, frame 48: resolving chord
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.625 s
E8 = BEAT / 2                  # 0.3125 s
S16 = BEAT / 4                 # 0.15625 s
RES_T = CUE_FRAMES[1] / FPS    # 1.6 s

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def attack_release(x: np.ndarray, a: float = 0.0004, r: float = 0.01) -> np.ndarray:
    """Sub-millisecond raised-cosine attack and a short cosine release (no clicks)."""
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


def peaking_eq(x, f0, gain_db, q):
    """RBJ cookbook peaking biquad."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * a_, -2 * np.cos(w0), 1 - alpha * a_]
    a = [1 + alpha / a_, -2 * np.cos(w0), 1 - alpha / a_]
    return signal.lfilter(b, a, x, axis=0)


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


# ---------------------------------------------------------------- voices
def kalimba(midi: float, dur: float = 1.6, vel: float = 1.0, ring: float = 1.0) -> np.ndarray:
    """Steel tine on a hollow box. Modes of a clamped bar are inharmonic, so the
    overtones sit near 5.9x and 17x the fundamental, and they die much faster than
    the fundamental. The fundamental is two slightly detuned partials (tine and box
    coupling), which gives a slow beat. A short thumb click marks the pluck."""
    t = tt(dur)
    f = hz(midi) * 2 ** (rng.uniform(-3, 3) / 1200)
    beat_hz = rng.uniform(0.5, 1.2)
    r1 = 5.93 * 2 ** (rng.uniform(-25, 25) / 1200)
    r2 = 17.1 * 2 ** (rng.uniform(-30, 30) / 1200)
    t60 = ring * 2.6 * (hz(67) / f) ** 0.35        # lower tines ring longer
    tau = t60 / 6.9
    # a pluck releases a displaced tine, so the fundamental starts at its peak (cosine phase)
    y = np.exp(-t / tau) * (0.72 * np.cos(2 * np.pi * f * t) + 0.28 * np.cos(2 * np.pi * (f + beat_hz) * t))
    y += 0.10 * np.exp(-t / (tau * 0.5)) * np.sin(2 * np.pi * 2 * f * t)          # body nonlinearity
    if r1 * f < 15000:
        y += 0.30 * vel * np.exp(-t / 0.055) * np.sin(2 * np.pi * r1 * f * t)
    if r2 * f < 15000:
        y += 0.07 * vel * np.exp(-t / 0.012) * np.sin(2 * np.pi * r2 * f * t)
    click_d = 0.006
    click = sos_filter(noise(click_d), "bandpass", [1800, 6000]) * np.exp(-tt(click_d) / 0.0012)
    y[: len(click)] += 0.25 * vel * click
    return attack_release(y * vel, a=0.0003, r=0.05)


def hand_drum(kind: str, vel: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Goblet hand drum. Returns (low, mid): `low` is the mono Helmholtz bass thump
    (pitch-dropping sine), `mid` is the membrane (circular-membrane mode ratios) plus
    the palm/finger noise."""
    dur = 0.45 if kind == "bass" else 0.3
    t = tt(dur)
    low = np.zeros_like(t)
    if kind in ("bass", "soft"):
        f = 72 + 30 * np.exp(-t / 0.03)
        low = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.16 if kind == "bass" else 0.2))
        low = attack_release(low, a=0.0004, r=0.03)
    f0 = 215 * 2 ** (rng.uniform(-15, 15) / 1200)
    modes = ((1.0, 1.0, 0.11), (1.594, 0.55, 0.07), (2.136, 0.4, 0.05),
             (2.296, 0.3, 0.045), (2.653, 0.22, 0.035), (2.918, 0.15, 0.03))
    mid = np.zeros_like(t)
    bright = {"bass": 0.35, "tone": 1.0, "slap": 1.6, "soft": 0.6}[kind]
    for i, (r, a, d) in enumerate(modes):
        w = a * bright ** (i / 2)
        mid += w * np.exp(-t / (d * (0.6 if kind == "slap" else 1.0))) * np.sin(2 * np.pi * r * f0 * t + rng.uniform(0, 6.28))
    hand = sos_filter(noise(dur), "bandpass", [700, 5500 if kind != "slap" else 8000])
    mid += (0.25 if kind != "slap" else 0.7) * hand * np.exp(-t / (0.006 if kind != "slap" else 0.012))
    mid = attack_release(mid * 0.5, a=0.0004, r=0.03)
    return low * vel, mid * vel * (0.5 if kind == "bass" else 1.0)


def shaker(vel: float = 1.0, dur: float = 0.11) -> np.ndarray:
    """Seed shaker swish: band-passed noise with a ~7 ms rise and grainy amplitude."""
    t = tt(dur)
    y = sos_filter(noise(dur), "bandpass", [3500, 11500], order=2)
    grains = 0.6 + 0.4 * np.abs(sos_filter(noise(dur), "lowpass", 900))
    env = (1 - np.exp(-t / 0.007)) * np.exp(-t / 0.03)
    return attack_release(y * grains * env * vel * 0.4, a=0.003, r=0.01)


def room(x: np.ndarray, rt60: float = 0.8, predelay: float = 0.012) -> np.ndarray:
    """Small wooden room: decorrelated noise IRs, darker as they decay."""
    t = tt(rt60 * 1.2)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [220, 5200]) * env
        ir = sos_filter(ir, "lowpass", 3800, order=1)
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    tines = np.zeros((N, 2))
    drum = np.zeros((N, 2))
    low = np.zeros(N)           # hand-drum bass thump: the only content below 120 Hz (mono)
    shake = np.zeros((N, 2))
    send = np.zeros((N, 2))

    # ---- kalimba motif: G4 B4 D5 E5 (8ths) then a sigh to D5, resolving on frame 48
    motif = ((0.0, 67, 1.0, -0.15), (E8, 71, 0.85, 0.25), (2 * E8, 74, 0.9, -0.3),
             (3 * E8, 76, 1.0, 0.3), (4 * E8, 74, 0.8, -0.2))
    for t0, m, v, pan in motif:
        k = kalimba(m, 1.7, v)
        place(tines, k, t0, 0.5, pan)
        place(send, k, t0, 0.18, pan)

    # ---- hand drum: bass on 1, open tones and a slap; the next bass thump is saved for the resolve
    hits = ((0.0, "bass", 1.0, 0.0), (3 * S16, "tone", 0.55, 0.15), (BEAT, "tone", 0.8, 0.15),
            (BEAT + 2 * S16, "slap", 0.55, -0.15), (BEAT + 3 * S16, "tone", 0.4, 0.15),
            (2 * BEAT, "tone", 0.6, -0.1))
    for t0, kind, v, pan in hits:
        lo, mi = hand_drum(kind, v)
        place(low[:, None], lo[:, None], t0, 0.9)
        place(drum, mi, t0, 0.55, pan)
        place(send, mi, t0, 0.12, pan)

    # ---- shaker: 16ths from the second 16th to just before the breath, off-beat accents
    s16 = [i * S16 for i in range(1, 9)]
    for i, t0 in enumerate(s16):
        acc = 1.0 if (i + 1) % 2 == 0 else 0.55
        place(shake, shaker(acc), t0, 0.5, pan=0.45)
        place(send, np.stack([shaker(acc * 0.5)] * 2, 1), t0, 0.1)

    # ---- the breath: every pre-resolve bus loses its tail over 3 ms ending 20 ms before frame 48.
    # Kalimba tines keep ringing (they are the motif) but are pulled down 6 dB from 1.45 s.
    s_cut = int(round((RES_T - 0.02) * SR))
    g = np.ones(N)
    g[s_cut - int(0.003 * SR):s_cut] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, int(0.003 * SR)))
    g[s_cut:] = 0.0
    shake *= g[:, None]
    gt = np.ones(N)
    a0, a1 = int(1.45 * SR), int((RES_T - 0.005) * SR)
    gt[a0:a1] = 1 - 0.5 * (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a1 - a0)))
    gt[a1:] = 0.5
    tines *= gt[:, None]

    # ---- frame 48: soft drum + five-tine G major chord (struck together, ringing out)
    chord = ((55, 0.85, 0.0), (62, 0.75, -0.3), (67, 0.75, 0.3), (71, 0.65, -0.45), (79, 0.55, 0.45))
    for m, v, pan in chord:
        k = kalimba(m, DURATION_SEC - RES_T, v, ring=1.6)
        place(tines, k, RES_T, 0.42, pan)
        place(send, k, RES_T, 0.2, pan)
    lo, mi = hand_drum("soft", 0.95)
    place(low[:, None], lo[:, None], RES_T, 0.9)
    place(drum, mi, RES_T, 0.5, 0.0)
    place(send, mi, RES_T, 0.12, 0.0)
    # one last soft shaker swish trailing the chord (starts 60 ms later, quieter)
    place(shake, shaker(0.6, 0.18), RES_T + 0.06, 0.4, pan=0.45)

    # ---- buses
    hp = lambda x, f=150: sos_filter(x, "highpass", f, order=4)
    tines = peaking_eq(hp(tines, 140), 320, 2.0, 1.0)          # hollow wooden box
    tines = peaking_eq(tines, 4200, -2.5, 0.8)                  # soften the steel
    drum = hp(drum, 130)
    shake = hp(shake, 2500)
    wet = hp(room(send), 180) * 0.45
    low = sos_filter(low, "lowpass", 400, order=2)
    mix = tines + drum + shake + wet + np.repeat(low[:, None], 2, axis=1)

    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=6)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 20, order=2)
    mix = sos_filter(mix, "lowpass", 16500, order=4)
    nf = int(0.35 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 80.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak; the gain is held
    over the look-ahead window, released by a one-pole, and box-smoothed edge-safely."""
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


def main() -> None:
    mix = render()
    y = master(mix)
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
