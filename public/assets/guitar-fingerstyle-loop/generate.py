"""guitar-fingerstyle-loop: Opus Sound Directory

A 20-second seamless loop of intimate fingerstyle steel-string acoustic guitar in
D major at 96 BPM: eight bars of alternating-thumb picking, played in standard
tuning with every note on a real string and fret. A lightly palm-muted thumb keeps
a steady boom-chick bass on the low strings (with a thumb-over F# and a walking
turnaround), the fingers pinch an original melody on the top strings, and open
strings ring on as drones between the moving notes. Bars 1-4 state the theme in
first position over D, Bm7, G and Asus4-A; bars 5-8 answer it up the neck over
open-string bass, peak on a hammered-on high E in bar 6, drop back to first
position with a pull-off, and turn around on A7sus4-A7 while the thumb walks
B-C# straight back into the opening D. A light thumb knock on the top marks beats 2
and 4, and two soft wound-string squeaks give away the position shifts. Each
string is a two-polarisation digital waveguide (loop low-pass, stiffness allpasses,
fractional tuning) plucked with a shaped flesh-and-nail impulse at a varying point
along the string, every string can only sound one note at a time, and all of them
drive one modelled guitar body (air and top-plate resonances near 100 and 200 Hz
plus a dense wooden mode field), picked up by a close stereo pair in a small warm
room. Rendered circularly so the last sample flows back into the first.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 96203
DURATION_SEC = 20
BPM = 96
KEY = "D major"
FPS = 30
CUE_FRAMES = (0,)              # loop top: thumb + melody pinch on sample 0
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0
SEAM_MAX_MS = 1.5              # the loop seam may sit up to 1.5 ms ahead of the downbeat (cue tolerance 5 ms)

SR = SAMPLE_RATE
N = DURATION_SEC * SR          # one loop cycle
CYC = 3                        # cycles rendered; the middle one is kept
BEAT = 60.0 / BPM              # 0.625 s
BAR = 4 * BEAT                 # 2.5 s; 8 bars = 20 s
SWING = 0.535                  # off-beat eighth lands at 53.5 % of the beat (barely lazy)

OPEN = {6: 40, 5: 45, 4: 50, 3: 55, 2: 59, 1: 64}   # standard tuning, MIDI

rng = np.random.default_rng(SEED)


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0) -> None:
    """Mix a snippet into the CYC-cycle bus at loop time t, once per cycle, so every
    event and its tail repeats identically and wraps across the loop point."""
    t = t % DURATION_SEC
    for k in range(CYC):
        s = int(round(t * SR)) + k * N
        if s >= len(bus):
            continue
        e = min(len(bus), s + len(x))
        bus[s:e] += gain * x[: e - s]


def sos_filter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def peaking_eq(x, f0, gain_db, q):
    """RBJ cookbook peaking biquad."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * a_, -2 * np.cos(w0), 1 - alpha * a_]
    a = [1 + alpha / a_, -2 * np.cos(w0), 1 - alpha / a_]
    return signal.lfilter(b, a, x, axis=0)


def shelf(x, f0, gain_db, high=True):
    """RBJ cookbook shelving biquad (S = 1)."""
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    al = np.sin(w0) / 2 * np.sqrt(2)
    c = np.cos(w0)
    sA = 2 * np.sqrt(A) * al
    if high:
        b = [A * ((A + 1) + (A - 1) * c + sA), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sA)]
        a = [(A + 1) - (A - 1) * c + sA, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sA]
    else:
        b = [A * ((A + 1) - (A - 1) * c + sA), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sA)]
        a = [(A + 1) + (A - 1) * c + sA, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sA]
    return signal.lfilter(b, a, x, axis=0)


def one_pole_lp(x, fc):
    p = np.exp(-2 * np.pi * fc / SR)
    return signal.lfilter([1 - p], [1, -p], x)


