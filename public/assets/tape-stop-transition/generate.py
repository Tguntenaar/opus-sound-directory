"""tape-stop-transition: Opus Sound Directory

A 1.5-second D minor funk transition at 120 BPM. It opens on frame 0 with a tight kick,
a bright clavinet-style Dm7 stab (struck-string additive tone with a pickup comb, slight
stiffness and a wah-ish mid peak), a round synth bass on D2 and an accented hat. A busy
sixteenth-note pocket follows: ghost clav chucks, an octave bass pop, ghost snare, a
cracking backbeat on beat 2 and a G9 stab on its "and". From 0.55 s the whole groove
(drums, reverb and all) tape-stops: one variable-rate read head decelerates, so speed and
pitch glide down together into a low mechanical groan. It lands dead silent exactly on
frame 30 (1.0 s) through a 1 ms fade ending on the cue sample. About 150 ms later a tiny,
soft mono thump (the reel settling) blooms and dies away. Below 120 Hz there is only the
mono kick, bass and thump.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 1230305
DURATION_SEC = 1.5
BPM = 120
KEY = "D minor"
FPS = 30
CUE_FRAMES = (0, 30)           # frame 0: groove hit, frame 30: tape stop lands in silence
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
STEP = 60.0 / BPM / 4          # sixteenth = 0.125 s
CUT_T = CUE_FRAMES[1] / FPS    # 1.0 s
CUT_S = int(round(CUT_T * SR))
STOP_T = 0.55                  # tape starts decelerating
SPEED_END = 0.10               # read speed reached at the cue (-40 semitones)
THUMP_T = CUT_T + 0.15

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.0005, r: float = 0.005) -> np.ndarray:
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    x[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
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


def peaking_eq(x, f0, gain_db, q):
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * a_, -2 * np.cos(w0), 1 - alpha * a_]
    a = [1 + alpha / a_, -2 * np.cos(w0), 1 - alpha / a_]
    return signal.lfilter(b, a, x, axis=0)


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


# ---------------------------------------------------------------- voices
def clav_note(midi: float, dur: float, mute: float = 0.0) -> np.ndarray:
    """Clavinet-ish struck string: additive partials with slight stiffness (inharmonic
    stretch), a pickup-position comb, faster decay for higher partials, and a damped
    key-off. mute > 0 gives the short, choked 'chuck'."""
    f0 = hz(midi)
    t = tt(dur + 0.03)
    y = np.zeros_like(t)
    B = 1.2e-4
    for k in range(1, 60):
        fk = k * f0 * np.sqrt(1 + B * k * k)
        if fk > 13000:
            break
        a = abs(np.sin(np.pi * k * 0.13)) / k ** 0.75
        dec = (0.55 / (1 + 0.09 * k)) * (1 - 0.8 * mute)
        y += a * np.exp(-t / dec) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 2 * np.pi))
    # key-off damping (tangent leaves the string, felt kills it)
    off = np.clip((t - dur) / 0.022, 0, 1)
    y *= 0.5 + 0.5 * np.cos(np.pi * off)
    # tangent 'tick'
    tick = sos_filter(noise(len(t) / SR), "bandpass", [2000, 7000]) * np.exp(-t / 0.002) * (0.08 + 0.25 * mute)
    return fade((y + tick) * 0.22, a=0.0004, r=0.004)


def clav_chord(midis, dur, mute=0.0, spread=0.35):
    out = np.zeros((int(round((dur + 0.03) * SR)), 2))
    for i, m in enumerate(midis):
        v = clav_note(m, dur, mute)
        pan = spread * (2 * i / max(1, len(midis) - 1) - 1)
        th = (pan + 1) * np.pi / 4
        out[: len(v), 0] += v * np.cos(th) * np.sqrt(2)
        out[: len(v), 1] += v * np.sin(th) * np.sqrt(2)
    return out


def bass_note(midi: float, dur: float, pop: float = 0.0) -> np.ndarray:
    """Round finger-style synth bass: bright plucked attack settling to a near-sine body."""
    t = tt(dur + 0.02)
    f = hz(midi)
    y = np.zeros_like(t)
    for k, a in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)):
        dec = 0.35 / k ** (1.2 - 0.6 * pop)
        y += a * (0.35 + 0.65 * np.exp(-t / dec)) * np.sin(2 * np.pi * k * f * t)
    off = np.clip((t - dur) / 0.018, 0, 1)
    y *= 0.5 + 0.5 * np.cos(np.pi * off)
    return fade(y * 0.42, a=0.0012, r=0.004)


def kick() -> np.ndarray:
    t = tt(0.24)
    f = 52 + (150 - 52) * np.exp(-t / 0.022)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.085)
    beater = sos_filter(noise(0.24), "bandpass", [1200, 5000]) * np.exp(-t / 0.003) * 0.3
    return fade(np.tanh(1.8 * (body + beater)) / np.tanh(1.8), a=0.0004, r=0.01)


def snare(ghost: bool = False) -> np.ndarray:
    d = 0.11 if ghost else 0.2
    t = tt(d)
    tone = (np.sin(2 * np.pi * 196 * t) + 0.5 * np.sin(2 * np.pi * 331 * t)) * np.exp(-t / 0.04)
    nz = sos_filter(noise(d), "bandpass", [1600, 9000]) * np.exp(-t / (0.035 if ghost else 0.07))
    crack = sos_filter(noise(d), "highpass", 3000) * np.exp(-t / 0.004)
    y = 0.55 * tone + 0.9 * nz + 0.5 * crack
    return fade(y * (0.18 if ghost else 0.5), a=0.0004, r=0.008)


def hat(accent: float = 1.0, open_: bool = False) -> np.ndarray:
    d = 0.16 if open_ else 0.05
    t = tt(d)
    y = sos_filter(noise(d), "highpass", 7500, order=4)
    y = sos_filter(y, "lowpass", 15000, order=4)
    y *= np.exp(-t / (0.05 if open_ else 0.012))
    return fade(y * 0.28 * accent, a=0.0004, r=0.004)


def reverb(x: np.ndarray, rt60: float, band=(300, 6000), predelay: float = 0.008) -> np.ndarray:
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", list(band)) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                     signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)


def thump() -> np.ndarray:
    """Tiny soft mono thump: a felt-damped low sine with a breath of low noise."""
    t = tt(N / SR - THUMP_T)
    f = 62 * (1 + 0.25 * np.exp(-t / 0.02))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / 0.07) + 0.3 * np.sin(2 * ph) * np.exp(-t / 0.035)
    y += sos_filter(noise(len(t) / SR), "lowpass", 350) * np.exp(-t / 0.02) * 0.25
    att = int(0.005 * SR)
    y[:att] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, att))
    return y


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


# ---------------------------------------------------------------- groove + tape stop
def groove(src_len: float) -> np.ndarray:
    """The funk pocket at normal speed (the 'tape'). Low bus is mono."""
    n = int(round(src_len * SR))
    low = np.zeros((n, 2))
    drums = np.zeros((n, 2))
    keys = np.zeros((n, 2))
    send = np.zeros((n, 2))

    Dm7 = (62, 65, 69, 72)         # D4 F4 A4 C5
    G9 = (59, 65, 69, 71 + 3)      # B3 F4 A4 D5 (rootless G9 colour)
    s = lambda i: i * STEP

    # kick / snare / hats (sixteenth grid)
    for i in (0, 3, 5):
        place(low, kick(), s(i), 1.0 if i == 0 else 0.85)
    place(drums, snare(), s(4), 1.0, pan=0.05)
    place(send, snare(), s(4), 0.35)
    for i in (2, 7):
        place(drums, snare(ghost=True), s(i), 1.0, pan=0.1)
    for i in range(8):
        acc = (1.0, 0.45, 0.75, 0.5)[i % 4]
        place(drums, hat(acc * rng.uniform(0.9, 1.05), open_=(i == 6)), s(i), 1.0, pan=-0.3)

    # clav: stab, chuck, chuck, stab(off), -, G9 stab (held into the stop), chuck
    place(keys, clav_chord(Dm7, 0.095), s(0), 1.0)
    place(keys, clav_chord(Dm7, 0.03, mute=1.0), s(1), 0.55)
    place(keys, clav_chord(Dm7, 0.03, mute=1.0), s(2) + 0.01, 0.45)
    place(keys, clav_chord(Dm7, 0.085), s(3), 0.85)
    place(keys, clav_chord(G9, 0.32), s(5), 0.95)
    place(keys, clav_chord(Dm7, 0.03, mute=1.0), s(7), 0.5)
    for v in (keys,):
        place(send, v, 0.0, 0.18)

    # bass: D2 . D3(pop) C3 | F2 G2~ (held into the stop)
    for i, m, d, p in ((0, 38, 0.11, 0.0), (2, 50, 0.06, 1.0), (3, 48, 0.1, 0.5),
                       (4, 41, 0.1, 0.0), (5, 43, 0.3, 0.3)):
        place(low, bass_note(m, d, p), s(i), 0.9)

    keys = peaking_eq(sos_filter(keys, "highpass", 180, order=2), 1400, 6.0, 1.3)
    drums = sos_filter(drums, "highpass", 140, order=2)
    wet = sos_filter(reverb(send, 0.35), "highpass", 250, order=2) * 0.4
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)
    return low * 0.9 + drums + keys * 1.1 + wet


def tape_stop(src: np.ndarray) -> np.ndarray:
    """Variable-rate read: speed 1 until STOP_T, then decelerates (concave curve) to
    SPEED_END on the cue. Reading slower than real time only lowers pitch, so a
    4x-oversampled source with linear interpolation stays alias-free."""
    t = np.arange(CUT_S) / SR
    tau = np.clip((t - STOP_T) / (CUT_T - STOP_T), 0, 1)
    speed = SPEED_END + (1 - SPEED_END) * (1 - tau) ** 1.35
    pos = np.concatenate([[0.0], np.cumsum(speed)[:-1]])        # source sample index
    up = signal.resample_poly(src, 4, 1, axis=0)
    xi = np.arange(len(up)) / 4.0
    out = np.stack([np.interp(pos, xi, up[:, c]) for c in range(2)], axis=1)
    # playback losses: a little level and top end go with the speed
    out *= (0.55 + 0.45 * speed)[:, None]
    return out, speed


def render() -> np.ndarray:
    src = groove(0.9)
    stopped, speed = tape_stop(src)

    mix = np.zeros((N, 2))
    mix[:CUT_S] = stopped
    # outgoing bus filtering FIRST: mono low end (steep side high-pass), DC guard, top
    m_, s_ = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    s_ = sos_filter(s_, "highpass", 250, order=6)
    mix = np.stack([m_ + s_, m_ - s_], axis=1)
    mix = sos_filter(mix, "highpass", 28, order=2)
    mix = sos_filter(mix, "lowpass", 16000, order=4)
    # the cut: 1 ms raised-cosine ending exactly on the cue sample, silence after
    nf = int(0.001 * SR)
    mix[CUT_S - nf:CUT_S] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf + 1)[1:]))[:, None]
    mix[CUT_S:] = 0.0

    # after the cut: the reel thump (mono)
    th = np.zeros((N, 2))
    place(th, thump(), THUMP_T, 0.28)
    th = sos_filter(th, "highpass", 22, order=2)
    th[: int(THUMP_T * SR)] = 0.0
    mix += th

    nt = int(0.12 * SR)
    mix[-nt:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nt)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    gap = slice(CUT_S, int(THUMP_T * SR))
    y[gap] = 0.0                                  # dead silent between the stop and the thump
    # DC: the cut truncates the high-pass settling of the kick/bass, leaving ~-1.5e-4 of
    # mean. Remove it with a 1 Hz-wide Hann-shaped offset over the groove (zero at both
    # ends, so the first sample and the cut stay exact).
    w = np.sin(np.pi * np.arange(CUT_S) / CUT_S) ** 2
    y[:CUT_S] -= (y.sum(axis=0) / w.sum())[None, :] * w[:, None]
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    dither[gap] = 0.0
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
