"""glitch-transition-digital: Opus Sound Directory

A 1.2-second digital glitch transition in F# minor at 140 BPM. It opens on one
sixteenth of a bright F# minor phrase: a hollow square-ish chord stab under a
fast arpeggiated bleep line. A buffer-repeat effect then grabs that slice and
stutters it faster and faster: sixteenths, thirty-seconds, sixty-fourths, then
1/128 and 1/256 repeats that blur into a buzzing tone. Each repeat is
re-pitched upward like a sped-up buffer and crushed a little harder. Gated noise
bursts flick left and right, and ring-modulated bleeps chirp between the slices.
A 44 ms digital drop-out sucks everything away. Then a hard slam lands exactly
on frame 18 (0.6 s): a mono F#1 sub hit, a crushed F# power chord, a downward
ring-mod zap and a noise blast. A short tail of high ring-modulated sparkle
grains ping-pongs out to silence. Everything is alias-free. Pitch shifts are
re-synthesised from band-limited partials. Bit-crushing uses a smooth quantiser
run at 8x oversampling and then filtered down. There is no naive sample-and-hold
anywhere.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 140018
DURATION_SEC = 1.2
BPM = 140
KEY = "F# minor"
FPS = 30
CUE_FRAMES = (18,)             # the digital slam
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
BEAT = 60.0 / BPM
S16 = BEAT / 4                 # 107.1 ms
SLAM_T = CUE_FRAMES[0] / FPS   # 0.6 s
OS = 8                         # oversampling factor for the crusher

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


def crush(x: np.ndarray, bits: float) -> np.ndarray:
    """Alias-free bit-crush. The signal is upsampled 8x, pushed through a smooth
    staircase quantiser y = x - s/(2 pi) sin(2 pi x / s), and then low-pass decimated
    back. Steps are flat but the corners are rounded, and the 8x headroom keeps the
    new partials from folding into the audio band."""
    s = 2.0 / (2 ** bits)
    up = signal.resample_poly(x, OS, 1, axis=0)
    y = up - s / (2 * np.pi) * np.sin(2 * np.pi * up / s)
    return signal.resample_poly(y, 1, OS, axis=0)[: len(x)]


# ---------------------------------------------------------------- source phrase
# One sixteenth of "music" that the buffer effect captures. It is defined as a
# function of continuous time, so a re-pitched (sped-up) read of the buffer is
# re-synthesised exactly. Partials above 15 kHz after the speed-up are dropped,
# so no pitch shift can alias.
STAB = (54, 57, 61, 66)          # F#3 A3 C#4 F#4
ARP = (78, 85, 81, 88)           # F#5 C#6 A5 E6, 32nds
PHASES = rng.uniform(0, 2 * np.pi, 64)


def source(ratio: float, length: float) -> np.ndarray:
    """Read `length` seconds of the captured buffer at playback speed `ratio`."""
    t = tt(length) * ratio
    y = np.zeros_like(t)
    # square-ish stab: odd harmonics, 1/k, gently rolled off, decaying
    for j, m in enumerate(STAB):
        f = hz(m)
        for k in range(1, 40, 2):
            if k * f * ratio > 15000:
                break
            a = (1 / k) / (1 + (k * f / 3500) ** 2)
            y += 0.22 * a * np.sin(2 * np.pi * k * f * t + PHASES[(j * 7 + k) % 64])
    y *= np.exp(-t / 0.09)
    # 32nd-note bleep arp on top (pure-ish tones with a 3rd harmonic)
    step = S16 / 2
    for i, m in enumerate(ARP):
        t0 = i * step / 2
        tl = t - t0
        on = tl >= 0
        f = hz(m)
        env = np.where(on, np.exp(-np.maximum(tl, 0) / 0.012) * (1 - np.exp(-np.maximum(tl, 0) / 0.0004)), 0)
        b = np.sin(2 * np.pi * f * tl)
        if 3 * f * ratio < 15000:
            b += 0.3 * np.sin(6 * np.pi * f * tl)
        y += 0.28 * env * b
    return y


# ---------------------------------------------------------------- voices
def ringmod_bleep(fc: float, fm: float, dur: float) -> np.ndarray:
    t = tt(dur)
    y = np.sin(2 * np.pi * fc * t) * np.sin(2 * np.pi * fm * t + 0.7)
    y *= np.exp(-t / (dur * 0.35))
    return fade(y, a=0.001, r=0.004)


def gated_noise(dur: float, lo: float, hi: float) -> np.ndarray:
    y = sos_filter(noise(dur), "bandpass", [lo, hi], order=2)
    y *= np.exp(-tt(dur) / (dur * 0.6))
    return fade(y, a=0.0008, r=0.002)


def sub_hit() -> np.ndarray:
    t = tt(0.6)
    f = 46.25 + (170 - 46.25) * np.exp(-t / 0.025)
    y = np.cos(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
    return fade(y, a=0.0005, r=0.05)


def power_chord(dur: float) -> np.ndarray:
    """F#2-C#3-F#3 band-limited saw stack (stereo detune), decaying, for the crusher."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for m in (42, 49, 54):
        for ch, c in ((0, -8), (1, 8)):
            f = hz(m) * 2 ** (c / 1200)
            for k in range(1, int(6000 // f) + 1):
                out[:, ch] += (1 / k) * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    out *= np.exp(-t / 0.11)[:, None] * 0.25
    return fade(out, a=0.0005, r=0.03)


def zap(dur: float) -> np.ndarray:
    """Downward ring-mod zap: carrier sweeps 4 kHz -> 180 Hz, times a 92.5 Hz (F#2) sine."""
    t = tt(dur)
    fc = 180 + 3820 * np.exp(-t / 0.035)
    y = np.sin(2 * np.pi * np.cumsum(fc) / SR) * np.sin(2 * np.pi * 92.5 * t + 0.4)
    y *= np.exp(-t / 0.07)
    return fade(y, a=0.0005, r=0.01)


def sparkle(f: float, dur: float) -> np.ndarray:
    t = tt(dur)
    y = np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 1109 * t))   # light ring-mod shimmer
    y *= np.exp(-t / (dur * 0.3))
    return fade(y, a=0.0015, r=0.006)


