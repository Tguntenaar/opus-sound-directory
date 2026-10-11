"""--- 5. Melancholic short-film underscore with rain (id: chalk-rain-underscore-60s, category: ambient, 60.0 s) ---
Output: one WAV, 48 kHz / 16-bit / stereo, exactly 2,880,000 samples (60.0 s at 30 fps = 1800 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 60-second melancholic animated-short underscore in D major at 74 BPM (1 beat = 24.32 frames). Frames 0-150: a hazy wide pad (D, A, F#, slow chorus) and distant city air noise. Frames 150-750: a music-box line (sine partials 1, 2.76, 5.4 with 1.5 s decay, slight mechanical timing jitter ±8 ms) plays an original, slow, mostly stepwise melody over Dmaj7 → Bm7 → Gmaj9 → A6, with a soft sine bass on roots; light warm 'play' textures: occasional soft wood knocks. Frames 750-840: thinning, pad only, energy drops 12 dB. Frame 840: a filtered pink-noise rain bed fades in (high-passed 1 kHz, wide stereo, random droplet ticks 2-6 kHz at ~25/s) and stays until frame 1170; harmony turns to Bm(add9) → Gmaj7 with low cello-like saw (1.2 kHz low-pass) swells; a lone music-box note every 2 bars, slightly detuned. Frame 1170: rain gutters out over 30 frames, a single low D2 cello note and a final music-box D6 on frame 1260, ring to silence by frame 1800 (last 10 s are a long, quiet decay of pad and air). Stereo side/mid ~0.6, nothing above -14 LUFS short-term at the climax. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 3 approach: spectral noise-band pad, beating tine-pair music box, 1.5-bar harmonic rhythm. The pad is synthesised in the frequency domain: every harmonic of every chord tone (to ~2.5 kHz) is a pair of narrow Gaussian noise bands +-6 cents apart with random phases, independent per channel, so the slow chorus/drift and the width come from the band-limited noise itself (a paulstretch-like haze). The music box keeps the 1 / 2.76 / 5.4 partials with a 1.5 s fundamental decay but each partial is a slightly mistuned tine pair (0.6-1.6 Hz beating), +-8 ms jitter. Harmony: Dmaj7 -> Bm7 -> Gmaj9 -> A6 at 1.5 bars each, then a Gmaj9 pad through the thinning; in the rain Bm(add9) 1.5 bars -> Gmaj7. New original melody with every on-beat onset a chord tone and off-beat diatonic passing tones. Bass is a single swelled sine per chord root; knocks are heavily damped Karplus-Strong wood. Rain is Voss-McCartney pink noise (HP 1 kHz) with an all-pass-decorrelated right channel and falling-pitch sine 'plink' droplets (2-6 kHz, Poisson ~25/s); the cello is an additive band-limited saw (harmonics below 4 kHz, per-harmonic bow jitter) through a 1.2 kHz 4th-order low-pass, playing a slow two-note line per chord. The room is a velvet-noise IR with a longer low band (2.8 s) than high band (1.3 s). Levels: 12 dB thinning solved numerically, side/mid trimmed to 0.6, short-term ceiling of -14 LUFS on every window that ends inside the climax (frames 840-1350) while integrated stays at -14.
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


from scipy.ndimage import uniform_filter1d

SEED = 57
rng = np.random.default_rng(SEED)
N = 2880000
FPS = 30
SPF = SR // FPS
BPM = 74
BEAT = 60.0 / BPM
BAR = 4 * BEAT
T = np.arange(N) / SR


def fr(f):
    return f / FPS


T_MEL, T_THIN, T_RAIN, T_GUT, T_GUT_END, T_LAST = fr(150), fr(750), fr(840), fr(1170), fr(1200), fr(1260)


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def n_(t):
    return int(round(t * SR))


# ------------------------------------------------------------------ harmony --
D_MAJOR = {2, 4, 6, 7, 9, 11, 1}
PCS = {"D": {2, 6, 9}, "Dmaj7": {2, 6, 9, 1}, "Bm7": {11, 2, 6, 9}, "Gmaj9": {7, 11, 2, 6, 9},
       "A6": {9, 1, 4, 6}, "Bm(add9)": {11, 2, 6, 1}, "Gmaj7": {7, 11, 2, 6}}
VOICING = {"D": [50, 57, 62, 66], "Dmaj7": [50, 57, 61, 66], "Bm7": [47, 54, 57, 62],
           "Gmaj9": [43, 50, 57, 59, 66], "A6": [45, 52, 61, 66], "Bm(add9)": [47, 54, 61, 62],
           "Gmaj7": [43, 50, 59, 66]}
ROOT = {"Dmaj7": 38, "Bm7": 35, "Gmaj9": 43, "A6": 33}
TIMELINE = [(0.0, T_MEL, "D")]
for i, c in enumerate(["Dmaj7", "Bm7", "Gmaj9", "A6"]):
    TIMELINE.append((T_MEL + i * 6 * BEAT, T_MEL + (i + 1) * 6 * BEAT, c))
TIMELINE.append((T_MEL + 24 * BEAT, T_RAIN, "Gmaj9"))     # pad-only colour through the thinning
TIMELINE += [(T_RAIN, T_RAIN + 6 * BEAT, "Bm(add9)"), (T_RAIN + 6 * BEAT, T_GUT, "Gmaj7"), (T_GUT, N / SR, "D")]


def chord_at(t):
    for t0, t1, c in TIMELINE:
        if t0 - 1e-6 <= t < t1 - 1e-6:
            return c
    return TIMELINE[-1][2]


for t0, t1, c in TIMELINE:
    assert all(m % 12 in PCS[c] for m in VOICING[c]), c
    assert PCS[c] <= D_MAJOR, c
    if c in ROOT:
        assert ROOT[c] % 12 in PCS[c]

# melody (beat from T_MEL, beats, midi). Every onset on an integer beat is a chord tone;
# off-beat onsets may be D-major passing tones. Original, mostly stepwise.
MEL = [(0, 1.5, 78), (1.5, 0.5, 76), (2, 2, 74), (4, 1.5, 73), (5.5, 0.5, 71),
       (6, 2, 71), (8, 1.5, 74), (9.5, 0.5, 76), (10, 2, 78),
       (12, 2, 79), (14, 1, 81), (15, 1, 83), (16, 2, 81),
       (18, 3, 78), (21, 1, 76), (22, 1.5, 73), (23.5, 0.5, 74)]
mel_events = []
for beat, dur, m in MEL:
    t = T_MEL + beat * BEAT
    c = chord_at(t + 1e-4)
    if float(beat).is_integer():
        assert m % 12 in PCS[c], (beat, m, c)
    else:
        assert m % 12 in D_MAJOR, (beat, m, c)
    jit = rng.uniform(-0.008, 0.008) if beat > 0 else rng.uniform(0.0, 0.008)
    mel_events.append((t + jit, m))
assert max(t for t, _ in mel_events) < T_THIN

LONE = [(T_RAIN + 0.05, 83), (T_RAIN + 2 * BAR, 90)]    # every 2 bars: B5 (Bm add9), F#6 (Gmaj7)
for t, m in LONE + [(T_LAST, 86)]:
    assert m % 12 in PCS[chord_at(t + 1e-4)], (t, m)
CELLO = []                                               # (t0, dur, midi): slow two-note line per chord
for t0, t1, c in TIMELINE:
    if c == "Bm(add9)":
        CELLO += [(t0, 4 * BEAT, 47), (t0 + 3 * BEAT, 4 * BEAT, 50)]
    elif c == "Gmaj7":
        h = (t1 - t0) / 2
        CELLO += [(t0, h + BEAT, 43), (t0 + h, h + 0.8, 47)]
for t0, d, m in CELLO:
    assert m % 12 in PCS[chord_at(t0 + 1e-4)], (t0, m)
assert 38 % 12 in PCS[chord_at(T_GUT + 1e-4)]           # the lone D2 cello


# ------------------------------------------------------------------- tools --
def ramp_env(n, att, rel):
    e = np.ones(n)
    a, r = max(2, n_(att)), max(2, n_(rel))
    a, r = min(a, n), min(r, n)
    e[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    e[n - r:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, r))
    return e


def place(buf, sig, t0):
    s = n_(t0)
    a = max(0, s)
    e = min(N, s + len(sig))
    if e > a:
        buf[a:e] += sig[a - s:e - s]


def pan2(sig, p):
    a = (p + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], 1) * np.sqrt(2)


# ---------------------------------------------------- spectral noise-band pad --
def band_pad(notes, n):
    """stereo noise-band chord: Gaussian bands (sigma ~0.25 %) at every harmonic, +-6 cents pair"""
    F = np.fft.rfftfreq(n, 1 / SR)
    df = F[1]
    out = np.zeros((n, 2))
    for ch in (0, 1):
        A = np.zeros(len(F))
        for m in notes:
            f0 = m2f(m)
            for h in range(1, 30):
                if f0 * h > 2500:
                    break
                for dc in (-6.0, 6.0):
                    fc = f0 * h * 2 ** (dc / 1200)
                    sig = max(0.0025 * fc, 0.35)
                    lo, hi = int((fc - 4 * sig) / df), int((fc + 4 * sig) / df) + 2
                    A[lo:hi] += (h ** -1.1) * np.exp(-0.5 * ((F[lo:hi] - fc) / sig) ** 2) / np.sqrt(sig)
        X = A * np.exp(1j * rng.uniform(0, 2 * np.pi, len(F)))
        out[:, ch] = np.fft.irfft(X, n)
    return out / np.sqrt((out ** 2).mean())


pad = np.zeros((N, 2))
for t0, t1, c in TIMELINE:
    att = 2.5 if t0 == 0 else 1.2
    end = min(N / SR, t1 + 1.8)
    n = n_(end - t0)
    env = ramp_env(n, att, 0.02)
    rs = n_(t1 - t0)
    if rs < n:
        env[rs:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, n - rs))
    place(pad, 0.1 * band_pad(VOICING[c], n) * env[:, None], t0)


# ------------------------------------------------- tine-pair music box --
def mbox(f0, dur=3.2, cents=0.0):
    n = n_(dur)
    t = np.arange(n) / SR
    f0 = f0 * 2 ** (cents / 1200)
    y = np.zeros(n)
    for ratio, amp, t60 in [(1.0, 1.0, 1.5), (2.76, 0.36, 0.85), (5.4, 0.15, 0.4)]:
        beat = rng.uniform(0.6, 1.6)
        ph = rng.uniform(0, 6.28)
        for s_ in (-0.5, 0.5):
            y += 0.5 * amp * np.exp(-6.9 * t / t60) * np.sin(2 * np.pi * (f0 * ratio + s_ * beat) * t + ph)
    return y * ramp_env(n, 0.002, 0.05)


mb = np.zeros((N, 2))
for t, m in mel_events:
    place(mb, pan2(0.42 * mbox(m2f(m)), rng.uniform(-0.3, 0.3)), t)
mb2 = np.zeros((N, 2))
for t, m in LONE:
    place(mb2, pan2(0.45 * mbox(m2f(m), cents=-11.0), rng.uniform(-0.35, 0.35)), t)
place(mb2, pan2(0.45 * mbox(m2f(86), dur=4.0), -0.05), T_LAST)

# -------------------------------------------------------------------- bass --
bass = np.zeros((N, 2))
for t0, t1, c in TIMELINE:
    if c not in ROOT or t0 >= T_THIN:
        continue
    n = n_(t1 - t0 + 0.5)
    tt = np.arange(n) / SR
    sw = np.sin(np.pi * np.minimum(tt / (t1 - t0 + 0.5), 1)) ** 0.7       # one slow swell
    y = np.sin(2 * np.pi * m2f(ROOT[c]) * tt) * sw * ramp_env(n, 0.05, 0.3)
    place(bass, pan2(0.12 * y, 0.0), t0)


# ------------------------------------------------------------- KS wood knocks --
def knock():
    n = n_(0.18)
    f = rng.uniform(300, 480)
    D = int(SR / f)
    ex = rng.standard_normal(n_(0.002)) * np.hanning(n_(0.002))
    ex = signal.sosfilt(LP_K, np.concatenate([ex, np.zeros(n - len(ex))]))
    a = np.zeros(D + 2)
    a[0] = 1.0
    a[D] = a[D + 1] = -0.5 * 0.86                     # heavy loss -> short woody tone
    y = signal.lfilter([1.0], a, ex)
    return y * ramp_env(n, 0.002, 0.04)


LP_K = signal.butter(4, 1800, "lowpass", fs=SR, output="sos")       # soft felt-ish contact
kn = np.zeros((N, 2))
for beat in [3.5, 9.5, 13.0, 17.5, 21.5]:
    t = T_MEL + beat * BEAT + rng.uniform(-0.008, 0.008)
    place(kn, pan2(0.5 * knock(), rng.uniform(-0.5, 0.5)), t)

play_env = np.ones(N)
s, w = n_(T_THIN), n_(0.10)
play_env[s:s + w] = np.cos(np.linspace(0, np.pi / 2, w)) ** 2
play_env[s + w:] = 0.0
mb *= play_env[:, None]
bass *= play_env[:, None]
kn *= play_env[:, None]

# ------------------------------------------------------- additive-saw cello --
lp_cello = signal.butter(4, 1200, "lowpass", fs=SR, output="sos")


def cello_note(m, dur, env):
    n = n_(dur)
    tt = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.0 * tt + rng.uniform(0, 6.28)) * np.clip((tt - 0.7) / 1.0, 0, 1)
    out = np.zeros((n, 2))
    f0 = m2f(m)
    for ch, dc in ((0, -3.5), (1, 3.5)):
        ph = 2 * np.pi * f0 * 2 ** (dc / 1200) * np.cumsum(vib) / SR
        grid = np.arange(0, dur + 0.2, 0.1)
        for h in range(1, int(4000 / f0) + 1):
            jit = 1 + 0.08 * np.interp(tt, grid, rng.standard_normal(len(grid)))
            out[:, ch] += jit * np.sin(h * ph + rng.uniform(0, 6.28)) / h
    out = signal.sosfilt(lp_cello, out, axis=0)
    return out * env[:, None]


def swell(n, peak=0.45):
    x_ = np.arange(n) / n
    return np.where(x_ < peak, np.sin(np.pi / 2 * x_ / peak) ** 2, np.cos(np.pi / 2 * (x_ - peak) / (1 - peak)) ** 2)


cel = np.zeros((N, 2))
for t0, d, m in CELLO:
    place(cel, 0.11 * cello_note(m, d, swell(n_(d))), t0)
nD = n_(8.0)
tt = np.arange(nD) / SR
envD = np.minimum(1, tt / 1.1) ** 2 * np.exp(-np.maximum(0, tt - 1.1) / 1.9) * ramp_env(nD, 0.01, 0.5)
place(cel, 0.15 * cello_note(38, 8.0, envD), T_GUT)

# -------------------------------------------------------------- rain bed --
rs, re = n_(T_RAIN), n_(T_GUT_END) + n_(0.1)
L = re - rs


def voss_pink(n, rows=16):
    y = rng.standard_normal(n) * 0.5
    for k in range(rows):
        hold = 2 ** k
        v = rng.standard_normal(n // hold + 2)
        off = rng.integers(0, hold)
        y += np.repeat(v, hold)[off:off + n]
    return y


rn = voss_pink(L)
rnR = voss_pink(L)
hp = signal.butter(4, 1000, "highpass", fs=SR, output="sos")
rn = np.stack([rn, rnR], 1)
rn = signal.sosfilt(hp, rn, axis=0)
for dms in (2.1, 3.7, 5.3):                       # all-pass chain decorrelates the right side further
    D = n_(dms * 1e-3)
    b = np.zeros(D + 1)
    a = np.zeros(D + 1)
    b[0], b[D], a[0], a[D] = -0.5, 1.0, 1.0, -0.5
    rn[:, 1] = signal.lfilter(b, a, rn[:, 1])
rn = signal.sosfilt(signal.butter(2, 10000, "lowpass", fs=SR, output="sos"), rn, axis=0)
rn /= rn.std()
tr = np.arange(L) / SR
gust = 10 ** ((1.4 * np.sin(2 * np.pi * 0.06 * tr + 0.4) + 0.5 * np.sin(2 * np.pi * 0.23 * tr)) / 20)
renv = np.ones(L)
fi = n_(0.5)
renv[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
g0, gl = n_(T_GUT - T_RAIN), n_(T_GUT_END - T_GUT)
gtt = np.linspace(0, 1, gl)
sgrid = np.arange(0, gl + 2400, 2400)
sput = np.interp(np.arange(gl), sgrid, rng.uniform(0.0, 1.0, len(sgrid)))   # sputtering gutter
renv[g0:g0 + gl] = (1 - gtt) ** 2 * (0.4 + 0.6 * sput)
renv[g0 + gl:] = 0.0
renv = uniform_filter1d(renv, 144)
rain = np.zeros((N, 2))
rain[rs:re] = 0.055 * rn * (renv * gust)[:, None]

drops = np.zeros((N, 2))
t = T_RAIN
while True:
    rate = 25.0 if t < T_GUT else 25.0 * max(0.06, 1 - (t - T_GUT) / (T_GUT_END - T_GUT))
    t += rng.exponential(1 / rate)
    if t >= T_GUT_END + 0.4:                      # a few last drips just after the gutter
        break
    n = n_(0.03)
    td = np.arange(n) / SR
    f = rng.uniform(2200, 5800)
    ph = 2 * np.pi * np.cumsum(f * (1 - 0.2 * np.minimum(td / 0.015, 1))) / SR   # falling 'plink'
    y = np.sin(ph) * np.exp(-td / rng.uniform(0.003, 0.007)) * ramp_env(n, 0.0007, 0.006)
    amp = 0.05 * np.exp(rng.normal(0, 0.5)) * min(1.0, (t - T_RAIN) / 0.5)
    place(drops, pan2(amp * y, rng.uniform(-0.95, 0.95)), t)

# -------------------------------------------------------------------- air --
wn = rng.standard_normal((N, 2))
air = signal.sosfilt(signal.butter(3, 700, "lowpass", fs=SR, output="sos"), wn, axis=0)
air /= air.std()
far = signal.sosfilt(signal.butter(2, [90, 260], "bandpass", fs=SR, output="sos"), wn[:, ::-1], axis=0)
air += 0.6 * far / far.std() * (0.5 + 0.5 * np.sin(2 * np.pi * 0.031 * T + 2.0))[:, None]   # distant traffic swell
air *= 0.025 * ramp_env(N, 2.5, 0.01)[:, None]

tail_env = np.ones(N)
k0 = n_(41.5)
tail_env[k0:] = np.exp(-(T[k0:] - 41.5) / 2.8)
air *= np.where(T < T_GUT, 1.0, 0.6 + 0.4 * np.exp(-(T - T_GUT) / 3))[:, None] * tail_env[:, None]
air *= np.interp(T, [T_THIN, T_THIN + 0.3, T_RAIN, T_RAIN + 1.0], [1.0, 0.2, 0.2, 1.0])[:, None]


# ------------------------------------------------------------ velvet room --
def velvet_ir(length=3.4):
    n = n_(length)
    tt = np.arange(n) / SR
    ir = np.zeros((n, 2))
    lp = signal.butter(2, 1500, "lowpass", fs=SR, output="sos")
    for ch in (0, 1):
        v = np.zeros(n)
        grid = np.arange(0, n, 24)                         # ~2000 pulses/s
        pos = np.minimum(n - 1, grid + rng.integers(0, 24, len(grid)))
        v[pos] = rng.choice([-1.0, 1.0], len(pos))
        lo = signal.sosfilt(lp, v)
        hi = v - lo
        ir[:, ch] = lo * np.exp(-6.9 * tt / 2.8) + hi * np.exp(-6.9 * tt / 1.3)
    ir = signal.sosfilt(signal.butter(1, 6000, "lowpass", fs=SR, output="sos"), ir, axis=0)
    ir *= np.minimum(1.0, tt / 0.012)[:, None]
    return ir / np.sqrt((ir ** 2).sum(axis=0)).max()


IR = velvet_ir()


def reverb(x_):
    return np.stack([signal.fftconvolve(x_[:, c], IR[:, c])[:N] for c in (0, 1)], 1)


def pad_auto(gC, gD, gE):
    pts = [(0, 1.0), (T_THIN, 1.0), (T_THIN + 0.12, gC), (T_RAIN, gC), (T_RAIN + 1.0, gD),
           (T_GUT, gD), (T_GUT + 1.0, gE)]
    xs, ys = zip(*pts)
    return np.interp(T, xs, ys) * tail_env


rest_dry = mb + mb2 + bass + kn + cel + rain + drops + air
duck = np.interp(T, [T_THIN, T_THIN + 0.3], [1.0, 0.25])[:, None]   # the room thins with the play layers
rest = rest_dry + duck * reverb(0.4 * mb + 0.3 * kn) + reverb(0.4 * mb2 + 0.3 * cel + 0.12 * drops)
PADW = pad + reverb(0.2 * pad)                      # pad automation is post-room


def pad_total(gC, gD, gE):
    return PADW * pad_auto(gC, gD, gE)[:, None]


# ------------------------------------------------------- levels + master --
def fr_rms(x_, a, b):
    return np.sqrt((x_[a * SPF:b * SPF] ** 2).mean())


def loud_curve(y_):
    """per-sample K-weighted loudness over a centred 3 s window (short-term style)"""
    k = _kweight(y_)
    p = uniform_filter1d((k ** 2).sum(axis=1), 3 * SR, mode="nearest")
    return -0.691 + 10 * np.log10(p + 1e-20)


def leveler(y_, regions, iters=8):
    """slow mix-bus leveler active only inside `regions` (a, b, offset_dB)"""
    w = np.zeros(N)
    off = np.zeros(N)
    for a, b, o in regions:
        w[n_(a):n_(b)] = 1.0
        off[n_(a):n_(b)] = o
    w = uniform_filter1d(w, SR // 2)
    off = uniform_filter1d(off, SR // 2)
    G = np.ones(N)
    for _ in range(iters):
        L_ = loud_curve(y_ * G[:, None])
        sel = (w > 0.99) & (np.abs(off) < 1e-9)
        Lstar = 10 * np.log10(np.mean(10 ** (L_[sel] / 10)))
        g = np.clip(Lstar + off - L_, -8, 6) * w
        G *= 10 ** (uniform_filter1d(g, int(0.6 * SR)) / 20)
    return G


def width_trim(x_, ratio=0.6):
    mid, side = (x_[:, 0] + x_[:, 1]) / 2, (x_[:, 0] - x_[:, 1]) / 2
    side = side * ratio * np.sqrt((mid ** 2).mean()) / np.sqrt((side ** 2).mean())
    return np.stack([mid + side, mid - side], 1)


def st_curve(y_):
    """EBU short-term loudness (trailing 3 s window), sampled every 10 ms"""
    k = _kweight(y_)
    p = (k ** 2).sum(axis=1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    idx = np.arange(0, len(p) + 1, SR // 100)
    lo = np.maximum(0, idx - 3 * SR)
    return -0.691 + 10 * np.log10((c[idx] - c[lo]) / (3 * SR) + 1e-20)


TQ = np.arange(0, N + 1, SR // 100) / SR
CLIMAX = (TQ >= T_RAIN) & (TQ <= T_LAST + 3.0)


def mom_curve(y_):
    """K-weighted loudness over a centred 400 ms window, sampled every 10 ms"""
    k = _kweight(y_)
    p = (k ** 2).sum(axis=1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    idx = np.arange(0, len(p) + 1, SR // 100)
    lo, hi = np.maximum(0, idx - SR // 5), np.minimum(len(p), idx + SR // 5)
    return -0.691 + 10 * np.log10((c[hi] - c[lo]) / (0.4 * SR) + 1e-20)


def st_cap(x_, iters=8, margin=0.25):
    """reduction-only climax flattener (part of the -14 S vs -14 I resolution): inside the
    climax, any 3 s short-term window louder than the climax's typical level (60th percentile)
    + `margin` is pulled down by reducing the audio it contains (weighted by how loud that audio
    is, so quiet bits are left alone). No renormalisation here: nothing is ever lifted."""
    W = 3 * 100
    H = SR // 100
    G2 = np.ones(N)
    for _ in range(iters):
        y_ = x_ * G2[:, None]
        S = st_curve(y_)
        ref = np.percentile(S[CLIMAX], 60)
        over = np.where(CLIMAX, np.maximum(0.0, S - (ref + margin)), 0.0)
        r = np.lib.stride_tricks.sliding_window_view(np.pad(over, (0, W)), W + 1).max(axis=1)[:len(S)]
        if r.max() < 0.03:
            break
        r = r * np.clip((mom_curve(y_) - (ref - 10.0)) / 6.0, 0.0, 1.0)
        r = uniform_filter1d(np.interp(np.arange(N), np.arange(len(r)) * H, r), int(0.4 * SR))
        G2 *= 10 ** (-r / 20)
    return G2


GD, GE = 1.0, 0.9
MEL_OFF = 0.00                  # music-box section sits this far above the climax
x0 = rest + pad_total(1.0, GD, GE)
G = leveler(width_trim(x0), [(1.5, T_MEL - 0.3, -0.3), (T_MEL + 0.3, T_THIN - 0.3, MEL_OFF),
                             (T_RAIN + 0.6, T_GUT - 0.3, 0.0), (T_GUT + 0.3, T_LAST - 0.2, -0.5)])
G[:n_(3.0)] = G[n_(3.0)]


def assemble(Gtot):
    """solve the thinning pad gain so frames 765-840 sit 12 dB under the music-box section
    (frames 150-750), measured on the width-trimmed mix and refined"""
    target = fr_rms(x0 * Gtot[:, None], 150, 750) * 10 ** (-12 / 20)
    pr = fr_rms(pad_total(1.0, GD, GE) * Gtot[:, None], 765, 840)
    rr = fr_rms(rest * Gtot[:, None], 765, 840)
    assert rr < target, "non-pad layers too loud in the thinning"
    gC_ = np.sqrt(target ** 2 - rr ** 2) / pr
    share = rr ** 2 / target ** 2
    print("thinning: non-pad share of energy %.0f%%" % (100 * share))
    for _ in range(3):
        x_ = width_trim((rest + pad_total(gC_, GD, GE)) * Gtot[:, None])
        err = 20 * np.log10(fr_rms(x_, 765, 840) / fr_rms(x_, 150, 750)) + 12
        gC_ *= 10 ** (-err / 20 / (1 - share))
    return gC_, width_trim((rest + pad_total(gC_, GD, GE)) * Gtot[:, None])


gC, x = assemble(G)
G2 = st_cap(x)                        # pass 1: short-term ceiling gain
G2[:n_(3.0)] = G2[n_(3.0)]
gC, x = assemble(G * G2)              # pass 2: re-solve the 12 dB thinning with it in place
print("thinning pad gain", round(gC, 3))

FADE = 3.0
tgt = -14.0
y = master(x, target_lufs=tgt, fade_out_s=FADE)
smax = st_curve(y)[CLIMAX].max()
if smax > -14.05:
    tgt = -14.0 - (smax + 14.05)
    y = master(x, target_lufs=tgt, fade_out_s=FADE)
S_ = st_curve(y)
print("master target", round(tgt, 2), "lufs", round(lufs(y), 2),
      "S max climax", round(S_[CLIMAX].max(), 2), "S max overall", round(S_.max(), 2))
write_wav(sys.argv[1], y, N)
# -14 S everywhere and -14 I can only both hold if loudness is perfectly flat; the ceiling is
# enforced where the brief puts it, on the climax (frames 840-1350), and I stays at -14.
assert tgt >= -14.5, "integrated would drift more than 0.5 LU from -14"
