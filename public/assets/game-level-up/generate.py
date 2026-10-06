"""game-level-up: Opus Sound Directory

A 2.5-second chiptune level-up fanfare in C major at 150 BPM, built like a
four-channel 8-bit sound chip. Frame 0 opens on a punch: a triangle kick, a
noise-channel crack and the first note of a 25 % duty pulse arpeggio. Sixteenth
note arpeggios then climb through C, F and G (I-IV-V), shadowed by a thinner
12.5 % duty pulse playing a "chip echo" a dotted thirty-second behind. A
triangle bass bounces in octaves, and the noise channel rolls from sixteenths
into thirty-seconds as the arpeggio breaks into a fast run up to C7. Everything
stops for a breath, and on frame 45 (1.5 s) a triumphant C major chord lands:
both pulses (with delayed vibrato), triangle root, kick and a noise crash. The
chord steps down in 60 Hz volume frames under a high, sparkling 12.5 % duty
arpeggio that ping-pongs across the stereo field and fades to silence. All
oscillators are additive and band-limited (partials below 16 kHz). The triangle
bass and kick are the only content below 120 Hz, and they are mono.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 150245
DURATION_SEC = 2.5
BPM = 150
KEY = "C major"
FPS = 30
CUE_FRAMES = (0, 45)           # frame 0: opening punch, frame 45: level-up chord
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
BEAT = 60.0 / BPM              # 0.4 s
S16 = BEAT / 4                 # 0.1 s
S32 = BEAT / 8                 # 0.05 s
HIT_T = CUE_FRAMES[1] / FPS    # 1.5 s
GAP_T = HIT_T - 0.05           # pre-hit breath starts here
F_MAX = 16000.0                # highest partial any oscillator may produce

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


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


def chip_env(n: int, levels: np.ndarray, attack_ms: float = 0.3, release_ms: float = 4.0) -> np.ndarray:
    """Volume envelope stepped at the 60 Hz chip frame rate (a 4-bit-ish staircase given
    as one level per 1/60 s), smoothed by 1.5 ms so steps never click. The attack is a
    sub-millisecond raised cosine and the tail ends in a short cosine release."""
    frame = SR / 60.0
    idx = np.minimum((np.arange(n) / frame).astype(int), len(levels) - 1)
    env = np.asarray(levels, float)[idx]
    env = uniform_filter1d(env, size=int(0.0015 * SR) + 1, mode="nearest")
    na = max(1, int(attack_ms * 1e-3 * SR))
    env[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    nr = max(1, int(release_ms * 1e-3 * SR))
    env[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    return env


def decay_levels(dur: float, start: float = 15, per_frame: float = 1.0, floor: float = 0) -> np.ndarray:
    """Chip-style linear volume decay in 1/15 steps: one step every `1/per_frame` frames."""
    nf = int(np.ceil(dur * 60)) + 1
    lv = np.maximum(floor, start - np.floor(np.arange(nf) * per_frame))
    return lv / 15.0


# ---------------------------------------------------------------- chip channels
def pulse(midi: float, dur: float, duty: float, levels: np.ndarray,
          vib_cents: float = 0.0, vib_delay: float = 0.15, vib_rate: float = 6.0,
          release_ms: float = 4.0) -> np.ndarray:
    """Band-limited pulse wave by additive synthesis: harmonic k has amplitude
    (2/(k*pi)) * sin(k*pi*duty), all partials below F_MAX even at the vibrato peak."""
    t = tt(dur)
    f0 = hz(midi)
    vib = np.zeros_like(t)
    if vib_cents:
        ramp = np.clip((t - vib_delay) / 0.12, 0, 1)
        vib = vib_cents * ramp * np.sin(2 * np.pi * vib_rate * t)
    f = f0 * 2 ** (vib / 1200)
    ph = 2 * np.pi * np.cumsum(f) / SR - 2 * np.pi * f[0] / SR   # phase starts at 0
    kmax = int(F_MAX // (f0 * 2 ** (abs(vib_cents) / 1200)))
    y = np.zeros_like(t)
    for k in range(1, kmax + 1):
        y += (2 / (k * np.pi)) * np.sin(k * np.pi * duty) * np.sin(k * ph)
    y /= 0.9
    return y * chip_env(len(t), levels, release_ms=release_ms)


def triangle(midi: float, dur: float, levels: np.ndarray | None = None,
             release_ms: float = 6.0) -> np.ndarray:
    """Band-limited triangle (odd harmonics, 1/k^2). The chip triangle has no volume
    control, so it is either on or off: default level is constant full."""
    t = tt(dur)
    f = hz(midi)
    y = np.zeros_like(t)
    for i, k in enumerate(range(1, int(F_MAX // f) + 1, 2)):
        y += ((-1) ** i) / k ** 2 * np.sin(2 * np.pi * k * f * t)
    y *= 8 / np.pi ** 2
    lv = np.ones(int(np.ceil(dur * 60)) + 1) if levels is None else levels
    return y * chip_env(len(t), lv, attack_ms=1.0, release_ms=release_ms)


def tri_kick(dur: float = 0.16) -> np.ndarray:
    """Triangle-channel kick: a fast pitch sweep 220 -> 48 Hz (band-limited, mono)."""
    t = tt(dur)
    f = 48 + (220 - 48) * np.exp(-t / 0.022)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) - (1 / 9) * np.sin(3 * ph) + (1 / 25) * np.sin(5 * ph)
    env = np.exp(-t / 0.07)
    na = int(0.0004 * SR)
    env[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    nr = int(0.01 * SR)
    env[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    return y * env * 0.9


def noise_hit(dur: float, levels: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Noise channel: white noise band-limited to [lo, hi] (no sample-and-hold
    decimation), shaped by a 60 Hz stepped envelope."""
    y = sos_filter(noise(dur), "bandpass", [lo, hi], order=2)
    y /= np.sqrt(np.mean(y ** 2)) + 1e-12
    return 0.32 * y * chip_env(len(y), levels, attack_ms=0.3, release_ms=3.0)


