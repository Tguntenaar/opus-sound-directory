"""--- 4. Feature callout pops (6-sound sprite) (id: ui-callout-pop-sprite, category: ui-sounds, 3.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 144,000 samples (3.0 s at 30 fps = 90 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 3.0-second UI sprite of six feature-callout pops for app-launch videos, each starting exactly on frames 0, 15, 30, 45, 60, 75 and fully silent before the next slot so each can be sliced. Each pop = a soft round body (sine with a 6 ms pitch drop from 2x), a 1 ms bright click, and a two-note mallet interval in Ab major (marimba-ish modal synthesis, partials at 1, 3.99, 9.2x with fast decay): 1 Ab5→C6, 2 C6→Eb6, 3 Eb6→Ab6, 4 Db6→F6, 5 Bb5→Eb6, 6 a 3-note Ab6-Eb6-C7 sparkle for the final 'all done' callout. Second note 60 ms after the first. Each pop under 350 ms, centred with slight stereo spread on the second note. Master the sprite to -17 LUFS integrated instead of -14 (UI level), true peak <= -1 dBTP. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm each slot starts on its frame and is silent (< -60 dBFS) before the next, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 1 approach: direct additive modal synthesis. Each mallet note is a sum of exponentially decaying sines at 1, 3.99 and 9.2x the fundamental (fast decay, brighter partials die first). The body is a sine on the chord root (octave 3/4) whose pitch falls from 2x to 1x over 6 ms; the click is a 1 ms Hann-windowed burst of 2 kHz high-passed noise. Second note pans +-0.25 (alternating per slot). Mastered to -17 LUFS (the brief's specific UI level; it overrides the generic -14 line), then a per-slot gate (2 ms fades) keeps each pop inside 345 ms so every slot can be sliced.
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


SEED = 55
rng = np.random.default_rng(SEED)
N = 144000
FPS = 30
SPF = SR // FPS
SLOTS = [0, 15, 30, 45, 60, 75]
POP_LEN = 0.345            # every pop is gated inside 345 ms (< 350 ms)
NOTE_GAP = 0.060           # second note 60 ms after the first


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ----- harmony (Ab major).  pitch classes: C=0 ... Ab=8
AB_MAJOR = {8, 10, 0, 1, 3, 5, 7}
CHORDS = {"Ab": {8, 0, 3}, "Db": {1, 5, 8}, "Eb": {3, 7, 10}}
#        chord, mallet notes (MIDI), body root (MIDI)
POPS = [("Ab", [80, 84], 56),        # Ab5 -> C6      body Ab3
        ("Ab", [84, 87], 56),        # C6  -> Eb6
        ("Ab", [87, 92], 56),        # Eb6 -> Ab6
        ("Db", [85, 89], 61),        # Db6 -> F6      body Db4
        ("Eb", [82, 87], 63),        # Bb5 -> Eb6     body Eb4
        ("Ab", [92, 87, 96], 56)]    # Ab6 - Eb6 - C7 sparkle
for ch, notes, root in POPS:
    for m in notes + [root]:
        assert m % 12 in CHORDS[ch], (ch, m)
        assert m % 12 in AB_MAJOR, m


def env_ar(n, att_s, rel_s):
    e = np.ones(n)
    a = max(2, int(att_s * SR))
    r = max(2, int(rel_s * SR))
    e[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    e[-r:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, r))
    return e


def mallet(f0, dur, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for ratio, amp, tau in [(1.0, 1.0, 0.072), (3.99, 0.32, 0.034), (9.2, 0.10, 0.011)]:
        f = f0 * ratio
        if f > 19000:
            continue
        ph = rng.uniform(0, 0.2)
        y += amp * np.exp(-t / tau) * np.sin(2 * np.pi * f * t + ph)
    return vel * y * env_ar(n, 0.0012, 0.06)   # 60 ms release: tail rounds off instead of being chopped


def body(fb, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = fb * 2 ** np.clip(1 - t / 0.006, 0, 1)        # 2x -> 1x over 6 ms
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.045) * env_ar(n, 0.0012, 0.02)


hp_click = signal.butter(4, 2000, "highpass", fs=SR, output="sos")


def click():
    n = int(0.001 * SR)
    z = signal.sosfilt(hp_click, rng.standard_normal(n + 256))[256:]
    return z * np.hanning(n) / (np.abs(z).max() + 1e-9)


def pan(p):
    a = (p + 1) * np.pi / 4
    return np.cos(a), np.sin(a)


x = np.zeros((N, 2))


def add(sig, start, p=0.0):
    gl, gr = pan(p)
    e = min(N, start + len(sig))
    x[start:e, 0] += sig[:e - start] * gl * np.sqrt(2)
    x[start:e, 1] += sig[:e - start] * gr * np.sqrt(2)


for k, (slot, (ch, notes, root)) in enumerate(zip(SLOTS, POPS)):
    s0 = slot * SPF
    add(0.55 * body(m2f(root), 0.30), s0)
    add(0.30 * click(), s0)
    side = 0.25 if k % 2 == 0 else -0.25
    for j, m in enumerate(notes):
        st = s0 + int(j * NOTE_GAP * SR)
        dur = POP_LEN - j * NOTE_GAP - 0.004
        p = 0.0 if j == 0 else (side if j == 1 else -side)
        vel = 0.8 if j == 0 else (0.7 if j == 1 else 0.75)
        add(vel * mallet(m2f(m), dur), st, p)

y = master(x, target_lufs=-17.0, fade_out_s=0.05)

# per-slot gate: kill filter/limiter smear outside each slot (2 ms fades)
mask = np.zeros(N)
fd = int(0.002 * SR)
for slot in SLOTS:
    s0 = slot * SPF
    e = s0 + int(POP_LEN * SR)
    mask[s0:e] = 1.0
    # gate opens exactly on the frame (0.25 ms ramp inside the pop's own 1.2 ms attack)
    mask[s0:s0 + 12] = np.linspace(0, 1, 14)[1:-1]
    mask[e:e + fd] = np.linspace(1, 0, fd + 2)[1:-1]
y = y * mask[:, None]
y[-1] = 0.0
write_wav(sys.argv[1], y, N)