# ---------------------------------------------------------------- the string
def waveguide(f0: float, exc: np.ndarray, t60: float, p_loss: float, disp: float, n_disp: int) -> np.ndarray:
    """Extended Karplus-Strong string: y[n] = x[n] + (G * y)[n - M], where the loop
    filter G = one-pole loss low-pass (frequency-dependent decay) x n_disp first-order
    allpasses (stiffness: higher partials travel faster, so they come out slightly
    sharp) x a fractional-delay allpass that tunes the loop to exactly SR/f0.
    Processed in blocks of M samples so each block only needs the previous one."""
    P = SR / f0
    g = 10 ** (-3.0 / (t60 * f0))
    b = np.array([g * (1 - p_loss)])
    a = np.array([1.0, -p_loss])
    for _ in range(n_disp):
        b = np.convolve(b, [disp, 1.0])
        a = np.convolve(a, [1.0, disp])
    w0 = 2 * np.pi * f0 / SR
    _, h = signal.freqz(b, a, worN=[w0])
    pd = -np.angle(h[0]) / w0
    D = P - pd
    M = int(np.floor(D - 0.5))
    d = D - M
    c = (1 - d) / (1 + d)
    for _ in range(3):                               # refine the allpass on its exact phase delay at f0
        _, ha = signal.freqz([c, 1.0], [1.0, c], worN=[w0])
        err = d - (-np.angle(ha[0]) / w0)
        d_t = (1 - c) / (1 + c) + err
        c = (1 - d_t) / (1 + d_t)
    b = np.convolve(b, [c, 1.0])
    a = np.convolve(a, [1.0, c])
    n = len(exc)
    y = np.zeros(n)
    zi = np.zeros(len(a) - 1)
    v = np.zeros(M)
    for s in range(0, n, M):
        e = min(n, s + M)
        yb = exc[s:e] + v[: e - s]
        y[s:e] = yb
        v, zi = signal.lfilter(b, a, yb, zi=zi)
    return y


STRING_T60 = {1: 3.6, 2: 4.2, 3: 5.0, 4: 6.0, 5: 6.5, 6: 7.0}


