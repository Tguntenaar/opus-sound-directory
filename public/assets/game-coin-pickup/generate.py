"""game-coin-pickup, take 1: glass bell, rising major sixth.

Creative brief: a 0.5-second game coin / collectible pickup, exactly 24,000 samples at 48 kHz stereo,
30 fps, onset on frame 0 (sample 0), instantly readable as "collect": its own two-note-ish sparkle.
Bright but not piercing (little energy above 10 kHz), centred core with a little stereo sparkle,
no low end, true silence before 0.48 s. Target about -17 LUFS, true peak <= -1 dBTP.

Take angle (glass bell, rising major sixth): D6 (1174.7 Hz) for ~45 ms, then B6 (1975.5 Hz) ringing.
Timbre is a soft two-operator FM glass bell (carrier:modulator 1:3.5, modulation index decaying
fast) plus six tiny inharmonic sparkle pings scattered in stereo over ~150 ms after the second note.

Legal rules honoured: no B5 -> E6, no rising perfect fourth between the main notes (this is a major
sixth, 9 semitones), no 987.8 Hz or 1318.5 Hz component, no square/pulse chip voice. Not modelled on
any game's sound.

usage: python take-1.py OUT.wav
"""

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")
import sys
import wave

import numpy as np
from scipy import signal

SEED = 42
SR = 48000
N = 24000
rng = np.random.default_rng(SEED)
t = np.arange(N) / SR


def onset_env(t0, attack, tau, release_at=None, release=0.015):
    """Raised-cosine attack from t0, exponential decay, optional raised-cosine release."""
    tt = t - t0
    env = np.zeros(N)
    on = tt >= 0
    a = np.clip(tt / attack, 0, 1)
    env[on] = (0.5 - 0.5 * np.cos(np.pi * a[on])) * np.exp(-tt[on] / tau)
    if release_at is not None:
        r = np.clip((tt - release_at) / release, 0, 1)
        env *= 0.5 + 0.5 * np.cos(np.pi * r)
    return env


def fm_bell(fc, t0, amp, tau, i0, itau, release_at=None):
    """Two-operator FM bell, c:m = 1:3.5, index decaying fast."""
    tt = np.maximum(t - t0, 0)
    fm = 3.5 * fc
    index = i0 * np.exp(-tt / itau)
    ph = rng.uniform(0, 2 * np.pi)
    y = np.sin(2 * np.pi * fc * tt + ph + index * np.sin(2 * np.pi * fm * tt))
    return amp * y * onset_env(t0, 0.0012, tau, release_at)


# --- core: centred two-note glass bell -------------------------------------------------------
D6, B6 = 1174.7, 1975.5
T2 = 0.045
core = fm_bell(D6, 0.0, 0.75, 0.20, 1.1, 0.020, release_at=T2 - 0.004)
core += fm_bell(B6, T2, 1.00, 0.105, 1.3, 0.028)

# --- sparkle: six tiny inharmonic pings, scattered in stereo over ~150 ms after the second note --
ping_f = np.array([3290.0, 4170.0, 5030.0, 3710.0, 6140.0, 4610.0])
ping_t = T2 + 0.012 + np.sort(rng.uniform(0, 0.15, 6))
ping_a = 0.16 * np.linspace(1.0, 0.55, 6) * rng.uniform(0.8, 1.0, 6)
ping_pan = rng.uniform(-0.75, 0.75, 6) * np.array([1, -1, 1, -1, 1, -1])
L = core.copy()
R = core.copy()
for f, t0, a, p in zip(ping_f, ping_t, ping_a, ping_pan):
    tt = np.maximum(t - t0, 0)
    y = a * np.sin(2 * np.pi * f * tt) * onset_env(t0, 0.0006, rng.uniform(0.012, 0.022))
    th = (p + 1) * np.pi / 4                      # constant-power pan
    L += np.cos(th) * np.sqrt(2) * y
    R += np.sin(th) * np.sqrt(2) * y
x = np.stack([L, R], axis=1)

# --- clean-up: DC/low-end removal, tame >10 kHz, guarantee silence by 0.475 s ------------------
x = signal.sosfilt(signal.butter(2, 25, "highpass", fs=SR, output="sos"), x, axis=0)
x = signal.sosfilt(signal.butter(4, 300, "highpass", fs=SR, output="sos"), x, axis=0)
x = signal.sosfilt(signal.butter(4, 9500, "lowpass", fs=SR, output="sos"), x, axis=0)
fade = np.clip((0.475 - t) / 0.045, 0, 1)
x *= (0.5 - 0.5 * np.cos(np.pi * fade))[:, None]


# --- master: BS.1770 loudness to -17 LUFS, then keep true peak <= -1.2 dBTP -------------------
def lufs(y):
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    k = signal.lfilter(b2, a2, signal.lfilter(b1, a1, y, axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(k[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(k) - blk + 1, hop)])
    z = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    z = z[-0.691 + 10 * np.log10(z) > rel]
    return -0.691 + 10 * np.log10(z.mean())


def true_peak_db(y):
    return 20 * np.log10(np.abs(signal.resample_poly(y, 4, 1, axis=0)).max() + 1e-12)


x *= 10 ** ((-17.0 - lufs(x)) / 20)
tp = true_peak_db(x)
if tp > -1.2:
    x *= 10 ** ((-1.2 - tp) / 20)
assert np.all(np.isfinite(x))

pcm = np.round(np.clip(x, -1, 32767 / 32768) * 32768).astype("<i2")
with wave.open(sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"take-1: {lufs(x):.2f} LUFS, {true_peak_db(x):.2f} dBTP")
