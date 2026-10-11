"""--- 12. Bouncing dot end-card sting (id: bouncing-dot-end-sting, category: logo-stings, 2.5 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 120,000 samples (2.5 s at 30 fps = 75 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 2.5-second end-card sting for a motion-design outro, F# minor at 128 BPM. Frame 0: a single soft 'pop' arrival (sine 180→90 Hz, 60 ms, plus a 1 ms click). Then a ball bounces 6 times with physically decaying gaps (0.42, 0.30, 0.21, 0.15, 0.10, 0.07 s) and amplitudes (each 0.7x), each bounce a rubbery sine 'boink' with a fast upward pitch blip (+5 semitones in 15 ms then settle), pitches stepping F#5, E5, C#5, A4, F#4, C#4. When it settles (about frame 40) a warm F#m(add9) chord swells on felt-piano-like partials with a low F#2 sine, and a tiny glass sparkle on frame 45. Ring out to exactly 0 by the last sample. Mono-centred bounces, chord wide. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 2 approach: boinks are tanh-saturated sines rendered at 4x and polyphase-decimated (anti-aliased rubbery buzz) whose +5 st / 15 ms blip settles with a springy damped wobble; the pop is a linear 180->90 Hz glide with a one-cycle 3 kHz click; the chord is a low-to-high strum (18 ms apart) of a two-string felt-piano model (double-decay partials, strings detuned and split L/R) in an open A3-C#4-F#4-G#4-C#5 voicing, with a soft sine pad doubling the chord tones on a 350 ms attack to make the swell, over a centred F#2 sine; the sparkle is two light FM glass pings (G#7, C#8).
"""
# ---------------------------------------------------------------- mastering --
# (shared block, pasted verbatim into every take so each script stands alone)
import sys
import wave
import numpy as np
from scipy import signal

SR = 48000


def hp_dc(x, fc=25.0, loop=False):
    """DC / rumble high-pass (2nd-order Butterworth, zero-phase).
    loop=True filters a 3x tiled copy and keeps the middle so the seam stays clean."""
    sos = signal.butter(2, fc, "highpass", fs=SR, output="sos")
    if loop:
        n = x.shape[0]
        t = np.concatenate([x, x, x], axis=0)
        return signal.sosfiltfilt(sos, t, axis=0)[n:2 * n]
    return signal.sosfiltfilt(sos, x, axis=0)


def _kweight(x):
    # ITU-R BS.1770-4 K-weighting coefficients for 48 kHz
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b1, a1, x, axis=0)
    return signal.lfilter(b2, a2, y, axis=0)


