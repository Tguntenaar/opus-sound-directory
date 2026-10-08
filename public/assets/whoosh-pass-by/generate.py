"""whoosh-pass-by, take 1 (faithful).

Creative brief:
A 1.2-second cinematic pass-by whoosh, 57,600 samples, 30 fps, closest approach exactly on frame 18
(0.6 s). Pink noise through two decorrelated band-passes whose centre rises from 300 Hz to 3.5 kHz into
the pass and falls to 900 Hz after it; a faint airy tonal partial (~700 Hz) carries a true Doppler bend
(+3 semitones approaching, -3 receding); the pan moves left to right with a 0.4 ms interaural delay at
the pass; a light comb flange (notches sweeping up) adds motion; distance is modelled as a low-pass that
opens to 9 kHz at the pass and closes after. Smooth fade-in from silence, ~0.4 s tail to true silence.
No low end below 80 Hz. About -14 LUFS integrated, true peak <= -1 dBTP.

Take angle 1 (faithful): implement the brief exactly as written.

Implementation notes:
- One source moves on a straight line past the listener (closest distance 2.5 m). Everything (pan, ITD,
  filters, level, Doppler) is driven by the retarded-time geometry, so what you hear at t was emitted
  at tau_e(t) with t = tau_e + r(tau_e)/c. Closest approach is *heard* at exactly 0.600 s.
- The tonal partial's phase is 2*pi*700*tau_e(t): a physically true Doppler curve. The speed
  (58.9 m/s, beta = 0.1716) gives a total bend of exactly 6 semitones. A real moving source cannot be
  log-symmetric, so it is about +3.25 st on approach and -2.74 st receding.
- ITD follows azimuth: 0.4 ms * sin(az), so it swings from left-leading to right-leading through the
  pass (most of the 0.4 ms swing happens within ~50 ms of frame 18).
- Time-varying band-pass / low-pass are applied as smooth per-frame STFT gain masks.
"""

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")
import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SEED = 42
SR = 48000
N = 57600
T_PASS = 0.6
C_SOUND = 343.0
rng = np.random.default_rng(SEED)
t = np.arange(N) / SR


# ---------------------------------------------------------------- helpers
def colored_noise(n, alpha):
    """Noise with power spectrum ~ 1/f^alpha (1 = pink, 2 = brown)."""
    w = rng.standard_normal(n)
    W = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / SR)
    W *= np.maximum(f, 20.0) ** (-alpha / 2)
    x = np.fft.irfft(W, n)
    return x / x.std()


def stft_filter(x, gain_fn, nper=1024, hop=256):
    """Apply a time-varying magnitude response gain_fn(f[:,None], t[None,:]) via STFT overlap-add."""
    f, tf, Z = signal.stft(x, SR, window="hann", nperseg=nper, noverlap=nper - hop)
    G = gain_fn(f[:, None], np.clip(tf, 0, (N - 1) / SR)[None, :])
    _, y = signal.istft(Z * G, SR, window="hann", nperseg=nper, noverlap=nper - hop)
    return y[: len(x)]


def bandpass_mag(f, fc, q):
    f = np.maximum(f, 1.0)
    return 1.0 / np.sqrt(1.0 + q * q * (f / fc - fc / f) ** 2)


def lowpass_mag(f, fl, order=2):
    return 1.0 / np.sqrt(1.0 + (f / fl) ** (2 * order))


def frac_delay(x, d):
    """Delay x by d samples (array, time-varying, fractional)."""
    n = np.arange(len(x), dtype=np.float64)
    return np.interp(n - d, n, x, left=0.0, right=0.0)


def agc(x, win_s=0.03):
    """Flatten the noise's own level fluctuations so the designed envelope defines the level."""
    e = np.sqrt(uniform_filter1d(x * x, int(win_s * SR)) + 1e-12)
    return x / e


def smoothstep(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


def geometry(v, d):
    """Retarded-time geometry of a straight pass-by heard with closest approach at T_PASS."""
    tau0 = T_PASS - d / C_SOUND
    tau = np.linspace(-2.0, 3.0, 500001)
    trec = tau + np.hypot(v * (tau - tau0), d) / C_SOUND
    tau_e = np.interp(t, trec, tau)
    x = v * (tau_e - tau0)
    r = np.hypot(x, d)
    return tau_e, r, np.arctan2(x, d)


def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x):
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_db(x):
    return 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)


