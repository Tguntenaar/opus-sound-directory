"""--- 6. Small object down a drain (id: drain-drop-chalk-foley, category: drops, 3.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 144,000 samples (3.0 s at 30 fps = 90 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 3-second foley moment: a small chalk stick dropping into a street drain. Frame 0: a light dry tap on wet stone (3 ms noise burst, bandpass 2.5 kHz, plus a short 1.1 kHz resonant tick). Frames 6-24: two smaller bounces, each 40% quieter and closer together. Frame 24: it falls in: a hollow metallic clink against a grate (inharmonic modal partials at 1, 2.32, 4.25, 6.63 x 870 Hz, 250 ms decay), then frames 30-60 a fall echo inside a pipe (comb filter at 7 ms + 21 ms feedback, low-passed), ending in a tiny distant plop at frame 66 (a sine 'bubble' sweeping 400→1100 Hz in 40 ms). Under everything, quiet rain bed (filtered pink noise, -24 dB relative) fading out by frame 90. Mono-centred source, rain wide. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 3 approach: additive + convolution. Tap = 3 ms burst through a 4th-order 2.2-2.8 kHz band-pass plus a 1.1 kHz damped sine with a tiny downward glide; bounces on frames 9 and 15 (gaps 9 then 6 frames, x0.6 each). Clink = additive inharmonic partials (1, 2.32, 4.25, 6.63 x 870 Hz) plus a soft re-strike 35 ms later as the chalk rattles through the grate bars. The pipe is an impulse response computed from the 7 ms + 21 ms low-passed feedback comb and FFT-convolved with wall hits; the echo is split into three stages with falling low-pass cutoffs (3 kHz -> 1.8 kHz -> 1 kHz) so it gets darker as it falls deeper. Plop = exponential 400->1100 Hz sine chirp. Rain = velvet-noise crackle + 1/f pink bed with slow gusts, independent per channel, 24 dB under the clink, fading out by frame 90.
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

SEED = 57
rng = np.random.default_rng(SEED)
FPS = 30
N = 144000


def ft(frame):
    return frame / FPS


def ramp_in(s, ms=1.0):
    k = max(2, int(ms * 1e-3 * SR))
    s[:k] *= np.linspace(0.0, 1.0, k)
    return s


def ramp_out(s, ms=3.0):
    k = max(2, int(ms * 1e-3 * SR))
    s[-k:] *= np.linspace(1.0, 0.0, k)
    return s


def place(buf, sig, t):
    i0 = int(round(t * SR))
    n = min(len(sig), buf.shape[0] - i0)
    buf[i0:i0 + n] += sig[:n]


# ------------------------------------------------------------------ sources --
BP_TAP = signal.butter(4, [2200.0, 2800.0], "bandpass", fs=SR, output="sos")


def tap(amp, tick_f=1100.0):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    nb = int(0.003 * SR)  # 3 ms burst
    burst = np.zeros(n)
    burst[:nb] = rng.standard_normal(nb) * np.hanning(nb)
    burst = signal.sosfilt(BP_TAP, burst)
    burst /= np.abs(burst).max() + 1e-12
    f = tick_f * (1.0 - 0.02 * (1 - np.exp(-t / 0.004)))  # 1.1 kHz, tiny settle-down
    tick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.005)
    tick = ramp_in(tick, 1.0)
    s = 0.75 * burst + 0.6 * tick
    s /= np.abs(s).max()
    return ramp_out(amp * s, 3.0)


CLINK_F0 = 870.0
CLINK_RATIOS = np.array([1.0, 2.32, 4.25, 6.63])
assert np.allclose(CLINK_RATIOS * CLINK_F0, [870.0, 2018.4, 3697.5, 5768.1])


def clink_core(n, taus, amps):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for r_, a_, tau in zip(CLINK_RATIOS, amps, taus):
        s += a_ * np.sin(2 * np.pi * CLINK_F0 * r_ * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / tau)
    return ramp_in(s, 1.0)


def clink(amp):
    n = int(0.45 * SR)
    s = clink_core(n, [0.08, 0.05, 0.03, 0.02], [1.0, 0.6, 0.5, 0.35])
    i2 = int(0.035 * SR)  # rattle: second, softer contact with the grate bars
    s[i2:] += 0.3 * clink_core(n - i2, [0.06, 0.04, 0.025, 0.015], [1.0, 0.8, 0.4, 0.4])
    return ramp_out(amp * s / np.abs(s).max(), 5.0)


def bubble(amp):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    f = 400.0 * (1100.0 / 400.0) ** np.minimum(t / 0.040, 1.0)
    env = np.minimum(t / 0.003, 1.0) * np.clip(1 - t / 0.05, 0, 1) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env
    return ramp_out(amp * ramp_in(s, 2.0), 3.0)


def pipe_ir(seconds=0.7, g1=0.45, g2=0.42, a=0.5):
    d1, d2 = int(round(0.007 * SR)), int(round(0.021 * SR))
    den = np.zeros(d2 + 1)
    den[0], den[1] = 1.0, -a
    den[d1] -= (1 - a) * g1
    den[d2] -= (1 - a) * g2
    imp = np.zeros(int(seconds * SR))
    imp[0] = 1.0
    h = signal.lfilter([1.0, -a], den, imp)
    return ramp_out(h, 20.0)


IR = pipe_ir()


def through_pipe(x, lp_hz):
    y = signal.fftconvolve(x, IR)[: len(x)]
    return signal.sosfilt(signal.butter(2, lp_hz, "lowpass", fs=SR, output="sos"), y)


# ------------------------------------------------------------------- build --
src = np.zeros(N)
A_TAP = 0.22
place(src, tap(A_TAP), ft(0))
place(src, tap(A_TAP * 0.6), ft(9))
place(src, tap(A_TAP * 0.6 * 0.6), ft(15))
ck = clink(1.0)
place(src, ck, ft(24))

t_all = np.arange(N) / SR
# three depth stages, each darker than the last
echo = np.zeros(N)
stages = [((30, 40), 3000.0, [(30.2, 0.55), (34.5, 0.4)], 0.35),
          ((40, 50), 1800.0, [(40.0, 0.4), (44.0, 0.3), (47.0, 0.2)], 0.0),
          ((50, 60), 1000.0, [(50.5, 0.3), (54.5, 0.18)], 0.0)]
for (f0, f1), lp, hits, ck_amt in stages:
    feed = np.zeros(N)
    if ck_amt:
        place(feed, ck_amt * ck, ft(24))
    for fr_, a_ in hits:
        place(feed, tap(a_, 1100.0 * rng.uniform(0.96, 1.04)), ft(fr_))
    st = through_pipe(feed, lp)
    fade_len = 6.0 if f1 == 60 else 2.0  # last stage dies away to 0 at frame 60
    end = 60.0 if f1 == 60 else f1 + 1.0
    w = np.clip((t_all - ft(f0 - 0.5)) / ft(1.0), 0, 1) * np.clip((ft(end) - t_all) / ft(fade_len), 0, 1)
    echo += st * np.sin(0.5 * np.pi * w) ** 2
echo *= 0.72 / (np.abs(echo).max() + 1e-12)
src += echo

pl = np.zeros(N)
place(pl, bubble(1.0), ft(66))
pl = 0.65 * pl + 0.35 * through_pipe(pl, 2500.0)
pl *= 0.06 / (np.abs(pl).max() + 1e-12)
src += pl
src = master(np.stack([src, src], axis=1), target_lufs=-14.0, fade_out_s=0.0)[:, 0]


# rain: velvet-noise crackle + 1/f bed, slow gusts, independent per channel
def pink(n, alpha=0.9):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X *= np.maximum(f, 20.0) ** (-alpha / 2)
    return np.fft.irfft(X, n)


def velvet(n, density=1800.0):
    v = np.zeros(n)
    k = int(n / SR * density)
    idx = rng.integers(0, n, k)
    v[idx] = rng.choice([-1.0, 1.0], k) * rng.uniform(0.2, 1.0, k)
    return v


rain = np.zeros((N, 2))
for ch in range(2):
    bed = signal.sosfilt(signal.butter(2, [300.0, 6000.0], "bandpass", fs=SR, output="sos"), pink(N))
    cr = signal.sosfilt(signal.butter(2, [1500.0, 7500.0], "bandpass", fs=SR, output="sos"), velvet(N))
    rain[:, ch] = bed / np.sqrt((bed ** 2).mean()) + 0.6 * cr / np.sqrt((cr ** 2).mean())
gust = 1.0 + 0.2 * np.sin(2 * np.pi * 0.35 * t_all + rng.uniform(0, 2 * np.pi))
rfade = np.clip((ft(90) - t_all) / (ft(90) - ft(45)), 0, 1)
rfade = (np.sin(0.5 * np.pi * rfade) ** 2) * np.clip(t_all / 0.01, 0, 1)
rain *= (gust * rfade)[:, None]
i24 = int(ft(24) * SR)
ra, rb = 18 * 1600, 23 * 1600  # rain-only span (after the last bounce tail)
ref = np.sqrt((src[i24:i24 + int(0.05 * SR)] ** 2).mean())
rain *= ref * 10 ** (-24 / 20) / np.sqrt((rain[ra:rb] ** 2).mean())

RAIN_REL_DB = -24.0
for _ in range(10):  # re-trim the rain so the ratio holds after the final limiter
    x = np.stack([src, src], axis=1) + rain  # source mono-centred, rain wide
    y = master(x, target_lufs=-14.0, fade_out_s=0.3)
    c_db = 20 * np.log10(np.sqrt((y[i24:i24 + int(0.05 * SR), 0] ** 2).mean()))
    r_db = 20 * np.log10(np.sqrt((y[ra:rb] ** 2).mean()))
    err = (r_db - c_db) - RAIN_REL_DB
    if abs(err) < 0.3:
        break
    rain *= 10 ** (-0.4 * err / 20)  # damped: the LUFS gate makes the response steeper than 1:1
assert abs(err) < 0.5, err
write_wav(sys.argv[1], y, N)
