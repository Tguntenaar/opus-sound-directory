"""--- 11. Kinetic typography 128 BPM bed (id: kinetic-type-128-bed-30s, category: ad-beds, 30.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 1,440,000 samples (30.0 s at 30 fps = 900 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 30-second kinetic-typography bed in F# minor at 128 BPM (1 beat = 14.0625 frames; place every event on round(beat*14.0625)). Frames 0-99 (bars 1-2): sparse dry hits on word reveals: a woody block click on frames 9, 30, 56, a short sub hit + paper-flap noise on frame 84. Frame 99 (beat 7): a paper TEAR (bandpassed noise with 30-60 Hz granular crackle, centroid sweeping 1→6 kHz over 0.35 s) into the drop. Frames 113-480: four-on-the-floor with a heavy sub kick (low end ~35% of energy), off-beat hats, a plucked F#m7 → Dmaj7 → Bm9 → C#7sus stab pattern sidechained to the kick (−5 dB), and bright square 'type-on' blips on 16ths during letter reveals; on each 3D-letter tumble (frames 169, 281, 394) a tom-like pitch-dropping hit. Frames 480-500: 1-beat stop. Frames 500-830: second half, add a rising acid-ish saw arp and a concentric-circle ripple (FM ping with 4 echoes at 1/16) every 2 bars. Frame 838: hard stop; frames 838-900: end card: a bouncing dot = 5 rubbery sine boinks (F#5, intervals shrinking 0.3, 0.2, 0.14, 0.1, 0.07 s, falling 3 semitones) over a held F#m(add9) pad that fades to 0. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 3 approach: Karplus-Strong plucked stabs (lfilter comb with a damped averaging loop) on a 3-3-2 dotted pattern;
sine kick with a short 1.5 kHz tone-burst click and a separate sub tail; closed/open noise hats with 16th ghost hats;
additive odd-harmonic square type-on blips (band-limited by construction); a 303-style acid line built from a
polyBLEP saw with per-step slides (portamento between chord tones), accents and an FFT-domain 24 dB resonant low-pass
per step whose cutoff rises across the second half while the line climbs an octave per 2-bar phrase; FM ripple at
ratio 4 with echoes that widen and get wetter; granular tear (band-passed micro-grains whose centre sweeps 1 -> 6 kHz
plus 30-60 Hz crackle grains); end-card pad of detuned polyBLEP saws low-passed. Boinks fall A5 -> F#5 as in take 1.
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


# ------------------------------------------------------------ synth helpers --
from scipy.signal import fftconvolve


def m2f(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def tt(n):
    return np.arange(n) / SR


def edges(env, a_s=0.002, r_s=0.003):
    """Force a linear attack ramp and a cosine release ramp onto an envelope (anti-click)."""
    n = len(env)
    na, nr = max(1, int(a_s * SR)), max(1, int(r_s * SR))
    na, nr = min(na, n // 2), min(nr, n // 2)
    env = env.copy()
    env[:na] *= np.linspace(0, 1, na)
    env[n - nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return env


def exp_env(n, tau, a_s=0.002, r_s=0.004):
    return edges(np.exp(-tt(n) / tau), a_s, r_s)


def _blep(p, dt):
    y = np.zeros_like(p)
    m = p < dt
    t = p[m] / dt[m]
    y[m] = t + t - t * t - 1.0
    m = p > 1.0 - dt
    t = (p[m] - 1.0) / dt[m]
    y[m] = t * t + t + t + 1.0
    return y


def blsaw(f, n=None, ph0=0.0):
    """polyBLEP saw, f scalar (with n) or per-sample array."""
    f = np.full(n, float(f)) if n is not None else np.asarray(f, dtype=float)
    dt = f / SR
    p = (ph0 + np.cumsum(dt)) % 1.0
    return 2 * p - 1 - _blep(p, dt)


def blsquare(f, n=None, ph0=0.0, pw=0.5):
    f = np.full(n, float(f)) if n is not None else np.asarray(f, dtype=float)
    dt = f / SR
    p = (ph0 + np.cumsum(dt)) % 1.0
    p2 = (p + pw) % 1.0
    return (2 * p - 1 - _blep(p, dt)) - (2 * p2 - 1 - _blep(p2, dt))


def osc_sine(f, n=None, ph0=0.0):
    f = np.full(n, float(f)) if n is not None else np.asarray(f, dtype=float)
    return np.sin(ph0 + 2 * np.pi * np.cumsum(f) / SR)


def pan2(sig, pan=0.0):
    """equal-power pan, pan in [-1, 1] (mono -> (n,2))."""
    a = (pan + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], axis=1)


def add(buf, start, sig, pan=0.0, gain=1.0):
    start = int(start)
    s = pan2(sig, pan) if sig.ndim == 1 else sig
    if start < 0:
        s, start = s[-start:], 0
    n = min(len(s), buf.shape[0] - start)
    if n > 0:
        buf[start:start + n] += gain * s[:n]


def sos_f(x, kind, f, order=2):
    sos = signal.butter(order, f, kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def rbj_lp(x, fc, q):
    w0 = 2 * np.pi * min(fc, 0.45 * SR) / SR
    al, cs = np.sin(w0) / (2 * q), np.cos(w0)
    b = np.array([(1 - cs) / 2, 1 - cs, (1 - cs) / 2])
    a = np.array([1 + al, -2 * cs, 1 - al])
    return signal.lfilter(b / a[0], a / a[0], x, axis=0)


def reverb(x, rng, dur=1.2, rt=0.5, lp=6000.0, pre_ms=12.0):
    """Stereo convolution reverb from decorrelated exponentially-decaying filtered noise."""
    n = int(dur * SR)
    t = tt(n)
    env = np.exp(-6.9 * t / rt)
    ir = rng.standard_normal((n, 2)) * env[:, None]
    ir = sos_f(ir, "lowpass", lp, 2)
    ir[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))[:, None]
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True))
    pre = int(pre_ms * 1e-3 * SR)
    out = np.zeros_like(x)
    for c in range(2):
        y = fftconvolve(x[:, c] if x.ndim == 2 else x, ir[:, c])[: x.shape[0]]
        out[pre:, c] = y[: x.shape[0] - pre]
    return out


def gate_mask(n_total, segs, ramp_s=0.002):
    """1 inside [a, b) sample segments, 0 outside, with short cosine ramps (inside the segment)."""
    g = np.zeros(n_total)
    r = max(2, int(ramp_s * SR))
    up = np.sin(np.linspace(0, np.pi / 2, r)) ** 2
    for a, b in segs:
        a, b = int(a), int(b)
        g[a:b] = 1.0
        g[a:a + r] = up
        g[b - r:b] = up[::-1]
    return g


def sidechain(n_total, starts, depth_db=-5.0, rec_s=0.14, att_s=0.004):
    """Gain curve dipping to depth_db at every trigger, exponential recovery."""
    d = 1 - 10 ** (depth_db / 20)
    L = int(rec_s * 5 * SR)
    t = tt(L)
    curve = 1 - d * np.exp(-t / rec_s)
    na = int(att_s * SR)
    curve[:na] = 1 - d * np.linspace(0, 1, na)
    g = np.ones(n_total)
    for s in starts:
        s = int(s)
        n = min(L, n_total - s)
        if n > 0:
            g[s:s + n] = np.minimum(g[s:s + n], curve[:n])
    return g


def check_harmony(notes, chords):
    """notes: list of (time_s, midi, chord_name); assert every pitch class is in its chord."""
    for (ts, m, ch) in notes:
        pc = int(round(m)) % 12
        assert pc in chords[ch], f"note {m} (pc {pc}) at {ts:.3f}s not in {ch} {sorted(chords[ch])}"
    return len(notes)
# -------------------------------------------------------- end synth helpers --


APPROACH = """Karplus-Strong plucked stabs (lfilter comb with a damped averaging loop) on a 3-3-2 dotted pattern;
sine kick with a short 1.5 kHz tone-burst click and a separate sub tail; closed/open noise hats with 16th ghost hats;
additive odd-harmonic square type-on blips (band-limited by construction); a 303-style acid line built from a
polyBLEP saw with per-step slides (portamento between chord tones), accents and an FFT-domain 24 dB resonant low-pass
per step whose cutoff rises across the second half while the line climbs an octave per 2-bar phrase; FM ripple at
ratio 4 with echoes that widen and get wetter; granular tear (band-passed micro-grains whose centre sweeps 1 -> 6 kHz
plus 30-60 Hz crackle grains); end-card pad of detuned polyBLEP saws low-passed. Boinks fall A5 -> F#5 as in take 1."""

