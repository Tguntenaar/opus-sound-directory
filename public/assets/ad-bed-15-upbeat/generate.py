"""ad-bed-15-upbeat: Opus Sound Directory

A 15-second upbeat retail pulse in E major at 128 BPM, written to sit under a
direct-to-consumer ad voiceover. It opens on a bright chord-stab hit at frame 0
(kick, crash and a full E major stab). It then settles into a four-on-the-floor
groove: off-beat bass, syncopated chord plucks moving I-V-vi-IV, claps on 2 and 4,
and shimmering hats. A filtered noise riser and a snare roll build through bar 5.
The bar at 9.375 s (the "about 10 s" lift) adds a crash, a wide pad and a
sparkling sixteenth-note arpeggio. The groove then drops out for half a beat, a
reverse swell pulls in, and a clean button tag on the tonic lands exactly on
frame 420 (14.0 s) and rings out to silence. Everything below 120 Hz is reserved
for a mono kick and bass. The music bus is gently scooped around 2.5 kHz so a
voice sits on top.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d

SAMPLE_RATE = 48000
SEED = 128015
DURATION_SEC = 15
BPM = 128
KEY = "E major"
FPS = 30
CUE_FRAMES = (0, 420)          # frame 0: opening hit, frame 420: button tag
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
BEAT = 60.0 / BPM              # 0.46875 s = exactly 22500 samples
BAR = 4 * BEAT                 # 15 s = exactly 8 bars
TAG_T = CUE_FRAMES[1] / FPS    # 14.0 s
LIFT_T = 5 * BAR               # 9.375 s, downbeat of bar 6

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


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
def additive_pluck(f0: float, dur: float, bright: float = 1.0, decay: float = 6.0,
                   detune_cents: float = 0.0) -> np.ndarray:
    """Band-limited saw-like pluck. Each harmonic decays faster than the one below
    it, which gives a filter-envelope sound with no aliasing (all partials < 16 kHz)."""
    t = tt(dur)
    f = f0 * 2 ** (detune_cents / 1200)
    y = np.zeros_like(t)
    kmax = int(min(16000, 0.4 * SR) // f)
    for k in range(1, kmax + 1):
        amp = (1.0 / k) * np.exp(-((k - 1) * 0.18) / bright)
        if amp < 1e-4:
            break
        env = np.exp(-t * decay * (1 + 0.35 * (k - 1) / bright))
        y += amp * env * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
    return fade(y / 1.6, a=0.002, r=0.02)


def stereo_pluck(midi, dur, bright=1.0, decay=6.0, spread=4.0):
    l = additive_pluck(hz(midi), dur, bright, decay, -spread)
    r = additive_pluck(hz(midi), dur, bright, decay, +spread)
    return np.stack([l, r], axis=1)


def pad_voice(midi: float, dur: float, att: float = 0.25, rel: float = 0.35) -> np.ndarray:
    """Soft detuned saw pad, harmonics rolled off above ~1.8 kHz, stereo detune."""
    t = tt(dur)
    out = np.zeros((len(t), 2))
    for ch, cents in enumerate((-9, -3, 3, 9)):
        f = hz(midi) * 2 ** (cents / 1200)
        y = np.zeros_like(t)
        for k in range(1, int(9000 // f) + 1):
            a = (1 / k) / (1 + (k * f / 1800) ** 2)
            y += a * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
        out[:, ch % 2] += y
    env = np.ones_like(t)
    na, nr = int(att * SR), int(rel * SR)
    env[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    env[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return out * env[:, None] * 0.35


def kick(big: bool = False) -> np.ndarray:
    t = tt(0.42 if big else 0.32)
    f = 47 + (170 - 47) * np.exp(-t / 0.032)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    body *= np.exp(-t / (0.20 if big else 0.14))
    click = sos_filter(noise(len(t) / SR), "bandpass", [1500, 6000]) * np.exp(-t / 0.004) * 0.25
    return fade(np.tanh(1.6 * (body + click)) / np.tanh(1.6), a=0.0005, r=0.01)


def clap(gain_tail: float = 1.0) -> np.ndarray:
    t = tt(0.25)
    env = np.zeros_like(t)
    for off in (0.0, 0.009, 0.019):
        m = t >= off
        env[m] += np.exp(-(t[m] - off) / 0.005)
    m = t >= 0.026
    env[m] += gain_tail * 0.7 * np.exp(-(t[m] - 0.026) / 0.06)
    y = sos_filter(noise(0.25), "bandpass", [900, 4200], order=2) * env
    return fade(y * 0.45, a=0.0005, r=0.01)


def hat(open_: bool = False) -> np.ndarray:
    d = 0.22 if open_ else 0.05
    t = tt(d)
    y = sos_filter(noise(d), "highpass", 7000, order=4)
    y = sos_filter(y, "lowpass", 15500, order=4)
    y *= np.exp(-t / (0.075 if open_ else 0.014))
    return fade(y * 0.35, a=0.0005, r=0.005)


def crash(dur: float = 2.2) -> np.ndarray:
    t = tt(dur)
    l = sos_filter(noise(dur), "bandpass", [3800, 14500], order=2)
    r = sos_filter(noise(dur), "bandpass", [3800, 14500], order=2)
    env = np.exp(-t / 0.55)
    return np.stack([fade(l * env, 0.0005, 0.05), fade(r * env, 0.0005, 0.05)], axis=1) * 0.28


def bass_note(midi: float, dur: float) -> np.ndarray:
    t = tt(dur)
    f = hz(midi)
    y = np.sin(2 * np.pi * f * t) + 0.32 * np.sin(4 * np.pi * f * t) + 0.10 * np.sin(6 * np.pi * f * t)
    env = np.exp(-t / 0.22) * 0.6 + 0.4
    return fade(y * env * 0.55, a=0.004, r=0.03)


def bell(midi: float, dur: float = 1.2) -> np.ndarray:
    t = tt(dur)
    f = hz(midi)
    y = np.zeros_like(t)
    for ratio, amp, dec in ((1.0, 1.0, 0.5), (2.756, 0.45, 0.28), (5.404, 0.22, 0.14), (8.933, 0.10, 0.08)):
        if ratio * f < 16000:
            y += amp * np.exp(-t / dec) * np.sin(2 * np.pi * ratio * f * t)
    return fade(y * 0.3, a=0.0008, r=0.05)


def svf_bandpass(x: np.ndarray, fc: np.ndarray, q: float) -> np.ndarray:
    """Zavalishin TPT state-variable band-pass with per-sample cutoff (for sweeps)."""
    g = np.tan(np.pi * np.clip(fc, 20, 0.45 * SR) / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    y = np.empty(len(x))
    ic1 = ic2 = 0.0
    for n, (xn, b1, b2, b3) in enumerate(zip(x.tolist(), a1.tolist(), a2.tolist(), a3.tolist())):
        v3 = xn - ic2
        v1 = b1 * ic1 + b2 * v3
        v2 = ic2 + b2 * ic1 + b3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[n] = v1
    return y


def riser(dur: float) -> np.ndarray:
    t = tt(dur)
    fc = 350 * (9000 / 350) ** (t / dur) ** 1.4
    amp = (t / dur) ** 2.2
    l = svf_bandpass(noise(dur), fc, 2.5) * amp
    r = svf_bandpass(noise(dur), fc * 1.04, 2.5) * amp
    return np.stack([fade(l, 0.01, 0.004), fade(r, 0.01, 0.004)], axis=1) * 0.55


def reverse_swell(dur: float) -> np.ndarray:
    t = tt(dur)
    env = (t / dur) ** 3
    l = sos_filter(noise(dur), "bandpass", [2500, 12000]) * env
    r = sos_filter(noise(dur), "bandpass", [2500, 12000]) * env
    return np.stack([fade(l, 0.01, 0.003), fade(r, 0.01, 0.003)], axis=1) * 0.22


def reverb(x: np.ndarray, rt60: float = 1.4, predelay: float = 0.018) -> np.ndarray:
    """Decorrelated stereo exponential-noise IR convolution (bright plate-ish)."""
    t = tt(rt60 * 1.1)
    env = np.exp(-6.9 * t / rt60)
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [250, 7500]) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    out = np.stack([signal.fftconvolve(x[:, 0], irs[0])[: len(x)],
                    signal.fftconvolve(x[:, 1], irs[1])[: len(x)]], axis=1)
    return out


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


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 90.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak.
    The gain curve is held over the look-ahead window, recovers through a one-pole
    release, and is box-smoothed. It never clips the waveform."""
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
    g = np.convolve(g, np.ones(L + 1) / (L + 1), mode="same")
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
    drums = np.zeros((N, 2))
    low = np.zeros((N, 2))      # kick + bass: the only content below 120 Hz
    music = np.zeros((N, 2))    # plucks, pad, arp
    fx = np.zeros((N, 2))
    verb_send = np.zeros((N, 2))

    # chord per half bar: E | B | C#m | A | E | B | C#m A | B -> tag E
    E, B, Cm, A = (64, 68, 71), (63, 66, 71), (61, 64, 68), (61, 64, 69)
    roots = {E: 40, B: 35, Cm: 37, A: 33}  # E2, B1, C#2, A1
    halves = [E, E, B, B, Cm, Cm, A, A, E, E, B, B, Cm, A, B, B]

    def chord_at(t):
        return halves[min(15, int(t // (BAR / 2)))]

    groove_end = 7 * BAR + BEAT                  # 13.594 s: last groove beat (bar 8, beat 2)
    kicks = []

    # --- drums
    nbeats = int(groove_end / BEAT) + 1
    for b in range(nbeats):
        t = b * BEAT
        bar, beat = divmod(b, 4)
        if bar == 4 and beat == 3:          # drop the last kick of bar 5 for tension
            continue
        kicks.append(t)
        place(low, kick(big=(b == 0)), t, 0.95 if (b == 0 or bar >= 1) else 0.7)
        if beat in (1, 3) and bar >= 1:
            place(drums, clap(), t, 0.55)
            place(verb_send, clap(), t, 0.25)
    # hats: 8ths in bar 1, 16ths from bar 2, offbeat open hats from bar 3
    step = BEAT / 4
    for s in range(int(groove_end / step) + 1):
        t = s * step
        if t >= groove_end + 1e-9:
            break
        bar = int(t // BAR)
        pos = s % 4
        if pos == 2 and bar >= 2:
            place(drums, hat(open_=True), t, 0.38, pan=0.2)
        elif bar == 0 and pos != 0 and pos != 2:
            continue
        else:
            vel = (0.32 if pos == 0 else 0.22 if pos == 2 else 0.16) * (1.4 if t >= LIFT_T else 1.0)
            place(drums, hat(), t, vel * rng.uniform(0.85, 1.1), pan=-0.25)
    # snare roll through second half of bar 5 (8ths -> 16ths), rising
    roll_start = 4 * BAR + 2 * BEAT
    ts = [roll_start + i * BEAT / 2 for i in range(2)] + [roll_start + BEAT + i * BEAT / 4 for i in range(4)]
    for i, t in enumerate(ts):
        place(drums, clap(gain_tail=0.4), t, 0.18 + 0.06 * i, pan=0.1 * (-1) ** i)

    # --- bass: off-beat 8ths, root of the current chord, from bar 2
    for b in range(4, int(groove_end / BEAT)):
        t = b * BEAT + BEAT / 2
        if t >= groove_end:
            break
        place(low, bass_note(roots[chord_at(t)], BEAT * 0.45), t, 0.55)

    # --- plucks: syncopated chord stabs (16th steps 0,3,6,10,12)
    pattern = (0, 3, 6, 10, 12)
    for bar in range(8):
        for st in pattern:
            t = bar * BAR + st * step
            if t >= groove_end - 1e-9:
                break
            ch = chord_at(t)
            lifted = t >= LIFT_T
            bright = 0.45 if bar == 0 else 0.8 if not lifted else 1.2
            vel = (0.30 if st == 0 else 0.22) * rng.uniform(0.9, 1.05) * (0.6 if bar == 0 else 1.3 if lifted else 1.0)
            voicing = list(ch) + ([ch[0] + 12, ch[2] + 12] if lifted else [])   # octave doubling in the lift
            for i, m in enumerate(voicing):
                p = stereo_pluck(m, 0.38, bright=bright, decay=7.0)
                place(music, p, t + i * 0.002, vel * (0.7 if i >= 3 else 1.0))
                place(verb_send, p, t, vel * 0.25)

    # --- opening hit (frame 0)
    for i, m in enumerate([52, 64, 68, 71, 76]):
        p = stereo_pluck(m, 1.2, bright=1.3, decay=3.0)
        place(music, p, 0.0, 0.32)
        place(verb_send, p, 0.0, 0.15)
    place(fx, crash(), 0.0, 0.9)

    # --- riser into the lift
    place(fx, riser(BAR), 4 * BAR, 0.9)

    # --- the lift at bar 6: crash + pad + arp
    place(fx, crash(), LIFT_T, 1.0)
    for h in range(10, 14):
        t0, t1 = h * BAR / 2, min((h + 1) * BAR / 2, groove_end + 0.15)
        ch = halves[h]
        for m in ch:
            pv = pad_voice(m, (t1 - t0) + 0.35)
            place(music, pv, t0, 0.32)
            place(verb_send, pv, t0, 0.08)
    arp_seq = (0, 1, 2, 3, 2, 1, 0, 2)
    s = 0
    t = LIFT_T
    while t < groove_end - 1e-9:
        ch = chord_at(t)
        tones = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[0] + 24]
        m = tones[arp_seq[s % 8]]
        p = additive_pluck(hz(m), 0.22, bright=0.7, decay=11.0)
        place(music, p, t, 0.15, pan=0.35 if s % 2 else -0.35)
        place(verb_send, np.stack([p, p], 1), t, 0.06)
        s += 1
        t = LIFT_T + s * step

    # --- pre-tag: drop-out + reverse swell into frame 420
    sw = 0.30
    place(fx, reverse_swell(sw), TAG_T - sw, 1.0)

    # --- button tag (frame 420): big kick, bright tonic stab, crash, bell sparkle
    place(low, kick(big=True), TAG_T, 1.0)
    place(low, bass_note(40, 0.9), TAG_T, 0.55)
    for i, m in enumerate([52, 64, 68, 71, 76]):
        p = stereo_pluck(m, 1.0, bright=1.4, decay=3.2)
        place(music, p, TAG_T, 0.34)
        place(verb_send, p, TAG_T, 0.22)
    place(fx, crash(1.0), TAG_T, 0.8)
    for i, m in enumerate([88, 95, 100]):
        b = bell(m, 0.95)
        place(fx, b, TAG_T + 0.03 * i, 0.38, pan=(-0.4, 0.4, 0.0)[i])
        place(verb_send, np.stack([b, b], 1), TAG_T + 0.03 * i, 0.12)

    # --- bus processing
    # sidechain pump on the music bus from every kick
    duck = np.ones(N)
    tk = tt(0.25)
    shape = 1 - 0.45 * np.exp(-tk / 0.07) * (1 - np.exp(-tk / 0.002))
    for k in kicks:
        s0 = int(round(k * SR))
        e = min(N, s0 + len(shape))
        duck[s0:e] = np.minimum(duck[s0:e], shape[: e - s0])
    music *= duck[:, None]

    hp = lambda x: sos_filter(x, "highpass", 150, order=4)
    music = peaking_eq(hp(music), 2500, -2.5, 0.9)          # VO pocket
    drums = hp(drums)
    fx = hp(fx)
    wet = hp(reverb(verb_send, rt60=1.3)) * 0.55

    # low bus: mono below 120 Hz, gentle glue
    low = np.repeat(low.mean(axis=1, keepdims=True), 2, axis=1)

    mix = low * 0.95 + drums * 1.0 + music * 1.0 + fx * 0.85 + wet
    # mono-ize everything below 120 Hz (M/S high-pass on the side channel)
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 120, order=4)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)              # DC / subsonic
    mix = sos_filter(mix, "lowpass", 17500, order=4)

    # final 0.25 s cosine tail-out so the last sample is exactly silent
    nf = int(0.25 * SR)
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