def snare(vel: float = 1.0, dur: float = 0.09) -> np.ndarray:
    lv = decay_levels(dur, 15, 3.0) * vel
    body = triangle(55, dur, levels=np.maximum(0, decay_levels(dur, 15, 6.0)) * 0.35 * vel)  # short G3 tick
    return noise_hit(dur, lv, 1200, 9000) + body


def crash(dur: float = 0.95) -> np.ndarray:
    lv = decay_levels(dur, 12, 0.26)
    return np.stack([noise_hit(dur, lv, 3000, 14000), noise_hit(dur, lv, 3000, 14000)], axis=1)


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    lead = np.zeros((N, 2))     # pulse 1 (25 %)
    echo = np.zeros((N, 2))     # pulse 2 (12.5 %) chip echo / harmony
    low = np.zeros((N, 2))      # triangle bass + kick: the only content below 120 Hz
    perc = np.zeros((N, 2))     # noise channel
    post = np.zeros((N, 2))     # everything from the level-up chord on

    # ---- arpeggio climb: C | F | G (16ths), then a 32nd run to G6
    C, F, G = (60, 64, 67, 72), (65, 69, 72, 77), (67, 71, 74, 79)
    notes = []
    for bar, ch in enumerate((C, F, G)):
        for i, m in enumerate(ch):
            notes.append((bar * BEAT + i * S16, m, S16))
    run = (71, 74, 77, 79, 84)                      # B5 D6 F6 G6 C7 (32nds into the breath)
    for i, m in enumerate(run):
        notes.append((3 * BEAT + i * S32, m, S32))
    for i, (t0, m, d) in enumerate(notes):
        accent = 15 if (i % 4 == 0 and t0 < 3 * BEAT) else 12
        lv = np.concatenate([[accent / 15, accent / 15], decay_levels(d, accent - 1, 1.0, floor=7)[:-2]])
        p = pulse(m, d * 0.92, 0.25, lv)
        place(lead, p, t0, 0.34 * (1 + 0.15 * (t0 / HIT_T)), pan=-0.2)
        # chip echo: same line on the 12.5 % channel, a dotted 32nd later, softer, other side
        te = t0 + 0.75 * S16
        if te < GAP_T - 0.01:
            pe = pulse(m + 12 if t0 >= 3 * BEAT else m, d * 0.85, 0.125, lv * 0.55)
            place(echo, pe, te, 0.30, pan=0.35)

    # ---- triangle bass: octave bounce in 8ths on the chord roots
    roots = (48, 53, 55)                            # C3 F3 G3
    for bar, r in enumerate(roots):
        for j in range(2):
            m = r - 12 if j == 0 else r
            place(low, triangle(m, S16 * 2 * 0.9), bar * BEAT + j * 2 * S16, 0.45)
    # climb under the run: G2 A2 B2 (8th-triplet-ish 32nds) stops at the breath
    for i, m in enumerate((43, 45, 47, 48)):
        t0 = 3 * BEAT + i * S32 * 1.25
        place(low, triangle(m, S32 * 1.15), t0, 0.55)

    # ---- kick + noise channel
    for t0 in (0.0, BEAT, 2 * BEAT):
        place(low, tri_kick(), t0, 0.9)
    place(perc, snare(1.0, 0.14), 0.0, 1.0)         # opening crack
    place(perc, snare(0.85), BEAT + 2 * S16, 0.9)
    # roll: 16ths through the G bar, 32nds through the run, rising velocity
    roll = [2 * BEAT + i * S16 for i in range(4)] + [3 * BEAT + i * S32 for i in range(5)]
    for i, t0 in enumerate(roll):
        v = 0.45 + 0.55 * i / (len(roll) - 1)
        place(perc, snare(v, 0.07), t0, 0.8, pan=0.12 * (-1) ** i)

    # ---- the breath before the hit: cut the pre-hit buses with a 3 ms fade ending at GAP_T
    pre = lead + echo + perc
    pre = sos_filter(pre, "lowpass", 16500, order=2)
    g = np.ones(N)
    s1 = int(round(GAP_T * SR)); s0 = s1 - int(0.003 * SR)
    g[s0:s1] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, s1 - s0))
    g[s1:] = 0.0
    pre *= g[:, None]
    low_pre = low * g[:, None]

    # ---- frame 45: the level-up chord
    hold = 0.95
    lv_chord = np.concatenate([np.ones(9), decay_levels(hold, 14, 0.33, floor=0)])
    lv_chord = lv_chord[: int(np.ceil(hold * 60)) + 1]
    for m, duty, gain, pan in ((72, 0.25, 0.48, -0.25), (76, 0.125, 0.36, 0.25),
                               (79, 0.25, 0.30, 0.0), (84, 0.125, 0.25, 0.0)):
        place(post, pulse(m, hold, duty, lv_chord, vib_cents=18, vib_delay=0.16, release_ms=20), HIT_T, gain, pan)
    tri_lv = np.concatenate([np.ones(int(0.55 * 60)), np.zeros(60)])
    place(post, triangle(36, 0.75, levels=tri_lv, release_ms=10), HIT_T, 0.5)
    place(post, triangle(48, 0.75, levels=tri_lv, release_ms=10), HIT_T, 0.25)
    place(post, tri_kick(0.2), HIT_T, 1.0)
    place(post, crash(), HIT_T, 0.7)

    # ---- sparkle: high 12.5 % arpeggio, ping-pong, decaying, 32nds
    sp = (84, 88, 91, 96, 91, 88, 96, 100, 96, 91, 100, 103, 100, 96, 103, 108)
    t0 = HIT_T + 0.12
    for i, m in enumerate(sp):
        tn = t0 + i * S32 * 0.95
        vol = 0.85 * (1 - i / len(sp)) ** 1.4 + 0.05
        lv = np.concatenate([[1.0], decay_levels(0.06, 13, 2.0)]) * vol
        place(post, pulse(m, 0.055, 0.125, lv), tn, 0.22, pan=0.6 * (-1) ** i)
        place(post, pulse(m, 0.05, 0.125, lv * 0.45), tn + 0.075, 0.22, pan=-0.6 * (-1) ** i)

    mix = pre + low_pre + post
    # mono below 120 Hz: low bus is mono already; steep side high-pass at 250 Hz
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=6)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 20, order=2)
    mix = sos_filter(mix, "lowpass", 17000, order=4)
    nf = int(0.12 * SR)
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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 60.0) -> np.ndarray:
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