SEED = 57
G_MUS = 5.6
G_HAT = 0.22
rng = np.random.default_rng(SEED)
N = 1440000
SPF = 1600
BEAT = 22500
S16 = BEAT // 4


def F(fr):
    return int(round(fr * SPF))


CH = {
    "F#m": {6, 9, 1},
    "F#m7": {6, 9, 1, 4},
    "Dmaj7": {2, 6, 9, 1},
    "Bm9": {11, 2, 6, 9, 1},
    "C#7sus": {1, 6, 8, 11},
    "F#m(add9)": {6, 9, 1, 8},
}
CYCLE = ["F#m7", "Dmaj7", "Bm9", "C#7sus"]
VOICE = {"F#m7": [52, 57, 61, 66], "Dmaj7": [50, 57, 61, 66],
         "Bm9": [50, 57, 61, 59 + 12], "C#7sus": [49, 56, 59, 66]}
notes = []

drums = np.zeros((N, 2))
music = np.zeros((N, 2))
send = np.zeros((N, 2))
intro = np.zeros((N, 2))
endc = np.zeros((N, 2))


def kick(n=int(0.4 * SR)):
    t = tt(n)
    body = osc_sine(50.0 + 110.0 * np.exp(-t / 0.028)) * exp_env(n, 0.11, 0.001, 0.01)
    tail = osc_sine(46.25, n) * edges(np.exp(-t / 0.2) * (1 - np.exp(-t / 0.02)), 0.003, 0.02)
    click = osc_sine(1500.0, n) * exp_env(n, 0.0018, 0.0004, 0.002)
    return body + 0.2 * tail + 0.18 * click