def reverb(x: np.ndarray, rt60: float, predelay: float = 0.008) -> np.ndarray:
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [400, 9000]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 1.5, rel_ms: float = 60.0) -> np.ndarray:
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
    glitch = np.zeros((N, 2))     # everything before the slam
    slam = np.zeros((N, 2))
    low = np.zeros((N, 2))        # mono sub only

    # --- buffer-repeat schedule: (repeat length, count, semitone shift per repeat)
    sched = [(S16, 2, 0.0), (S16 / 2, 2, 1.0), (S16 / 4, 4, 1.0), (S16 / 8, 8, 0.75), (S16 / 16, 3, 0.5)]
    t = 0.0
    semis = 0.0
    n_rep = 0
    events = []
    for length, count, dsemi in sched:
        for _ in range(count):
            events.append((t, length, semis, n_rep))
            t += length
            semis += dsemi
            n_rep += 1
    stutter_end = t                                   # ~0.563 s
    total = len(events)
    for (t0, length, sm, i) in events:
        ratio = 2 ** (sm / 12)
        seg = source(ratio, length)
        edge = min(0.001, length * 0.15)
        seg = fade(seg, a=edge if i else 0.002, r=edge)
        prog = i / (total - 1)
        bits = 9 - 5.5 * prog                         # 9 bits -> 3.5 bits
        seg = (1 - 0.35 - 0.4 * prog) * seg + (0.35 + 0.4 * prog) * crush(seg, bits)
        pan = 0.0 if length >= S16 / 2 else 0.45 * (-1) ** i
        place(glitch, seg, t0, 0.9 + 0.25 * prog, pan=pan)

    # --- gated noise flicks on the 32nd/64th grid, alternating sides
    gpos = [0.16, 0.214, 0.255, 0.321, 0.348, 0.375, 0.415, 0.455, 0.482, 0.509, 0.53]
    for k, g0 in enumerate(gpos):
        d = 0.018 if g0 < 0.4 else 0.01
        lo, hi = (2500, 9000) if k % 2 else (1200, 5000)
        place(glitch, gated_noise(d, lo, hi), g0, 0.25 + 0.2 * k / len(gpos), pan=0.7 * (-1) ** k)

    # --- ring-mod bleeps between slices (F# minor carriers)
    for (t0, fc, fm, d, pan) in ((0.12, hz(85), hz(66), 0.045, -0.5), (0.24, hz(90), hz(61), 0.03, 0.5),
                                 (0.36, hz(93), hz(73), 0.025, -0.3), (0.44, hz(97), hz(78), 0.02, 0.4),
                                 (0.50, hz(102), hz(85), 0.02, -0.6)):
        place(glitch, ringmod_bleep(fc, fm, d), t0, 0.22, pan=pan)

    # --- drop-out: everything before the slam is gone by stutter_end (+ a 1 ms fade)
    glitch = sos_filter(glitch, "highpass", 150, order=4) * 0.7
    se = int(stutter_end * SR)
    nfo = int(0.001 * SR)
    glitch[se - nfo:se] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nfo)))[:, None]
    glitch[se:] = 0.0

    # --- the slam (frame 18)
    place(low, sub_hit(), SLAM_T, 0.9)
    pc = power_chord(0.5)
    place(slam, 0.5 * pc + 0.6 * crush(pc, 3.0), SLAM_T, 1.35)
    place(slam, zap(0.25), SLAM_T, 0.45)
    blast = np.stack([sos_filter(noise(0.25), "bandpass", [800, 12000], order=2) for _ in range(2)], 1)
    blast *= np.exp(-tt(0.25) / 0.03)[:, None]
    place(slam, fade(blast, a=0.0005, r=0.02), SLAM_T, 0.6)

    # --- sparkle tail: high ring-modded grains, thinning out, ping-ponged
    sp_notes = (90, 97, 93, 102, 99, 105, 97, 102, 94, 100)
    tg = SLAM_T + 0.035
    for k, m in enumerate(sp_notes):
        d = rng.uniform(0.05, 0.11)
        place(slam, sparkle(hz(m), d), tg, 0.22 * (1 - k / len(sp_notes)) + 0.06, pan=0.75 * (-1) ** k)
        tg += 0.022 + 0.008 * k
    slam_hp = sos_filter(slam, "highpass", 150, order=4)
    wet = sos_filter(reverb(slam_hp, rt60=0.45), "highpass", 300, order=4) * 0.35
    # ping-pong echo of the sparkle region (eighth-triplet at 140 BPM)
    dly = int(BEAT / 3 * SR)
    echo = np.zeros_like(slam_hp)
    echo[dly:, 0] = slam_hp[:-dly, 1] * 0.25
    echo[2 * dly:, 1] = slam_hp[:-2 * dly, 0] * 0.12
    slam_bus = slam_hp + wet + sos_filter(echo, "highpass", 1500, order=2)

    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    low = sos_filter(low, "highpass", 22, order=2)

    mix = glitch + slam_bus + low
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "lowpass", 16500, order=4)
    nf = int(0.15 * SR)
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
