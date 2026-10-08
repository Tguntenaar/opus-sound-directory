"""Trailer braam hit, take 1 (faithful).

Creative brief:
A 4-second trailer braam in C minor, 192,000 samples at 48 kHz stereo, 30 fps.
0-0.5 s: a short reversed-noise "suck" rising into a 40 ms vacuum (true digital silence
0.46-0.50 s). Frame 15 (0.5 s): the braam hits, a stack on C1, C2, G2, C3, Eb3 with three
detuned band-limited saws per note, a brass formant peak near 700 Hz, a resonant low-pass
snapping open from 200 Hz to 3.5 kHz in 80 ms and slowly closing over 2.5 s, a -60 cent pitch
scoop into the note, 30 Hz growl amplitude modulation with gentle waveshaping, a sub knock and a
short noise crack on the attack. A dark 3 s hall tail ends in true silence by 3.95 s. Side
channel high-passed at 250 Hz; mono below 120 Hz. About -14 LUFS, true peak <= -1 dBTP.
Must NOT resemble the THX Deep Note or any registered sound mark: no converging glissando from a
random cluster, no spread D-major resolution; this is a hard hit, not a swell.

Usage: python take-1.py OUT.wav
"""

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")
import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 48000
N = 192000
SEED = 42
HIT = int(0.5 * SR)            # frame 15 at 30 fps
VAC0 = HIT - int(0.040 * SR)   # start of the 40 ms vacuum
END = int(3.95 * SR)           # true silence from here
rng = np.random.default_rng(SEED)
t = np.arange(N) / SR


# ---------------------------------------------------------------- helpers
def sos_f(kind, f, order=2, x=None):
    return signal.butter(order, f, btype=kind, fs=SR, output="sos")


def filt(x, kind, f, order=2):
    return signal.sosfilt(sos_f(kind, f, order), x, axis=0)


def polyblep_saw(freq, sr, phase0):
    """Band-limited (PolyBLEP) saw from a per-sample frequency array, vectorised."""
    dt = freq / sr
    ph = (phase0 + np.cumsum(dt)) % 1.0
    y = 2.0 * ph - 1.0
    # PolyBLEP residual around the wrap
    a = ph < dt
    u = ph[a] / dt[a]
    y[a] -= u + u - u * u - 1.0
    b = ph > 1.0 - dt
    u = (ph[b] - 1.0) / dt[b]
    y[b] -= u * u + u + u + 1.0
    return y


def saw_os(freq48, phase0, os=2):
    """Render the saw at 2x and decimate for extra alias suppression."""
    f_up = np.repeat(freq48, os)
    y = polyblep_saw(f_up, SR * os, phase0)
    return signal.resample_poly(y, 1, os)


def biquad_lp(fc, q):
    w = 2 * np.pi * fc / SR
    al = np.sin(w) / (2 * q)
    cw = np.cos(w)
    b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2])
    a = np.array([1 + al, -2 * cw, 1 - al])
    return b / a[0], a / a[0]


def tv_lowpass(x, fc, q, block=32):
    """Time-varying resonant low-pass: biquad coefficients updated every `block` samples."""
    y = np.zeros_like(x)
    zi = np.zeros((2,) + x.shape[1:])
    for s in range(0, len(x), block):
        e = min(len(x), s + block)
        b, a = biquad_lp(fc[(s + e) // 2], q)
        y[s:e], zi = signal.lfilter(b, a, x[s:e], axis=0, zi=zi)
    return y


def peaking(x, f0, gain_db, q):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A])
    a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    return signal.lfilter(b / a[0], a / a[0], x, axis=0)


def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x):
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    p = np.cumsum(np.concatenate([[0.0], (y ** 2).sum(axis=1)]))
    st = np.arange(0, len(y) - blk + 1, hop)
    z = (p[st + blk] - p[st]) / blk
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return -0.691 + 10 * np.log10(z2.mean())


def true_peak_env(x):
    up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    return up[: len(x) * 4].reshape(-1, 4).max(axis=1)


def limit(x, ceiling_db=-1.3):
    thr = 10 ** (ceiling_db / 20)
    pk = true_peak_env(x)
    g = np.minimum(1.0, thr / (pk + 1e-12))
    g = minimum_filter1d(g, 2 * 480 + 1)
    g = uniform_filter1d(g, 480)
    return x * g[:, None]


