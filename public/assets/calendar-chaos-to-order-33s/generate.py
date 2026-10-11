"""--- 3. Calendar chaos → everything fits (id: calendar-chaos-to-order-33s, category: chaos-calm, 33.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 1,584,000 samples (33.0 s at 30 fps = 990 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 33-second app-launch bed at 118 BPM in Ab major that goes from overloaded to tidy. Frames 0-174 (chaos): overlapping calendar-alert pings at clashing rates (sine+2nd partial, pitches drawn from a whole-tone set so they clash), muffled notification buzzes, a ticking clock at 1.7 Hz against the grid, and a sub drone on Ab0 slowly swelling; a filtered-noise riser climbs from frame 120. Frame 174 (5.8 s): everything cuts to 6 frames of silence. Frame 180: logo hit: sub boom on Ab1, warm Abmaj9 bell-pad chord, glass shimmer. Frames 180-420: a light four-on-the-floor (soft round kick, shaker on 16ths, no snare) with a plucked arpeggio on Abmaj9 → Fm9 → Dbmaj7 → Eb6, and a soft sine-chime on frames 210, 270, 330 and 390 (typing / reorganising accents, rising Ab5, C6, Eb6, G6). Frames 420-840: full groove, a 1/8-note marimba ostinato and three bright callout 'pops' on frames 450, 540 and 630 (each a 2-note rising mallet interval, different every time). Frames 840-870: 1-bar riser. Frame 870: 'Everything fits' resolve on Abmaj9 with a gentle impact, groove continues sparser, final logo hit on frame 930, ring-out to 0 by frame 990. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 2 approach: FM + Karplus-Strong + convolution room. Chaos: five ping streams (sine+2nd partial, Ab whole-tone set) that often fire as 2-note whole-tone clusters, FM phone buzzes (1:1 FM, 3-pulse pattern, low-passed at 500 Hz), a wooden tick-tock clock (two damped resonator modes) at 1.7 Hz, Ab0+Ab1 drone with slow beating, narrow resonant noise riser from frame 120, hard cut at 174. Order: FM bells (1:3.5) and a detuned additive-saw pad for the logo hits, Karplus-Strong plucks (lfilter comb with fractional-delay taps) arpeggiating in 3-against-4 groups, FM marimba ostinato in 1/8s, root/octave 8th bass, all sent to a synthetic stereo noise-IR room (fftconvolve). Same 4/6/2/4-beat harmonic rhythm as take 1 for the chime section, then 2 bars per chord in the full groove (Abmaj9, Fm9, Dbmaj7, Eb6 under the riser). Pops: P5, m6, octave.
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
FPS = 30
N = 1584000
BPM = 118.0
BEAT = 60.0 / BPM
T0 = 180 / FPS
TR = 870 / FPS
TEND = N / SR


def ft(frame):
    return frame / FPS


def bt(k):
    return T0 + k * BEAT


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------ harmony map --
WT = {8, 10, 0, 2, 4, 6}
CH = {"Abmaj9": {8, 0, 3, 7, 10}, "Fm9": {5, 8, 0, 3, 7}, "Dbmaj7": {1, 5, 8, 0}, "Eb6": {3, 7, 10, 0}}
SPANS = [(0, 4, "Abmaj9"), (4, 10, "Fm9"), (10, 12, "Dbmaj7"), (12, 16, "Eb6"),
         (16, 24, "Abmaj9"), (24, 32, "Fm9"), (32, 40, "Dbmaj7")]
TIMELINE = [(bt(a), bt(b), n) for a, b, n in SPANS] + [(bt(40), TR, "Eb6"), (TR, TEND, "Abmaj9")]


def chord_at(t):
    for a, b, n in TIMELINE:
        if a - 1e-9 <= t < b:
            return n
    return None


NOTES = []


def reg(t, m, ctx="chord"):
    NOTES.append((t, m, ctx))


ARP = {"Abmaj9": [56, 60, 63, 67, 70, 72, 75], "Fm9": [53, 56, 60, 63, 67, 68, 72],
       "Dbmaj7": [49, 53, 56, 60, 65, 68, 72], "Eb6": [51, 55, 58, 60, 63, 67, 70]}
MAR = {"Abmaj9": [75, 79, 80, 84, 82], "Fm9": [72, 75, 77, 80, 79],
       "Dbmaj7": [72, 73, 77, 80, 77], "Eb6": [70, 72, 75, 79, 75]}
PAD = {"Abmaj9": [44, 55, 60, 63, 70], "Fm9": [41, 56, 60, 63, 67],
       "Dbmaj7": [37, 56, 60, 65], "Eb6": [39, 55, 58, 60]}
ROOT = {"Abmaj9": 32, "Fm9": 29, "Dbmaj7": 37, "Eb6": 39}

x = np.zeros((N, 2))
wet = np.zeros((N, 2))
tt = np.arange(N) / SR


def tvec(dur):
    return np.arange(int(round(dur * SR))) / SR


def ramp(s, a_ms=2.0, r_ms=4.0):
    ka, kr = max(2, int(a_ms * 1e-3 * SR)), max(2, int(r_ms * 1e-3 * SR))
    s[:ka] *= np.linspace(0, 1, ka)
    s[-kr:] *= np.linspace(1, 0, kr)
    return s


def place(sig, t, pan=0.0, g=1.0, buf=None, send=0.0):
    buf = x if buf is None else buf
    i0 = int(round(t * SR))
    if i0 >= N:
        return
    n = min(len(sig), N - i0)
    th = (pan + 1) * np.pi / 4
    for b, gg in ((buf, g), (wet, g * send)):
        if gg:
            b[i0:i0 + n, 0] += gg * np.cos(th) * sig[:n]
            b[i0:i0 + n, 1] += gg * np.sin(th) * sig[:n]


def lp(s, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "lowpass", fs=SR, output="sos"), s)


def res_sweep(dur, f0, f1, q=6.0, curve=1.0):
    """white noise through a block-updated resonant 2-pole bandpass (narrow, whistling riser)"""
    n = int(dur * SR)
    w = rng.standard_normal(n)
    out = np.zeros(n)
    blk = 256
    zi = np.zeros(2)
    for i in range(0, n, blk):
        fc = f0 * (f1 / f0) ** ((i / n) ** curve)
        b, a = signal.iirpeak(min(fc, 17000.0), q, fs=SR)
        out[i:i + blk], zi = signal.lfilter(b, a, w[i:i + blk], zi=zi)
    return out / (np.abs(out).max() + 1e-12)


# ------------------------------------------------------------- voices --
def ping(f):
    t = tvec(0.35)
    s = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.05)) * np.exp(-t / 0.07)
    return ramp(s, 1.5, 5)


def fm_buzz(f, dur):
    t = tvec(dur)
    s = np.sin(2 * np.pi * f * t + 2.2 * np.sin(2 * np.pi * f * t))
    s *= 0.7 + 0.3 * np.sign(np.sin(2 * np.pi * 24 * t))  # motor rattle
    s = lp(lp(s, 500, 4), 900)
    return ramp(s, 10, 15)


def clock(tick):
    t = tvec(0.06)
    exc = rng.standard_normal(len(t)) * np.exp(-t / 0.0008)
    modes = [(2350, 0.012), (4100, 0.006)] if tick else [(1650, 0.016), (2900, 0.008)]
    s = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, d in modes)
    s = s + 0.3 * lp(exc, 6000)
    return ramp(s / np.abs(s).max(), 0.5, 4)


def boom(m, dur=2.6, tau=0.6):
    t = tvec(dur)
    f = hz(m) * (1 + 0.9 * np.exp(-t / 0.05))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau)
    s += 0.25 * lp(rng.standard_normal(len(t)) * np.exp(-t / 0.02), 300)
    return ramp(s, 2, 30)


def fm_bell(f, dur=3.2, tau=1.2):
    t = tvec(dur)
    idx = 1.6 * np.exp(-t / 0.5)
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * 3.5 * f * t)) * np.exp(-t / tau)
    s += 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / (tau * 0.4))
    return ramp(s, 3, 40)


def saw_pad(f, dur, att=0.5, rel=0.8):
    t = tvec(dur)
    s = np.zeros_like(t)
    for det in (-0.004, 0.0, 0.0045):
        ph0 = rng.uniform(0, 6.28)
        k = 1
        while k * f < 3500 and k <= 14:
            s += (1 / k) * np.sin(2 * np.pi * k * f * (1 + det) * t + k * ph0) * (0.85 ** k)
            k += 1
    env = np.clip(np.minimum(t / att, (dur - t) / rel), 0, 1)
    return ramp(s * env / 3, 5, 10)


def glass(t0, g=1.0):
    for m in [96, 99, 103, 106, 108, 111]:
        reg(t0, m)
        t = tvec(1.8)
        s = np.sin(2 * np.pi * hz(m) * t + 0.4 * np.sin(2 * np.pi * hz(m) * 2 * t)) * np.exp(-t / 0.5)
        s *= 1 + 0.4 * np.sin(2 * np.pi * rng.uniform(5, 9) * t)
        place(ramp(s, 4, 30), t0 + rng.uniform(0, 0.12), pan=rng.uniform(-0.9, 0.9), g=0.025 * g, send=0.6)


def kick(g=1.0):
    t = tvec(0.35)
    f = 50 + 60 * np.exp(-t / 0.035)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)
    return ramp(s, 3, 10) * g


def shaker():
    t = tvec(0.07)
    s = rng.standard_normal(len(t)) * (t / 0.012) * np.exp(1 - t / 0.012)
    s = signal.sosfilt(signal.butter(2, [6500.0, 13000.0], "bandpass", fs=SR, output="sos"), s)
    return ramp(s / np.abs(s).max(), 2, 3)


def ks_pluck(f, dur=0.9, damp=0.996):
    """Karplus-Strong: comb with fractional-delay (linear interp) taps in the feedback path."""
    L = SR / f
    D = int(np.floor(L))
    p = L - D
    n = int(dur * SR)
    exc = np.zeros(n)
    burst = lp(rng.standard_normal(D), min(5000.0, 8 * f))
    exc[:D] = burst * np.hanning(D)
    a = np.zeros(D + 2)
    a[0] = 1.0
    a[D] -= damp * (1 - p)
    a[D + 1] -= damp * p
    s = signal.lfilter([1.0], a, exc)
    s = lp(s, 7000)
    s *= np.exp(-np.arange(n) / SR / 0.35)
    return ramp(s / (np.abs(s).max() + 1e-12), 1, 10)


def fm_marimba(f, dur=0.7):
    t = tvec(dur)
    idx = 1.4 * np.exp(-t / 0.025)
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * 4 * f * t)) * np.exp(-t / 0.3)
    s = lp(s, 14000)
    return ramp(s, 1.5, 10)


def chime(f, dur=2.4):
    t = tvec(dur)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.7) * (1 + 0.15 * np.sin(2 * np.pi * 5 * t))
    s += 0.2 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.2)
    return ramp(s, 4, 30)


def pop(f):
    t = tvec(0.45)
    fi = f * (1 + 0.08 * np.exp(-t / 0.004))
    ph = 2 * np.pi * np.cumsum(fi) / SR
    s = np.sin(ph + 0.9 * np.exp(-t / 0.02) * np.sin(3 * ph)) * np.exp(-t / 0.14)
    return ramp(lp(s, 15000), 1, 8)


def bass(f, dur):
    t = tvec(dur)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.1)
    return ramp(s * np.exp(-t / 0.35), 5, 25)


# ================================================================ CHAOS ==
CUT = ft(174)
chaos = np.zeros((N, 2))
for period, lo, gain in [(0.27, 79, 0.07), (0.41, 74, 0.08), (0.53, 84, 0.06), (0.67, 70, 0.08), (0.83, 76, 0.07)]:
    t = rng.uniform(0, period)
    while t < CUT - 0.05:
        pool = [p for p in range(lo, lo + 12) if p % 12 in WT]
        k = int(rng.integers(len(pool) - 1))
        ms = pool[k:k + 2] if rng.random() < 0.35 else [pool[k]]  # whole-tone dyads clash
        for j, m in enumerate(ms):
            reg(t, m, "chaos")
            place(ping(hz(m)), t + 0.012 * j, pan=rng.uniform(-0.8, 0.8),
                  g=gain * (0.45 + 0.55 * t / CUT), buf=chaos, send=0.3)
        t += period * rng.uniform(0.7, 1.3)
for t0, m in [(0.2, 52), (1.25, 54), (2.4, 50), (3.1, 56), (3.95, 54), (4.7, 52), (5.3, 50)]:
    reg(t0, m, "chaos")
    for k in range(3):
        place(fm_buzz(hz(m), 0.18), t0 + k * 0.24, pan=rng.uniform(-0.5, 0.5), g=0.08, buf=chaos)
k = 0
while 0.05 + k / 1.7 < CUT - 0.03:
    place(clock(k % 2 == 0), 0.05 + k / 1.7, pan=-0.3, g=0.12, buf=chaos, send=0.2)
    k += 1
td = tvec(CUT)
for m in (20, 32):
    reg(0.0, m, "chaos")
dr = np.sin(2 * np.pi * hz(20) * td) + 0.5 * np.sin(2 * np.pi * hz(32) * 1.003 * td) + 0.5 * np.sin(2 * np.pi * hz(32) * td)
dr *= (td / CUT) ** 2
place(ramp(dr, 50, 2), 0.0, g=0.2, buf=chaos)
rd0 = CUT - ft(120)
rz = res_sweep(rd0, 500.0, 9000.0, q=5.0, curve=1.2) * np.linspace(0, 1, int(rd0 * SR)) ** 1.6
place(ramp(rz, 5, 2), ft(120), g=0.12, buf=chaos)
chaos *= np.clip((CUT - tt) / 0.002, 0, 1)[:, None]
x += chaos


# ============================================================ LOGO HIT ==
def logo_hit(t0, g=1.0):
    reg(t0, 32)
    place(boom(32), t0, g=0.5 * g)
    for i, m in enumerate([56, 60, 63, 67, 70, 72]):
        reg(t0, m)
        place(fm_bell(hz(m)), t0 + 0.006 * i, pan=-0.6 + 0.24 * i, g=0.05 * g, send=0.5)
        place(saw_pad(hz(m), 3.0, att=0.08, rel=2.0), t0, pan=0.6 - 0.24 * i, g=0.03 * g, send=0.4)
    glass(t0, g)


logo_hit(T0)

# ====================================================== GROOVE A (180-420) ==
for kb in range(1, 16):
    place(kick(), bt(kb), g=0.33)
for s16 in range(64):
    place(shaker(), bt(s16 / 4) + rng.normal(0, 0.002), pan=-0.35, g=0.03 * (1.0 if s16 % 2 else 0.55), send=0.2)
grp = [0, 2, 4, 1, 3, 5, 2, 4, 6, 3, 5, 4]  # 3-note groups against the 16th grid
for s16 in range(64):
    t = bt(s16 / 4)
    c = chord_at(t + 1e-6)
    m = ARP[c][grp[s16 % 12]]
    reg(t, m)
    place(ks_pluck(hz(m)), t, pan=0.4 * np.sin(s16 * 0.7), g=0.07 * (1.0 if s16 % 3 == 0 else 0.7), send=0.35)
for fr_, m in [(210, 80), (270, 84), (330, 87), (390, 91)]:
    reg(ft(fr_), m)
    place(chime(hz(m)), ft(fr_), pan=-0.15, g=0.1, send=0.6)

# ====================================================== GROOVE B (420-840) ==
# beat 15.75 sits on frame 420.4: shaker fill + marimba pickup into the full groove
for j in range(3):
    reg(bt(15.25 + 0.25 * j), [63, 67, 70][j])
    place(fm_marimba(hz([63, 67, 70][j])), bt(15.25 + 0.25 * j), pan=0.2, g=0.1 + 0.03 * j, send=0.3)
for kb in range(16, 44):
    place(kick(), bt(kb), g=0.42)
for e8 in range(32, 88):
    t = bt(e8 / 2)
    c = chord_at(t + 1e-6)
    r = ROOT[c] + (12 if e8 % 2 else 0)
    reg(t, r)
    place(bass(hz(r), BEAT * 0.48), t, g=0.2 if e8 % 2 == 0 else 0.12)
for s16 in range(64, 176):
    place(shaker(), bt(s16 / 4) + rng.normal(0, 0.002), pan=-0.35, g=0.035 * (1.0 if s16 % 2 else 0.55), send=0.2)
pat8 = [0, 1, 2, 1, 3, 2, 4, 2]
for e8 in range(32, 88):
    t = bt(e8 / 2)
    c = chord_at(t + 1e-6)
    m = MAR[c][pat8[e8 % 8]]
    reg(t, m)
    place(fm_marimba(hz(m)), t, pan=0.25 if e8 % 2 else -0.1, g=0.12 * (1.0 if e8 % 2 == 0 else 0.75), send=0.3)
for a, b, c in TIMELINE:
    if bt(16) - 1e-6 <= a < TR:
        for m in PAD[c][1:]:
            reg(a, m)
            place(saw_pad(hz(m), b - a + 0.4, att=0.4, rel=0.6), a, pan=rng.uniform(-0.6, 0.6), g=0.02, send=0.5)
for fr_, (m1, m2) in [(450, (75, 82)), (540, (84, 92)), (630, (77, 89))]:  # P5, m6, octave
    for i, m in enumerate((m1, m2)):
        reg(ft(fr_) + 0.07 * i, m)
        place(pop(hz(m)), ft(fr_) + 0.07 * i, pan=0.3 - 0.6 * i, g=0.16, send=0.4)

# ========================================================= RISER 840-870 ==
rd = TR - ft(840)
rz = res_sweep(rd, 300.0, 10000.0, q=3.0, curve=1.0) * np.linspace(0.1, 1, int(rd * SR)) ** 2
place(ramp(rz, 5, 2), ft(840), g=0.35, send=0.3)
nz = signal.sosfilt(signal.butter(2, 4000, "highpass", fs=SR, output="sos"), rng.standard_normal(int(rd * SR)))
place(ramp(nz * np.linspace(0, 1, len(nz)) ** 3, 5, 2), ft(840), pan=0.0, g=0.08)
rs = TR - bt(44)  # Eb1 sub swell after the last kick (beat 44) keeps the floor under the riser
ts_ = tvec(rs)
reg(bt(44), 39)
place(ramp(np.sin(2 * np.pi * hz(39) * ts_) * (0.3 + 0.7 * ts_ / rs), 20, 2), bt(44), g=0.2)

# ===================================================== RESOLVE 870-990 ==
reg(TR, 32)
place(boom(32, tau=0.45), TR, g=0.32)
imp = lp(rng.standard_normal(int(0.4 * SR)) * np.exp(-tvec(0.4) / 0.08), 700)
place(ramp(imp / np.abs(imp).max(), 2, 10), TR, g=0.14, send=0.6)
for i, m in enumerate([56, 63, 67, 70, 72, 75]):
    reg(TR, m)
    place(fm_bell(hz(m), tau=0.9), TR + 0.006 * i, pan=-0.5 + 0.2 * i, g=0.045, send=0.5)
    place(saw_pad(hz(m), 2.0, att=0.05, rel=1.4), TR, pan=0.5 - 0.2 * i, g=0.028, send=0.4)


def br(k):
    return TR + k * BEAT


for kb in range(4):
    place(kick(), br(kb), g=0.28)
for e8 in range(1, 8, 2):
    place(shaker(), br(e8 / 2), pan=-0.35, g=0.03, send=0.3)
for kq, m in enumerate([72, 75, 79, 80, 84, 87]):
    t = br(kq * 0.75)
    reg(t, m)
    place(ks_pluck(hz(m), 1.2), t, pan=-0.3 + 0.12 * kq, g=0.06, send=0.5)
logo_hit(ft(930), g=0.9)

# ---------------------------------------------------------- room + checks --
ir_n = int(1.8 * SR)
it = np.arange(ir_n) / SR
ir = rng.standard_normal((ir_n, 2)) * np.exp(-it / 0.42)[:, None]
ir = signal.sosfilt(signal.butter(2, 5500, "lowpass", fs=SR, output="sos"), ir, axis=0)
ir[: int(0.012 * SR)] = 0.0  # pre-delay
ir /= np.sqrt((ir ** 2).sum(axis=0))
x[:, 0] += 0.5 * signal.fftconvolve(wet[:, 0], ir[:, 0])[:N]
x[:, 1] += 0.5 * signal.fftconvolve(wet[:, 1], ir[:, 1])[:N]

for t, m, ctx in NOTES:
    if ctx == "chaos":
        assert m % 12 in WT, (t, m)
    else:
        c = chord_at(t)
        assert c is not None and m % 12 in CH[c], (t, m, c)
gate = np.clip(np.maximum((CUT - tt) / 0.002, (tt - T0) / 0.002), 0, 1)[:, None]
x *= gate
y = master(x, target_lufs=-14.0, fade_out_s=1.2)
y *= gate
write_wav(sys.argv[1], y, N)
