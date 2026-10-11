"""--- 13. Dev-log build with breakdown and drop (id: devlog-build-drop-56s, category: drops, 56.0 s) ---

Output: one WAV, 48 kHz / 16-bit / stereo, exactly 2,688,000 samples (56.0 s at 30 fps = 1680 frames). Python + numpy/scipy only. Synthesise everything (no samples, no downloads, no speech). Fixed random seed (np.random.default_rng(55)). A 56-second 'how it was made' tech bed in F minor at 128 BPM (1 beat = 14.0625 frames). Frames 0-112: muted glitchy intro (bit-crushed 8 kHz, a terminal-cursor tick each beat). Frame 112: full groove: sub kick four-on-the-floor, off-beat sub bass gate (−7 dB pump), Fm9 → Dbmaj7 → Ebsus4 → Cm7 pluck chords, rolling 16th hats; energy flat for 32 bars at -20 dBFS RMS. Frames 1060-1200: gradual brightening, white-noise riser and snare roll accelerating 8ths → 32nds; loudness climbs 4 LU. Frame 1200: 3-beat breakdown to pad only, 20 dB quieter (a near-silence gasp). Frame 1252: re-entry with a downward sub drop (F2→F0 sine sweep 300 ms) and a crash; then 12 bars of the loudest section with bright bell arps (FM, 1/16) and 1/8 chord stabs. Frame 1650: quick fade to 0 by frame 1680. Keep true peak ≤ -1 dBTP even though the drop is loud. Master: -14 LUFS integrated, true peak <= -1 dBTP (4x oversampled peak check), last frames fade to exactly 0. You can't listen, so verify: measure loudness and true peak with ffmpeg ebur128 (peak=true), check the exact sample count, confirm the energy change lands on each cue frame, check every note fits the chord under it, render a spectrogram PNG and inspect it. Fix and re-render until every check passes, then report the numbers.

Take 1 approach: additive band-limited plucks (one chord per bar, syncopated 3-3-2 16th pattern) whose harmonic roll-off opens during the build; sine sub kick + sine bass with a smooth -7 dB beat-synchronous duck (off-beat swell); noise 16th hats; dark additive pad underneath. Intro = the Fm9 pluck pattern bit-crushed (8 kHz sample-and-hold, 6-bit) with random 1/16 stutter repeats and a clean C7 cursor blip per beat. Build = STFT white-noise riser 400 Hz -> 9 kHz + snare roll 8ths -> 16ths -> 32nds + gain ramp. Breakdown = Ebsus4 pad alone (dominant-like suspension into the drop). Drop = sub drop F2->F0, crash, FM bells (ratio 3.5) as up/down 1/16 arps, 1/8 bright stabs.
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
SPF = SR // FPS  # 1600 samples per frame
N = 2688000  # 56.0 s
BEAT = 22500  # 128 BPM -> 0.46875 s = 14.0625 frames
BAR = 4 * BEAT
S16 = BEAT // 4  # 5625 samples
F = lambda fr: int(round(fr * SPF))
G0 = F(112)  # groove downbeat
B0 = F(1060)  # build start
K0 = F(1200)  # breakdown
D0 = F(1252)  # drop re-entry
E0 = F(1650)  # fade start

F_MINOR = {5, 7, 8, 10, 0, 1, 3}  # F G Ab Bb C Db Eb
CHORDS = {  # name: (pitch-class set, mid voicing in MIDI)
    "Fm9": ({5, 8, 0, 3, 7}, [53, 56, 60, 63, 67]),
    "Dbmaj7": ({1, 5, 8, 0}, [49, 53, 56, 60]),
    "Ebsus4": ({3, 8, 10}, [51, 56, 58, 63]),
    "Cm7": ({0, 3, 7, 10}, [51, 55, 58, 60]),
}
PROG = ["Fm9", "Dbmaj7", "Ebsus4", "Cm7"]
ROOT = {"Fm9": 41, "Dbmaj7": 37, "Ebsus4": 39, "Cm7": 36}  # F2 Db2 Eb2 C2
NOTE_LOG = []  # (sample, midi, chord or None=scale) for the harmony assertion


def hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def log_note(s, m, chord):
    NOTE_LOG.append((int(s), float(m), chord))


def check_harmony():
    for s, m, ch in NOTE_LOG:
        pcs = F_MINOR if ch is None else CHORDS[ch][0]
        assert abs(m - round(m)) < 1e-9 and int(round(m)) % 12 in pcs, ("note outside chord/scale", s, m, ch)
    return len(NOTE_LOG)


def chord_in(t0, start, bars_per_chord=1):
    """Chord active at sample t0 for a progression that starts on Fm9 at `start`."""
    i = int((t0 - start) // (BAR * bars_per_chord))
    return PROG[i % 4]


def env_ar(n, a, r):
    e = np.ones(n)
    a, r = min(a, n // 2), min(r, n // 2)
    if a > 0:
        e[:a] = 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    if r > 0:
        e[n - r:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, r + 1) / r)
    return e


def place(buf, start, sig, gl=1.0, gr=1.0):
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
    th = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.cos(th), np.sin(th)


def seg_gate(n_total, s0, s1, ramp=96):
    """1 inside [s0, s1) with raised-cosine ramps (inside the segment), 0 elsewhere."""
    g = np.zeros(n_total)
    g[s0:s1] = env_ar(s1 - s0, ramp, ramp)
    return g


_PL = {}


def pluck(m, n, bright, tau=0.35, kmax=40):
    """Band-limited additive pluck: harmonic k amp 1/k * exp(-k f0 / bright), higher partials decay faster."""
    key = (m, n, int(bright // 100), int(tau * 1000))
    if key in _PL:
        return _PL[key]
    f0 = hz(m)
    K = int(min(kmax, 15000 // f0))
    k = np.arange(1, K + 1)[:, None]
    t = np.arange(n)[None, :] / SR
    amp = (1.0 / k) * np.exp(-k * f0 / bright)
    taus = tau / (1.0 + k * f0 / 1500.0)
    y = (amp * np.sin(2 * np.pi * f0 * k * t) * np.exp(-t / taus)).sum(axis=0)
    y = y / (np.abs(y).max() + 1e-12) * env_ar(n, 48, 480)
    _PL[key] = y
    return y


def kick(n=int(0.32 * SR), f_hi=150.0, f_lo=hz(29)):
    t = np.arange(n) / SR
    f = f_lo + (f_hi - f_lo) * np.exp(-t / 0.035)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
    return y * env_ar(n, 24, 960)


def hat(rng, n=int(0.05 * SR), fc=7500.0, tau=0.012):
    y = signal.sosfilt(signal.butter(4, fc, "highpass", fs=SR, output="sos"), rng.standard_normal(n))
    y = signal.sosfilt(signal.butter(2, 16000, "lowpass", fs=SR, output="sos"), y)
    return y / (np.abs(y).max() + 1e-12) * np.exp(-np.arange(n) / (tau * SR)) * env_ar(n, 24, 240)


def snare(rng, n, tau=0.06):
    t = np.arange(n) / SR
    nz = signal.sosfilt(signal.butter(2, [900, 9000], "bandpass", fs=SR, output="sos"), rng.standard_normal(n))
    nz /= np.abs(nz).max() + 1e-12
    body = np.sin(2 * np.pi * 185.0 * t) * np.exp(-t / 0.03)
    return (0.8 * nz * np.exp(-t / tau) + 0.6 * body) * env_ar(n, 24, min(480, n // 3))


def crash(rng, n=int(2.2 * SR)):
    t = np.arange(n) / SR
    nz = rng.standard_normal((n, 2))
    nz = signal.sosfilt(signal.butter(2, 3500, "highpass", fs=SR, output="sos"), nz, axis=0)
    nz = signal.sosfilt(signal.butter(2, 15000, "lowpass", fs=SR, output="sos"), nz, axis=0)
    nz /= np.abs(nz).max()
    return nz * (np.exp(-t / 0.7) * env_ar(n, 48, 4800))[:, None]


def sub_drop(n=int(0.3 * SR)):
    """F2 -> F0 exponential sine sweep over 300 ms, then a short F0 hold/decay tail."""
    tail = int(0.25 * SR)
    t = np.arange(n + tail) / SR
    f = np.where(t < 0.3, hz(41) * 0.25 ** (t / 0.3), hz(17))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR)
    e = np.where(t < 0.3, 1.0, np.exp(-(t - 0.3) / 0.08))
    return y * e * env_ar(n + tail, 48, 1200)


def fm_bell(m, n, index=2.2, ratio=3.5, tau=0.25):
    t = np.arange(n) / SR
    f0 = hz(m)
    I = index * np.exp(-t / (tau * 0.4))
    y = np.sin(2 * np.pi * f0 * t + I * np.sin(2 * np.pi * f0 * ratio * t)) * np.exp(-t / tau)
    return y * env_ar(n, 48, 480)


def pad_note(m, n, rng, detune=0.08, bright=1200.0):
    """Soft additive pad voice: 3 detuned copies of a dark harmonic stack."""
    t = np.arange(n) / SR
    f0 = hz(m)
    y = np.zeros(n)
    for d in (-detune, 0.0, detune):
        fd = f0 * 2 ** (d / 12)
        for k in range(1, 9):
            if fd * k < 12000:
                y += np.exp(-k * f0 / bright) / k * np.sin(2 * np.pi * fd * k * t + rng.uniform(0, 2 * np.pi))
    return y / (np.abs(y).max() + 1e-12)


def bitcrush(x, sr_target=8000, bits=6):
    """Sample-and-hold to 8 kHz + quantise, then a gentle low-pass ('muted')."""
    h = SR // sr_target
    idx = (np.arange(x.shape[0]) // h) * h
    y = x[idx]
    q = 2 ** (bits - 1)
    y = np.round(y * q) / q
    return signal.sosfilt(signal.butter(2, 3800, "lowpass", fs=SR, output="sos"), y, axis=0)


def stft_riser(rng, n, f_from, f_to, width_oct=0.6):
    """White noise with a log-Gaussian band gliding f_from -> f_to (exponential), stereo-decorrelated."""
    wn = rng.standard_normal((2, n))
    f, t, Z = signal.stft(wn, fs=SR, nperseg=2048)
    u = np.clip(t / (n / SR), 0, 1)
    fc = f_from * (f_to / f_from) ** u
    mask = np.exp(-0.5 * ((np.log2(f[:, None] + 1.0) - np.log2(fc[None, :])) / width_oct) ** 2)
    _, y = signal.istft(Z * mask[None], fs=SR, nperseg=2048)
    y = y[:, :n].T
    return y / (np.sqrt((y ** 2).mean()) + 1e-12)
# ------------------------------------------------------------- end helpers --

SEED = 55
rng = np.random.default_rng(SEED)
x = np.zeros((N, 2))

# ======================================================== intro (0 - 112)
intro = np.zeros((N, 2))
PAT = [0, 3, 6, 8, 11, 14]  # 16th positions in the bar
start_bar = G0 - 2 * BAR
for b in range(2):
    for p in PAT:
        s = start_bar + b * BAR + p * S16
        if s + S16 <= 0:
            continue
        for v, m in enumerate(CHORDS["Fm9"][1]):
            log_note(max(s, 0), m, "Fm9")
            place(intro, s, 0.12 * pluck(m, 12000, 3000.0), *pan(-0.4 + 0.2 * v))
# glitch: random 1/16 stutters (repeat the previous 16th slice)
for k in range(int(G0 // S16)):
    if rng.random() < 0.18:
        s = G0 - (k + 1) * S16
        if s - S16 >= 0:
            intro[s:s + S16] = intro[s - S16:s] * env_ar(S16, 48, 48)[:, None]
intro = bitcrush(intro, 8000, 6)
intro *= seg_gate(N, 0, G0, 96)[:, None]
x += 0.8 * intro
tb = np.arange(int(0.03 * SR)) / SR
cursor = (np.sin(2 * np.pi * hz(96) * tb) + 0.25 * np.sin(2 * np.pi * 3 * hz(96) * tb)) * np.exp(-tb / 0.006) * env_ar(len(tb), 24, 240)
for k in range(1, 8):
    s = G0 - k * BEAT
    log_note(s, 96, None)  # C7, in F minor scale
    place(x, s, 0.25 * cursor, *pan(0.15))

# ======================================================== groove + build (112 - 1200)
grv = np.zeros((N, 2))
t_all = np.arange(N)
ph = ((t_all - G0) % BEAT) / BEAT
duck_db = -7.0 * np.clip(1 - ph / 0.45, 0, 1) ** 1.5
tail = ph > 0.96
duck_db[tail] = -7.0 * (ph[tail] - 0.96) / 0.04
duck = 10 ** (duck_db / 20)  # -7 dB on the beat, full on the off-beat
duck_p = 10 ** (duck_db * 3 / 7 / 20)  # lighter -3 dB pump for plucks/pad
u_build = np.clip((t_all - B0) / (K0 - B0), 0, 1)

kk = kick()
hh = [hat(rng) for _ in range(6)]
nbars = int(np.ceil((K0 - G0) / BAR))
bass = np.zeros(N)
pad = np.zeros((N, 2))
for b in range(nbars):
    s0 = G0 + b * BAR
    ch = PROG[b % 4]
    voic = CHORDS[ch][1]
    # kick
    for q in range(4):
        place(grv, s0 + q * BEAT, 0.55 * kk)
    # bass (root + sub octave), continuous within the bar
    r = ROOT[ch]
    log_note(s0, r, ch)
    log_note(s0, r - 12, ch)
    tt = np.arange(BAR) / SR
    bn = (np.sin(2 * np.pi * hz(r) * tt) + 0.6 * np.sin(2 * np.pi * hz(r - 12) * tt)) * env_ar(BAR, 240, 240)
    e = min(N, s0 + BAR)
    bass[s0:e] += bn[:e - s0]
    # pad
    for v, m in enumerate(voic):
        log_note(s0, m + 12, ch)
        place(pad, s0, 0.05 * pad_note(m + 12, BAR, rng) * env_ar(BAR, 1440, 1440), *pan(-0.5 + v * 0.25))
    # plucks
    for p in PAT:
        s = s0 + p * S16
        if s >= K0:
            break
        br = 2500.0 + 9000.0 * u_build[s] ** 1.5
        vel = 0.8 + 0.2 * rng.random()
        for v, m in enumerate(voic):
            log_note(s, m, ch)
            pl = pluck(m, 14000, br)
            n_ = min(len(pl), N - s)
            place(grv, s, vel * 0.13 * pl[:n_] * duck_p[s:s + n_], *pan(-0.45 + 0.3 * v))
    # hats
    for q in range(16):
        s = s0 + q * S16
        if s >= K0:
            break
        acc = 1.0 if q % 4 == 2 else (0.55 if q % 2 else 0.4)
        g = acc * (0.16 + 0.1 * u_build[s])
        place(grv, s, g * hh[rng.integers(6)], *pan(0.25 if q % 2 else -0.1))
grv[:, 0] += 0.2 * bass * duck
grv[:, 1] += 0.2 * bass * duck
grv += pad * (0.6 + 0.4 * duck)[:, None]

# build: riser + snare roll + gain climb
nb = K0 - B0
ris = stft_riser(rng, nb, 400.0, 9000.0) * ((np.arange(nb) / nb) ** 2.2)[:, None]
place(grv, B0, 0.055 * ris)
k8 = int(np.ceil((B0 - G0) / (BEAT / 2)))
s = G0 + k8 * BEAT // 2
while s < K0 - 200:
    u = (s - B0) / nb
    step = BEAT // 2 if u < 0.4 else (BEAT // 4 if u < 0.7 else BEAT // 8)
    n_sn = min(int(step * 1.6), int(0.15 * SR))
    place(grv, s, (0.12 + 0.25 * u) * snare(rng, n_sn, tau=0.05 if step > BEAT // 8 else 0.025), *pan(0.05))
    s += step
grv *= (10 ** (2.5 * u_build ** 1.2 / 20))[:, None]
grv *= seg_gate(N, G0, K0, 144)[:, None]
x += grv

# ======================================================== breakdown (1200 - 1252)
brk = np.zeros((N, 2))
nk = D0 - K0
for v, m in enumerate(CHORDS["Ebsus4"][1]):
    log_note(K0, m + 12, "Ebsus4")
    place(brk, K0, pad_note(m + 12, nk, rng, bright=900.0) * env_ar(nk, 480, 480), *pan(-0.4 + 0.27 * v))
x += 0.055 * brk

# ======================================================== drop (1252 - end)
drp = np.zeros((N, 2))
place(drp, D0, 0.9 * sub_drop())
log_note(D0, 41, "Fm9")
log_note(D0, 17, "Fm9")
place(drp, D0, 0.22 * crash(rng))
nd = int(np.ceil((N - D0) / BAR))
bass = np.zeros(N)
for b in range(nd):
    s0 = D0 + b * BAR
    ch = PROG[b % 4]
    pcs, voic = CHORDS[ch]
    for q in range(4):
        if b == 0 and q == 0:
            continue  # the sub drop owns the downbeat
        place(drp, s0 + q * BEAT, 0.6 * kk)
    r = ROOT[ch]
    log_note(s0, r, ch)
    log_note(s0, r - 12, ch)
    tt = np.arange(BAR) / SR
    bn = (np.sin(2 * np.pi * hz(r) * tt) + 0.6 * np.sin(2 * np.pi * hz(r - 12) * tt)
          + 0.15 * np.sin(2 * np.pi * hz(r + 12) * tt)) * env_ar(BAR, 240, 240)
    e = min(N, s0 + BAR)
    bass[s0:e] += bn[:e - s0]
    for v, m in enumerate(voic):
        log_note(s0, m + 12, ch)
        place(drp, s0, 0.06 * pad_note(m + 12, BAR, rng, bright=1600.0) * env_ar(BAR, 1440, 1440), *pan(-0.5 + v * 0.25))
    # 1/8 stabs
    for q in range(8):
        s = s0 + q * BEAT // 2
        for v, m in enumerate(voic):
            log_note(s, m + 12, ch)
            place(drp, s, 0.09 * pluck(m + 12, 6000, 9000.0, tau=0.12), *pan(-0.4 + 0.27 * v))
    # 1/16 FM bell arp over chord tones in C5..C6
    tones = sorted({mm for mm in range(72, 85) if mm % 12 in pcs})
    seq = tones + tones[-2:0:-1]
    for q in range(16):
        s = s0 + q * S16
        m = seq[(b * 16 + q) % len(seq)]
        log_note(s, m, ch)
        place(drp, s, 0.12 * fm_bell(m, 14000), *pan(0.6 if q % 2 else -0.6))
    for q in range(16):
        s = s0 + q * S16
        acc = 1.0 if q % 4 == 2 else (0.6 if q % 2 else 0.45)
        place(drp, s, acc * 0.22 * hh[rng.integers(6)], *pan(0.25 if q % 2 else -0.1))
ph2 = ((t_all - D0) % BEAT) / BEAT
dd = -7.0 * np.clip(1 - ph2 / 0.45, 0, 1) ** 1.5
tl = ph2 > 0.96
dd[tl] = -7.0 * (ph2[tl] - 0.96) / 0.04
duck2 = 10 ** (dd / 20)
drp[:, 0] += 0.22 * bass * duck2
drp[:, 1] += 0.22 * bass * duck2
drp *= seg_gate(N, D0, N, 48)[:, None]
x += 1.5 * drp

n_notes = check_harmony()
y = master(x, target_lufs=-14.0, fade_out_s=1.0)
write_wav(sys.argv[1], y, N)
print("notes checked", n_notes)