def master(x, gate, target=-14.0):
    """Loudness gain, DC block + silence gates, then true-peak limiter; iterated so the limiter's
    gain riding on the sub (which creates a small offset) is re-blocked and its last pass is tiny."""
    for _ in range(6):
        x = x * 10 ** ((target - lufs(x)) / 20)
        x = filt(x, "highpass", 22, 2) * (gate > 0)[:, None]   # hard zeros only; fade applied once
        x = limit(x)
    return x


def write_wav(path, x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- 1. reversed-noise suck
def make_suck():
    out = np.zeros((N, 2))
    L = VAC0 - int(0.04 * SR)          # suck lives 0.04 .. 0.46 s
    n = L
    tt = np.arange(n) / SR
    # a "forward" noise hit with a short reverb, then reversed so it swells toward the vacuum
    burst = rng.standard_normal((n, 2))
    burst = filt(burst, "bandpass", [500, 7000], 2)
    env = np.exp(-tt / 0.11)
    fwd = burst * env[:, None]
    rev = fwd[::-1]
    # rising band-pass sweep layer, 300 Hz -> 6 kHz, louder toward the end
    sw = rng.standard_normal((n, 2))
    fc = 300 * (6000 / 300) ** (tt / tt[-1]) ** 1.6
    sw_lp = tv_lowpass(sw, fc, 4.0)
    sw_bp = sw_lp - tv_lowpass(sw_lp, fc * 0.5, 0.7)
    sw_bp *= ((tt / tt[-1]) ** 3)[:, None]
    s = rev + 0.8 * sw_bp / (np.abs(sw_bp).max() + 1e-9) * np.abs(rev).max()
    # fade-in from silence and a 2 ms hard-cut into the vacuum
    fi = np.clip(tt / 0.03, 0, 1)
    fo = np.clip((tt[-1] - tt) / 0.002, 0, 1)
    s *= (fi * fo)[:, None]
    out[VAC0 - n:VAC0] = s
    return out / (np.abs(out).max() + 1e-12)


# ---------------------------------------------------------------- 2. the braam
NOTES = [(32.703, 0.85), (65.406, 1.0), (97.999, 0.8), (130.813, 0.65), (155.563, 0.55)]


def make_braam():
    th = np.clip(t - 0.5, 0, None)
    on = t >= 0.5
    # -60 cent scoop resolving to pitch over ~110 ms (smoothstep)
    u = np.clip(th / 0.11, 0, 1)
    cents = -60 * (1 - (3 * u ** 2 - 2 * u ** 3))
    scoop = 2 ** (cents / 1200)
    stack = np.zeros((N, 2))
    for f0, amp in NOTES:
        for det, pan in ((0.0, 0.0), (-9.0, -0.55), (+8.0, 0.55)):
            drift = 1 + 0.0012 * np.sin(2 * np.pi * rng.uniform(0.15, 0.4) * t + rng.uniform(0, 6.28))
            f = f0 * 2 ** (det / 1200) * scoop * drift
            v = saw_os(f, rng.uniform())
            gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            stack[:, 0] += amp * gl * v
            stack[:, 1] += amp * gr * v
    stack /= np.abs(stack).max()
    # 30 Hz growl AM, fading a little over time, then gentle waveshaping
    gdepth = 0.45 * np.exp(-th / 1.6)
    stack *= (1 - gdepth * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * t)))[:, None]
    stack = np.tanh(1.8 * stack) / np.tanh(1.8)
    # brass formant near 700 Hz (+ a lighter second formant)
    stack = peaking(stack, 700, 9.0, 1.6)
    stack = peaking(stack, 1250, 3.0, 2.0)
    # resonant LP: 200 Hz -> 3.5 kHz in 80 ms, then closes back over 2.5 s
    fc = np.full(N, 200.0)
    a = np.clip(th / 0.08, 0, 1)
    fc_open = 200 * (3500 / 200) ** a
    c = np.clip((th - 0.08) / 2.5, 0, 1)
    fc_close = 3500 * (220 / 3500) ** (c ** 0.8)
    fc = np.where(th < 0.08, fc_open, fc_close)
    stack = tv_lowpass(stack, fc, 2.6)
    # amplitude envelope: hard 1.5 ms attack, sustain sag, release to zero at ~2.9 s (hall carries on)
    att = np.clip(th / 0.0015, 0, 1)
    body = 0.55 + 0.45 * np.exp(-th / 0.35)
    rel = np.clip(1 - (th - 1.1) / 1.3, 0, 1) ** 1.6
    env = att * body * rel * on
    stack *= env[:, None]
    return stack / (np.abs(stack).max() + 1e-12)