KICK = kick()


def noise_hat(dur, tau, lo):
    n = int(dur * SR)
    x = sos_f(rng.standard_normal(n), "highpass", lo, 4)
    x = sos_f(x, "lowpass", 16000, 2)
    return x * exp_env(n, tau, 0.0008, 0.006)


def ks(m, dur=0.35, damp=0.5, bright=0.25):
    n = int(dur * SR)
    f0 = float(m2f(m))
    D = SR / f0
    Di = int(np.floor(D - 0.5))
    frac = D - 0.5 - Di
    exc = sos_f(rng.uniform(-1, 1, Di + 1), "lowpass", 2000 + 8000 * bright, 1)
    x = np.zeros(n)
    x[: len(exc)] = exc
    g = 0.996 - 0.01 * damp
    # y[n] = x[n] + g * ((1-frac)*y[n-Di] + frac*y[n-Di-1]) averaged with y[n-Di-1] (loop low-pass)
    a = np.zeros(Di + 3)
    a[0] = 1.0
    a[Di] -= g * 0.5 * (1 - frac)
    a[Di + 1] -= g * 0.5
    a[Di + 2] -= g * 0.5 * frac
    y = signal.lfilter([1.0], a, x)
    return y / (np.abs(y).max() + 1e-9) * exp_env(n, 0.16, 0.001, 0.03)


PL = {}


def stab(start, chord, gain):
    for i, m in enumerate(VOICE[chord]):
        if m not in PL:
            PL[m] = ks(m)
        pn = [-0.4, 0.4, -0.15, 0.15][i]
        add(music, start, PL[m], pn, gain)
        add(send, start, PL[m], pn, gain * 0.5)
        notes.append((start / SR, m, chord))


def blip(start, m, chord, gain=0.09):
    n = int(0.05 * SR)
    t = tt(n)
    f0 = float(m2f(m))
    s = np.zeros(n)
    for h in range(1, 40, 2):
        if h * f0 > 14000:
            break
        s += np.sin(2 * np.pi * h * f0 * t) / h
    s *= exp_env(n, 0.02, 0.0015, 0.008)
    p = rng.uniform(-0.5, 0.5)
    add(music, start, s, p, gain)
    add(send, start, s, p, gain * 0.5)
    notes.append((start / SR, m, chord))


def tom(start, pan):
    n = int(0.5 * SR)
    t = tt(n)
    f = 70.0 + 220.0 * np.exp(-t / 0.05)
    s = osc_sine(f) * exp_env(n, 0.18, 0.001, 0.02) + 0.4 * osc_sine(f * 2.3) * exp_env(n, 0.04, 0.001, 0.02)
    s += 0.2 * noise_hat(0.5, 0.015, 600)
    add(drums, start, s, pan, 0.55)
    add(send, start, s, pan, 0.25)


def chord_tones(chord, lo, hi):
    return [m for m in range(lo, hi + 1) if m % 12 in CH[chord]]


# ------------------------------------------------------------- intro
def woodblock(start, pan):
    n = int(0.1 * SR)
    t = tt(n)
    m = 81
    f0 = float(m2f(m))
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t / 0.03) * (1 + 0.6 * np.exp(-t / 0.004))
    s += 0.35 * np.sin(2 * np.pi * 3.9 * f0 * t) * np.exp(-t / 0.006)
    s = np.tanh(1.6 * s)
    add(intro, start, s * edges(np.ones(n), 0.0006, 0.01), pan, 0.8)
    notes.append((start / SR, m, "F#m"))


