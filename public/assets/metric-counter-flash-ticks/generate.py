"""--- 10. Metric counter flash ticks (id: metric-counter-flash-ticks, category: ui-sounds, 3.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 144,000 samples (3.0 s at 30 fps = 90 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 3-second counting-up metric flash for dashboards and ad promos. Frames 0-60: a numeric counter ticks: clean digital clicks (1 ms 5 kHz sine burst + tiny noise transient) starting at 6/s and accelerating to 30/s, with pitch rising from B5 to F#7 in B minor scale steps every 6 ticks. Under it a faint sine riser B3→B4. Frame 60: the number locks: a bright two-layer 'ding' (FM bell B6 + glass partial at F#7, 600 ms decay) plus a soft sub tap on B1 and a 30 ms white-noise sparkle, panned centre; frames 60-90: light stereo shimmer tail (short ping-pong 125 ms delay). Silence from frame 84 to the end apart from the decaying tail. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 2 approach: smoothstep acceleration 6 -> 30 ticks/s (eases in, rushes, then settles into the lock; still exactly 36 ticks); each tick = 1 ms 5 kHz burst + noise transient + a short band-limited square 'LCD digit' blip; FM bell at a harmonic 1:1 ratio with index decaying 3 -> 0 (bright DX-style strike melting to a pure tone) plus a slowly beating glass partial; ping-pong echoes that get darker on every repeat.
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


import time
T0 = time.time()

N = 144000
FR = 1600
LOCK = 60 * FR
B_MINOR = {11, 1, 2, 4, 6, 7, 9}
BM = {11, 2, 6}                # B minor triad: the 'chord' under the whole cue
NOTES = []


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def reg(sample, midi):
    NOTES.append((sample, midi))
    return mtof(midi)


def tarr(n):
    return np.arange(n) / SR


def ramps(n, att, rel):
    e = np.ones(n)
    att, rel = max(1, min(att, n // 2)), max(1, min(rel, n // 2))
    e[:att] = 0.5 - 0.5 * np.cos(np.pi * np.arange(att) / att)
    e[n - rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, rel + 1) / rel)
    return e


def add(buf, start, sig, pan=0.0, gain=1.0):
    start = int(start)
    sig = sig[: buf.shape[0] - start]
    th = (pan + 1) * np.pi / 4
    buf[start:start + len(sig), 0] += gain * np.sqrt(2) * np.cos(th) * sig
    buf[start:start + len(sig), 1] += gain * np.sqrt(2) * np.sin(th) * sig


def hp(x, fc, order=4):
    return signal.sosfilt(signal.butter(order, fc, "highpass", fs=SR, output="sos"), x, axis=0)


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "lowpass", fs=SR, output="sos"), x, axis=0)


def tick_times(rate_fn, n_ticks=36):
    tt = np.arange(LOCK + 1) / SR
    rate = rate_fn(tt / 2.0)
    ph = np.concatenate([[0.0], np.cumsum((rate[1:] + rate[:-1]) / 2) / SR])
    assert abs(ph[-1] - n_ticks) < 0.05, ph[-1]
    return np.searchsorted(ph, np.arange(n_ticks))


STEPS = [83, 86, 90, 95, 98, 102]   # B5 D6 F#6 B6 D7 F#7 : B-minor scale tones (triad steps), 6 ticks each
times = tick_times(lambda u: 6 + 24 * u * u * (3 - 2 * u))
iv = np.diff(np.append(times, LOCK)) / SR
assert abs(1 / iv[0] - 6) < 1.0 and abs(1 / iv[-1] - 30) < 1.5, (1 / iv[0], 1 / iv[-1])


def tick(sample, midi):
    n = int(0.025 * SR)
    t = tarr(n)
    k = int(0.001 * SR)
    burst = np.zeros(n)
    burst[:k] = np.sin(2 * np.pi * 5000 * t[:k]) * ramps(k, 10, 10)
    m = int(0.0004 * SR)
    nz = np.zeros(n)
    nz[:m] = rng.standard_normal(m) * np.hanning(m)
    f = reg(sample, midi)
    sq = sum(np.sin(2 * np.pi * h * f * t) / h for h in (1, 3, 5) if h * f < 16000)
    blip = sq * np.exp(-t / 0.006) * ramps(n, int(0.001 * SR), int(0.003 * SR))
    return 0.9 * burst + 0.2 * nz + 0.4 * blip


x = np.zeros((N, 2))
for i, s in enumerate(times):
    add(x, s, tick(int(s), STEPS[i // 6]), pan=0.12 if i % 2 else -0.12, gain=0.5)

fa, fb = reg(0, 59), reg(LOCK - 1, 71)        # sine riser B3 -> B4, smoothstep pitch curve
t = tarr(LOCK)
u = t / t[-1]
fr_ = fa * (fb / fa) ** (u * u * (3 - 2 * u))
riser = np.sin(2 * np.pi * np.cumsum(fr_) / SR) * u ** 0.6 * ramps(LOCK, int(0.25 * SR), int(0.012 * SR))
add(x, 0, riser, gain=0.025)

# ------------------------------------------------------------- lock at 60 --
n = N - LOCK
t = tarr(n)
fc = reg(LOCK, 95)                       # B6 carrier, modulator at 1:1
index = 3.0 * np.exp(-t / 0.06)
bell = np.sin(2 * np.pi * fc * t + index * np.sin(2 * np.pi * fc * t)) * np.exp(-t / 0.13)
fg = reg(LOCK, 102)                      # F#7 glass partial, two sines 0.7 Hz apart (slow shimmer)
glass = 0.5 * (np.sin(2 * np.pi * (fg - 0.35) * t) + np.sin(2 * np.pi * (fg + 0.35) * t + 1.0)) * np.exp(-t / 0.11)
ding = (bell + 0.6 * glass) * ramps(n, int(0.0015 * SR), int(0.01 * SR))
sub = np.sin(2 * np.pi * reg(LOCK, 35) * t) * np.exp(-t / 0.06) * ramps(n, int(0.004 * SR), int(0.01 * SR))
k = int(0.03 * SR)
spark = np.zeros(n)
spark[:k] = rng.standard_normal(k) * ramps(k, int(0.001 * SR), int(0.008 * SR))
add(x, LOCK, 0.55 * ding + 0.5 * sub + 0.08 * spark)

wet = hp(0.55 * ding + 0.08 * spark, 1200, 2)
D = int(0.125 * SR)
for r in range(1, 7):
    wet = lp(wet, 9000 - 900 * r)             # each repeat a little darker
    add(x, LOCK + r * D, wet, pan=-0.8 if r % 2 else 0.8, gain=0.45 * 0.52 ** (r - 1))

for s, m in NOTES:
    assert float(m).is_integer() and int(m) % 12 in BM, (s, m)
print(f"harmony ok: {len(NOTES)} notes, all B-minor triad tones (scale {sorted(B_MINOR)})")
y = master(x, target_lufs=-14.0, fade_out_s=0.2)
print(f"ticks {len(times)}  first rate {1 / iv[0]:.1f}/s  last {1 / iv[-1]:.1f}/s  "
      f"lufs {lufs(y):.2f} tp {true_peak_db(y):.2f} runtime {time.time() - T0:.2f}s")
write_wav(sys.argv[1], y, N)
