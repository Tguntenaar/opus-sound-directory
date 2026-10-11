"""--- 1. Era-dial tick sweep → whoosh hit (id: explainer-era-dial-ticks, category: drops, 4.0 s) ---

Output: one WAV, 48 kHz / 16-bit / stereo, exactly 192,000 samples (4.0 s at 30 fps = 120 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 4-second timeline-dial transition in D minor at 120 BPM (1 beat = 15 frames) for a dark wireframe explainer. Frames 0-75: a mechanical dial ticks through 'eras': short bright clicks (2 ms noise burst through a 4.5 kHz resonant bandpass plus a 1 ms 2.2 kHz sine blip), starting at 4 ticks/s and accelerating exponentially to 28 ticks/s, each tick panned slightly further right then snapping left, with a faint pitched detent ring (D6, 30 ms decay) every 4th tick. Under it, a filtered noise whoosh rises from 300 Hz to 6 kHz bandpass centre over frames 30-75. Frame 75: ticks stop dead and a soft impact lands: sine sub thump on D1 dropping from 90 Hz to 45 Hz over 120 ms, a felt-mallet D minor add9 cluster (D4 F4 A4 E5) and a short reversed-noise tail. Frames 75-120: the cluster rings out with a gentle 1/8-note ping-pong delay (250 ms, 3 repeats, -6 dB each). Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 2 approach: glassier ticks (Q=22 two-pole resonator at 4.5 kHz) whose pan creeps right in finer steps over groups of 8 before snapping left, detent D6 with a D7 partial every 4th tick; whoosh = block-wise time-varying biquad bandpass (state carried across 5 ms blocks) with rising Q; felt mallet = modal bar partials (1, 2.76, 5.40) struck as a fast 15 ms upward strum; the reversed-noise tail sits AFTER the hit (a backwards-decay swell that cuts off 190 ms later); ping-pong repeats progressively darker.
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

# ----------------------------------------------------------------- helpers --
FPS = 30
SPF = SR // FPS  # 1600 samples per video frame
N = 192000
HIT = 75 * SPF  # frame 75 = sample 120000
D_MINOR = {2, 4, 5, 7, 9, 10, 0}  # D E F G A Bb C
DM_ADD9 = {2, 5, 9, 4}  # D F A E


def hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def assert_pcs(midis, pcs, what):
    for m in midis:
        assert int(round(m)) % 12 in pcs, (what, m)


def env_ar(n, a, r):
    """Unity envelope of length n with raised-cosine attack (a samples) and release to exactly 0 (r samples)."""
    e = np.ones(n)
    a, r = min(a, n // 2), min(r, n // 2)
    if a > 0:
        e[:a] = 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    if r > 0:
        e[n - r:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, r + 1) / r)
    return e


def place(buf, start, sig, gl=1.0, gr=1.0):
    """Mix a mono (n,) or stereo (n,2) signal into buf at sample `start` (clipped to the buffer)."""
    n = sig.shape[0]
    s0, s1 = max(0, start), min(buf.shape[0], start + n)
    if s1 <= s0:
        return
    seg = sig[s0 - start:s1 - start]
    if seg.ndim == 1:
        buf[s0:s1, 0] += gl * seg
        buf[s0:s1, 1] += gr * seg
    else:
        buf[s0:s1] += seg


def pan(p):
    """Constant-power pan, p in [-1, 1]."""
    th = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.cos(th), np.sin(th)


def gate_before(n_total, end, ramp):
    """1 until end-ramp, raised-cosine to 0 at `end`, 0 after (the 'stop dead')."""
    g = np.zeros(n_total)
    g[:end - ramp] = 1.0
    g[end - ramp:end] = 0.5 + 0.5 * np.cos(np.pi * np.arange(ramp) / ramp)
    return g


def tick_times(t_end=2.5, r0=4.0, r1=28.0):
    """Exponentially accelerating tick rate r(t)=r0*exp(kt), r(t_end)=r1; ticks at integer phase."""
    k = np.log(r1 / r0) / t_end
    n_max = int(np.floor(r0 / k * (np.exp(k * t_end) - 1)))
    t = np.log(1 + np.arange(n_max + 1) * k / r0) / k
    return t[t < t_end - 0.012]


def ping_pong(dry, start, delay_s=0.25, repeats=3, gain_db=-6.0, side=0.85, lp=None):
    """1/8-note ping-pong: each repeat -6 dB, alternating R/L; optional low-pass per repeat (cutoff list)."""
    out = dry.copy()
    m = dry.mean(axis=1)
    d = int(round(delay_s * SR))
    for r in range(1, repeats + 1):
        tap = np.zeros_like(m)
        tap[d * r:] = m[:len(m) - d * r]
        if lp is not None:
            tap = signal.sosfilt(signal.butter(2, lp[r - 1], "lowpass", fs=SR, output="sos"), tap)
        g = 10 ** (gain_db * r / 20)
        gl, gr = pan(side if r % 2 == 1 else -side)
        out[:, 0] += g * gl * tap
        out[:, 1] += g * gr * tap
    return out


def sub_thump(dur, glide=True):
    """Sine sub: 90 -> 45 Hz over 120 ms (brief), then settles onto D1 (36.71 Hz)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = np.where(t < 0.12, 90.0 * 0.5 ** (t / 0.12),
                 hz(26) + (45.0 - hz(26)) * np.exp(-(t - 0.12) / 0.05))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.3) * env_ar(n, 144, int(0.05 * SR))
