"""--- 14. Motion-graphics arp bed with glide drop-out (id: motion-graphics-glide-dropout-25s, category: risers, 25.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 1,200,000 samples (25.0 s at 30 fps = 750 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 25-second bright motion-graphics bed in C major at 120 BPM (1 beat = 15 frames). Frames 0-60: intro of descending sine blips (C7, G6, E6, C6 on frames 18, 30, 42, 54) with tiny pitch slides, like UI elements landing. Frame 60: full bed: driving 1/8 sine-square arpeggio on Cmaj7 → Am9 → Fmaj7 → G6 (2 beats each), round kick on every beat, soft sub, clap on 2 and 4. Frames 450-525: a pure sine glide rises smoothly from C5 (523 Hz) to C7 (2093 Hz) on an exponential curve while the kick fades out. Frames 525-540: total silence (half a bar). Frame 540: hit and groove returns. Frame 660: switch to an outro: no drums, a gentle tremolo pad on Cmaj9 and sparse high chimes (C7, E7, G7) every half bar; fade to 0 by frame 750. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 1 approach: sine + polyBLEP-square blend for the 1/8 arpeggio (straight 'up' pattern through the four chord tones of
each 2-beat chord, ping-pong panned), round sine-sweep kick, soft sine sub on the chord roots (8th-note pulse), clap from
three band-passed noise bursts plus a short tail, exponential pure-sine glide C5 -> C7 with the kick and sub fading
to zero, a noise crash + chord stab hit at frame 540, and an additive detuned-sine Cmaj9 pad with 5.5 Hz tremolo plus
additive-partial chimes for the outro. The 525-540 gap is gated to digital silence (mask re-applied after master).
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


APPROACH = """sine + polyBLEP-square blend for the 1/8 arpeggio (straight 'up' pattern through the four chord tones of
each 2-beat chord, ping-pong panned), round sine-sweep kick, soft sine sub on the chord roots (8th-note pulse), clap from
three band-passed noise bursts plus a short tail, exponential pure-sine glide C5 -> C7 with the kick and sub fading
to zero, a noise crash + chord stab hit at frame 540, and an additive detuned-sine Cmaj9 pad with 5.5 Hz tremolo plus
additive-partial chimes for the outro. The 525-540 gap is gated to digital silence (mask re-applied after master)."""

SEED = 55
G_ARP, G_SUB, G_CLAP, G_KICK = 0.75, 0.08, 0.8, 0.5
rng = np.random.default_rng(SEED)
N = 1200000
SPF = 1600
BEAT = 24000            # 120 BPM
E8 = BEAT // 2


def F(fr):
    return int(round(fr * SPF))


CH = {"C": {0, 4, 7}, "Cmaj7": {0, 4, 7, 11}, "Am9": {9, 0, 4, 7, 11}, "Fmaj7": {5, 9, 0, 4},
      "G6": {7, 11, 2, 4}, "Cmaj9": {0, 4, 7, 11, 2}}
CYCLE = ["Cmaj7", "Am9", "Fmaj7", "G6"]
ARP = {"Cmaj7": [72, 76, 79, 83], "Am9": [69, 72, 76, 83], "Fmaj7": [69, 72, 76, 77], "G6": [71, 74, 76, 79]}
ROOT = {"Cmaj7": 36, "Am9": 33, "Fmaj7": 29, "G6": 31}
notes = []

drums = np.zeros((N, 2))
kickb = np.zeros((N, 2))
music = np.zeros((N, 2))
send = np.zeros((N, 2))
glide = np.zeros((N, 2))
outro = np.zeros((N, 2))

# ----------------------------------------------------------------- intro blips
for fr, m, pn in [(18, 96, 0.35), (30, 91, -0.35), (42, 88, 0.2), (54, 84, -0.2)]:
    n = int(0.16 * SR)
    t = tt(n)
    semis = m + 0.6 * np.exp(-t / 0.012)          # tiny downward slide onto the note ("landing")
    s = osc_sine(m2f(semis)) * exp_env(n, 0.05, 0.002, 0.02)
    add(music, F(fr), s, pn, 0.35)
    add(send, F(fr), s, pn, 0.3)
    notes.append((F(fr) / SR, m, "C"))


# ----------------------------------------------------------------- bed
def kick(n=int(0.35 * SR)):
    t = tt(n)
    f = 52.0 + 90.0 * np.exp(-t / 0.04)
    s = osc_sine(f) * exp_env(n, 0.14, 0.0015, 0.02)
    s += 0.08 * sos_f(sos_f(rng.standard_normal(n), "bandpass", [1000, 4000]) * exp_env(n, 0.002, 0.001, 0.002),
                      "lowpass", 7000)
    return s


KICK = kick()


def clap():
    n = int(0.25 * SR)
    t = tt(n)
    nz = sos_f(rng.standard_normal(n), "bandpass", [900, 3200], 2)
    env = np.zeros(n)
    for k, d in enumerate([0.0, 0.009, 0.019]):
        i0 = int(d * SR)
        env[i0:] += np.exp(-(t[: n - i0]) / (0.005 if k < 2 else 0.06))
    return nz * edges(env, 0.0008, 0.02)


CLAPS = [clap() for _ in range(3)]


def arp_note(m, gain, pan, start):
    n = int(E8 * 0.9)
    f = float(m2f(m))
    s = 0.65 * osc_sine(f, n) + 0.35 * sos_f(blsquare(f, n), "lowpass", 9000, 2) * 0.6
    s *= exp_env(n, 0.12, 0.002, 0.01)
    add(music, start, s, pan, gain)
    add(send, start, s, pan, gain * 0.5)


def bed(s0, s1, kick_fade=None):
    nb = (s1 - s0) // BEAT
    for k in range(nb + 1):
        sb = s0 + k * BEAT
        if sb >= s1 - 2000:
            break
        chord = CYCLE[(k // 2) % 4]
        add(kickb, sb, KICK, 0.0, G_KICK)
        if k % 2 == 1:
            add(drums, sb, CLAPS[k % 3], 0.05, G_CLAP)
            add(send, sb, CLAPS[k % 3], 0.0, 0.2)
        for e in range(2):
            st = sb + e * E8
            idx = (k % 2) * 2 + e
            m = ARP[chord][idx]
            arp_note(m, G_ARP,-0.4 if idx % 2 == 0 else 0.4, st)
            notes.append((st / SR, m, chord))
            # soft sub on chord roots, 8th pulse
            n = int(E8 * 0.85)
            sub = osc_sine(m2f(ROOT[chord]), n) * edges(np.exp(-tt(n) / 0.25), 0.006, 0.02)
            add(subb, st, sub, 0.0, G_SUB)
            notes.append((st / SR, ROOT[chord], chord))


subb = np.zeros((N, 2))
bed(F(60), F(525))
bed(F(540), F(660))

# kick + sub fade 450 -> 525
fade = np.ones(N)
a, b = F(450), F(525)
fade[a:b] = np.cos(np.linspace(0, np.pi / 2, b - a)) ** 2
fade[b:F(540)] = 0.0
fade *= gate_mask(N, [(0, F(660))], 0.012)          # outro: no drums from 660
kickb *= fade[:, None]
subb *= fade[:, None]
drums *= gate_mask(N, [(0, F(660))], 0.012)[:, None]

# glide C5 -> C7, exponential, 450 -> 525
n = b - a
t = tt(n)
fg = 523.25 * 4 ** (t / t[-1])
g = osc_sine(fg) * edges(np.linspace(0.35, 1.0, n) ** 1.5, 0.02, 0.003)
glide[a:b] += pan2(g, 0.0) * 0.4

# frame 540 hit
h0 = F(540)
n = int(1.4 * SR)
t = tt(n)
crash = sos_f(sos_f(rng.standard_normal((n, 2)), "highpass", 3500, 2), "lowpass", 13000, 2) \
    * exp_env(n, 0.45, 0.002, 0.05)[:, None]
add(drums, h0, crash, gain=0.12)
for m, pn in zip([48, 60, 64, 67, 71, 76], [0, -0.5, 0.5, -0.3, 0.3, 0]):
    nn = int(0.9 * SR)
    s = sos_f(blsaw(m2f(m), nn), "lowpass", 5000, 2) * exp_env(nn, 0.3, 0.002, 0.05)
    add(music, h0, s, pn, 0.18)
    add(send, h0, s, pn, 0.15)
    notes.append((h0 / SR, m, "Cmaj7"))

# ----------------------------------------------------------------- outro 660 -> 750
o0 = F(660)
no = N - o0
t = tt(no)
pad = np.zeros((no, 2))
for j, m in enumerate([48, 55, 59, 62, 64, 67]):
    f0 = float(m2f(m))
    for d, pn in [(-0.07, -0.6), (0.07, 0.6)]:
        ff = f0 * 2 ** (d / 12)
        for h in range(1, 5):
            pad += pan2(np.sin(2 * np.pi * h * ff * t + rng.uniform(0, 6.28)) / h ** 2, pn)
    notes.append((o0 / SR, m, "Cmaj9"))
trem = 1 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.5 * t))
penv = np.minimum(1, t / 0.25) * np.cos(np.linspace(0, np.pi / 2, no)) ** 1.2
add(outro, o0, pad * (trem * penv)[:, None] * 0.12)
for i, (fr, m) in enumerate([(660, 96), (690, 100), (720, 103)]):
    nn = int(1.2 * SR)
    tc = tt(nn)
    f0 = float(m2f(m))
    s = np.zeros(nn)
    for r, gg, tau in [(1.0, 1.0, 0.6), (2.0, 0.35, 0.25), (3.0, 0.15, 0.12), (4.07, 0.08, 0.06)]:
        if f0 * r < 18000:
            s += gg * np.sin(2 * np.pi * f0 * r * tc) * np.exp(-tc / tau)
    s *= edges(np.ones(nn), 0.001, 0.05)
    pn = [-0.4, 0.4, 0.0][i]
    add(outro, F(fr), s, pn, 0.2)
    add(send, F(fr), s, pn, 0.2)
    notes.append((F(fr) / SR, m, "Cmaj9"))

wet = reverb(send, rng, 1.6, 0.9, 7000, pre_ms=15)
def hole_mask(n_total, a, b, ramp_s=0.002):
    """0 on [a, b) exactly (true digital silence), cosine ramps placed OUTSIDE the hole."""
    g = np.ones(n_total)
    r = int(ramp_s * SR)
    dn = np.cos(np.linspace(0, np.pi / 2, r)) ** 2
    g[a - r:a] = dn
    g[a:b] = 0.0
    g[b:b + r] = dn[::-1]
    return g


silence = hole_mask(N, F(525), F(540), 0.002)
x = (drums + kickb + subb + music + glide + 0.35 * wet) * silence[:, None] + outro
# outro fade already in the pad envelope; make sure everything after 660 also fades
x[o0:] *= np.cos(np.linspace(0, np.pi / 2, no))[:, None] ** 0.5
print("harmony notes checked:", check_harmony(notes, CH))
y = master(x, target_lufs=-14.0, fade_out_s=0.2)
y *= silence[:, None]
write_wav(sys.argv[1], y, N)