def lufs(x):
    """Integrated loudness (BS.1770-4, gated)."""
    y = _kweight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    p = (y ** 2).sum(axis=1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    starts = np.arange(0, max(1, len(p) - blk + 1), hop)
    ms = (c[np.minimum(starts + blk, len(p))] - c[starts]) / blk
    ms = ms[ms > 0]
    if ms.size == 0:
        return -120.0
    l = -0.691 + 10 * np.log10(ms)
    g = ms[l > -70]
    if g.size == 0:
        return -120.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = g[(-0.691 + 10 * np.log10(g)) > rel]
    return float(-0.691 + 10 * np.log10(g2.mean()))


def _os_peak(x):
    """Per-sample peak envelope of the 4x oversampled signal (max over channels)."""
    up = signal.resample_poly(x, 4, 1, axis=0)
    a = np.abs(up).max(axis=1)
    return a[: (len(a) // 4) * 4].reshape(-1, 4).max(axis=1)[: x.shape[0]]


def true_peak_db(x):
    return float(20 * np.log10(_os_peak(x).max() + 1e-12))


def _limit(x, ceil_db=-1.3, win_ms=8.0, loop=False):
    """Look-ahead peak limiter on the oversampled envelope (vectorised).
    min-filter then box-smooth over the same centred window: the smoothed gain
    is never above the gain each peak needs, and moves over ~win_ms."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    thr = 10 ** (ceil_db / 20)
    pk = _os_peak(x)
    g = np.minimum(1.0, thr / np.maximum(pk, 1e-12))
    R = max(3, int(win_ms * 1e-3 * SR) | 1)
    m = "wrap" if loop else "nearest"
    g = uniform_filter1d(minimum_filter1d(g, size=R, mode=m), size=R, mode=m)
    return x * g[:, None]


def master(x, target_lufs=-14.0, fade_out_s=0.25, tp_ceiling=-1.0, loop=False):
    """DC high-pass -> loudness normalise -> true-peak limit (iterated) -> end fade."""
    x = np.nan_to_num(np.asarray(x, dtype=np.float64))
    x = hp_dc(x, loop=loop)
    for _ in range(8):
        lu = lufs(x)
        x = x * 10 ** ((target_lufs - lu) / 20)
        if true_peak_db(x) > tp_ceiling - 0.25:
            x = _limit(x, ceil_db=tp_ceiling - 0.4, loop=loop)
        if abs(lufs(x) - target_lufs) < 0.15 and true_peak_db(x) <= tp_ceiling - 0.15:
            break
    tp = true_peak_db(x)
    if tp > tp_ceiling - 0.15:
        x = x * 10 ** ((tp_ceiling - 0.15 - tp) / 20)
    if not loop and fade_out_s > 0:
        n = int(fade_out_s * SR)
        x[-n:] *= (np.cos(np.linspace(0, np.pi / 2, n)) ** 2)[:, None]
        x[-1] = 0.0
    return x


def write_wav(path, x, n_expected):
    assert x.shape == (n_expected, 2), x.shape
    assert np.isfinite(x).all()
    pcm = np.clip(np.round(x * 32767), -32767, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
# ------------------------------------------------------------ end mastering --


SEED = 56
rng = np.random.default_rng(SEED)
N = 120000
FPS = 30
SPF = SR // FPS
OS = 4


def mhz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ramp_env(n, a, r):
    e = np.ones(n)
    if a > 0:
        e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if r > 0:
        e[-r:] *= np.cos(np.linspace(0, np.pi / 2, r)) ** 2
    return e


def add(dst, sig, start):
    n = min(sig.shape[0], dst.shape[0] - start)
    if sig.ndim == 1:
        dst[start:start + n] += sig[:n, None]
    else:
        dst[start:start + n] += sig[:n]


GAPS = [0.42, 0.30, 0.21, 0.15, 0.10, 0.07]
T_BOUNCE = np.cumsum(GAPS)
AMP = 0.7 ** np.arange(1, 7)
PITCH = [78, 76, 73, 69, 66, 61]                # F#5 E5 C#5 A4 F#4 C#4
T_CHORD = 40 / FPS
T_SPARK = 45 / FPS
FSM_SCALE = {6, 8, 9, 11, 1, 2, 4}
CHORD_PC = {6, 9, 1, 8}
CHORD = [57, 61, 66, 68, 73]                    # A3 C#4 F#4 G#4 C#5
BASS = 42
SPARK = [104, 109]                              # G#7 C#8 (3322 / 4435 Hz)
assert all(p % 12 in FSM_SCALE for p in PITCH)
assert all(p % 12 in CHORD_PC for p in CHORD + SPARK + [BASS])

x = np.zeros((N, 2))

# ----------------------------------------------------------------- pop --
n = int(0.08 * SR)
t = np.arange(n) / SR
f = np.where(t < 0.06, 180 - 90 * t / 0.06, 90.0)
pop = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.025) * ramp_env(n, 48, int(0.015 * SR))
nb = SR // 3000                                 # one 3 kHz cycle (~0.33 ms) inside a 1 ms window
click = np.zeros(48)
click[:nb] = np.sin(2 * np.pi * np.arange(nb) / nb)
click *= np.hanning(48) ** 0.5
pop[:48] += 0.2 * click
add(x, 1.4 * pop, 0)


# --------------------------------------------------------------- boinks --
def boink(f0, n):
    t = np.arange(n * OS) / (SR * OS)
    tau = t - 0.015
    st = np.where(t < 0.015, 5 * np.sin(np.pi / 2 * t / 0.015),
                  5 * np.exp(-tau / 0.014) * np.cos(2 * np.pi * 18 * tau))
    ph = 2 * np.pi * np.cumsum(f0 * 2 ** (st / 12)) / (SR * OS)
    y = np.tanh(2.2 * np.sin(ph)) / np.tanh(2.2)
    y = signal.resample_poly(y, 1, OS)[:n]
    tt = np.arange(n) / SR
    return y * np.exp(-tt / 0.05) * ramp_env(n, 72, int(0.03 * SR))


for tb, a, p in zip(T_BOUNCE, AMP, PITCH):
    add(x, 0.75 * a * boink(mhz(p), int(0.2 * SR)), int(round(tb * SR)))


# ---------------------------------------------------------- felt piano --
def felt2(f0, n):
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    B = 0.0003
    for k in range(1, 12):
        fk = k * f0 * np.sqrt(1 + B * k * k)
        if fk > 8000:
            break
        a = (1 / k ** 1.4) / (1 + (fk / 1200) ** 2)
        tf, ts = 0.25 / k ** 0.5, 1.4 / (1 + 0.3 * (k - 1))
        env = 0.6 * np.exp(-t / tf) + 0.4 * np.exp(-t / ts)
        for ch, d in ((0, -1.2), (1, 1.2)):
            out[:, ch] += a * env * np.sin(2 * np.pi * fk * 2 ** (d / 1200) * t + rng.uniform(0, 2 * np.pi))
    return out * ramp_env(n, int(0.006 * SR), int(0.05 * SR))[:, None]


s0 = int(round(T_CHORD * SR))
for i, (m, p) in enumerate(zip(CHORD, np.linspace(-0.8, 0.8, len(CHORD)))):
    st = s0 + i * int(0.018 * SR)
    v = felt2(mhz(m), N - st)
    gl, gr = np.sqrt((1 - p) / 2), np.sqrt((1 + p) / 2)
    add(x, 0.12 * 1.414 * np.stack([v[:, 0] * gl, v[:, 1] * gr], 1), st)

nc = N - s0
tc = np.arange(nc) / SR
swell_env = ramp_env(nc, int(0.35 * SR), int(0.05 * SR)) * np.exp(-np.maximum(tc - 0.35, 0) / 0.8)
pad = np.zeros((nc, 2))
for m, p in zip(CHORD, np.linspace(0.8, -0.8, len(CHORD))):
    v = np.sin(2 * np.pi * mhz(m) * tc + rng.uniform(0, 2 * np.pi))
    gl, gr = np.sqrt((1 - p) / 2), np.sqrt((1 + p) / 2)
    pad += np.stack([v * gl, v * gr], 1)
add(x, 0.045 * pad * swell_env[:, None], s0)
bass = np.sin(2 * np.pi * mhz(BASS) * tc) * np.exp(-tc / 0.9) * ramp_env(nc, int(0.12 * SR), int(0.05 * SR))
add(x, 0.2 * bass, s0)

# --------------------------------------------------------------- sparkle --
s1 = int(round(T_SPARK * SR))
for j, (m, p) in enumerate(zip(SPARK, (0.7, -0.7))):
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    fc = mhz(m)
    I = 0.8 * np.exp(-t / 0.03)
    v = np.sin(2 * np.pi * fc * t + I * np.sin(2 * np.pi * fc * 1.5 * t))
    v *= np.exp(-t / 0.08) * ramp_env(n, 48, int(0.05 * SR))
    gl, gr = np.sqrt((1 - p) / 2), np.sqrt((1 + p) / 2)
    add(x, 0.12 * np.stack([v * gl, v * gr], 1), s1 + j * int(0.04 * SR))

y = master(x, target_lufs=-14.0, fade_out_s=0.35)
write_wav(sys.argv[1], y, N)