def make_knock():
    th = np.clip(t - 0.5, 0, None)
    f = 38 + 62 * np.exp(-th / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    ph -= ph[HIT]
    k = np.sin(ph) * np.exp(-th / 0.22) * np.clip(th / 0.001, 0, 1) * (t >= 0.5)
    k = np.tanh(1.5 * k)
    return np.stack([k, k], axis=1)


def make_crack():
    th = np.clip(t - 0.5, 0, None)
    n = rng.standard_normal((N, 2))
    n = filt(n, "bandpass", [1200, 7500], 2)
    env = np.exp(-th / 0.012) * np.clip(th / 0.0004, 0, 1) * (t >= 0.5)
    env[th > 0.08] = 0
    return n * env[:, None] / 3.0


# ---------------------------------------------------------------- 3. dark hall
def hall_ir(length=3.0, rt60=2.6):
    n = int(length * SR)
    tt = np.arange(n) / SR
    ir = rng.standard_normal((n, 2))
    # darker over time: blend a bright and a dark copy with different decays
    dark = filt(ir, "lowpass", 1800, 2)
    bright = filt(ir, "lowpass", 4500, 2)
    dec = np.exp(-6.91 * tt / rt60)
    dec_b = np.exp(-6.91 * tt / (rt60 * 0.35))
    ir = dark * dec[:, None] + 0.5 * bright * dec_b[:, None]
    ir *= np.clip(tt / 0.025, 0, 1)[:, None]          # soft onset (diffuse build)
    pre = int(0.022 * SR)
    ir = np.concatenate([np.zeros((pre, 2)), ir])[:n]
    ir = filt(ir, "highpass", 160, 2)                   # no reverb mud below the sub
    return ir / np.sqrt((ir ** 2).sum(axis=0, keepdims=True))


def main(path):
    suck = make_suck()
    braam = make_braam()
    knock = make_knock()
    crack = make_crack()
    dry = 0.45 * suck + 1.0 * braam + 0.75 * knock + 0.35 * crack
    dry = filt(dry, "highpass", 25, 2)
    ir = hall_ir()
    hit_part = dry.copy()
    hit_part[:HIT] = 0                                 # only the hit feeds the hall
    wet = np.stack([signal.fftconvolve(hit_part[:, ch], ir[:, ch])[:N] for ch in range(2)], axis=1)
    mix = dry + 0.42 * wet / (np.abs(wet).max() + 1e-12) * np.abs(dry).max()
    # M/S: side high-passed at 250 Hz -> mono below 120 Hz
    m = 0.5 * (mix[:, 0] + mix[:, 1])
    s = 0.5 * (mix[:, 0] - mix[:, 1])
    s = filt(s, "highpass", 250, 4)
    mix = np.stack([m + s, m - s], axis=1)
    mix = filt(mix, "highpass", 25, 2)
    # vacuum + tail gates (applied before mastering so loudness is measured on the final shape)
    gate = np.ones(N)
    gate[VAC0:HIT] = 0.0
    tail = np.clip((3.95 - t) / 0.65, 0, 1)
    gate *= np.where(t > 3.30, 0.5 - 0.5 * np.cos(np.pi * tail), 1.0)
    gate[END:] = 0.0
    mix *= gate[:, None]
    mix = master(mix, gate, -14.0)
    assert np.all(np.isfinite(mix))
    assert np.abs(mix.mean(axis=0)).max() < 1e-4, "DC"
    assert 20 * np.log10(true_peak_env(mix).max()) <= -1.1, "true peak"
    write_wav(path, mix)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT)