for fr, pn in [(9, 0.3), (30, -0.3), (56, 0.0)]:
    woodblock(F(fr), pn)
n = int(0.3 * SR)
t = tt(n)
sub = osc_sine(46.25 + 40 * np.exp(-t / 0.015)) * exp_env(n, 0.1, 0.002, 0.02)
add(intro, F(84), sub, 0.0, 0.9)
notes.append((F(84) / SR, 30, "F#m"))
n = int(0.18 * SR)
t = tt(n)
fl = np.zeros(n)
for k in range(5):                              # paper flap = a few quick flutter bursts
    s0 = int(k * 0.03 * SR)
    ln = int(0.025 * SR)
    seg = sos_f(rng.standard_normal(ln), "bandpass", [600 + 200 * k, 3000 + 300 * k]) * np.hanning(ln)
    fl[s0:s0 + ln] += seg * 0.8 ** k
add(intro, F(84), fl, 0.15, 0.8)

# granular tear
n = int(0.35 * SR)
tear = np.zeros(n)
pos = 0
while pos < n - 300:
    gl = int(rng.uniform(0.001, 0.004) * SR)
    gl = min(gl, n - pos)
    c = 1000 * 6 ** (pos / n)
    g = sos_f(rng.standard_normal(gl + 64), "bandpass", [c / 1.3, min(c * 1.3, 20000)], 2)[64:]
    tear[pos:pos + gl] += g * np.hanning(gl) * rng.uniform(0.3, 1.0)
    pos += int(rng.uniform(0.0006, 0.002) * SR)
cr = np.zeros(n)
pos = 0
while pos < n:
    gl = min(int(0.003 * SR), n - pos)
    c = 1000 * 6 ** (pos / n)                   # crackle grains follow the sweeping centre too
    cr[pos:pos + gl] += sos_f(rng.standard_normal(gl + 64), "bandpass", [c / 1.6, min(c * 1.6, 20000)])[64:] * np.hanning(gl)
    pos += int(SR / rng.uniform(30, 60))
tear = (tear / np.abs(tear).max() + 0.8 * cr / np.abs(cr).max()) * edges(np.linspace(0.5, 1, n), 0.006, 0.02)
tear_st = np.stack([tear, np.roll(tear, 31)], axis=1)
add(intro, F(99), tear_st, gain=1.3)

# ------------------------------------------------------------------ grooves
A0, A1 = F(113), F(480)
B0, B1 = F(500), F(838)
kicks = []


def lp24_fft(x, fc, q):
    nf = 1 << int(np.ceil(np.log2(len(x) * 2)))
    X = np.fft.rfft(x, nf)
    f = np.fft.rfftfreq(nf, 1 / SR)
    r = f / fc
    H = 1.0 / ((1 - r ** 2) ** 2 / 1.0 + (r / q) ** 2) ** 1.0
    H = np.minimum(H, q ** 2) / q
    y = np.fft.irfft(X * H, nf)[: len(x)]
    return y


def acid_step(m_prev, m, nn, slide, accent, cut):
    t = tt(nn)
    if slide:
        mm = m + (m_prev - m) * np.exp(-t / 0.02)
    else:
        mm = np.full(nn, float(m))
    saw = blsaw(m2f(mm))
    y = lp24_fft(saw, cut * (1.6 if accent else 1.0), 3.5)
    env = np.exp(-t / (0.09 if accent else 0.05))
    y = np.tanh(2.0 * y * (0.4 + 0.6 * env))
    return y * edges(np.ones(nn), 0.002 if not slide else 0.004, 0.006)


def ripple(st, chord):
    m = {"F#m7": 85, "Bm9": 85, "Dmaj7": 85, "C#7sus": 85}[chord]
    n = int(0.5 * SR)
    t = tt(n)
    fc = float(m2f(m))
    idx = 1.4 * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * fc * t + idx * np.sin(2 * np.pi * 4 * fc * t)) * exp_env(n, 0.14, 0.002, 0.05)
    for e in range(5):
        pn = 0.18 * e * (-1) ** e
        add(music, st + e * S16, s, pn, 0.11 * 0.58 ** e)
        add(send, st + e * S16, s, pn, 0.05 * (1 + 1.5 * e) * 0.58 ** e)
    notes.append((st / SR, m, chord))