def pluck(string: int, fret: int, dur: float, vel: float, role: str, legato: bool = False,
          legato_out: bool = False, muted: bool = True) -> np.ndarray:
    """One plucked note on a given string/fret, with its own release when the string is
    stopped (re-plucked, lifted or palm-damped). Two polarisations: a louder one that
    couples strongly to the top and dies sooner, a weaker, slightly sharper one that
    rings longer, which gives the two-stage decay and slow shimmer of a steel string."""
    midi = OPEN[string] + fret
    f0 = hz(midi)
    P = SR / f0
    rel = 0.006 if legato_out else (0.05 if role == "thumb" else 0.03)
    n = int(round((dur + rel) * SR))
    n = max(n, int(0.08 * SR))
    t = np.arange(n) / SR

    # --- excitation: flesh pulse (+ a little nail), low-passed, combed by the pluck point
    if role == "thumb":
        width, lp, nail, beta = 0.7, 1500.0, 0.08, 0.20
    elif role == "mel":
        width, lp, nail, beta = 0.18, 7000.0, 0.55, 0.14
    else:                                            # fills / pinch partners: softer fingertip
        width, lp, nail, beta = 0.3, 3600.0, 0.25, 0.16
    if legato:                                       # hammer-on / pull-off: no pluck, the string is set going by the fret
        width, lp, nail, beta = 1.1, 1400.0, 0.0, 0.32
    beta = beta + rng.uniform(-0.025, 0.025)
    lp *= 0.65 + 0.5 * vel
    w = max(4, int(width * 1e-3 * SR))
    ex = np.zeros(n)
    ex[:w] = np.hanning(w + 2)[1:-1]
    ex = one_pole_lp(ex, lp)
    nz = rng.standard_normal(n) * np.exp(-t / 0.0007) * (1 - np.exp(-t / 0.00012))
    nz = sos_filter(nz, "bandpass", [1800, 7500], order=2)
    ex = ex / (np.abs(ex).max() + 1e-12) + nail * nz / (np.abs(nz).max() + 1e-12)
    sh = max(1, int(round(beta * P)))
    exc = ex.copy()
    exc[sh:] -= ex[:-sh]                             # pluck-position comb: |sin(n pi beta)| on partial n

    # --- loss / stiffness per string
    t60 = STRING_T60[string] * (1.35 if fret == 0 else 1.0)
    p_loss = 0.05 + 0.01 * string
    if role == "thumb" and muted:                    # light palm mute on the thumb bass
        t60, p_loss = 0.75, 0.36
    elif role == "thumb":                            # palm lifted: the open bass strings drone under the high melody
        t60, p_loss = 2.4, 0.22
    disp, nd = (-0.45, 6) if string >= 4 else (-0.35, 3)
    pol1 = waveguide(f0, exc, t60 * 0.6, p_loss, disp, nd)
    pol2 = waveguide(f0 * 2 ** (0.7 / 1200), exc, t60 * 1.5, p_loss * 0.85, disp, nd)
    y = 0.68 * pol1 + 0.32 * pol2
    y /= np.sqrt(np.mean(y[: int(0.08 * SR)] ** 2)) * 3.0 + 1e-12   # level by energy, not by the spikiest sample

    # --- release: finger/palm stops the string
    nd_ = int(round(dur * SR))
    nr = n - nd_
    if nr > 0:
        y[nd_:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    y[: max(2, int(0.0002 * SR))] *= np.linspace(0, 1, max(2, int(0.0002 * SR)))
    return y * vel


def knock(vel: float) -> np.ndarray:
    """Thumb knock on the top beside the soundhole: a soft force pulse (drives the body's
    low modes) plus a little muted-string slap from the thumb brushing the bass strings."""
    t = tt(0.06)
    w = int(0.0032 * SR)
    f = np.zeros(len(t))
    f[:w] = np.hanning(w + 2)[1:-1]
    f -= np.concatenate([np.zeros(int(0.0045 * SR)), f[: len(t) - int(0.0045 * SR)]])   # top rebound: no net push
    slap = sos_filter(rng.standard_normal(len(t)), "bandpass", [350, 2600], order=2)
    slap *= (1 - np.exp(-t / 0.0004)) * np.exp(-t / 0.006)
    y = 1.0 * f + 0.5 * slap / (np.abs(slap).max() + 1e-12)
    return sos_filter(y, "highpass", 60, order=2) * vel


def squeak(dur: float, f_peak: float, vel: float) -> np.ndarray:
    """Fingertip sliding along a wound string: a scrape whose pitch is set by how fast
    the finger crosses the windings, so it rises and falls with the hand's speed.
    Band-limited additive harmonics of that sweeping rate, plus a little rasp."""
    t = tt(dur)
    u = t / dur
    f = 380 + f_peak * np.sin(np.pi * u) ** 0.8
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros(len(t))
    for k in range(1, 6):
        y += np.clip((9000 - k * f) / 1500, 0, 1) * np.sin(k * ph + rng.uniform(0, 6.28)) / k ** 1.2
    y += 0.35 * sos_filter(rng.standard_normal(len(t)), "bandpass", [1500, 6000], order=2) * 0.3
    env = np.sin(np.pi * u) ** 1.6 * (0.6 + 0.4 * np.sin(np.pi * u * 3) ** 2)
    y = sos_filter(y * env, "bandpass", [700, 7000], order=2)
    return y / (np.abs(y).max() + 1e-12) * vel


# ---------------------------------------------------------------- body + room
def body_irs() -> np.ndarray:
    """Stereo body+mic impulse response: the bridge force excites decaying modes
    (Helmholtz air ~102 Hz, top plate ~198 Hz, back ~232 Hz, higher plate modes at
    390/520 Hz, then a dense wooden mode field to ~7 kHz). Mic L sits by the 12th fret
    (more string, less boom), mic R faces the lower bout (more body)."""
    t = tt(0.35)
    low = [(102, 0.075, 0.8), (198, 0.048, 0.85), (232, 0.036, 0.35), (392, 0.026, 0.45),
           (520, 0.02, 0.32), (690, 0.016, 0.22)]
    nh = 70
    fh = np.exp(rng.uniform(np.log(750), np.log(7200), nh))
    qh = rng.uniform(22, 55, nh)
    ah = (fh / 750) ** -0.45 * rng.lognormal(0, 0.45, nh) * 0.28
    irs = []
    for ch, (direct, lowg, delay) in enumerate(((0.5, 0.75, 0.0), (0.38, 1.0, 0.00006))):
        ir = np.zeros(len(t))
        for f, tau, a in low:
            ir += lowg * a * np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
        mix = rng.lognormal(0, 0.2, nh)              # each mic hears the high modes a little differently
        for f, q, a, m in zip(fh, qh, ah, mix):
            ir += a * m * np.sin(2 * np.pi * f * t) * np.exp(-t * np.pi * f / q)
        ir *= 0.05
        ir[0] += direct
        ds = int(round(delay * SR))
        ir = np.concatenate([np.zeros(ds), ir])[: len(t)]
        irs.append(ir)
    irs = np.stack(irs, axis=1)
    irs = irs @ np.array([[0.78, 0.22], [0.22, 0.78]])   # near-coincident pair: each mic hears some of the other's view
    irs = sos_filter(irs, "lowpass", 14000, order=2)
    return irs / np.sqrt((irs ** 2).sum(axis=0).mean())


def room(x: np.ndarray) -> np.ndarray:
    """Small warm room: a few early reflections then a soft, dark noise tail (RT60 ~0.55 s)."""
    rt = 0.55
    t = tt(rt * 1.2)
    out = []
    for ch in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [220, 5200], order=2)
        ir *= np.exp(-6.9 * t / rt) * (1 - np.exp(-t / 0.012))
        ir = ir / np.sqrt((ir ** 2).sum()) * 0.8
        for d_ms, gdb in ((3.1 + ch * 0.9, -6), (5.7 - ch * 0.6, -8), (8.9 + ch * 1.3, -10), (12.4, -12)):
            ir[int(d_ms * 1e-3 * SR)] += 10 ** (gdb / 20)
        ir = np.concatenate([np.zeros(int(0.004 * SR)), ir])
        out.append(signal.fftconvolve(x[:, ch], ir)[: len(x)])
    return np.stack(out, axis=1)


