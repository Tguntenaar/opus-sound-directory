"""--- 2. Wireframe explainer VO bed (id: wireframe-explainer-vo-bed-20s, category: ad-beds, 20.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 960,000 samples (20.0 s at 30 fps = 600 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 20-second dark, minimal explainer bed in F minor at 128 BPM (1 beat = 14.0625 frames; bars every 56.25 frames), built to sit UNDER a voiceover: keep 200 Hz-3 kHz quiet (pad and bells high-passed or notched there by ~6 dB). Frame 0: low mono sine-sub hit on F1 with a click transient. Bars 1-2: a sub pulse on every beat (F1, 80 ms decay) plus a ghostly airy pad (detuned saws, 2.5 kHz low-pass, very wide) on Fm9 → Dbmaj7 → Bbm9 → C7sus4, two bars each. Every 2 bars a sparse glass bell (FM, ratio 3.5, 1.2 s decay) plays one note of the chord, panned alternately. Frames 270-300: a 1-bar drop-out (pad only) for a narration beat. Frames 540-600: final bar, sub hit on frame 540, pad swells and fades to 0. No melody hooks, no drums brighter than the bells. Target low end 20-25% of energy, stereo side/mid ~0.3. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 1 approach: polyBLEP detuned saws (3 independent voices per note per channel -> very wide) through a 4th-order 2.5 kHz low-pass; pure sine sub pulses (F1, 80 ms decay to -20 dB) and two pitch-settling F1 hits with a soft 1 ms click; 2-op FM glass bells (ratio 3.5, T60 1.2 s) high in octave 5/6, panned alternately; the VO band (200 Hz-3 kHz) of pad and bells is dipped ~6 dB by subtracting half of a zero-phase band-pass copy. Sub level and pad width are auto-calibrated to 22.5 % low end and side/mid 0.30.
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


# ------------------------------------------------------------------ setup --
SEED = 55
rng = np.random.default_rng(SEED)
N = 960000
FPS = 30
SPF = SR // FPS            # 1600 samples per frame
BEAT = 22500               # 128 BPM -> 0.46875 s = 14.0625 frames
BAR = 4 * BEAT             # 56.25 frames


def mhz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ramp_env(n, a, r):
    """flat 1 with raised-cosine attack a / release r samples"""
    e = np.ones(n)
    if a > 0:
        e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if r > 0:
        e[-r:] *= np.cos(np.linspace(0, np.pi / 2, r)) ** 2
    return e


def add(dst, sig, start):
    """add (n,) or (n,2) sig into dst at start (clipped to buffer)"""
    if start >= dst.shape[0]:
        return
    n = min(sig.shape[0], dst.shape[0] - start)
    if sig.ndim == 1:
        dst[start:start + n] += sig[:n, None]
    else:
        dst[start:start + n] += sig[:n]


# chord timeline (2 bars each, Fm9 returns for bars 8+)
PC = {"Fm9": {5, 8, 0, 3, 7}, "Dbmaj7": {1, 5, 8, 0}, "Bbm9": {10, 1, 5, 8, 0}, "C7sus4": {0, 5, 7, 10}}
VOICE = {"Fm9": [53, 56, 60, 63, 67], "Dbmaj7": [49, 56, 60, 61, 65],
         "Bbm9": [53, 56, 58, 60, 61], "C7sus4": [48, 55, 58, 60, 65]}
TIMELINE = [("Fm9", 0, 2 * BAR), ("Dbmaj7", 2 * BAR, 4 * BAR), ("Bbm9", 4 * BAR, 6 * BAR),
            ("C7sus4", 6 * BAR, 8 * BAR), ("Fm9", 8 * BAR, N)]
# one bell note per 2 bars, chord tone, alternating pan
BELLS = [(0, 79, -0.6), (2 * BAR, 84, 0.6), (4 * BAR, 85, -0.6), (6 * BAR, 79, 0.6), (8 * BAR, 80, -0.6)]
F1 = 29  # MIDI F1


def chord_at(s):
    for name, a, b in TIMELINE:
        if a <= s < b:
            return name
    return TIMELINE[-1][0]


# harmony assertions
for name, notes in VOICE.items():
    assert all(m % 12 in PC[name] for m in notes), name
for s, m, _ in BELLS:
    assert m % 12 in PC[chord_at(s)], (s, m)
for name, _, _ in TIMELINE:
    assert F1 % 12 in PC[name], "sub F must sit in every chord"

DROP0, DROP1 = 270 * SPF, 300 * SPF      # narration drop-out (pad only)
END_HIT = 540 * SPF


# ------------------------------------------------------------------- pad --
def saw_blep(f, n, ph0):
    dt = f / SR
    ph = (ph0 + dt * np.arange(n)) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    t = ph[m] / dt
    y[m] -= t + t - t * t - 1
    m = ph > 1 - dt
    t = (ph[m] - 1) / dt
    y[m] -= t * t + t + t + 1
    return y


pad = np.zeros((N, 2))
XF = int(0.45 * SR)
for i, (name, a, b) in enumerate(TIMELINE):
    att = int(1.2 * SR) if i == 0 else XF
    rel = XF if b < N else 0
    n = (b - a) + rel
    seg = np.zeros((n, 2))
    for m in VOICE[name]:
        f = mhz(m)
        for ch in range(2):
            for cents in rng.uniform(-14, 14, 3):
                seg[:, ch] += saw_blep(f * 2 ** (cents / 1200), n, rng.uniform())
    seg *= ramp_env(n, att, rel)[:, None]
    add(pad, seg, a)
pad = signal.sosfilt(signal.butter(4, 2500, "lowpass", fs=SR, output="sos"), pad, axis=0)
# slow breathing amplitude so it stays ghostly
pad *= (1 + 0.12 * np.sin(2 * np.pi * np.arange(N) / (2 * BAR)))[:, None]

# final bar: swell from frame 540 to ~570 then fade to 0 at 600
g = np.ones(N)
sw0, sw1 = END_HIT, 572 * SPF
g[sw0:sw1] = 1 + 0.9 * np.sin(np.linspace(0, np.pi / 2, sw1 - sw0)) ** 2
g[sw1:] = 1.9 * np.cos(np.linspace(0, np.pi / 2, N - sw1)) ** 2
pad *= g[:, None]

# ----------------------------------------------------------------- bells --
def fm_bell(f, n, ratio=3.5, I0=2.6):
    t = np.arange(n) / SR
    I = I0 * np.exp(-t / 0.25) + 0.25
    y = np.sin(2 * np.pi * f * t + I * np.sin(2 * np.pi * f * ratio * t))
    return y * np.exp(-t * 6.91 / 1.2) * ramp_env(n, 96, 2400)


bells = np.zeros((N, 2))
for s, m, p in BELLS:
    b = fm_bell(mhz(m), int(1.6 * SR))
    gl, gr = np.sqrt((1 - p) / 2), np.sqrt((1 + p) / 2)
    add(bells, np.stack([b * gl, b * gr], 1), s)
bells = signal.sosfilt(signal.butter(4, 14000, "lowpass", fs=SR, output="sos"), bells, axis=0)


# VO-band dip (~ -6 dB between 200 Hz and 3 kHz) on pad and bells
def vo_dip(x):
    sos = signal.butter(4, [200, 3000], "bandpass", fs=SR, output="sos")
    return x - 0.56 * signal.sosfiltfilt(sos, x, axis=0)


def band_db(a, b, lo=200, hi=3000):
    fa = np.fft.rfftfreq(a.shape[0], 1 / SR)
    k = (fa >= lo) & (fa <= hi)
    pa = (np.abs(np.fft.rfft(a, axis=0)) ** 2).sum(1)[k].sum()
    pb = (np.abs(np.fft.rfft(b, axis=0)) ** 2).sum(1)[k].sum()
    return 10 * np.log10(pb / pa)


pad_d = vo_dip(pad)
print("pad VO-band change dB", round(band_db(pad, pad_d), 2), file=sys.stderr)
pad = pad_d
bells = vo_dip(bells)

# ------------------------------------------------------------------- sub --
def sub_hit(n, f0, tau, drop=0.0, click=0.0):
    t = np.arange(n) / SR
    f = f0 * (1 + drop * np.exp(-t / 0.025))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau)
    y *= ramp_env(n, 96, int(0.03 * SR))
    if click > 0:
        c = rng.standard_normal(96) * np.hanning(96)           # ~2 ms soft burst
        c = signal.sosfilt(signal.butter(2, 3500, "lowpass", fs=SR, output="sos"), c)
        y[:96] += click * c / np.abs(c).max()
    return y


sub = np.zeros(N)
hit = sub_hit(int(1.0 * SR), mhz(F1), 0.30, drop=0.6, click=0.35)
sub[:hit.size] += hit
sub[END_HIT:END_HIT + min(hit.size, N - END_HIT)] += hit[:N - END_HIT]
pulse = sub_hit(int(0.22 * SR), mhz(F1), 0.08 / np.log(10))    # -20 dB at 80 ms
k = 1
while k * BEAT < 525 * SPF:
    s = k * BEAT
    if not (DROP0 <= s < DROP1):
        sub[s:s + pulse.size] += 0.8 * pulse
    k += 1
sub[DROP1:DROP1 + pulse.size] += 0.9 * pulse                    # re-entry pulse on frame 300

# drop-out: pad only (mute sub + bells with 3 ms ramps)
mute = np.ones(N)
r = int(0.008 * SR)
mute[DROP0:DROP1] = 0
mute[DROP0 - r:DROP0] = np.cos(np.linspace(0, np.pi / 2, r)) ** 2
bells *= mute[:, None]
# narration beat: pad stays alone and sits back 3 dB (30 ms ramps)
dd = np.ones(N)
rr = int(0.03 * SR)
dd[DROP0:DROP1] = 10 ** (-3 / 20)
dd[DROP0:DROP0 + rr] = 1 - (1 - 10 ** (-3 / 20)) * np.sin(np.linspace(0, np.pi / 2, rr)) ** 2
dd[DROP1 - rr:DROP1] = 1 - (1 - 10 ** (-3 / 20)) * np.cos(np.linspace(0, np.pi / 2, rr)) ** 2
pad *= dd[:, None]
sub[DROP0:DROP1] *= 0
sub[DROP0 - r:DROP0] *= np.cos(np.linspace(0, np.pi / 2, r)) ** 2

# ------------------------------------------------------------- calibrate --
fr = np.fft.rfftfreq(N, 1 / SR)
LOW = fr < 150


def pw(x):
    X = np.fft.rfft(x, axis=0)
    return (np.abs(X) ** 2).sum(axis=1) if X.ndim == 2 else 2 * np.abs(X) ** 2


PAD_G, BELL_G = 1.0, 0.9 * np.abs(pad).max() / np.abs(bells).max() * 0.35
pad *= PAD_G
bells *= BELL_G
other = pad + bells
Po, Ps = pw((other[:, 0] + other[:, 1]) / 2), pw(hp_dc(sub))  # low-end measured on the mid signal, post DC filter
target = 0.225
gs2 = (target * Po.sum() - Po[LOW].sum()) / (Ps[LOW].sum() - target * Ps.sum())
sub *= np.sqrt(max(gs2, 0.0))

# stereo width: scale pad side so total side/mid ~= 0.30
mid_o = (bells[:, 0] + bells[:, 1]) / 2 + sub + (pad[:, 0] + pad[:, 1]) / 2
side_b = (bells[:, 0] - bells[:, 1]) / 2
side_p = (pad[:, 0] - pad[:, 1]) / 2
Mr = (mid_o ** 2).mean()
w = np.sqrt(max(0.30 ** 2 * Mr - (side_b ** 2).mean(), 0) / (side_p ** 2).mean())
pm = (pad[:, 0] + pad[:, 1]) / 2
pad = np.stack([pm + w * side_p, pm - w * side_p], 1)

x = pad + bells + sub[:, None]
m_, s_ = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
P = pw(m_)
print("low frac", round(P[LOW].sum() / P.sum(), 3), "side/mid", round(np.sqrt((s_ ** 2).mean() / (m_ ** 2).mean()), 3),
      "width w", round(w, 3), file=sys.stderr)

y = master(x, target_lufs=-14.0, fade_out_s=0.5)
write_wav(sys.argv[1], y, N)