def groove(s0, s1, part):
    nb = (s1 - s0) // BEAT + 1
    m_prev = 54
    for k in range(nb):
        sb = s0 + k * BEAT
        if sb + int(0.06 * SR) > s1:
            break
        add(drums, sb, KICK, 0.0, 1.0)
        kicks.append(sb)
        bar, beat = divmod(k, 4)
        chord = CYCLE[bar % 4]
        for b16 in range(4):
            pos = beat * 4 + b16
            st = sb + b16 * S16
            if st + 2000 > s1:
                continue
            if b16 == 2:
                h = noise_hat(0.22 if beat == 3 else 0.06, 0.07 if beat == 3 else 0.02, 6500)
                add(drums, st, h, 0.25, G_HAT)
            elif b16 in (1, 3):
                add(drums, st, noise_hat(0.04, 0.01, 9000), -0.35, G_HAT * 0.35)
            if pos in (0, 3, 6, 8, 11, 14):
                stab(st, chord, 0.26 if pos else 0.15)
            reveal = (part == "A" and bar % 2 == 0 and 4 <= pos < 12) or (part == "B" and bar % 4 == 3 and pos >= 8)
            if reveal:
                tones = chord_tones(chord, 78, 90)
                blip(st, tones[(pos - 4) % len(tones)], chord)
        if part == "B":
            prog = (sb - s0) / (s1 - s0)
            tones = chord_tones(chord, 42, 70)
            for b16 in range(4):
                st = sb + b16 * S16
                if st + S16 > s1:
                    continue
                step = (bar % 2) * 16 + beat * 4 + b16
                m = tones[min(step * len(tones) // 32 + (b16 % 2) * 1, len(tones) - 1)]  # climbs ~ an octave+ per phrase
                if b16 == 3 and beat % 2 == 1:
                    m = m + 12 if m + 12 <= 76 else m
                slide = (b16 == 1)
                accent = (b16 == 0 and beat % 2 == 0)
                nn = int(S16 * (1.0 if slide else 0.8))
                y = acid_step(m_prev, m, nn, slide, accent, 500 + 3500 * prog ** 1.3)
                add(music, st, y, -0.1 + 0.2 * (b16 % 2), 0.11)
                add(send, st, y, 0.0, 0.03)
                notes.append((st / SR, m, chord))
                m_prev = m
            if beat == 0 and bar % 2 == 0:
                ripple(sb, chord)


groove(A0, A1, "A")
groove(B0, B1, "B")
for fr, pn in [(169, 0.0), (281, -0.35), (394, 0.35)]:
    tom(F(fr), pn)

sc = sidechain(N, kicks, -5.0, 0.13)
music *= sc[:, None]
gate = gate_mask(N, [(A0, A1), (B0, B1)], 0.002)
groove_bus = (drums + G_MUS * music) * gate[:, None]
wet = reverb(send * gate[:, None], rng, 1.2, 0.6, 5000, pre_ms=8)
wet *= gate_mask(N, [(A0, B1)], 0.002)[:, None]

# ------------------------------------------------------------------ end card
E0 = F(838)
gaps = [0.3, 0.2, 0.14, 0.1, 0.07]
bt = E0 + np.concatenate([[0], np.cumsum(gaps[:4])]) * SR
for i, s0 in enumerate(bt):
    n = int((0.2 if i < 4 else 0.5) * SR)
    t = tt(n)
    semis = 78 + 3 * np.exp(-t / 0.03) - 0.25 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.04)
    s = osc_sine(m2f(semis))
    s = np.tanh(1.3 * s) / np.tanh(1.3)
    s = sos_f(s, "lowpass", 5000, 2) * exp_env(n, 0.065 if i < 4 else 0.15, 0.002, 0.02)
    add(endc, s0, s, 0.0, 0.42 * 0.76 ** i)
    notes.append((s0 / SR, 78, "F#m(add9)"))
    notes.append((s0 / SR, 81, "F#m(add9)"))
npad = N - E0
t = tt(npad)
pad = np.zeros((npad, 2))
for j, m in enumerate([42, 49, 57, 61, 68]):
    for d, pn in [(-0.1, -0.7), (0.1, 0.7)]:
        s = blsaw(m2f(m + d), npad, ph0=rng.uniform()) if m > 42 else osc_sine(m2f(m), npad) * 2
        pad += pan2(s, pn)
    notes.append((E0 / SR, m, "F#m(add9)"))
pad = sos_f(pad, "lowpass", 1400, 2)
penv = np.minimum(1, t / 0.2) * np.cos(np.linspace(0, np.pi / 2, npad)) ** 1.4
add(endc, E0, pad * penv[:, None] * 0.03)
endc += reverb(endc, rng, 1.0, 0.5, 6000) * 0.25

x = intro + groove_bus + 0.25 * G_MUS * wet + endc
print("harmony notes checked:", check_harmony(notes, CH))
y = master(x, target_lufs=-14.0, fade_out_s=0.15)
write_wav(sys.argv[1], y, N)
