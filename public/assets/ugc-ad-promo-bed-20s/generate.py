"""--- 9. Fast UGC ad-tool promo bed (id: ugc-ad-promo-bed-20s, category: ad-beds, 20.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 960,000 samples (20.0 s at 30 fps = 600 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 20-second punchy SaaS-promo bed in B minor at 120 BPM (1 beat = 15 frames, 10 bars). Frame 0: hit (kick + 808-ish sine sub on B1 + short noise crash). Frames 0-60: filtered intro, drums at 800 Hz low-pass opening up, typing-style clicks on 16ths (URL paste moment), a 'paste' pop on frame 45. Frame 60: full beat: tight kick on 1 and 3, clap on 2 and 4, 16th hats, sidechained (−6 dB pump, 150 ms release) supersaw chords Bm9 → Gmaj7 → D → A6, gliding 808 bass. Frames 120-360: a metric-flash tick (bright 6 kHz sine blip + 1 ms click, 60 ms) on every beat 2 and the '&' of 4, and a quick stutter (4 x 1/32 repeats of the chord) on frames 180, 240 and 300 for clip-cycling cuts. Frame 450: launch-toggle accent (two-tone up-chirp E6→B6 with a soft switch click). Frames 525-540: 1-beat drop-out. Frame 540: end-card hit on Bm(add9), tail fades to 0 by frame 600. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 2 approach: band-limited wavetable supersaw (5 detuned additive-table saws per note) played as off-beat 8th stabs over a quiet sustained layer, both pumped; heavier-driven 808 with a syncopated slide pattern; metallic 808-style hats from six band-limited square oscillators; intro bus swept by a faster-opening LP bank plus a reverse-noise riser into frame 60.
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

# ------------------------------------------------------------------ common --
N = 960000            # 20.0 s
FR = 1600             # samples per video frame (30 fps)
BEAT = 24000          # 120 BPM -> 1 beat = 15 frames
BAR = 4 * BEAT
S16 = BEAT // 4
S32 = BEAT // 8       # 1/32 note = 62.5 ms


def fr(f):
    return int(round(f * FR))


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


# pitch classes: C=0 C#=1 D=2 E=4 F#=6 G=7 A=9 B=11
B_MINOR = {11, 1, 2, 4, 6, 7, 9}
CHORD_PCS = {
    "Bm9": {11, 2, 6, 9, 1},
    "Gmaj7": {7, 11, 2, 6},
    "D": {2, 6, 9},
    "A6": {9, 1, 4, 6},
    "Bm(add9)": {11, 2, 6, 1},
}
# harmonic rhythm: (start frame, end frame, chord). Intro sits on Bm9, then 2 bars per chord.
TIMELINE = [(0, 180, "Bm9"), (180, 300, "Gmaj7"), (300, 420, "D"),
            (420, 540, "A6"), (540, 600, "Bm(add9)")]
VOICING = {
    "Bm9": [59, 62, 66, 69, 73],        # B3 D4 F#4 A4 C#5
    "Gmaj7": [55, 59, 62, 66, 71],      # G3 B3 D4 F#4 B4
    "D": [57, 62, 66, 69, 74],          # A3 D4 F#4 A4 D5
    "A6": [57, 61, 64, 66, 69],         # A3 C#4 E4 F#4 A4
    "Bm(add9)": [59, 62, 66, 71, 73],   # B3 D4 F#4 B4 C#5
}
ROOT = {"Bm9": 35, "Gmaj7": 31, "D": 38, "A6": 33, "Bm(add9)": 35}   # B1 G1 D2 A1
FIFTH = {"Bm9": 42, "Gmaj7": 38, "D": 45, "A6": 40, "Bm(add9)": 42}  # F#2 D2 A2 E2

NOTES = []   # (sample, midi, role) for the harmony assertion


def reg(sample, midi, role="chord"):
    NOTES.append((int(sample), midi, role))
    return mtof(midi)


def chord_at(sample):
    f = sample / FR
    for a, b, c in TIMELINE:
        if a <= f < b:
            return c
    return TIMELINE[-1][2]


def check_harmony():
    bad = []
    for s, m, role in NOTES:
        assert float(m).is_integer(), m
        pc = int(m) % 12
        c = chord_at(s)
        ok = (pc in B_MINOR) if role == "passing" else (pc in CHORD_PCS[c])
        if not ok:
            bad.append((s / FR, m, role, c))
    assert not bad, f"notes outside chord: {bad}"
    print(f"harmony ok: {len(NOTES)} notes checked "
          f"({sum(1 for n in NOTES if n[2] == 'passing')} diatonic passing tones)")


# ------------------------------------------------------------------ helpers --
def lp(x, fc, order=4):
    return signal.sosfilt(signal.butter(order, fc, "lowpass", fs=SR, output="sos"), x, axis=0)


def hp(x, fc, order=4):
    return signal.sosfilt(signal.butter(order, fc, "highpass", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi_, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi_], "bandpass", fs=SR, output="sos"), x, axis=0)


def tarr(n):
    return np.arange(n) / SR


def ramps(n, att, rel):
    """flat envelope with raised-cosine attack/release (in samples)."""
    e = np.ones(n)
    att, rel = max(1, min(att, n // 2)), max(1, min(rel, n // 2))
    e[:att] = 0.5 - 0.5 * np.cos(np.pi * np.arange(att) / att)
    e[n - rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, rel + 1) / rel)
    return e


def perc_env(n, tau, att_s=0.0015, rel_s=0.004):
    e = np.exp(-tarr(n) / tau)
    return e * ramps(n, int(att_s * SR), int(rel_s * SR))


def add(buf, start, sig, pan=0.0, gain=1.0):
    start = int(start)
    if start >= buf.shape[0]:
        return
    if start < 0:
        sig = sig[-start:]
        start = 0
    sig = sig[: buf.shape[0] - start]
    if sig.ndim == 1:
        th = (pan + 1) * np.pi / 4
        buf[start:start + len(sig), 0] += gain * np.sqrt(2) * np.cos(th) * sig
        buf[start:start + len(sig), 1] += gain * np.sqrt(2) * np.sin(th) * sig
    else:
        buf[start:start + len(sig)] += gain * sig


# ------------------------------------------------------------------- drums --
def kick(f0=170.0, f1=55.0, dec=0.26, click=0.25, n=int(0.5 * SR)):
    t = tarr(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * perc_env(n, dec, 0.001, 0.01)
    clk = hp(rng.standard_normal(n), 2500, 2) * perc_env(n, 0.003, 0.0005, 0.002)
    return body + click * clk


def clap(n=int(0.35 * SR), tail=0.09):
    t = tarr(n)
    nz = rng.standard_normal(n)
    e = np.zeros(n)
    for k, d in enumerate([0.0, 0.009, 0.018]):
        s = int(d * SR)
        e[s:] += (0.8 + 0.1 * k) * np.exp(-(t[: n - s]) / 0.0045)
    s = int(0.024 * SR)
    e[s:] += 0.7 * np.exp(-(t[: n - s]) / tail)
    e *= ramps(n, int(0.0008 * SR), int(0.01 * SR))
    return bp(nz * e, 900, 2800)


def hat(dec=0.03, n=int(0.15 * SR), fc=7000):
    return hp(rng.standard_normal(n), fc) * perc_env(n, dec, 0.001, 0.005)


def crash(dur=1.3, dec=0.4, fc=3500):
    n = int(dur * SR)
    nz = hp(rng.standard_normal((n, 2)), fc)
    return nz * perc_env(n, dec, 0.002, 0.05)[:, None]


def sub808(midi, dur=0.9, dec=0.45, drive=1.5, sample=0):
    f = reg(sample, midi, "sub")
    n = int(dur * SR)
    s = np.sin(2 * np.pi * f * tarr(n))
    return np.tanh(drive * s) / np.tanh(drive) * perc_env(n, dec, 0.002, 0.03)


def type_click(n=int(0.03 * SR)):
    c = bp(rng.standard_normal(n), 1800, 5500) * perc_env(n, 0.0035, 0.001, 0.003)
    c2 = np.zeros(n)
    s = int(0.011 * SR)
    c2[s:] = 0.35 * bp(rng.standard_normal(n - s), 2500, 7000) * perc_env(n - s, 0.002, 0.001, 0.002)
    return c + c2


def metric_tick(sample, n=int(0.060 * SR)):
    """bright ~6 kHz sine blip (tuned to F#8 = 5920 Hz, a tone of every chord) + 1 ms click, 60 ms."""
    f = reg(sample, 114, "tick")
    t = tarr(n)
    blip = np.sin(2 * np.pi * f * t) * perc_env(n, 0.016, 0.001, 0.006)
    k = int(0.001 * SR)
    clk = np.zeros(n)
    clk[:k] = hp(rng.standard_normal(k + 64), 3000, 2)[64:] * ramps(k, 12, 12)
    return blip + 0.6 * clk


def launch_chirp(sample, n=int(0.45 * SR)):
    """two-tone up-chirp E6 -> B6 with a soft switch click."""
    fa = reg(sample, 88, "chord")                      # E6: chord tone of A6
    fb = reg(sample + int(0.08 * SR), 95, "passing")   # B6: diatonic passing tone (9th over A)
    t = tarr(n)
    lf = np.full(n, np.log2(fb))
    a, g = int(0.07 * SR), int(0.018 * SR)
    # each tone has a tiny upward scoop into pitch (chirp), tone 2 glides up from tone 1
    lf[:a] = np.log2(fa) - (1 / 12) * np.exp(-t[:a] / 0.012)
    lf[a:a + g] = np.linspace(np.log2(fa), np.log2(fb), g)
    ph = 2 * np.pi * np.cumsum(2 ** lf) / SR
    tone = np.sin(ph) + 0.18 * np.sin(2 * ph)
    env = np.ones(n)
    env[a + g:] = np.exp(-(t[a + g:] - t[a + g]) / 0.11)
    env *= ramps(n, int(0.002 * SR), int(0.02 * SR))
    clk = bp(rng.standard_normal(n), 1200, 4000) * perc_env(n, 0.004, 0.001, 0.002)
    return tone * env + 0.35 * clk


def paste_pop(sample, n=int(0.12 * SR)):
    f = reg(sample, 83, "chord")   # B5 over Bm9
    t = tarr(n)
    lf = np.log2(f) + 0.5 * np.exp(-t / 0.004)   # quick drop into B5 (pop)
    s = np.sin(2 * np.pi * np.cumsum(2 ** lf) / SR) * perc_env(n, 0.03, 0.001, 0.01)
    nz = bp(rng.standard_normal(n), 600, 3000) * perc_env(n, 0.003, 0.0005, 0.002)
    return s + 0.4 * nz


# ----------------------------------------------------------- dynamics/fx --
def pump(kick_samples, n, depth_db=-6.0, rel=0.150, att=0.003):
    """sidechain gain: -6 dB duck on each kick (3 ms in), 150 ms raised-cosine release."""
    g = np.ones(n)
    d = 1 - 10 ** (depth_db / 20)
    L = int((att + rel) * SR)
    t = tarr(L)
    shape = np.where(t < att, t / att, 0.5 * (1 + np.cos(np.pi * np.clip((t - att) / rel, 0, 1))))
    for k in kick_samples:
        m = min(L, n - k)
        if m > 0:
            g[k:k + m] = np.minimum(g[k:k + m], 1 - d * shape[:m])
    return g


def sweep_lp(x, f_start, f_end, n_sweep, bank=8):
    """time-varying low-pass by crossfading a bank of zero-phase LP copies (log-spaced cutoffs)."""
    cuts = np.geomspace(f_start, f_end, bank)
    ys = [signal.sosfiltfilt(signal.butter(2, c, "lowpass", fs=SR, output="sos"), x, axis=0) for c in cuts]
    pos = np.full(x.shape[0], bank - 1.0)
    pos[:n_sweep] = np.linspace(0, 1, n_sweep) ** 1.6 * (bank - 1)
    out = np.zeros_like(x)
    for i in range(bank):
        w = np.clip(1 - np.abs(pos - i), 0, 1)
        out += ys[i] * w[:, None]
    return out


def gate(n, segments, ramp=int(0.002 * SR)):
    """1 inside [a, b) segments, 0 elsewhere, with short ramps that finish at the boundary edges."""
    g = np.zeros(n)
    for a, b in segments:
        a, b = max(0, a), min(n, b)
        g[a:b] = ramps(b - a, ramp, ramp)
    return g


def bass_line(events, n, glide_s=0.05, drive=2.0):
    """808 sine bass. events = [(start, end, midi, legato)], legato notes glide from the previous pitch."""
    lf = np.full(n, np.nan)
    amp = np.zeros(n)
    prev = None
    G = int(glide_s * SR)
    for s, e, m, leg in events:
        f = reg(s, m, "bass")
        lf[s:e] = np.log2(f)
        if leg and prev is not None:
            g = min(G, e - s)
            lf[s:s + g] = np.linspace(prev, np.log2(f), g)
        prev = np.log2(f)
        L = e - s
        env = np.exp(-tarr(L) / 0.9) * 0.4 + 0.6
        env *= ramps(L, 1 if leg else int(0.003 * SR), int(0.006 * SR))
        if leg:
            env[:int(0.006 * SR)] = 1.0 * env[int(0.006 * SR)]
        amp[s:e] = np.maximum(amp[s:e], env)
    # hold pitch between notes (no jumps when silent)
    idx = np.where(np.isnan(lf), 0, np.arange(n))
    np.maximum.accumulate(idx, out=idx)
    lf = lf[idx]
    lf = np.where(np.isnan(lf), np.log2(55.0), lf)
    amp = signal.sosfiltfilt(signal.butter(1, 400, "lowpass", fs=SR, output="sos"), amp)  # de-click legato joins
    ph = 2 * np.pi * np.cumsum(2 ** lf) / SR
    s = np.tanh(drive * np.sin(ph)) / np.tanh(drive)
    return lp(s * amp, 900, 2)


def bl_saw_table(f, size=4096, top=17000.0):
    H = max(1, int(top // f))
    ph = np.arange(size) / size
    k = np.arange(1, H + 1)
    tab = (np.sin(2 * np.pi * np.outer(ph, k)) / k).sum(axis=1) * (2 / np.pi)
    return np.append(tab, tab[0])


def wt_saw(f, n, phase0=0.0, size=4096):
    tab = bl_saw_table(f, size)
    ph = (phase0 + f * np.arange(n) / SR) % 1.0
    p = ph * size
    i = p.astype(np.int64)
    fr_ = p - i
    return tab[i] * (1 - fr_) + tab[i + 1] * fr_


def polyblep_saw(f, n, phase0=0.0):
    dt = f / SR
    ph = (phase0 + dt * np.arange(n)) % 1.0
    s = 2 * ph - 1
    m = ph < dt
    u = ph[m] / dt
    s[m] -= u + u - u * u - 1
    m = ph > 1 - dt
    u = (ph[m] - 1) / dt
    s[m] -= u * u + u + u + 1
    return s


def kicks_list():
    """beat-section kicks on 1 and 3 from frame 60 to 525 (drop-out)."""
    return [fr(60) + b * BEAT for b in range(0, 31, 2)]   # beats 0..30 even -> frames 60..510


TICK_FRAMES = [b + o for b in (120, 180, 240, 300) for o in (15, 52.5)]   # beat 2 and '&' of 4
STUTTER_FRAMES = [180, 240, 300]
# ------------------------------------------------------------- end common --

import time
T0 = time.time()

DET = [-0.17, -0.08, 0.0, 0.08, 0.17]   # semitones
PANS = [-0.8, -0.4, 0.0, 0.4, 0.8]


def wsaw_chord(chord, n, s0, att=0.004, rel=0.01):
    out = np.zeros((n, 2))
    for m in VOICING[chord]:
        f = reg(s0, m)
        for d, p in zip(DET, PANS):
            add(out, 0, wt_saw(f * 2 ** (d / 12), n, rng.random()), pan=p, gain=1 / 5)
    out = hp(lp(out, 8500, 2), 200, 2)
    return out * ramps(n, int(att * SR), int(rel * SR))[:, None]


def square_table_osc(f, n, top=16000.0):
    H = np.arange(1, int(top // f) + 1, 2)
    ph = np.arange(2048) / 2048
    tab = (np.sin(2 * np.pi * np.outer(ph, H)) / H).sum(axis=1)
    tab = np.append(tab, tab[0])
    p = ((rng.random() + f * np.arange(n) / SR) % 1.0) * 2048
    i = p.astype(np.int64)
    return tab[i] * (1 - (p - i)) + tab[i + 1] * (p - i)


HAT_N = int(0.25 * SR)
METAL = sum(square_table_osc(f, HAT_N) for f in (205.3, 304.4, 369.6, 522.7, 540.0, 800.0))
METAL = bp(METAL, 7000, 11500, 3)
METAL /= np.abs(METAL).max()


def metal_hat(dec):
    return METAL * perc_env(HAT_N, dec, 0.001, 0.005) + 0.3 * hat(dec, HAT_N, 8000)


# ------------------------------------------------------------ frame 0 hit --
hit = np.zeros((N, 2))
add(hit, 0, kick(f0=230, f1=50, dec=0.24, click=0.35), gain=1.0)
add(hit, 0, sub808(35, dur=1.6, dec=0.6, drive=2.5, sample=0), gain=0.75)
add(hit, 0, crash(dur=0.8, dec=0.14, fc=4500), gain=0.5)

# ---------------------------------------------------------- intro 0-60 --
IN_END = fr(60)
intro = np.zeros((IN_END + 4000, 2))
add(intro, fr(30), kick(f0=230, f1=50, dec=0.2), gain=0.9)
add(intro, fr(52.5), kick(f0=230, f1=50, dec=0.15), gain=0.6)
for f_ in (15, 45):
    add(intro, fr(f_), clap(), gain=0.45)
for i in range(16):
    add(intro, fr(i * 3.75), metal_hat(0.025 if i % 2 == 0 else 0.05), pan=-0.15, gain=0.09 if i % 2 else 0.06)
pad = wsaw_chord("Bm9", IN_END, 0, att=0.6, rel=0.05)
add(intro, 0, pad * np.linspace(0.3, 1, IN_END)[:, None], gain=0.2)
cut = np.full(intro.shape[0], 1.0)
intro = sweep_lp(intro, 800, 16000, IN_END, bank=10)
intro *= gate(intro.shape[0], [(0, IN_END)])[:, None]

typing = np.zeros((N, 2))
for i in range(1, 12):
    jit = int(rng.uniform(-0.004, 0.004) * SR)
    add(typing, fr(i * 3.75) + jit, type_click(), pan=rng.uniform(-0.4, 0.4), gain=rng.uniform(0.22, 0.42))
add(typing, fr(45), paste_pop(fr(45)), gain=0.9)
n_sw = IN_END - fr(37.5)                    # reverse-crash riser into the drop
rv = crash(dur=n_sw / SR, dec=0.25, fc=2500)[::-1]
rv *= ramps(n_sw, 200, 96)[:, None]
add(typing, fr(37.5), rv, gain=0.3)

# ------------------------------------------------------- beat 60-525 --
KICKS = kicks_list()
drums = np.zeros((N, 2))
for k in KICKS:
    add(drums, k, kick(f0=230, f1=50, dec=0.22, click=0.35), gain=1.0)
for b in range(1, 31, 2):
    add(drums, fr(60) + b * BEAT, clap(tail=0.12), pan=-0.05, gain=0.55)
for i in range(31 * 4):
    s = fr(60) + i * S16
    open_ = i % 4 == 2
    add(drums, s, metal_hat(0.11 if open_ else 0.025), pan=0.2,
        gain=0.11 if open_ else (0.09 if i % 2 else 0.06))
add(drums, fr(60), crash(dur=1.6, dec=0.5, fc=4500), gain=0.4)

sus = np.zeros((N, 2))
for a, b, c in TIMELINE[:4]:
    s0, s1 = max(fr(a), fr(60)), fr(b)
    add(sus, s0, wsaw_chord(c, s1 - s0 + int(0.02 * SR), s0, att=0.02, rel=0.02))
stab_env = np.zeros(N)
L = int(0.25 * BEAT * 2)          # one 8th
se = perc_env(L, 0.09, 0.002, 0.01)
for b in range(31):
    s = fr(60) + b * BEAT + BEAT // 2
    stab_env[s:s + L] = np.maximum(stab_env[s:s + L], se[: N - s])
chords = sus * (0.3 + 1.1 * stab_env)[:, None]
chords *= pump(KICKS, N)[:, None]
for S in STUTTER_FRAMES:
    s = fr(S)
    chords *= (1 - gate(N, [(s, s + 4 * S32)]))[:, None]
    snip = wsaw_chord(chord_at(s), S32, s, att=0.0015, rel=0.006)
    snip *= np.exp(-tarr(S32) / 0.05)[:, None]
    for r in range(4):
        add(chords, s + r * S32, snip, gain=1.2)

ev = []
for bar in range(8):
    s = fr(60) + bar * BAR
    c = chord_at(s)
    R, F5 = ROOT[c], FIFTH[c]
    for (b0, b1, m, leg) in [(0, 0.75, R, bar > 0), (0.75, 1.5, R + 12, True), (1.5, 2.5, R, True),
                             (2.5, 3.0, F5, False), (3.0, 4.0, R + 12, True)]:
        a_, e_ = s + int(b0 * BEAT), min(s + int(b1 * BEAT), fr(525))
        if a_ < e_:
            ev.append((a_, e_, m, leg))
bass = bass_line(ev, N, glide_s=0.08, drive=3.0)[:, None] * np.ones((1, 2))
bass *= pump(KICKS, N, depth_db=-5.0, rel=0.12)[:, None]

fx = np.zeros((N, 2))
for f_ in TICK_FRAMES:
    add(fx, fr(f_), metric_tick(fr(f_)), pan=-0.35 if f_ % 15 else 0.35, gain=0.45)
add(fx, fr(450), launch_chirp(fr(450)), gain=0.45)

beat = drums + 0.85 * chords + 0.5 * bass + fx
beat *= gate(N, [(fr(60) - int(0.002 * SR), fr(525))])[:, None]

# ------------------------------------------------- end card hit 540 --
end = np.zeros((N, 2))
E0 = fr(540)
add(end, E0, kick(f0=230, f1=50, dec=0.3, click=0.35), gain=1.0)
add(end, E0, sub808(35, dur=2.0, dec=0.55, drive=2.5, sample=E0), gain=0.75)
add(end, E0, crash(dur=2.0, dec=0.55, fc=4500), gain=0.45)
stab = wsaw_chord("Bm(add9)", N - E0, E0, att=0.004, rel=0.05)
stab = lp(stab, 6000, 2) * np.exp(-tarr(N - E0) / 0.45)[:, None]
add(end, E0, stab, gain=0.6)

x = hit + typing + beat + end
x[:intro.shape[0]] += intro
check_harmony()
y = master(x, target_lufs=-14.0, fade_out_s=1.0)
print(f"lufs {lufs(y):.2f}  tp {true_peak_db(y):.2f}  runtime {time.time() - T0:.1f}s")
write_wav(sys.argv[1], y, N)
