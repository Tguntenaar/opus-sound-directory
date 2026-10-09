"""guitar-chime-logo: Opus Sound Directory

A 3-second clean electric-guitar logo sting in A major. From frame 0 three bell-like natural harmonics
ring out one beat apart in a rising figure, each on its own string so they overlap: A4 at the 7th fret
of the D string, B4 at the 12th fret of the B string, then E5 at the 12th fret of the high E string.
Each one is a picked string with a finger resting on a node, so only the partials that are multiples of
3 (7th fret) or 2 (12th fret) survive, after a tiny damped "tick" from the rest. On frame 45 (1.5 s) the
fretting hand lands and a fast downstroke rolls an open-voiced A major add9 chord across all six strings
(A2 E3 A3 C#4 B3 E4; the open B rubs against the fretted C#). A light touch of the tremolo arm adds a
shimmer. The tone is a clean single-coil neck pickup, with a touch of the middle coil, into a light
compressor and a clean tube amp with a 1x12 open-back cab, then a lush stereo chorus. A dotted-eighth
ping-pong delay with a faint octave-up shimmer and a small plate fill the space. Everything rings out to silence by 3.0 s. Only the guitar's own
low notes sit below 120 Hz, and they are mono.

Run:  python3 generate.py   -> writes out.wav next to this file.

Physics notes: every string is additive, with integrated phase. It uses stiff-string inharmonicity
f_n = n f0 sqrt(1 + B n^2) and a pick-position comb sin(n pi p)/n (the velocity of a released triangle
pluck). A magnetic-pickup comb sin(n pi q) with a sinc aperture follows, then per-partial loss
sigma = s0 + s2 f^2. There are two transverse polarisations (a detuned, slower and weaker second
component that gives beating and a two-stage decay) and a pitch-glide on the attack from tension
modulation. A natural harmonic damps every mode that is not a multiple of k within a few milliseconds.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 45903
DURATION_SEC = 3
BPM = None
KEY = "A major"
FPS = 30
CUE_FRAMES = (0, 45)           # frame 0: first natural harmonic, frame 45: rolled Aadd9 chord
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR
PULSE = 0.5                    # internal pulse (s): harmonics one pulse apart, chord on pulse 3
CHORD_T = CUE_FRAMES[1] / FPS  # 1.5 s
DELAY_T = 0.375                # dotted eighth of the internal pulse

# open strings, standard tuning (Hz)
OPEN = {"E2": 82.4069, "A2": 110.0, "D3": 146.8324, "G3": 195.9977, "B3": 246.9417, "E4": 329.6276}
STRING_B = {"E2": 6e-5, "A2": 5e-5, "D3": 6e-5, "G3": 9e-5, "B3": 1.1e-4, "E4": 1.3e-4}  # stiffness
Q_NECK, Q_MID = 0.243, 0.155   # pickup positions as a fraction of scale length from the bridge
APERTURE = 0.017               # pickup magnetic window / scale length

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0) -> None:
    s = int(round(t * SR))
    if s >= len(bus):
        return
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


def high_shelf(x, f0, gain_db, s=0.8):
    """RBJ cookbook high shelf."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / 2 * np.sqrt((a_ + 1 / a_) * (1 / s - 1) + 2)
    c = np.cos(w0)
    b = [a_ * ((a_ + 1) + (a_ - 1) * c + 2 * np.sqrt(a_) * alpha),
         -2 * a_ * ((a_ - 1) + (a_ + 1) * c),
         a_ * ((a_ + 1) + (a_ - 1) * c - 2 * np.sqrt(a_) * alpha)]
    a = [(a_ + 1) - (a_ - 1) * c + 2 * np.sqrt(a_) * alpha,
         2 * ((a_ - 1) - (a_ + 1) * c),
         (a_ + 1) - (a_ - 1) * c - 2 * np.sqrt(a_) * alpha]
    return signal.lfilter(b, a, x, axis=0)


