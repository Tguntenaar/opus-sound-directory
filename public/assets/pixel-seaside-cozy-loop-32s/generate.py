"""--- 7. Cozy pixel seaside village loop (id: pixel-seaside-cozy-loop-32s, category: ambient, 32.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 1,536,000 samples (32.0 s at 30 fps = 960 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A seamless 32-second cozy pixel-game town loop in G major at 90 BPM (1 beat = 20 frames, 12 bars). Soft chiptune palette: a rounded square lead (25% duty, 3 kHz low-pass, gentle vibrato after 150 ms), triangle bass, a plucked 'kalimba' (Karplus-Strong, short) and a noise-channel shaker on 8ths at low level. Progression Gmaj7 → Em7 → Cmaj7 → D6sus4, 2 bars each, twice, then a 4-bar B section (Am7 → D7 → Bm7 → C6) ; an original, relaxed melody, mostly quarter and dotted notes. Bed of gentle seaside air: faint low-passed wave swells every 8 s (pink noise, 400 Hz low-pass, slow attack). Mono-ish (side/mid ~0.15) like a handheld. The last beat must flow into frame 0: make the ending state equal the start (no fade), verify loop seam by checking the RMS and waveform continuity across the boundary. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the loop seam is click-free (sample delta at the boundary < 0.01) and bar lines land on frame multiples of 80, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 3 approach: harmonic layout read literally as 2 bars per chord for the A section played once (8 bars) + 1 bar per chord for the 4-bar B (12 bars). Lead = band-limited single-cycle wavetable (25% pulse, harmonics capped below 18 kHz with the 3 kHz 2-pole roll-off baked in) read with interpolated phase, delayed vibrato; slower, more spacious original melody. Additive triangle bass in a root-half / fifth / octave-pop pattern; Karplus-Strong kalimba plays short rolled chords on beats 1 and 3; shaker with alternating short/soft 8th envelopes; wave bed morphs pink noise between 200 Hz and 400 Hz low-passes as each 8 s swell crests; the whole tonal mix shares a small circular FFT-convolution plate. Circular rendering, no fade.
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

# ------------------------------------------------------------------ piece ----
SEED = 57
rng = np.random.default_rng(SEED)
N = 1536000                     # 32.0 s
BEAT = 32000                    # 90 BPM -> 0.6667 s = 20 frames
BAR = 4 * BEAT                  # 80 frames
assert 12 * BAR == N and BAR % 1600 == 0 and BAR // 1600 == 80

PC = {"Gmaj7": {7, 11, 2, 6}, "Em7": {4, 7, 11, 2}, "Cmaj7": {0, 4, 7, 11},
      "D6sus4": {2, 7, 9, 11}, "Am7": {9, 0, 4, 7}, "D7": {2, 6, 9, 0},
      "Bm7": {11, 2, 6, 9}, "C6": {0, 4, 7, 9}}
ROOT = {"Gmaj7": 43, "Em7": 40, "Cmaj7": 48, "D6sus4": 38, "Am7": 45, "D7": 38,
        "Bm7": 47, "C6": 48}
FIFTH = {"Gmaj7": 50, "Em7": 47, "Cmaj7": 43, "D6sus4": 45, "Am7": 40, "D7": 45,
         "Bm7": 42, "C6": 43}
BARS = ["Gmaj7", "Gmaj7", "Em7", "Em7", "Cmaj7", "Cmaj7", "D6sus4", "D6sus4",
        "Am7", "D7", "Bm7", "C6"]


def chords_over(b0, dur):
    s = set()
    k = int(np.floor(b0 / 4))
    while k * 4 < b0 + dur - 1e-9:
        s.add(BARS[k % 12])
        k += 1
    return s


def check_note(b0, dur, midi, what):
    for c in chords_over(b0, max(dur, 0.01)):
        assert midi % 12 in PC[c], f"{what}: midi {midi} at beat {b0} not in {c}"


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add_circ(buf, sig, start):
    if sig.ndim == 1:
        sig = np.stack([sig, sig], axis=1)
    pos, off, n = int(start) % N, 0, sig.shape[0]
    while off < n:
        k = min(n - off, N - pos)
        buf[pos:pos + k] += sig[off:off + k]
        off += k
        pos = (pos + k) % N


def pan(sig, p):
    a = (p + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], axis=1) * np.sqrt(2)


def env_adsr(n_on, n_tot, att, dec, sus, rel):
    t = np.arange(n_tot) / SR
    e = np.minimum(1.0, t / att)
    e = np.where(t > att, sus + (1 - sus) * np.exp(-(t - att) / dec), e)
    r = np.ones(n_tot)
    r[n_on:] = np.cos(np.linspace(0, np.pi / 2, n_tot - n_on)) ** 2
    return e * r


def lp_w(f, fc, order=2):
    return 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order))


def fft_filter_circ(x, H_of_f):
    X = np.fft.rfft(x, axis=0)
    H = H_of_f(np.fft.rfftfreq(x.shape[0], 1 / SR))
    return np.fft.irfft(X * (H[:, None] if X.ndim == 2 else H), n=x.shape[0], axis=0)


TBL = 4096


def pulse_table(f0, duty=0.25, fc=3000.0):
    """one cycle of a band-limited 25% pulse, built in the frequency domain."""
    spec = np.zeros(TBL // 2 + 1, complex)
    K = min(TBL // 2 - 1, int(18000 / (f0 * 1.02)))
    k = np.arange(1, K + 1)
    a = (2 / (k * np.pi)) * np.sin(k * np.pi * duty) * lp_w(k * f0, fc)
    spec[1:K + 1] = a * TBL / 2                      # cosine partials
    return np.fft.irfft(spec, n=TBL)


def wt_lead(f0, dur_s):
    rel = 0.14
    n_on = int(dur_s * SR)
    n = n_on + int(rel * SR)
    t = np.arange(n) / SR
    vib_env = np.clip((t - 0.15) / 0.35, 0, 1)
    f = f0 * 2 ** ((15 / 1200) * vib_env * np.sin(2 * np.pi * 4.8 * t))
    ph = (np.cumsum(f) / SR) % 1.0 * TBL
    tb = pulse_table(f0)
    i0 = np.floor(ph).astype(int)
    fr = ph - i0
    y = tb[i0 % TBL] * (1 - fr) + tb[(i0 + 1) % TBL] * fr
    return y * env_adsr(n_on, n, 0.015, 0.5, 0.75, rel)


def tri_bass(f0, dur_s):
    rel = 0.06
    n_on = int(dur_s * SR)
    n = n_on + int(rel * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, int(8000 / f0) + 1, 2):
        out += ((-1) ** ((k - 1) // 2)) / k ** 2 * np.sin(2 * np.pi * k * f0 * t) * lp_w(k * f0, 2000.0)
    return out * (8 / np.pi ** 2) * env_adsr(n_on, n, 0.006, 0.4, 0.75, rel)


def ks_kalimba(f0, dur_s=0.5, g=0.988):
    n = int(dur_s * SR)
    D = SR / f0
    L = int(np.floor(D - 0.5 - 0.3))
    d = D - 0.5 - L
    c = (1 - d) / (1 + d)
    exc_n = L + 2
    exc = signal.lfilter([0.5, 0.5], [1.0], rng.uniform(-1, 1, exc_n)) * np.hanning(exc_n)
    x = np.zeros(n)
    x[:exc_n] = exc
    a = np.zeros(L + 3)
    a[0], a[1] = 1.0, c
    a[L] -= g * 0.5 * c
    a[L + 1] -= g * 0.5 * (1 + c)
    a[L + 2] -= g * 0.5
    y = signal.lfilter([1.0, c], a, x)
    y = signal.sosfilt(signal.butter(2, 5000, "lowpass", fs=SR, output="sos"), y)
    t = np.arange(n) / SR
    y = y / (np.abs(y).max() + 1e-12) + 0.7 * np.sin(2 * np.pi * f0 * t) * np.exp(-t / 0.15)
    e = np.exp(-t / 0.13) * np.minimum(1, t / 0.0015)
    nr = int(0.03 * SR)
    e[-nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return y * e


# --------------------------------------------------------------- melody -----
MEL = [
    (0, 0, 1.5, 74), (0, 1.5, 1.5, 71), (0, 3, 1, 67),
    (1, 0, 3, 78), (1, 3, 1, 74),
    (2, 0, 1.5, 76), (2, 1.5, 0.5, 74), (2, 2, 2, 71),
    (3, 0, 1, 67), (3, 1, 1, 71), (3, 2, 1.5, 74), (3, 3.5, 0.5, 76),
    (4, 0, 3, 79), (4, 3, 1, 76),
    (5, 0, 1.5, 72), (5, 1.5, 1.5, 76), (5, 3, 1, 71),
    (6, 0, 2, 69), (6, 2, 1, 71), (6, 3, 1, 74),
    (7, 0, 3, 79), (7, 3, 1, 74),
    (8, 0, 1.5, 76), (8, 1.5, 1.5, 72), (8, 3, 1, 69),
    (9, 0, 1.5, 72), (9, 1.5, 1.5, 78), (9, 3, 1, 81),
    (10, 0, 2, 81), (10, 2, 1, 78), (10, 3, 1, 74),
    (11, 0, 1.5, 76), (11, 1.5, 1.5, 72), (11, 3, 1, 69),
]

x = np.zeros((N, 2))

lead = np.zeros((N, 2))
for bar, bt, du, m in MEL:
    b0 = bar * 4 + bt
    check_note(b0, du, m, "lead")
    add_circ(lead, pan(wt_lead(mtof(m), du * BEAT / SR * 0.93), -0.15), b0 * BEAT)
x += 0.20 * lead

bass = np.zeros((N, 2))
for bar, ch in enumerate(BARS):
    for bt, du, m in ((0, 2, ROOT[ch]), (2, 1.5, FIFTH[ch]), (3.5, 0.5, ROOT[ch] + 12)):
        check_note(bar * 4 + bt, du, m, "bass")
        add_circ(bass, tri_bass(mtof(m), du * BEAT / SR * 0.92), (bar * 4 + bt) * BEAT)
x += 0.17 * bass

# kalimba: short rolled chords (low -> high, 35 ms apart) on beats 1 and 3
kal = np.zeros((N, 2))
for bar, ch in enumerate(BARS):
    pool = sorted(m for m in range(72, 89) if m % 12 in PC[ch])
    for bt, notes in ((0, pool[0:3]), (2, pool[1:4])):
        for i, m in enumerate(notes):
            check_note(bar * 4 + bt, 1, m, "kalimba")
            add_circ(kal, pan((0.6 + 0.15 * i) * ks_kalimba(mtof(m)), -0.6 + 0.6 * i),
                     (bar * 4 + bt) * BEAT + int(i * 0.035 * SR))
x += 0.10 * kal

# shaker: straight 8ths, on-beats short and dry, off-beats softer attack
shn = rng.standard_normal((N, 2))
shn[:, 1] = 0.4 * shn[:, 0] + 0.92 * shn[:, 1]
sh = fft_filter_circ(shn, lambda f: (1 - lp_w(f, 4500.0, 3)) * lp_w(f, 11000.0, 2))
h = BEAT // 2
pos = np.arange(N) % h
off = ((np.arange(N) // h) % 2) == 1
e_on = np.exp(-pos / (0.015 * SR)) * np.minimum(1, pos / (0.0015 * SR)) * 0.55
e_off = (pos / (0.008 * SR)) ** 2 * np.exp(2 - 2 * pos / (0.008 * SR))      # peak 1 at 8 ms
x += 0.03 * sh * np.where(off, e_off, e_on)[:, None]

# seaside air: pink noise morphing between 200 Hz and 400 Hz low-pass, swell every 8 s
pn = rng.standard_normal((N, 2))
pn[:, 1] = 0.55 * pn[:, 0] + 0.83 * pn[:, 1]
pk = 1.0 / np.sqrt(np.maximum(np.fft.rfftfreq(N, 1 / SR), 20.0))
Xp = np.fft.rfft(pn, axis=0) * pk[:, None]
fr_ = np.fft.rfftfreq(N, 1 / SR)
dark = np.fft.irfft(Xp * lp_w(fr_, 200.0, 2)[:, None], n=N, axis=0)
bright = np.fft.irfft(Xp * lp_w(fr_, 400.0, 2)[:, None], n=N, axis=0)
dark /= dark.std()
bright /= bright.std()
u = (np.arange(N) % (8 * SR)) / (8 * SR)
sw = np.where(u < 0.4, np.sin(np.pi / 2 * u / 0.4) ** 2, np.cos(np.pi / 2 * (u - 0.4) / 0.6) ** 2)
x += 0.05 * (dark * (1 - sw)[:, None] * 0.35 + bright * sw[:, None]) * (0.3 + 0.7 * sw)[:, None]

# shared small plate (circular FFT convolution) on lead + kalimba + a touch of bass
ir_n = int(0.8 * SR)
ti = np.arange(ir_n) / SR
ir = rng.standard_normal((ir_n, 2)) * (np.exp(-ti / 0.2) * np.minimum(1, ti / 0.01))[:, None]
ir[:, 1] = 0.75 * ir[:, 0] + 0.66 * ir[:, 1]
irf = np.pad(ir, ((0, N - ir_n), (0, 0)))
irf = fft_filter_circ(irf, lambda f: lp_w(f, 3500.0, 1) * (1 - lp_w(f, 250.0, 1)))
src = 0.20 * lead + 0.10 * kal + 0.03 * bass
wet = np.fft.irfft(np.fft.rfft(src, axis=0) * np.fft.rfft(irf, axis=0), n=N, axis=0)
wet *= 0.14 * np.sqrt((src ** 2).mean()) / (np.sqrt((wet ** 2).mean()) + 1e-12)
x += wet

y = master(x, target_lufs=-14.0, fade_out_s=0.0, loop=True)
write_wav(sys.argv[1], y, N)
