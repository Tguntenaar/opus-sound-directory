"""podcast-intro-10s: Opus Sound Directory

A friendly 10-second podcast intro in Bb major at 96 BPM, played by a small jazz
trio. A tine electric piano (two-operator FM bark plus a short bell-like tine,
pickup asymmetry and a 4.8 Hz stereo tremolo) comps rootless voicings in a
Charleston rhythm and plays a swung, singable top melody. A round upright-style
bass walks quarter notes (Bbmaj7 Gm7 | Cm7 F7 | Ebmaj7 Cm7 F7) under brushed
snare swirls, taps on 2 and 4 and a feathered kick. It opens on a full-band hit
with a brushed cymbal at frame 0. The last bar slows into a gentle ritardando
and a quick triplet brush pickup, the band takes a short breath, and a Bb6/9
button (bass, piano chord, cymbal) lands exactly on frame 240 (8.0 s). It then
rings out to silence over the final two seconds, leaving room for the host to
start talking. Everything below 120 Hz is a mono bass and kick.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 960810
DURATION_SEC = 10
BPM = 96
KEY = "Bb major"
FPS = 30
CUE_FRAMES = (0, 240)          # frame 0: full-band intro hit, frame 240: button
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.625 s
BUTTON_T = CUE_FRAMES[1] / FPS  # 8.0 s
SWING = 0.64                   # swung "and" position inside a beat

rng = np.random.default_rng(SEED)

# Beat clock: beats 0..8 strict at 96 BPM (bars 1-2 and the bar-3 downbeat),
# then a ritardando so beat 12 (the button) lands on 8.0 s.
_BEATS = [i * BEAT for i in range(9)]
for d in (0.64, 0.70, 0.78, 0.88):
    _BEATS.append(_BEATS[-1] + d)
assert abs(_BEATS[12] - BUTTON_T) < 1e-9


def T(b: float) -> float:
    """Time of a (fractional) beat position on the tempo map."""
    i = min(int(np.floor(b)), 11)
    return _BEATS[i] + (b - i) * (_BEATS[i + 1] - _BEATS[i])


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    """Raised-cosine attack/release so nothing starts or stops with a click."""
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na)))[(slice(None),) + (None,) * (x.ndim - 1)]
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr)))[(slice(None),) + (None,) * (x.ndim - 1)]
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


# ---------------------------------------------------------------- voices
def epiano(midi: float, dur: float, vel: float = 0.8, att: float = 0.002, ring: float = 1.0) -> np.ndarray:
    """Tine electric piano. A 1:1 FM pair whose index falls fast (the 'bark' into a
    round body), a short inharmonic tine partial at 7.0x, and a gentle even-order
    pickup asymmetry. All sidebands stay under ~6 kHz."""
    t = tt(dur)
    f = hz(midi)
    idx = vel * (2.0 * np.exp(-t / 0.10) + 0.35 * np.exp(-t / 1.5))
    ph = rng.uniform(0, 2 * np.pi)
    body = np.sin(2 * np.pi * f * t + ph + idx * np.sin(2 * np.pi * f * t))
    tine = (0.22 * vel ** 2 * np.sin(2 * np.pi * 7.0 * f * t + 0.6 * np.sin(2 * np.pi * f * t))
            * np.exp(-t / 0.035))
    y = body + tine
    y = y + 0.16 * y ** 2
    y -= 0.16 * 0.5                                  # remove most of the asymmetry's DC
    dec = 1.9 * ring * (440.0 / f) ** 0.35           # low notes ring longer
    env = np.exp(-t / dec) * (0.7 + 0.3 * np.exp(-t / 0.25))
    return fade(y * env * 0.25 * vel, a=att, r=min(0.12, dur * 0.4))


def upright(midi: float, dur: float, vel: float = 1.0, att: float = 0.003) -> np.ndarray:
    """Round upright-style bass: plucked fundamental with a small pitch settle,
    upper harmonics dying faster than the fundamental, and a soft finger thump."""
    t = tt(dur)
    f = hz(midi) * (1 + 0.010 * np.exp(-t / 0.035))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros_like(t)
    for k, a in ((1, 1.0), (2, 0.55), (3, 0.28), (4, 0.13), (5, 0.06), (6, 0.03)):
        y += a * np.sin(k * ph) * np.exp(-t * (1.1 + 2.4 * (k - 1)))
    thump = sos_filter(noise(dur), "bandpass", [150, 700]) * np.exp(-t / 0.012) * 0.35
    env = 0.75 * np.exp(-t / 0.9) + 0.25 * np.exp(-t / 2.5)
    return fade((y * env + thump) * 0.5 * vel, a=att, r=min(0.06, dur * 0.3))


def feather_kick(vel: float = 1.0, att: float = 0.001) -> np.ndarray:
    t = tt(0.3)
    f = 50 + (95 - 50) * np.exp(-t / 0.03)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
    return fade(sos_filter(y, "lowpass", 400) * 0.6 * vel, a=att, r=0.03)


def brush_tap(vel: float = 1.0) -> np.ndarray:
    """Brush slap on the snare: a soft wire-buzz noise burst with a hint of drum body."""
    d = 0.30
    t = tt(d)
    wires = sos_filter(noise(d), "bandpass", [1100, 7500], order=2)
    wires *= (1 - np.exp(-t / 0.003)) * np.exp(-t / 0.065)
    body = np.sin(2 * np.pi * 196 * t) * np.exp(-t / 0.035) * 0.25
    return fade((wires + body) * 0.55 * vel, a=0.001, r=0.03)


def brush_sweep(dur: float, vel: float = 1.0) -> np.ndarray:
    """One circular brush stroke across the snare head: a soft 'shhh' that swells and
    fades within the beat, with the band drifting as the brush turns (stereo)."""
    t = tt(dur)
    ph = t / dur
    env = np.sin(np.pi * ph) ** 1.6
    out = []
    for ch in range(2):
        lo = sos_filter(noise(dur), "bandpass", [1600, 5000], order=2)
        hi = sos_filter(noise(dur), "bandpass", [4500, 11000], order=2)
        mix = (0.5 + 0.5 * np.cos(2 * np.pi * (ph + 0.25 * ch)))
        out.append((lo * (1 - 0.5 * mix) + hi * 0.5 * mix) * env)
    return np.stack(out, axis=1) * 0.16 * vel


def brushed_cymbal(dur: float = 2.2, vel: float = 1.0, att: float = 0.001) -> np.ndarray:
    """Brushed ride/crash: band-limited noise wash plus a few inharmonic bell partials."""
    t = tt(dur)
    out = []
    for ch in range(2):
        wash = sos_filter(noise(dur), "bandpass", [3200, 13500], order=2) * np.exp(-t / 0.75)
        bell = np.zeros_like(t)
        for r in (1.0, 1.47, 1.83, 2.41, 2.97):
            fr = 2350 * r * rng.uniform(0.99, 1.01)
            bell += np.sin(2 * np.pi * fr * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / 0.5)
        out.append(fade(wash + 0.05 * bell, a=att, r=0.08))
    return np.stack(out, axis=1) * 0.22 * vel


def reverb(x: np.ndarray, rt60: float = 1.0, predelay: float = 0.014) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR (small warm room)."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [300, 6000]) * env
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
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    os = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os)) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 110.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak. Gain is held
    over the look-ahead window, released through a one-pole, then box-smoothed
    (edge-safe). It never clips the waveform."""
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
    keys = np.zeros((N, 2))     # EP comping + melody (gets the tremolo)
    drums = np.zeros((N, 2))
    low = np.zeros((N, 2))      # bass + kick: the only content below 120 Hz (mono)
    verb_send = np.zeros((N, 2))
    end_play = T(11) + 0.82 * (BUTTON_T - T(11))   # everything before the button releases by ~7.84 s

    # --- comping: Charleston (beat 1 + pushed "and of 2"), rootless voicings
    Bbmaj7, Gm7 = (57, 60, 62, 65), (53, 57, 58, 62)
    Cm7, F7 = (51, 55, 58, 62), (51, 55, 57, 62)
    Ebmaj7 = (55, 58, 62, 65)
    comps = [(0, Bbmaj7, 1.0), (1 + SWING, Gm7, 0.62), (4, Cm7, 0.66), (5 + SWING, F7, 0.62),
             (8, Ebmaj7, 0.66), (10, Cm7, 0.6), (11, F7, 0.62)]
    for i, (b, ch, vel) in enumerate(comps):
        t0 = T(b)
        t1 = T(comps[i + 1][0]) - 0.03 if i + 1 < len(comps) else end_play
        for j, m in enumerate(ch):
            v = epiano(m, t1 - t0, vel)
            place(keys, v, t0 + 0.004 * j * (b != 0), 0.55, pan=(-0.25, -0.08, 0.08, 0.25)[j])
            place(verb_send, v, t0, 0.18, pan=(-0.25, -0.08, 0.08, 0.25)[j])

    # --- melody (EP right hand, an octave above the comping)
    mel = [(0, 77), (1, 74), (1 + SWING, 77), (2, 79), (3 + SWING, 77),
           (4, 75), (5, 74), (5 + SWING, 72), (6, 69), (7, 72),
           (8, 79), (8 + SWING, 77), (9, 75), (10, 74), (11, 69)]
    for i, (b, m) in enumerate(mel):
        t0 = T(b)
        t1 = T(mel[i + 1][0]) - 0.015 if i + 1 < len(mel) else end_play
        vel = 0.95 if b == int(b) else 0.8
        v = epiano(m, t1 - t0, vel)
        place(keys, v, t0, 0.74 * (1.12 if i == 0 else 1.0), pan=0.05)
        place(verb_send, v, t0, 0.25, pan=0.05)

    # --- walking bass, quarter notes
    walk = [34, 38, 43, 37, 36, 39, 41, 40, 39, 43, 36, 41]
    for b, m in enumerate(walk):
        t0 = T(b)
        t1 = T(b + 1) - 0.02 if b < 11 else end_play
        place(low, upright(m, t1 - t0, 1.1 if b == 0 else 0.9 + 0.06 * (b % 2 == 0)), t0, 1.0)

    # --- drums
    for b in range(12):
        place(drums, brush_sweep(T(b + 1) - T(b) if b < 11 else end_play - T(b), 0.85 + 0.25 * (b >= 8)),
              T(b), 1.0, pan=-0.15)
        if b % 2 == 1:
            place(drums, brush_tap(0.8 if b < 8 else 0.9), T(b), 1.0, pan=-0.1)
            place(verb_send, brush_tap(0.8), T(b), 0.2)
        if b % 2 == 0:
            place(low, feather_kick(0.55 if b else 1.0), T(b), 1.0)
        if b % 4 == 3 and b < 11:
            place(drums, brush_tap(0.35), T(b + SWING), 1.0, pan=-0.1)   # swung "and of 4"
    for k, b in enumerate((11 + 1 / 3, 11 + 2 / 3)):                     # triplet pickup into the button
        place(drums, brush_tap(0.45 + 0.15 * k), T(b), 1.0, pan=-0.1)
    place(drums, brushed_cymbal(2.4, 0.9), 0.0, 1.0)
    place(verb_send, brushed_cymbal(1.2, 0.5), 0.0, 0.3)

    # --- button on frame 240: bass, kick, Bb6/9 chord, melody resolve, cymbal
    ring = DURATION_SEC - BUTTON_T
    place(low, upright(34, ring, 1.25, att=0.0004), BUTTON_T, 1.0)
    place(low, feather_kick(1.1, att=0.0004), BUTTON_T, 1.0)
    for j, m in enumerate((50, 55, 60, 65, 70, 74)):
        v = epiano(m, ring, 0.95 if m < 70 else 1.0, att=0.0004, ring=0.6)
        pan = (-0.3, -0.15, 0.0, 0.15, 0.05, 0.1)[j]
        place(keys, v, BUTTON_T, 0.55 if m < 70 else 0.6, pan=pan)
        place(verb_send, v, BUTTON_T, 0.32, pan=pan)
    place(drums, brushed_cymbal(ring, 1.0, att=0.0004), BUTTON_T, 1.0)
    place(drums, brush_tap(1.0), BUTTON_T, 0.8, pan=-0.1)
    place(verb_send, brushed_cymbal(1.5, 0.6), BUTTON_T, 0.3)

    # --- bus processing
    tr = 1 + 0.22 * np.sin(2 * np.pi * 4.8 * np.arange(N) / SR)        # stereo tremolo (autopan)
    keys = keys * np.stack([tr, 2 - tr], axis=1)
    keys = sos_filter(keys, "highpass", 140, order=4)
    keys = sos_filter(keys, "lowpass", 9000, order=2)                  # warm, not glassy
    drums = sos_filter(drums, "highpass", 160, order=4)
    wet = sos_filter(reverb(verb_send, rt60=1.1), "highpass", 200, order=4) * 0.5
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    low = sos_filter(low, "lowpass", 2500, order=2)

    mix = low * 0.78 + keys * 1.0 + drums * 0.9 + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 20, order=2)
    mix = sos_filter(mix, "lowpass", 16500, order=4)

    nf = int(0.25 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    y = y - y.mean(axis=0, keepdims=True)                 # constant per-channel DC trim
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    pcm[0] = 0
    pcm[-48:] = 0
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