# ---------------------------------------------------------------- the string
def string_note(f0: float, dur: float, *, vel: float, p: float, b_stiff: float,
                harmonic_k: int = 0, bright_fc: float = 4000.0, s0: float = 1.3, s2: float = 0.32,
                glide_cents: float = 3.0, vib_cents: float = 0.0, vib_start: float = 0.35,
                damp_at: float | None = None, damp_tau: float = 0.012,
                transpose: float = 1.0, pol_amp: float = 0.28) -> np.ndarray:
    """One plucked electric-guitar string as heard through the neck (+ a little middle) pickup.

    Additive modal synthesis with integrated phase, so the pitch can glide (tension modulation on the
    attack) and wobble (tremolo-arm shimmer) without any zipper. `harmonic_k` > 0 makes it a natural
    harmonic: a finger at 1/k of the string damps every mode that has no node there.
    `transpose` re-synthesises the same performance an octave up for the shimmer send.
    """
    t = tt(dur)
    # time warp: tension-modulation pitch glide (sharp on the attack, settling in ~70 ms) + bar vibrato
    g = 2 ** (glide_cents / 1200) - 1
    tau_g = 0.07
    tw = t + g * tau_g * (1 - np.exp(-t / tau_g))
    if vib_cents:
        ramp = np.clip((t - vib_start) / 0.35, 0, 1) ** 2
        m = (2 ** (vib_cents / 1200) - 1) * np.sin(2 * np.pi * 5.2 * np.maximum(t - vib_start, 0)) * ramp
        tw = tw + np.cumsum(m) / SR
    n = np.arange(1, int(12000 / (f0 * transpose)) + 1)
    fn = n * f0 * np.sqrt(1 + b_stiff * n ** 2)
    keep = fn * transpose < 12000
    n, fn = n[keep], fn[keep]
    pick = np.sin(n * np.pi * p) / n / (1 + (fn / bright_fc) ** 2)
    pickup = (np.sin(n * np.pi * Q_NECK) + 0.35 * np.sin(n * np.pi * Q_MID)) * np.sinc(n * APERTURE)
    amp = pick * pickup
    sig = s0 + s2 * (fn / 1000) ** 2
    if harmonic_k:
        dead = (n % harmonic_k) != 0
        amp = np.where(dead, amp * 0.3, amp)          # finger at the node point barely lets them start
        sig = np.where(dead, 1 / 0.0045, sig * 1.08)  # ...and kills them within a few ms
        # the fingertip is ~1 cm wide, not a point: surviving modes above the first are damped too,
        # so the bright ping relaxes into an almost pure, bell-like tone
        sig = np.where(dead, sig, sig + 5.5 * np.maximum(n / harmonic_k - 1, 0) ** 1.3)
    y = np.zeros_like(t)
    det = rng.uniform(0.15, 0.9, len(n)) * rng.choice([-1, 1], len(n))   # polarisation split (cents)
    for a, f, s, d in zip(amp, fn * transpose, sig, det):
        if abs(a) < 1e-5:
            continue
        ph = 2 * np.pi * f * tw
        y += a * ((1 - pol_amp) * np.exp(-s * t) * np.sin(ph)
                  + pol_amp * np.exp(-0.55 * s * t) * np.sin(ph * 2 ** (d / 1200)))
    # pick release (~0.4 ms) and, if asked, the fretting hand / pick coming down on the string
    na = max(2, int(0.0004 * SR))
    y[:na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    if damp_at is not None:
        td = np.maximum(t - damp_at, 0)
        y *= np.exp(-td / damp_tau) * (1 - np.clip(td / (6 * damp_tau), 0, 1)) ** 2
    nr = int(0.01 * SR)
    y[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    return y * vel


# ---------------------------------------------------------------- the rig
def compressor(x: np.ndarray, thr: float, ratio: float = 3.0, att: float = 0.004, rel: float = 0.15) -> np.ndarray:
    """Feed-forward peak compressor (gentle, pedal-style)."""
    ca, cr = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    env = np.empty_like(x)
    e = 0.0
    for i, v in enumerate(np.abs(x).tolist()):
        e = ca * e + (1 - ca) * v if v > e else cr * e + (1 - cr) * v
        env[i] = e
    gain = np.where(env > thr, (np.maximum(env, 1e-9) / thr) ** (1 / ratio - 1), 1.0)
    return x * gain


def amp_and_cab(x: np.ndarray) -> np.ndarray:
    """Clean tube amp (tone stack + barely-driven asymmetric triode, 4x oversampled) into a 1x12 open-back cab."""
    x = sos_filter(x, "highpass", 70, order=2)
    x = peaking_eq(x, 240, -3.0, 1.0)            # tone stack: bass knob down for a glassy clean
    x = peaking_eq(x, 520, -2.5, 0.7)            # tone stack mid scoop
    x = high_shelf(x, 2400, 5.0)                 # bright cap / treble
    pk = np.max(np.abs(x)) + 1e-12
    xs = signal.resample_poly(x / pk * 0.55, 4, 1)
    bias, drive = 0.12, 1.5
    ys = (np.tanh(drive * (xs + bias)) - np.tanh(drive * bias)) / drive
    y = signal.resample_poly(ys, 1, 4)[: len(x)] * pk / 0.55
    # cab: open-back low thump, upper-mid presence, steep roll-off (no fizz above 7 kHz)
    y = peaking_eq(y, 115, 1.5, 1.1)
    y = peaking_eq(y, 2300, 2.0, 1.2)
    y = peaking_eq(y, 4200, 2.5, 2.0)            # pickup resonance peak
    y = sos_filter(y, "lowpass", 7000, order=4)
    y = sos_filter(y, "lowpass", 9500, order=2)
    return sos_filter(y, "highpass", 75, order=2)


def frac_delay(x: np.ndarray, d_samples: np.ndarray) -> np.ndarray:
    idx = np.arange(len(x)) - d_samples
    return np.interp(idx, np.arange(len(x)), x, left=0.0, right=0.0)


def chorus(x: np.ndarray) -> np.ndarray:
    """Stereo analog-style chorus: dry centre, two modulated (opposite-phase) dark wet voices L/R."""
    t = np.arange(len(x)) / SR
    wet_in = sos_filter(x, "highpass", 160, order=2)
    out = np.zeros((len(x), 2))
    for ch, ph in enumerate((0.0, np.pi)):
        lfo = np.sin(2 * np.pi * 0.85 * t + ph) + 0.25 * np.sin(2 * np.pi * 0.23 * t + 1.3 * ph + 0.4)
        d = (0.0095 + 0.0024 * lfo) * SR
        w = sos_filter(frac_delay(wet_in, d), "lowpass", 7000, order=2)     # BBD-ish darker wet
        out[:, ch] = x + 0.78 * w
    return out


def pingpong_delay(x_mono: np.ndarray, shimmer: np.ndarray) -> np.ndarray:
    """Dotted-eighth ping-pong delay. Each repeat is darker; an octave-up copy joins the repeats."""
    D = int(round(DELAY_T * SR))
    out = np.zeros((len(x_mono), 2))
    cur = sos_filter(x_mono + shimmer, "highpass", 320, order=2)
    fb = 0.46
    for k in range(1, 8):
        cur = sos_filter(cur, "lowpass", 4200, order=2) * fb
        s = k * D
        if s >= len(out):
            break
        seg = cur[: len(out) - s]
        l, r = (0.95, 0.30) if k % 2 else (0.30, 0.95)
        out[s:, 0] += seg * l
        out[s:, 1] += seg * r
    return out


def plate(x: np.ndarray, rt60: float = 1.5, predelay: float = 0.016) -> np.ndarray:
    """Small plate: decorrelated stereo noise IRs, highs decaying faster than lows."""
    t = tt(rt60 * 1.1)
    out = np.zeros_like(x)
    for ch in range(2):
        lo = sos_filter(rng.standard_normal(len(t)), "bandpass", [300, 2500]) * np.exp(-6.9 * t / rt60)
        hi = sos_filter(rng.standard_normal(len(t)), "bandpass", [2500, 8000]) * np.exp(-6.9 * t / (0.55 * rt60))
        ir = np.concatenate([np.zeros(int(predelay * SR)), lo + 0.7 * hi])
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, ch] = signal.fftconvolve(x[:, ch], ir)[: len(x)]
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
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak; never clips the waveform."""
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


# ---------------------------------------------------------------- performance
def plan() -> dict:
    """All the human randomness of the take, drawn once so the octave shimmer copy follows it exactly."""
    return {
        "h_jit": [0.0] + list(rng.uniform(-0.008, 0.006, 2)),
        "h_tune": list(rng.uniform(-1.5, 1.5, 3)),
        "c_offs": np.cumsum([0.0] + list(rng.uniform(0.0075, 0.0105, 5))),
        "c_tune": list(rng.uniform(-1.8, 1.8, 6)),
        "c_vel": list(rng.uniform(0.94, 1.04, 6)),
        "c_pos": list(rng.uniform(-0.01, 0.01, 6)),
    }


def perform(pl: dict, transpose: float = 1.0) -> np.ndarray:
    """The dry guitar (mono, straight off the pickup) for the whole sting."""
    gtr = np.zeros(N)
    # --- three natural harmonics, one pulse apart, on three different strings (they overlap and ring)
    #     (open string, k, time, velocity): D-string 7th fret = 3 x D3 = A4, B 12th = B4, high-E 12th = E5
    harms = (("D3", 3, 0.0, 1.00), ("B3", 2, PULSE, 0.80), ("E4", 2, 2 * PULSE, 0.78))
    fret_hand = CHORD_T - 0.034          # fretting hand lands on the chord shape just before the roll
    for i, (s, k, t0, v) in enumerate(harms):
        t0 = t0 + pl["h_jit"][i]
        f0 = OPEN[s] * 2 ** (pl["h_tune"][i] / 1200)
        dur = fret_hand - t0 + 0.12
        y = string_note(f0, dur, vel=v, p=0.085, b_stiff=STRING_B[s], harmonic_k=k, bright_fc=5200,
                        s0=1.05, s2=0.22, glide_cents=1.5, damp_at=fret_hand - t0, damp_tau=0.010,
                        transpose=transpose)
        place(gtr, y, t0)

    # --- the chord: Aadd9, 5-7-7-6-0-0 (A2 E3 A3 C#4 B3 E4), fast downstroke roll, accent on the root
    chord = (("E2", 5), ("A2", 7), ("D3", 7), ("G3", 6), ("B3", 0), ("E4", 0))
    vels = (1.0, 0.86, 0.80, 0.78, 0.74, 0.80)
    for i, ((s, fret), v) in enumerate(zip(chord, vels)):
        off = pl["c_offs"][i]
        f0 = OPEN[s] * 2 ** (fret / 12) * 2 ** (pl["c_tune"][i] / 1200)
        vj = v * pl["c_vel"][i]
        y = string_note(f0, DURATION_SEC - CHORD_T - off, vel=vj, p=0.13 + pl["c_pos"][i],
                        b_stiff=STRING_B[s], bright_fc=5000 * vj ** 0.5, s0=1.25 + 0.0018 * f0, s2=0.26,
                        glide_cents=4.0 * vj, vib_cents=5.0, vib_start=0.42 - off, transpose=transpose)
        place(gtr, y, CHORD_T + off)
    return gtr


def render() -> np.ndarray:
    pl = plan()
    dry = perform(pl)
    shimmer_src = perform(pl, transpose=2.0)       # same performance an octave up, for the delay only

    lvl_h = np.sqrt(np.mean(dry[: int(1.4 * SR)] ** 2))
    lvl_c = np.sqrt(np.mean(dry[int(1.5 * SR): int(1.8 * SR)] ** 2))
    print(f"dry rms harmonics {20*np.log10(lvl_h):.1f} dB, chord {20*np.log10(lvl_c):.1f} dB")

    # pedalboard: compressor -> amp + cab (mono) -> stereo chorus -> ping-pong delay -> plate
    pk = np.max(np.abs(dry))
    comp = compressor(dry / pk, thr=0.32, ratio=3.0) * pk
    amped = amp_and_cab(comp)
    sh = amp_and_cab(shimmer_src) * 0.22
    ch = chorus(amped)
    dly = pingpong_delay(amped, sh) * 0.42
    verb = plate(ch * 0.6 + dly * 0.5) * 0.16

    mix = ch + dly + verb
    # side high-passed at 330 Hz: the guitar's lows stay mono
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 330, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 16000, order=4)

    # ring-out: cosine tail-out over the last 0.45 s so the last sample is exactly silent
    nf = int(0.45 * SR)
    mix[-nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf)))[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    nf = int(0.45 * SR)
    dither[-nf:] *= np.linspace(1, 0, nf)[:, None]
    dither[:1] = 0
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