def master(x, target_lufs=-14.0, ceiling_db=-1.1):
    sos = signal.butter(4, 80, "highpass", fs=SR, output="sos")      # DC + nothing below 80 Hz
    x = signal.sosfiltfilt(sos, x, axis=0)
    x *= 10 ** ((target_lufs - lufs(x)) / 20)
    thr = 10 ** (ceiling_db / 20)
    for _ in range(4):                                                 # look-ahead peak limiter
        os4 = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
        pk = os4[: 4 * len(x)].reshape(-1, 4).max(axis=1)
        need = np.minimum(1.0, thr / np.maximum(pk, 1e-12))
        if need.min() >= 1.0:
            break
        g = minimum_filter1d(need, 241)
        g = uniform_filter1d(g, 241)
        x *= g[:, None]
    tp = true_peak_db(x)
    if tp > ceiling_db:
        x *= 10 ** ((ceiling_db - tp) / 20)
    return x


def write_wav(path, x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- the sound
V, D = 58.9, 2.5
tau_e, r, az = geometry(V, D)
g = D / r                                    # proximity, 1.0 exactly at the heard pass
q = (g - g.min()) / (1 - g.min())            # 0..1 distance curve
pre = t < T_PASS

# band-pass centre: 300 Hz -> 3.5 kHz into the pass, 3.5 kHz -> 900 Hz after
lo = np.where(pre, 300.0, 900.0)
fc_t = lo * (3500.0 / lo) ** (q ** 0.8)
# distance low-pass: opens to 9 kHz at the pass, closes after
lp_lo = np.where(pre, 1800.0, 1500.0)
lp_t = lp_lo * (9000.0 / lp_lo) ** (q ** 0.8)


def frame_curve(curve):
    return lambda tt: np.interp(tt, t, curve)


fc_f, lp_f = frame_curve(fc_t), frame_curve(lp_t)


def band(ratio):
    noise = colored_noise(N, 1.0)                                 # pink
    y = stft_filter(noise, lambda f, tt: bandpass_mag(f, fc_f(tt) * ratio, 1.8) * lowpass_mag(f, lp_f(tt)))
    return agc(y)


A = band(0.84)                       # two decorrelated band-passes (independent pink sources)
B = band(1.19)

env = g ** 1.0 * smoothstep(t / 0.32) * np.cos(0.5 * np.pi * smoothstep((t - 0.70) / 0.30)) ** 2
env[t >= 1.0] = 0.0

# faint airy tonal partial with true Doppler (phase = 2 pi f0 * emission time)
f0 = 700.0
air_am = signal.sosfiltfilt(signal.butter(2, 25, fs=SR, output="sos"), rng.standard_normal(N))
air_am = 1 + 0.35 * air_am / np.abs(air_am).max()
breath = agc(stft_filter(colored_noise(N, 1.0), lambda f, tt: bandpass_mag(f, f0 * np.interp(tt, t, np.gradient(tau_e, 1 / SR)), 18.0)))
tone = (np.sin(2 * np.pi * f0 * tau_e) * air_am + 0.25 * breath / np.sqrt(2)) * 0.30

src_l = (A + 0.45 * B) / np.hypot(1, 0.45) * env + tone * env
src_r = (B + 0.45 * A) / np.hypot(1, 0.45) * env + tone * env

# light comb flange, delay shrinking 5 ms -> 0.8 ms so the notches sweep up
fl_d = 5e-3 * (0.8 / 5.0) ** (t / t[-1]) * SR
src_l = src_l + 0.38 * frac_delay(src_l, fl_d)
src_r = src_r + 0.38 * frac_delay(src_r, fl_d)

# pan left -> right (equal power) + interaural time difference
p = 0.92 * np.sin(az)
gl, gr = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)
itd = 0.4e-3 * np.sin(az) * SR                       # +: source on the right -> left ear later
L = frac_delay(src_l * gl, np.maximum(itd, 0.0))
R = frac_delay(src_r * gr, np.maximum(-itd, 0.0))

out = master(np.stack([L, R], axis=1))
out *= (1 - smoothstep((t - 1.05) / 0.05))[:, None]   # guarantee true silence at the end
out[0] = 0.0

if __name__ == "__main__":
    inst = f0 * np.gradient(tau_e, 1 / SR)
    print(f"take-1: {lufs(out):.2f} LUFS, {true_peak_db(out):.2f} dBTP, doppler "
          f"{12*np.log2(inst[0]/f0):+.2f} / {12*np.log2(inst[-1]/f0):+.2f} st", file=sys.stderr)
    write_wav(sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT, out)