# ------------------------------------------------------------- end helpers --

SEED = 56
rng = np.random.default_rng(SEED)

CLUSTER = [62, 65, 69, 76]  # D4 F4 A4 E5
DETENT = 86  # D6
assert_pcs(CLUSTER + [26], DM_ADD9, "impact")
assert_pcs([DETENT, DETENT + 12], D_MINOR, "detent")

x = np.zeros((N, 2))

# ---------------- ticks
tk = np.zeros((N, 2))
b_pk, a_pk = signal.iirpeak(4500.0, 22.0, fs=SR)
TL = 720
blip = np.sin(2 * np.pi * 2200.0 * np.arange(48) / SR) * np.hanning(48)
td = np.arange(int(0.05 * SR)) / SR
ring = (np.sin(2 * np.pi * hz(DETENT) * td) + 0.25 * np.sin(2 * np.pi * hz(DETENT + 12) * td) * np.exp(-td / 0.006)) \
    * np.exp(-td / 0.011) * env_ar(len(td), 48, 300)
for i, t0 in enumerate(tick_times()):
    s = int(round(t0 * SR))
    nb = np.zeros(TL)
    nb[:96] = rng.standard_normal(96) * env_ar(96, 8, 40)
    rb = signal.lfilter(b_pk, a_pk, nb)
    rb = rb / (np.abs(rb).max() + 1e-12) * env_ar(TL, 1, 300)
    tick = 0.75 * rb
    tick[:48] += 0.5 * blip
    amp = 0.5 + 0.4 * t0 / 2.5
    j = i % 8
    place(tk, s, amp * tick, *pan(-0.3 + 0.1 * j))
    if i % 4 == 3:
        place(tk, s, 0.2 * ring, *pan(-0.3 + 0.1 * j))
tk *= gate_before(N, HIT, 96)[:, None]
x += tk

# ---------------- whoosh: time-varying biquad, block processed
w0, w1 = 30 * SPF, HIT
BLK = 240
seg_n = w1 - w0
noise = rng.standard_normal((seg_n, 2))
out = np.zeros_like(noise)
zi = np.zeros((2, 2, 2))  # (channel, section, state)
for b in range(0, seg_n, BLK):
    u = (b + BLK / 2) / seg_n
    fc = 300.0 * 20.0 ** u
    q = 1.5 + 2.0 * u
    bb, aa = signal.iirpeak(fc, q, fs=SR)
    sos = np.vstack([signal.tf2sos(bb, aa)] * 2)  # same resonant biquad twice -> steeper skirts
    for c in range(2):
        out[b:b + BLK, c], zi[c] = signal.sosfilt(sos, noise[b:b + BLK, c], zi=zi[c])
uu = np.arange(seg_n) / seg_n
wenv = (np.sin(np.pi / 2 * uu) ** 2) ** 1.3 * gate_before(seg_n, seg_n, 240) * env_ar(seg_n, 2400, 0)
out *= wenv[:, None]
out /= np.sqrt((out ** 2).mean()) + 1e-12
place(x, w0, 0.085 * out)

# ---------------- impact
place(x, HIT, 0.8 * sub_thump(1.4))
cl = np.zeros((N, 2))
nn = N - HIT
t = np.arange(nn) / SR
modes = [(1.0, 1.0, 1.0), (2.76, 0.22, 0.28), (5.40, 0.06, 0.09)]
pans = [-0.4, -0.1, 0.15, 0.4]
for idx, (m, p) in enumerate(zip(CLUSTER, pans)):
    f0 = hz(m)
    note = np.zeros(nn)
    for r_, a, dec in modes:
        if f0 * r_ < 15000:
            note += a * np.sin(2 * np.pi * f0 * r_ * t) * np.exp(-t / dec)
    # felt: soft 9 ms attack + a little low-passed contact noise
    cn = signal.sosfilt(signal.butter(2, 1200, "lowpass", fs=SR, output="sos"), rng.standard_normal(nn))
    note += 0.15 * cn * np.exp(-t / 0.008)
    note *= env_ar(nn, int(0.009 * SR), int(0.1 * SR))
    off = int(idx * 0.005 * SR)
    place(cl, HIT + off, 0.22 * note[:nn - off], *pan(p))
cl = ping_pong(cl, HIT, lp=[5000, 3000, 1800])
x += cl

# reversed-noise tail after the hit: a decaying noise grain played backwards (swells, then cuts)
L = int(0.19 * SR)
g = signal.sosfilt(signal.butter(2, [1500, 7000], "bandpass", fs=SR, output="sos"), rng.standard_normal((L, 2)), axis=0)
g = g / np.abs(g).max() * np.exp(-np.arange(L) / (0.05 * SR))[::-1, None] * env_ar(L, 96, 144)[:, None]
place(x, HIT, 0.22 * g)

y = master(x, target_lufs=-14.0, fade_out_s=0.35)
write_wav(sys.argv[1], y, N)