# ---------------------------------------------------------------- loudness / peak
def k_weight(x: np.ndarray) -> np.ndarray:
    """ITU-R BS.1770 K-weighting (48 kHz coefficients)."""
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def integrated_lufs(x: np.ndarray) -> float:
    """BS.1770-4 integrated loudness: 400 ms blocks, 75 % overlap, -70 LUFS abs + -10 LU rel gates."""
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    os = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os)) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 60.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak, with
    wrap-around windows so the kept middle cycle's gain curve is itself periodic."""
    ceil = 10 ** (ceiling_db / 20)
    os = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = os[: len(x) * 4].reshape(len(x), 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    L = int(look_ms * 1e-3 * SR)
    held = minimum_filter1d(need, size=2 * L + 1, mode="wrap")
    rc = np.exp(-1.0 / (rel_ms * 1e-3 * SR))
    g = np.empty_like(held)
    prev = 1.0
    for n, h in enumerate(held.tolist()):
        prev = min(h, prev * rc + (1 - rc))
        g[n] = prev
    g = uniform_filter1d(g, size=L + 1, mode="wrap")
    return x * g[:, None]


def compressor(x: np.ndarray, thresh_db: float, ratio: float, tau_det: float = 0.006,
               tau_gain: float = 0.08) -> np.ndarray:
    """Gentle program compressor (mono-linked RMS detector, smoothed gain), to even out
    the pluck transients the way a careful close-mic chain would."""
    p = np.exp(-1 / (tau_det * SR))
    e = signal.lfilter([1 - p], [1, -p], (x ** 2).mean(axis=1))
    lv = 10 * np.log10(e + 1e-12)
    over = np.maximum(0.0, lv - thresh_db)
    gdb = -over * (1 - 1 / ratio)
    q = np.exp(-1 / (tau_gain * SR))
    gdb = signal.lfilter([1 - q], [1, -q], gdb)
    return x * (10 ** (gdb / 20))[:, None]


def peak_shaver(x: np.ndarray, over_db: float, ratio: float, tau: float = 0.006) -> np.ndarray:
    """Transparent transient shaver: the gain is computed from the instantaneous peak
    above (loop RMS + over_db), held over 3 ms and smoothed forwards AND backwards, so
    it dips just before each nail attack and recovers within ~10 ms. No clipping and
    no long release pumping; runs on the periodic buffer with wrap-around holds."""
    lv = 20 * np.log10(np.abs(x).max(axis=1) + 1e-9)
    thresh = 10 * np.log10(np.mean(mid_cycle(x) ** 2) * 2 + 1e-20) + over_db
    gdb = -np.maximum(0.0, lv - thresh) * (1 - 1 / ratio)
    gdb = minimum_filter1d(gdb, size=int(0.003 * SR) | 1, mode="wrap")
    q = np.exp(-1 / (tau * SR))
    gdb = signal.filtfilt([1 - q], [1, -q], gdb)
    return x * (10 ** (gdb / 20))[:, None]


def mid_cycle(x: np.ndarray) -> np.ndarray:
    return x[N:2 * N]


def master(mix: np.ndarray) -> np.ndarray:
    """Normalise the kept cycle to TARGET_LUFS; limit the whole periodic buffer."""
    gain_db = TARGET_LUFS - integrated_lufs(mid_cycle(mix))
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(mid_cycle(y))
        if abs(err) < 0.03:
            break
        gain_db += err
    # Loop point: like trimming a recorded loop, put the seam on the quietest sample (a zero
    # crossing of the ringing tails) at most SEAM_MAX_MS ahead of the downbeat, so the
    # loop-top pinch lands r samples (<= 1.5 ms) into the file and the wrap stays click-free.
    rmax = int(SEAM_MAX_MS * 1e-3 * SR)
    cand = np.abs(y[N - rmax:N + 1]).max(axis=1)[::-1]        # cand[r] = |y[N - r]|
    r = int(np.argmin(cand))
    y = y[N - r:2 * N - r]
    print(f"loop seam {r} samples ({r / SR * 1e3:.2f} ms) ahead of the downbeat")
    return y - y.mean(axis=0)          # constant offset only, so the loop seam is untouched


# ---------------------------------------------------------------- the arrangement
# Per bar: thumb (string, fret) on beats 1-4; fill frets (string 3, string 2) for each
# half-bar; melody (slot, string, fret, velocity, technique). Slots are eighths 0-7,
# fractional slots are sixteenth graces. 'h' = hammer-on, 'p' = pull-off.
BARS = [
    dict(name="D", thumb=[(4, 0), (5, 0), (6, 2), (5, 0)], fills=[(2, 3), (2, 3)],
         mel=[(0, 1, 2, 1.05, ""), (2.5, 1, 3, 0.62, ""), (3, 1, 5, 0.8, "h"), (5, 1, 2, 0.7, ""),
              (6, 1, 0, 0.78, "")]),
    dict(name="Bm7", thumb=[(5, 2), (4, 0), (6, 2), (4, 0)], fills=[(2, 0), (2, 0)],
         mel=[(0, 2, 3, 0.85, ""), (2, 1, 0, 0.7, ""), (3, 1, 2, 0.9, ""), (5, 1, 0, 0.66, ""),
              (6, 2, 3, 0.74, "")]),
    dict(name="G", thumb=[(6, 3), (4, 0), (5, 2), (4, 0)], fills=[(0, 3), (0, 3)],
         mel=[(0, 1, 3, 0.95, ""), (2, 1, 5, 0.8, ""), (3, 1, 3, 0.74, ""), (4, 1, 2, 0.8, ""),
              (6, 1, 0, 0.72, "")]),
    dict(name="Asus4-A", thumb=[(5, 0), (4, 2), (6, 0), (4, 2)], fills=[(2, 3), (2, 2)],
         mel=[(0, 1, 5, 0.86, ""), (2, 1, 2, 0.74, ""), (3, 1, 0, 0.7, ""), (4, 2, 3, 0.76, ""),
              (5, 2, 2, 0.66, "p"), (7, 1, 5, 0.82, "")]),
    dict(name="D hi", open_bass=True, thumb=[(4, 0), (5, 0), (4, 0), (5, 0)], fills=[(7, 7), (7, 7)],
         mel=[(0, 1, 10, 1.0, ""), (3, 1, 9, 0.82, ""), (4, 1, 7, 0.86, ""), (5, 1, 9, 0.72, "h"),
              (6, 2, 10, 0.8, "")]),
    dict(name="Em7 hi", open_bass=True, thumb=[(6, 0), (4, 0), (5, 7), (4, 0)], fills=[(7, 8), (7, 8)],
         mel=[(0, 1, 7, 0.9, ""), (2, 1, 10, 0.92, ""), (3, 1, 12, 0.98, "h"), (5, 1, 10, 0.82, ""),
              (6, 1, 7, 0.8, ""), (7, 2, 8, 0.7, "")]),
    dict(name="G", thumb=[(6, 3), (4, 0), (5, 2), (4, 0)], fills=[(0, 0), (0, 0)],
         mel=[(0, 1, 5, 0.86, ""), (1, 1, 3, 0.7, "p"), (3, 1, 2, 0.76, ""), (4, 1, 3, 0.8, ""),
              (6, 1, 0, 0.74, ""), (7, 2, 3, 0.68, "")]),
    dict(name="A7sus4-A7", thumb=[(5, 0), (4, 2), (5, 0), (5, 2)], fills=[(0, 3), (0, 2)],
         mel=[(0, 1, 0, 0.8, ""), (2, 2, 3, 0.76, ""), (3, 2, 2, 0.64, "p"), (5, 3, 2, 0.6, ""),
              (6, 1, 0, 0.74, ""), (7, 2, 3, 0.72, "")],
         extra_thumb=[(7, 5, 4)]),                   # C# on the 4-and walks into the top D
]
BAR_DYN = [0.88, 0.86, 0.9, 0.92, 1.03, 1.07, 0.9, 0.91]
# chord shapes (string -> fret) per half-bar, used to decide when the left hand stops a string
SHAPES = [
    ({6: 2, 5: 0, 4: 0, 3: 2, 2: 3},) * 2,
    ({6: 2, 5: 2, 4: 0, 3: 2, 2: 0},) * 2,
    ({6: 3, 5: 2, 4: 0, 3: 0, 2: 3},) * 2,
    ({6: 0, 5: 0, 4: 2, 3: 2, 2: 3}, {6: 0, 5: 0, 4: 2, 3: 2, 2: 2}),
    ({5: 0, 4: 0, 3: 7, 2: 7},) * 2,
    ({6: 0, 5: 7, 4: 0, 3: 7, 2: 8},) * 2,
    ({6: 3, 5: 2, 4: 0, 3: 0, 2: 0},) * 2,
    ({5: 0, 4: 2, 3: 0, 2: 3}, {5: 0, 4: 2, 3: 0, 2: 2}),
]
SHIFTS = [4 * BAR - 0.07, 6 * BAR - 0.07]           # left hand changes position (all fretted notes stop)
SQUEAKS = [(4 * BAR - 0.19, 0.14, 1900, 1.0), (6 * BAR - 0.17, 0.11, 1500, 0.6)]


def slot_time(bar: int, slot: float) -> float:
    def st(k: int) -> float:
        beat, off = divmod(k, 2)
        return (beat + SWING * off) * BEAT
    k = int(np.floor(slot))
    fr = slot - k
    t = st(k) if fr == 0 else st(k) + fr * (st(k + 1) - st(k))
    return bar * BAR + t


def build_events() -> list[dict]:
    ev = []
    for b, bar in enumerate(BARS):
        dyn = BAR_DYN[b]
        for i, (s, f) in enumerate(bar["thumb"]):
            jit = 0.0 if (b == 0 and i == 0) else float(np.clip(rng.normal(0, 0.0035), -0.007, 0.007))
            v = (0.8 if i % 2 == 0 else 0.72) * rng.uniform(0.94, 1.04) * (0.6 + 0.4 * dyn)
            ev.append(dict(t=slot_time(b, 2 * i) + jit, s=s, f=f, v=v * (0.85 if bar.get("open_bass") else 1.0),
                           role="thumb", tech="", muted=not bar.get("open_bass", False)))
        for sl, s, f in bar.get("extra_thumb", []):
            ev.append(dict(t=slot_time(b, sl) + rng.normal(0, 0.003), s=s, f=f, v=0.84 * dyn, role="thumb", tech=""))
        mel_slots = []
        for sl, s, f, v, tech in bar["mel"]:
            lag = 0.004 + float(np.clip(rng.normal(0, 0.006), -0.012, 0.012))
            if b == 0 and sl == 0:
                lag = 0.0                            # the loop-top pinch lands on sample 0
            if tech:
                lag = 0.006 + float(np.clip(rng.normal(0, 0.004), -0.008, 0.008))
            ev.append(dict(t=slot_time(b, sl) + lag, s=s, f=f, v=v * dyn * rng.uniform(0.95, 1.03), role="mel",
                           tech=tech))
            mel_slots.append((sl, s))
        # beat-1 pinch partner on string 3 (unless the melody is there)
        f3 = bar["fills"][0][0]
        if not any(abs(sl) < 0.01 and s == 3 for sl, s in mel_slots):
            ev.append(dict(t=slot_time(b, 0) + 0.007 + rng.uniform(0, 0.004), s=3, f=f3, v=0.46 * dyn,
                           role="fill", tech=""))
        # off-beat fills on strings 2/3 where the melody rests
        for sl in (1, 3, 5, 7):
            if any(abs(ms - sl) < 0.6 for ms, _ in mel_slots):
                continue
            want = 2 if sl in (1, 5) else 3
            recent = [s for ms, s in mel_slots if 0 < sl - ms <= 1.5]
            if recent and recent[-1] == want:
                want = 5 - want
            half = 0 if sl < 4 else 1
            f = bar["fills"][half][0 if want == 3 else 1]
            ev.append(dict(t=slot_time(b, sl) + float(np.clip(rng.normal(0.003, 0.006), -0.01, 0.014)), s=want,
                           f=f, v=rng.uniform(0.44, 0.56) * dyn, role="fill", tech=""))
    return sorted(ev, key=lambda e: e["t"])


def note_ends(ev: list[dict]) -> None:
    """Each string sounds one note at a time. A note stops at the next event on its
    string (circularly), when the chord shape re-frets or lifts that string, or at a
    position shift if it is fretted."""
    T = DURATION_SEC
    HB = BAR / 2
    for e in ev:
        te = e["t"] % T
        same = [(x["t"] % T, x) for x in ev if x["s"] == e["s"] and x is not e]
        nxt_t, nxt = min((((tx if tx > te else tx + T), x) for tx, x in same), key=lambda q: q[0]) \
            if same else (te + T, None)
        end, legato = nxt_t, bool(nxt is not None and nxt["tech"])
        if e["s"] != 1:                              # chord-shape changes on the lower five strings
            hb = int(te // HB)
            for k in range(1, 17):
                bt = (hb + k) * HB
                if bt >= end:
                    break
                fr = SHAPES[((hb + k) % 16) // 2][(hb + k) % 2].get(e["s"])
                if fr is not None and fr != e["f"]:
                    end, legato = bt + 0.012, False
                    break
        if e["f"] > 0:                               # fretted notes stop when the hand shifts position
            for sh in SHIFTS:
                sa = sh if sh > te else sh + T
                if sa < end:
                    end, legato = sa, False
        e["dur"] = min(end - te, 7.0)
        e["legato_out"] = legato


def render() -> np.ndarray:
    L = CYC * N
    bridge = np.zeros(L)                             # mono force at the bridge: every string drives the same top
    direct = np.zeros((L, 2))                        # things the close mics hear straight off the strings
    ev = build_events()
    note_ends(ev)
    role_gain = {"thumb": 0.36, "fill": 0.36, "mel": 0.82}
    for e in ev:
        # if the next note on this string is a hammer/pull, the old pitch hands straight over (6 ms)
        y = pluck(e["s"], e["f"], e["dur"], e["v"], e["role"], legato=bool(e["tech"]), legato_out=e["legato_out"],
                  muted=e.get("muted", True))
        place(bridge, y, e["t"], role_gain[e["role"]])
        if e["role"] == "thumb":                     # flesh on a wound string: a whisper of winding noise
            nz = sos_filter(rng.standard_normal(int(0.03 * SR)), "bandpass", [2200, 6500], order=2)
            tn = np.arange(len(nz)) / SR
            nz *= (1 - np.exp(-tn / 0.0006)) * np.exp(-tn / 0.006) * 0.012 * e["v"]
            place(direct, np.stack([nz * 0.8, nz * 1.1], 1), e["t"])

    # thumb knocks on beats 2 and 4, just ahead of the bass note
    for b in range(8):
        for beat in (1, 3):
            v = rng.uniform(0.85, 1.05) * (0.9 + 0.1 * BAR_DYN[b])
            place(bridge, knock(v), slot_time(b, 2 * beat) - 0.004, 0.15)

    for t0, dur, fpk, v in SQUEAKS:
        sq = squeak(dur, fpk, v) * 0.03
        place(direct, np.stack([sq * 1.0, sq * 0.65], 1), t0)

    # body + close stereo pair
    ir = body_irs()
    mics = np.stack([signal.fftconvolve(bridge, ir[:, c])[:L] for c in range(2)], axis=1)
    mics += direct
    mics = sos_filter(mics, "highpass", 55, order=2)
    mics = peaking_eq(mics, 95, -1.5, 1.0)          # keep the thumb and the air mode from booming
    mics = peaking_eq(mics, 300, -2.5, 1.0)         # take out the boxiness
    mics = peaking_eq(mics, 3500, 3.5, 0.8)         # presence / string definition
    mics = shelf(mics, 6000, 5.0, high=True)        # steel-string sparkle and air
    mics = compressor(mics, thresh_db=10 * np.log10(np.mean(mid_cycle(mics) ** 2) * 2) - 2, ratio=2.0)
    mics = peak_shaver(mics, over_db=9.0, ratio=3.0)

    wet = room(mics) * 0.22
    wet = sos_filter(wet, "highpass", 180, order=2)
    mix = mics + wet
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22, order=2)
    mix = sos_filter(mix, "lowpass", 15000, order=4)
    return mix


def main() -> None:
    y = master(render())
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP  "
          f"seam step {np.abs(f[0] - f[-1]).max():.4f}")


if __name__ == "__main__":
    main()
