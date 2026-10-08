"""endless-riser-shepard, take 2 (dark orchestral): an endlessly rising string section over a tom Risset rhythm.

Creative brief:
A 12-second seamless endless riser, 576,000 samples at 48 kHz stereo, loopable sample-for-sample.
(1) Shepard-Risset glissando played by strings: ten octave-spaced voices under a raised-cosine
log-frequency window centred on 440 Hz glide up exactly two octaves per loop. Each voice is a soft
band-limited saw (harmonics 1/h, rolled off smoothly between 2.5 and 6 kHz so nothing pops in or
out), a slow 5 Hz vibrato whose depth is a fixed number of cents, and a gentle three-voice chorus
(+-7 cent detune, different in left and right). Every phase term is a function of the voice's
log-frequency position plus a loop-periodic vibrato, so the ensemble maps onto itself at the loop
point. A warm low-pass (2.4 kHz) and a dark hall put it in a cinematic room.
(2) Risset rhythm on a low tom-like pulse: two tempo layers an octave apart on a log-tempo beat
counter, the too-fast layer fading out while the half-tempo one fades in, accelerating forever.
A quiet sub (49 Hz, an integer number of cycles per loop) pulses with the same accents.
(3) No clock: a muted hi-hat tick (short high band-passed noise) locked to the faster tom layer,
itself a two-layer Risset stream so it loops too.
Rendered circularly (three cycles, keep the middle) so reverb and limiting wrap. Dark-to-bright
constant tension, no climax, no fades. Mono below 120 Hz. About -14 LUFS, true peak <= -1 dBTP.

usage: python take-2.py OUT.wav
"""
from __future__ import annotations

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")

import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SEED = 43
SR = 48000
T = 12.0                       # loop length (s)
N = 576000                     # samples per loop
CYC = 3                        # cycles rendered; middle one kept
TARGET_LUFS = -14.0
CEIL_DBTP = -1.0

# Shepard
NPART = 10                     # octave-spaced partials
OCT_PER_LOOP = 2.0             # glide: two octaves per loop
FCENTER = 440.0
FMIN = FCENTER / 2 ** (NPART / 2)     # 13.75 Hz at position 0, 440 Hz at position 5
SEC_PER_OCT = T / OCT_PER_LOOP        # 6 s

# Risset rhythm: beat counter B(x) = K * 2**x; slow layer x in [0,1), fast layer x in [1,2)
K = 14                          # slow layer starts at K*ln2/T beats/s (48.5 BPM); fast layer 97 -> 194 BPM

rng = np.random.default_rng(SEED)
tn = np.arange(N) / SR


def bf(x, kind, freq, order=2):
    return signal.sosfilt(signal.butter(order, freq, btype=kind, fs=SR, output="sos"), x, axis=0)


def tt(d):
    return np.arange(int(round(d * SR))) / SR


# ------------------------------------------------------------------ Shepard string section (one exact cycle)
def shepard() -> np.ndarray:
    out = np.zeros((N, 2))
    A = 2 * np.pi * FMIN * SEC_PER_OCT / np.log(2)          # phase(p) = A * 2**p
    FV = 5.0                                               # vibrato rate: 60 cycles per loop
    VD = 0.0035                                            # vibrato depth (~6 cents) as a frequency ratio
    detune = {0: (-7, 0.0, 6), 1: (-5, 1.5, 8)}            # chorus cents per channel
    off = rng.uniform(0, 2 * np.pi, (2, 2, 3))             # [voice parity, channel, chorus copy]
    vph = rng.uniform(0, 2 * np.pi, (2, 2, 3))
    for k in range(NPART):
        p = (k + tn / SEC_PER_OCT) % NPART
        w = 0.5 - 0.5 * np.cos(2 * np.pi * p / NPART)
        f = FMIN * 2.0 ** p
        base = A * 2.0 ** p
        for c in range(2):
            for j, cents in enumerate(detune[c]):
                r = 2 ** (cents / 1200)
                ph = r * base + off[k % 2, c, j] + (VD * r * f / FV) * np.sin(2 * np.pi * FV * tn + vph[k % 2, c, j])
                for h in range(1, 9):
                    fh = h * r * f
                    g = np.clip((6000 - fh) / 3500, 0, 1) ** 2      # smooth band-limit, 2.5 -> 6 kHz
                    if not np.any(g * w > 1e-4):
                        continue
                    out[:, c] += (w * g / h) * np.sin(h * ph)
    return out * 0.07


# ------------------------------------------------------------------ voices
def low_tom() -> np.ndarray:
    t = tt(0.55)
    f = 72 + (118 - 72) * np.exp(-t / 0.06)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = (np.sin(ph) + 0.35 * np.sin(1.5 * ph) * np.exp(-t / 0.08)) * np.exp(-t / 0.22)
    skin = bf(rng.standard_normal(len(t)), "bandpass", [150, 1100]) * np.exp(-t / 0.02) * 0.4
    y = (1 - np.exp(-t / 0.0015)) * (body + skin)
    y = bf(np.tanh(1.2 * y) / np.tanh(1.2), "lowpass", 1800)
    y[-2400:] *= np.linspace(1, 0, 2400) ** 2
    return y


