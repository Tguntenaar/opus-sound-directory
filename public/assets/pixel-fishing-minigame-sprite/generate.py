"""--- 8. Pixel fishing minigame (8-sound sprite) (id: pixel-fishing-minigame-sprite, category: ui-sounds, 4.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 192,000 samples (4.0 s at 30 fps = 120 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 4.0-second sprite of eight soft synthesized pixel-game sounds for a fishing/timing minigame, each starting exactly on frames 0, 15, 30, ..., 105 and silent before the next: 1 cast (short rising square sweep 300→900 Hz + noise swish 120 ms), 2 bobber plop (sine bubble 500→1200 Hz, 50 ms), 3 waiting tick (tiny 2 kHz triangle blip), 4 bite! (two quick pulse notes D6-G6, bright), 5 reel tick (three 3 kHz clicks 40 ms apart), 6 perfect-timing hit (G major triad arpeggio G5-B5-D6-G6 in 30 ms steps, sparkle), 7 miss (a soft descending pulse D5→A4, not comical), 8 catch fanfare (original 4-note pulse figure ending on G6 with a triangle G3 under it). All band-limited, 25%/12.5% duty pulse, gentle 4 kHz low-pass for a cozy feel. Master to -17 LUFS integrated, true peak <= -1 dBTP. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm each slot starts on its frame and is silent (< -60 dBFS) before the next, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 3 approach: console-style rendering: every pitched voice is a naive pulse / 16-step triangle generated at 16x the sample rate and decimated with a polyphase anti-alias FIR (band-limited), volume envelopes are 4-bit (16-level) steps at a 240 Hz 'frame counter' smoothed by a 1 ms ramp, pitch slides are stepped per 4 ms like a sound driver, the cast swish is a 1-bit LFSR-style noise whose clock speeds up, and a 1-pole 4 kHz low-pass softens the whole bus. Figures differ from takes 1-2: fanfare G5-D6-B5-G6 with delayed vibrato on the last note, the perfect hit adds quiet G7 sparkle blips. Mastered to -17 LUFS (UI-specific instruction) and gated per slot (2 ms fades).
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

# ------------------------------------------------------------------ sprite ---
SEED = 57
rng = np.random.default_rng(SEED)
N = 192000
SPF = 1600
SLOT = 15 * SPF
SLOTS = [i * 15 for i in range(8)]
OS = 16
G_MAJOR = {7, 9, 11, 0, 2, 4, 6}
G_TRIAD = {7, 11, 2}
NOTE = {"G3": 55, "A4": 69, "D5": 74, "G5": 79, "B5": 83, "D6": 86, "G6": 91, "G7": 103}


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def note(name, pcs):
    m = NOTE[name]
    assert m % 12 in pcs, f"{name} not in {pcs}"
    return mtof(m)


def secs(s):
    return int(round(s * SR))


def hold(v, step_s, n):
    """sample-and-hold a per-step value array to n samples (step = step_s)."""
    k = secs(step_s)
    return np.repeat(v, k)[:n] if len(v) * k >= n else np.pad(np.repeat(v, k), (0, n - len(v) * k), mode="edge")


def vol_env(n, att_s, decay_s, rel_s):
    """4-bit stepped envelope at 240 Hz, 1 ms smoothing, plus clean 1.5 ms start / end ramps."""
    t_steps = np.arange(int(np.ceil(n / secs(1 / 240)))) / 240
    lv = np.minimum(1, (t_steps + 1 / 240) / max(att_s, 1 / 240)) * np.exp(-t_steps / decay_s)
    lv = np.round(lv * 15) / 15
    e = hold(lv, 1 / 240, n)
    e = np.convolve(e, np.ones(48) / 48, mode="same")
    na, nr = secs(0.0015), max(secs(0.0015), secs(rel_s))
    e[:na] *= np.linspace(0, 1, na)
    e[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return e


def os_pulse(freq, duty):
    """naive pulse at 16x, decimated -> band-limited.  freq: per-output-sample array."""
    fo = np.repeat(freq, OS) / OS
    ph = np.cumsum(fo / SR) % 1.0
    p = np.where(ph < duty, 1.0, -1.0) - (2 * duty - 1)
    return signal.resample_poly(p, 1, OS)[: len(freq)]


def os_tri(freq):
    fo = np.repeat(freq, OS) / OS
    ph = np.cumsum(fo / SR) % 1.0
    step = np.floor(ph * 32).astype(int)
    lv = np.where(step < 16, 15 - step, step - 16) / 7.5 - 1.0
    return signal.resample_poly(lv, 1, OS)[: len(freq)]


def place(buf, sig, slot, at_s=0.0, p=0.0):
    s0 = slot * SLOT + secs(at_s)
    a = (p + 1) * np.pi / 4
    buf[s0:s0 + len(sig), 0] += sig * np.cos(a) * np.sqrt(2)
    buf[s0:s0 + len(sig), 1] += sig * np.sin(a) * np.sqrt(2)


x = np.zeros((N, 2))

# 1 cast: driver-style stepped 300 -> 900 Hz slide (4 ms steps) + 1-bit noise swish with rising clock
n = secs(0.16)
steps = np.arange(int(np.ceil(n / secs(0.004))))
f_steps = 300 * 3 ** np.minimum(steps * 0.004 / 0.15, 1)
cast = 0.3 * os_pulse(hold(f_steps, 0.004, n), 0.25) * vol_env(n, 0.004, 0.2, 0.03)
ns = secs(0.12)
tn = np.arange(ns * OS) / (SR * OS)
clock = 2000 * 6 ** (tn / 0.12)                               # noise 'period' speeds up 2 kHz -> 12 kHz
idx = np.floor(np.cumsum(clock) / (SR * OS)).astype(int)
bits = rng.integers(0, 2, idx.max() + 1) * 2.0 - 1.0
nz = signal.resample_poly(bits[idx], 1, OS)[:ns]
nz *= vol_env(ns, 0.03, 0.06, 0.04)
cast[:ns] += 0.18 * nz
place(x, cast, 0)

# 2 bobber plop: sine bubble 500 -> 1200 Hz (log-shaped), 50 ms, faint 2nd harmonic
n = secs(0.05)
t = np.arange(n) / SR
f = 500 + 700 * np.log1p(9 * t / 0.05) / np.log(10)
ph = 2 * np.pi * np.cumsum(f) / SR
e = np.exp(-t / 0.025)
e[:secs(0.0015)] *= np.linspace(0, 1, secs(0.0015))
e[-secs(0.01):] *= np.cos(np.linspace(0, np.pi / 2, secs(0.01))) ** 2
place(x, 0.5 * (np.sin(ph) + 0.12 * np.sin(2 * ph)) * e, 1)

# 3 waiting tick: tiny 2 kHz 16-step triangle blip
n = secs(0.02)
place(x, 0.4 * os_tri(np.full(n, 2000.0)) * vol_env(n, 0.002, 0.008, 0.006), 2)

# 4 bite!: staccato D6, G6 (12.5% duty)
for nm, at, d in (("D6", 0.0, 0.05), ("G6", 0.065, 0.10)):
    n = secs(d)
    place(x, 0.35 * os_pulse(np.full(n, note(nm, G_TRIAD)), 0.125) * vol_env(n, 0.002, 0.12, 0.015), 3, at)

# 5 reel tick: three 3 kHz clicks (12 cycles of 25% pulse, 4 ms grain), 40 ms apart
for i in range(3):
    n = secs(0.004)
    s = os_pulse(np.full(n, 3000.0), 0.25)
    s *= np.sin(np.linspace(0, np.pi, n)) ** 2                 # smooth 2 ms grain
    place(x, 0.4 * s, 4, 0.04 * i)

# 6 perfect-timing hit: G5-B5-D6-G6 at 30 ms steps (each note keeps ringing) + quiet G7 sparkle blips
for i, nm in enumerate(("G5", "B5", "D6", "G6")):
    n = secs(0.3 - 0.03 * i)
    place(x, 0.2 * os_pulse(np.full(n, note(nm, G_TRIAD)), 0.25) * vol_env(n, 0.002, 0.09, 0.07),
          5, 0.03 * i, p=(-0.2, -0.07, 0.07, 0.2)[i])
for at in np.sort(rng.uniform(0.12, 0.3, 4)):
    n = secs(0.03)
    place(x, 0.07 * os_pulse(np.full(n, note("G7", G_TRIAD)), 0.125) * vol_env(n, 0.002, 0.01, 0.015),
          5, float(at), p=float(rng.uniform(-0.5, 0.5)))

# 7 miss: soft 25% pulse sliding D5 -> A4 in 4 ms driver steps (G-major scale tones)
n = secs(0.34)
steps = np.arange(int(np.ceil(n / secs(0.004)))) * 0.004
u = np.clip((steps - 0.08) / 0.14, 0, 1)
fa, fb = note("D5", G_MAJOR), note("A4", G_MAJOR)
f = hold(fa * (fb / fa) ** (u * u * (3 - 2 * u)), 0.004, n)
s = os_pulse(f, 0.25) * vol_env(n, 0.01, 0.3, 0.1)
s = signal.sosfilt(signal.butter(1, 1600, "lowpass", fs=SR, output="sos"), s)
place(x, 0.32 * s, 6)

# 8 catch fanfare: original G5-D6-B5-G6 figure, last note with delayed vibrato, triangle G3 under
for nm, at, d in (("G5", 0.0, 0.065), ("D6", 0.07, 0.065), ("B5", 0.14, 0.065), ("G6", 0.21, 0.2)):
    n = secs(d)
    t = np.arange(n) / SR
    f0 = note(nm, G_TRIAD)
    f = f0 * 2 ** ((15 / 1200) * np.clip((t - 0.06) / 0.05, 0, 1) * np.sin(2 * np.pi * 7 * t)) if nm == "G6" else np.full(n, f0)
    place(x, 0.3 * os_pulse(f, 0.25) * vol_env(n, 0.002, 0.3, 0.09 if nm == "G6" else 0.01), 7, at)
n = secs(0.41)
place(x, 0.16 * os_tri(np.full(n, note("G3", G_TRIAD))) * vol_env(n, 0.004, 0.6, 0.12), 7)

# cozy bus: gentle 1-pole 4 kHz low-pass
x = signal.lfilter(*signal.butter(1, 4000, "lowpass", fs=SR), x, axis=0)

y = master(x, target_lufs=-17.0, fade_out_s=0.02)

gate = np.zeros(N)
fd = secs(0.002)
for s in SLOTS:
    a, b = s * SPF, s * SPF + SLOT - SPF
    gate[a:b] = 1.0
    gate[b - fd:b] = np.cos(np.linspace(0, np.pi / 2, fd)) ** 2
y = y * gate[:, None]
y[-1] = 0.0
write_wav(sys.argv[1], y, N)
