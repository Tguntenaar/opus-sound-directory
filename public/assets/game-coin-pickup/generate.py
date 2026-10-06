"""game-coin-pickup: Opus Sound Directory

A retro 8-bit coin pickup in E, instantly readable as "collect". A NES-style pulse channel
plays a two-step blip: a short B5 on frame 0, then E6 a fourth higher four NES frames (67 ms)
later. The E6 holds at full volume, then steps down the 4-bit volume ladder (16 linear levels,
one step per 1/60 s frame, each step smoothed over 1 ms) until it is silent. The square wave is
built additively from band-limited odd harmonics that taper off above 12 kHz, so it never
aliases, and the note change glides over 2 ms so it steps without splatter. The output goes
through the console's own gentle filter stage: two first-order high-passes (90 Hz and 440 Hz)
and a 14 kHz low-pass. A second pulse channel provides the tiny echo, the way old games faked
delay. It replays the same two notes six frames later at a third of the volume, with a 25 %
duty and a slower decay, so it trails just past the main note and is nudged slightly right. A
fainter third repeat comes six frames after that. The core is centred, has no low end at all,
and fades to silence before 0.5 s.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 4404
DURATION_SEC = 0.5
BPM = None
KEY = "E major"
FPS = 30
CUE_FRAMES = (0,)               # frame 0: the B5 blip starts (0.5 ms attack)
TARGET_LUFS = -17.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
NES_FRAME = 1 / 60              # envelope / sequencer tick
STEP2_T = 4 * NES_FRAME         # B5 lasts four frames (66.7 ms), then E6
ECHO_DELAY = 6 * NES_FRAME      # echo channel runs six frames (100 ms) behind

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a mono (L,) snippet into a stereo bus at time t (equal-power pan)."""
    s = int(round(t * SR))
    if s >= len(bus):
        return
    th = (pan + 1) * np.pi / 4
    x = np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)
    e = min(len(bus), s + len(x))
    bus[s:e] += gain * x[: e - s]


def one_pole(x: np.ndarray, fc: float, kind: str) -> np.ndarray:
    """First-order (6 dB/oct) filter, like the RC stages on the console's audio output."""
    b, a = signal.butter(1, fc, btype=kind, fs=SR)
    return signal.lfilter(b, a, x, axis=0)


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


# ---------------------------------------------------------------- voices
def pulse_channel(notes, dur: float, duty: float, hold_frames: int, step_frames: float,
                  start_level: int = 15, attack: float = 0.0005) -> np.ndarray:
    """Band-limited NES-style pulse channel.

    notes: [(t_start, midi), ...] -- the period changes within 2 ms and the phase stays continuous
    (like the hardware timer). The waveform is an additive pulse: harmonic k has amplitude
    sin(pi k duty) / k, tapered by a raised cosine from 12 to 15 kHz, so nothing near Nyquist.
    The volume is a 4-bit linear ladder: hold for hold_frames at start_level, then drop one
    step every step_frames NES frames; each step is smoothed over 1 ms so it never clicks.
    """
    t = tt(dur)
    f = np.zeros_like(t)
    for t0, m in notes:
        f[t >= t0] = hz(m)
    # the period changes over 2 ms: still heard as a hard step, but a short linear glide keeps the
    # phase derivative continuous, so the note change does not splatter broadband energy
    f = uniform_filter1d(f, size=int(0.002 * SR) + 1, mode="nearest")
    f[t < notes[0][0] + 0.002] = hz(notes[0][1])
    phase = 2 * np.pi * np.cumsum(f) / SR
    phase += rng.uniform(0, 2 * np.pi)
    y = np.zeros_like(t)
    kmax = int(15000 / f[f > 0].min()) + 1
    for k in range(1, kmax + 1):
        a = np.sin(np.pi * k * duty) / k
        if abs(a) < 1e-9:
            continue
        fk = k * f
        taper = np.where(fk < 12000, 1.0, np.where(fk < 15000, 0.5 + 0.5 * np.cos(np.pi * (fk - 12000) / 3000), 0.0))
        y += a * taper * np.sin(k * phase)
    y *= 4 / np.pi
    # 4-bit volume ladder on the 60 Hz frame clock, restarting at full on every new note
    vol = np.zeros_like(t)
    last_t0 = notes[-1][0]
    for i, (t0, _) in enumerate(notes):
        t1 = notes[i + 1][0] if i + 1 < len(notes) else dur
        seg = (t >= t0) & (t < t1)
        if t0 < last_t0:
            vol[seg] = start_level                            # the blip just holds full volume
        else:
            fr = np.floor((t[seg] - t0) / NES_FRAME)
            vol[seg] = np.clip(start_level - np.floor(np.maximum(fr - hold_frames, -1) / step_frames + 1), 0, 15)
    vol /= 15.0
    vol = uniform_filter1d(vol, size=int(0.001 * SR) + 1, mode="nearest")    # 1 ms smoothed steps
    # raised-cosine key-on so the first sample is exactly zero (0.5 ms on the cue, softer on echoes)
    na = int(attack * SR)
    vol[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    return y * vol


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 60.0) -> np.ndarray:
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
    lead = np.zeros((N, 2))
    echo = np.zeros((N, 2))
    notes = [(0.0, 83), (STEP2_T, 88)]               # B5 -> E6

    # main channel: 50 % duty (hollow square), E6 holds 2 frames then steps down every frame
    main = pulse_channel(notes, 0.40, duty=0.5, hold_frames=2, step_frames=1.0)
    place(lead, main, 0.0, 1.0, pan=-0.04)
    # echo channel: same notes six frames later, 25 % duty, volume 5/15, slower decay so it trails
    # past the main note, slightly right; a softer third repeat six frames after that, slightly left
    e1 = pulse_channel(notes, 0.34, duty=0.25, hold_frames=2, step_frames=2.5, start_level=5, attack=0.003)
    place(echo, e1, ECHO_DELAY, 1.0, pan=0.35)
    e2 = pulse_channel(notes, 0.23, duty=0.25, hold_frames=1, step_frames=3.0, start_level=2, attack=0.003)
    place(echo, e2, 2 * ECHO_DELAY, 1.0, pan=-0.30)

    mix = lead + echo
    # console output stage: 90 Hz + 440 Hz first-order high-passes, 14 kHz first-order low-pass
    mix = one_pole(one_pole(mix, 90, "highpass"), 440, "highpass")
    mix = one_pole(mix, 14000, "lowpass")
    mix = sos_filter(mix, "lowpass", 16000, order=4)          # extra guard below the ultrasonic band
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 650, order=8)         # echo width only well above the low end
    mix = np.stack([mid + side, mid - side], axis=1)

    # cosine tail-out so the last sample is exactly silent
    nf = int(0.06 * SR)
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