def sub_env() -> np.ndarray:
    t = tt(0.6)
    e = (1 - np.exp(-t / 0.012)) * np.exp(-t / 0.16)
    e[-2400:] *= np.linspace(1, 0, 2400) ** 2
    return e


def muted_hat() -> np.ndarray:
    t = tt(0.04)
    y = bf(rng.standard_normal(len(t)), "bandpass", [6500, 11000], 2)
    y *= (1 - np.exp(-t / 0.0007)) * np.exp(-t / 0.007)
    y[-240:] *= np.linspace(1, 0, 240)
    return y / np.abs(y).max()


def risset_events(x_lo: int, x_hi: int):
    """(time, x) for every beat of the layers whose log-tempo position runs x_lo..x_hi, one loop."""
    ev = []
    for j in range(x_lo, x_hi):
        for n in range(K * 2 ** j, K * 2 ** (j + 1)):
            t = T * (np.log2(n / K) - j)
            ev.append((t, j + t / T))
    return ev


def place(bus, x, t, gain=1.0, pan=0.0):
    if x.ndim == 1:
        th = (pan + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], 1) * np.sqrt(2)
    t = t % T
    for k in range(CYC):
        s = int(round(t * SR)) + k * N
        e = min(len(bus), s + len(x))
        if s < len(bus):
            bus[s:e] += gain * x[: e - s]
    # an event's tail that would run past the 3-cycle buffer is dropped; the middle cycle gets
    # the tails from cycle 1, which is all that matters


def hall(x, rt60=1.8):
    t = tt(rt60 * 1.15)
    env = np.exp(-6.9 * t / rt60) * (1 - np.exp(-t / 0.02))
    out = np.zeros_like(x)
    for c in range(2):
        ir = bf(rng.standard_normal(len(t)), "bandpass", [200, 3500]) * env
        ir = np.concatenate([np.zeros(int(0.02 * SR)), ir])
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, c] = signal.fftconvolve(x[:, c], ir)[: len(x)]
    return out


# ------------------------------------------------------------------ mastering (periodic)
def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x):
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    z1 = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak(x):
    return float(20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-20))


def limiter(x, ceil_db, hold_ms=6.0):
    """Vectorised look-ahead limiter on the periodic buffer (all windows wrap). The gain is the
    minimum of the needed gain over +-H, smoothed by two boxes whose total support is +-H, so it
    never exceeds the need at any sample and it is itself periodic."""
    ceil = 10 ** (ceil_db / 20)
    os4 = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = os4[: len(x) * 4].reshape(len(x), 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    H = int(hold_ms * 1e-3 * SR)
    g = minimum_filter1d(need, 2 * H + 1, mode="wrap")
    g = uniform_filter1d(uniform_filter1d(g, H + 1, mode="wrap"), H + 1, mode="wrap")
    return x * g[:, None]


def mid(x):
    return x[N:2 * N]


def master(mix):
    gain = TARGET_LUFS - lufs(mid(mix))
    for _ in range(10):
        y = limiter(mix * 10 ** (gain / 20), CEIL_DBTP - 0.35)
        err = TARGET_LUFS - lufs(mid(y))
        if abs(err) < 0.03:
            break
        gain += err
    y = mid(y)
    return y - y.mean(axis=0)


# ------------------------------------------------------------------ render
def render():
    L = CYC * N
    strings = np.tile(shepard(), (CYC, 1))
    toms = np.zeros((L, 2))
    env = np.zeros((L, 2))
    hats = np.zeros((L, 2))

    tom, se = low_tom(), sub_env()
    for t, x in risset_events(0, 2):                     # two tom layers an octave apart
        a = np.sin(np.pi * x / 2) ** 2
        place(toms, tom, t, a)
        place(env, se, t, a)
    for t, x in risset_events(1, 3):                     # muted hat on the fast-layer beats + subdivisions
        a = np.sin(np.pi * (x - 1) / 2) ** 2
        place(hats, muted_hat() * rng.uniform(0.85, 1.0), t, 0.12 * a, pan=rng.uniform(-0.3, 0.3))

    n = np.arange(L) / SR
    sub = np.sin(2 * np.pi * 49.0 * n)[:, None] * env[:, :1] * 0.32      # 588 cycles per loop
    strings = bf(strings, "lowpass", 2400, 2)
    wet = hall(strings * 0.5 + toms * 0.12 + hats * 0.4, rt60=2.6)
    low = bf((toms.mean(1, keepdims=True) + sub).repeat(2, 1), "highpass", 30, 2)
    mix = strings + wet * 0.55 + low * 0.8 + hats
    m, s = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    s = bf(s, "highpass", 120, 8)
    mix = np.stack([m + s, m - s], 1)
    return bf(mix, "highpass", 25, 2)


def write_wav(path, y):
    d = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + d) * 32767, -32768, 32767)).astype("<i2")
    assert pcm.shape == (N, 2)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {path}: {len(f)} samples, {lufs(f):.2f} LUFS, {true_peak(f):.2f} dBTP, "
          f"seam step {np.abs(f[0] - f[-1]).max():.4f}")


if __name__ == "__main__":
    out = master(render())
    assert np.all(np.isfinite(out))
    write_wav(sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT, out)
