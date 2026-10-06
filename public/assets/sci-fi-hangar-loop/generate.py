"""sci-fi-hangar-loop: Opus Sound Directory

A 20-second seamless starship-hangar ambience centred on C#. The core is a deep,
mono engine hum (a C#1 sub and a C#2 harmonic stack with slow beating partials
and an idle throb) over a filtered mono rumble, with a faint wobbling turbine
whine riding above it. Two ventilation ducts breathe in stereo (resonant duct
hiss with fan-blade flutter). Around them the space speaks: distant metallic
clanks, a dropped-tool double clank, a chain rattle and a heavy bulkhead clang,
a loader arm's hydraulic servo and a pneumatic hiss, all thrown into a huge
metal hall with slap echoes and a long dark tail. Now and then a console nearby
chirps: glides, a telemetry burble, an acknowledge tone. The loop starts on a
soft clank at frame 0 and is rendered circularly: three identical cycles are
synthesised with every oscillator on a 0.05 Hz grid, tails, reverb and the
wrap-mode limiter run across them, and the middle cycle is kept, so the last
sample flows straight back into the first with no fade. Only the mono engine
core sits below 120 Hz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 141420
DURATION_SEC = 20
BPM = None
KEY = "C# (drone)"
FPS = 30
CUE_FRAMES = (0,)              # loop top: a soft distant clank on sample 0
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = DURATION_SEC * SR          # one loop cycle
CYC = 3                        # cycles rendered; the middle one is kept
L3 = CYC * N
GRID = 1.0 / DURATION_SEC      # 0.05 Hz: every continuous oscillator completes whole cycles per loop
DEBUG = bool(os.environ.get("HANGAR_DEBUG"))

rng = np.random.default_rng(SEED)
T3 = np.arange(L3) / SR        # time over the three cycles


# ---------------------------------------------------------------- utilities
def q(f: float) -> float:
    """Snap a frequency to the loop grid so it is exactly periodic over DURATION_SEC."""
    return round(f / GRID) * GRID


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def tt(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR))) / SR


def fade(x: np.ndarray, a: float = 0.001, r: float = 0.005) -> np.ndarray:
    x = x.copy()
    na, nr = min(len(x), max(1, int(a * SR))), min(len(x), max(1, int(r * SR)))
    shp = (-1,) + (1,) * (x.ndim - 1)
    x[:na] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))).reshape(shp)
    x[-nr:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))).reshape(shp)
    return x


def pan2(x: np.ndarray, pan: float) -> np.ndarray:
    th = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2)


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Mix a snippet into the 3-cycle bus at loop time t, once per cycle, so every
    event (and its tail) repeats identically and wraps across the loop point."""
    if x.ndim == 1:
        x = pan2(x, pan)
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


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(round(dur * SR)))


def loop_noise() -> np.ndarray:
    """One cycle of white noise tiled over the three cycles: after any filter has
    settled in cycle 1, the middle cycle is exactly periodic."""
    return np.tile(rng.standard_normal(N), CYC)


def peaking(x, f0, gain_db, qf):
    """RBJ peaking EQ (static)."""
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    al = np.sin(w) / (2 * qf)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]
    a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return signal.lfilter(b, a, x, axis=0)


def periodic_lfo(rate_cycles: int, phase: float = 0.0) -> np.ndarray:
    """Sine LFO with an integer number of cycles per loop."""
    return np.sin(2 * np.pi * rate_cycles * GRID * T3 + phase)


# ---------------------------------------------------------------- continuous layers
def engine_core() -> np.ndarray:
    """Mono engine hum: C#1 sub + C#2 harmonic stack. Partials 2, 3 and 5 have a
    twin detuned by 0.15-0.25 Hz for slow beating; the stack throbs at 0.35 Hz.
    All phases start at 0 so the hum crosses zero exactly at the loop point."""
    f0 = q(hz(37))                                   # C#2 = 69.30 Hz
    y = 0.75 * np.sin(2 * np.pi * q(f0 / 2) * T3)    # C#1 sub
    amps = {1: 1.0, 2: 0.55, 3: 0.42, 4: 0.2, 5: 0.16, 6: 0.1, 7: 0.06, 8: 0.05, 10: 0.03, 12: 0.02}
    for h, a in amps.items():
        y += a * np.sin(2 * np.pi * q(h * f0) * T3)
    for h, det, a in ((2, 0.15, 0.3), (3, 0.25, 0.25), (5, 0.2, 0.1)):
        y += a * np.sin(2 * np.pi * (q(h * f0) + det) * T3)
    throb = 1 + 0.10 * periodic_lfo(7) + 0.05 * periodic_lfo(2, 1.1)
    return y * throb


def engine_rumble() -> np.ndarray:
    """Mono low rumble: band-passed noise 35-160 Hz, following the throb."""
    r = sos_filter(loop_noise(), "bandpass", [35, 160], order=2)
    r /= np.sqrt(np.mean(r ** 2))
    return r * (1 + 0.15 * periodic_lfo(7, 0.4))


def turbine_whine() -> np.ndarray:
    """Faint turbine: C#5 and G#5 partials whose pitch wobbles +-0.3 %, slightly
    different L/R so it hangs a little wide above the mono core."""
    out = np.zeros((L3, 2))
    for c, ph in enumerate((0.0, 1.9)):
        for f, a in ((q(hz(73)), 1.0), (q(hz(80)), 0.55), (q(hz(85)), 0.25)):
            # f(t) = f + d*sin(2*pi*2*GRID*t): the phase integral of the sine term is periodic
            d = 0.003 * f
            ph_t = 2 * np.pi * f * T3 - d / (2 * GRID) * np.cos(2 * np.pi * 2 * GRID * T3 + ph)
            out[:, c] += a * np.sin(ph_t)
    swell = 0.75 + 0.25 * periodic_lfo(1, -0.8)
    return out * swell[:, None]


def vents() -> np.ndarray:
    """Two ventilation ducts: stereo resonant hiss with fan-blade flutter, plus a
    thin air layer up to ~10 kHz."""
    out = np.zeros((L3, 2))
    for (pan, flutter, f1, f2, lvl) in ((-0.55, 227, 470, 1250, 1.0), (0.6, 149, 610, 1720, 0.7)):
        ch = []
        for _ in range(2):
            n = loop_noise()
            n = sos_filter(sos_filter(n, "highpass", 280, order=2), "lowpass", 5200, order=2)
            n = peaking(n, f1, 9, 4.0)
            n = peaking(n, f2, 6, 3.0)
            ch.append(n / np.sqrt(np.mean(n ** 2)))
        st = np.stack(ch, 1)
        # partially correlated L/R, then panned towards the duct
        mid = st.mean(1)
        st = 0.6 * mid[:, None] + 0.4 * st
        th = (pan + 1) * np.pi / 4
        st *= np.array([np.cos(th), np.sin(th)]) * np.sqrt(2)
        flut = 1 + 0.10 * np.sin(2 * np.pi * flutter * GRID * T3)      # blade pass 11.35 / 7.45 Hz
        breath = 1 + 0.18 * periodic_lfo(3 if pan < 0 else 4, pan)
        out += lvl * st * (flut * breath)[:, None]
    air = np.stack([sos_filter(loop_noise(), "bandpass", [3500, 10500], order=2) for _ in range(2)], 1)
    air /= np.sqrt(np.mean(air ** 2))
    return out + 0.35 * air


# ---------------------------------------------------------------- events
def clank(base: float, dur: float, bright: float = 1.0, attack: float = 0.0015) -> np.ndarray:
    """Struck steel: free-bar modes plus random plate modes, each decaying faster
    the higher it is, an impact noise burst, and a distance low-pass."""
    t = tt(dur)
    ratios = [1.0, 2.756, 5.404, 8.933] + list(rng.uniform(1.4, 11.0, 7))
    y = np.zeros(len(t))
    for i, r in enumerate(ratios):
        f = base * r
        amp = rng.uniform(0.35, 1.0) / r ** 0.55 * (bright if i >= 4 else 1.0)
        ph = rng.uniform(0, 2 * np.pi)
        if f > 8500:
            continue
        tau = dur * 0.3 / (1 + f / 1400)
        y += amp * np.sin(2 * np.pi * f * t + ph) * np.exp(-t / tau)
    hit = sos_filter(noise(dur), "bandpass", [500, 3200], order=2) * np.exp(-t / 0.005) * 0.8
    y = fade(y + hit, a=attack, r=min(0.08, dur * 0.2))
    y = sos_filter(y, "lowpass", 3600, order=2)
    return y / np.max(np.abs(y))


def servo() -> np.ndarray:
    """Loader-arm hydraulics: a band-limited buzzy tone gliding up, holding, gliding
    back down, with a soft noise hiss of fluid."""
    dur = 2.2
    t = tt(dur)
    f = np.interp(t, [0, 0.8, 1.3, 2.0, dur], [112, 186, 190, 124, 120])
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = sum(np.sin(k * ph) / k ** 1.2 for k in range(1, 30) if 190 * k < 7000)
    env = np.interp(t, [0, 0.12, 1.9, dur], [0, 1, 1, 0]) ** 1.5
    hiss = sos_filter(noise(dur), "bandpass", [1800, 6000]) * 0.25
    y = sos_filter((y * 0.35 + hiss) * env, "lowpass", 2600, order=2)
    return fade(y, a=0.01, r=0.05)


def pneumatic() -> np.ndarray:
    dur = 1.8
    t = tt(dur)
    env = (1 - np.exp(-t / 0.025)) * np.where(t < 0.7, 1.0, np.exp(-(t - 0.7) / 0.28))
    y = sos_filter(noise(dur), "bandpass", [1600, 9000], order=2)
    y = peaking(y, 3800, 6, 2.0)
    return fade(y * env * 0.5, a=0.004, r=0.05)


def sine_glide(f_curve: np.ndarray, amp_curve: np.ndarray) -> np.ndarray:
    ph = 2 * np.pi * np.cumsum(f_curve) / SR
    return np.sin(ph) * amp_curve


def blip_env(n: int, a: float = 0.002, r: float = 0.006) -> np.ndarray:
    return fade(np.ones(n), a=a, r=r)


def chirp_trill() -> np.ndarray:
    """Three quick sine blips, each with an upward glide: C#6, G#6, C#7."""
    out = []
    for m in (85, 92, 97):
        n = int(0.055 * SR)
        f = hz(m) * (0.94 + 0.06 * np.linspace(0, 1, n) ** 0.5)
        out.append(sine_glide(f, blip_env(n)))
        out.append(np.zeros(int(0.03 * SR)))
    return np.concatenate(out)


def chirp_burble() -> np.ndarray:
    """Telemetry burble: 11 steps of C#-minor-pentatonic pitches with 6 ms portamento."""
    pent = [85, 88, 90, 92, 95, 97, 100]
    steps = rng.choice(pent, 11)
    step = int(0.034 * SR)
    f = np.repeat([hz(m) for m in steps], step)
    f = uniform_filter1d(f, size=int(0.006 * SR), mode="nearest")
    gate = np.tile(np.concatenate([np.ones(step - int(0.008 * SR)), np.zeros(int(0.008 * SR))]), len(steps))
    gate = uniform_filter1d(gate, size=int(0.002 * SR), mode="nearest")
    return fade(sine_glide(f, gate) * 0.8, a=0.002, r=0.006)


def chirp_ack() -> np.ndarray:
    """Acknowledge: G#6 gliding down to C#6, a gap, then C#6 sliding up to E6."""
    n1, n2 = int(0.11 * SR), int(0.13 * SR)
    a = sine_glide(np.geomspace(hz(92), hz(85), n1), blip_env(n1, 0.002, 0.02))
    b = sine_glide(np.geomspace(hz(85), hz(88), n2) * 1.0, blip_env(n2, 0.002, 0.05))
    return np.concatenate([a, np.zeros(int(0.06 * SR)), b])


def chirp_sweep() -> np.ndarray:
    """Two fast upward FM-ish sweeps 1.2 -> 3.4 kHz with a light vibrato."""
    out = []
    for k in range(2):
        n = int(0.12 * SR)
        s = np.linspace(0, 1, n)
        f = 1200 * (3400 / 1200) ** (s ** 1.6) * (1 + 0.02 * np.sin(2 * np.pi * 38 * s * 0.12))
        out.append(sine_glide(f, blip_env(n, 0.002, 0.03) * (1 - 0.3 * k)))
        out.append(np.zeros(int(0.05 * SR)))
    return np.concatenate(out)


def hall_ir(rt60: float = 3.8, length: float = 5.0) -> np.ndarray:
    """Huge metal hall: discrete slap echoes off far walls, then a slowly building
    diffuse tail with HF damping (two bands decaying at different rates)."""
    t = tt(length)
    pre = int(0.03 * SR)
    irs = []
    for c in range(2):
        lo = sos_filter(rng.standard_normal(len(t)), "bandpass", [120, 1500]) * np.exp(-6.9 * t / rt60)
        hi = sos_filter(rng.standard_normal(len(t)), "bandpass", [1500, 6000]) * np.exp(-6.9 * t / (rt60 * 0.42))
        tail = (lo + 0.6 * hi) * (1 - np.exp(-t / 0.07))
        ir = np.zeros(len(t) + pre)
        ir[pre:] = tail * 0.5
        for k, (d, g) in enumerate(((0.047, 0.9), (0.096, 0.7), (0.151, 0.6), (0.226, 0.5),
                                    (0.301, 0.42), (0.388, 0.33), (0.47, 0.25))):
            s = pre + int((d + 0.006 * c * (1 if k % 2 else -1)) * SR)
            if (k + c) % 2 == 0:
                ir[s] += g * 3.0
            else:
                ir[s] += g * 1.6
        irs.append(ir)
    irs = [sos_filter(ir, "lowpass", 5500) for ir in irs]
    nrm = np.sqrt(np.sum(irs[0] ** 2))
    return np.stack([ir / nrm for ir in irs], 1)


def convolve(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)


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
    if y.ndim == 1:
        y = y[:, None]
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    os_ = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(os_)) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 150.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x-oversampled (true) peak, on the
    periodic 3-cycle buffer with wrap-mode hold and smoothing windows. The release
    recursion runs on 8-sample blocks of the held gain (block minimum, so it never
    under-limits), then the step curve is smoothed with an L+1 wrap window."""
    ceil = 10 ** (ceiling_db / 20)
    os_ = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = os_[: len(x) * 4].reshape(len(x), 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    L = int(look_ms * 1e-3 * SR)
    held = minimum_filter1d(need, size=2 * L + 1, mode="wrap")
    B = 8
    hb = held.reshape(-1, B).min(axis=1)
    rc = np.exp(-B / (rel_ms * 1e-3 * SR))
    g = np.empty_like(hb)
    prev = 1.0
    for n, h in enumerate(hb.tolist()):
        prev = min(h, prev * rc + (1 - rc))
        g[n] = prev
    g = np.repeat(g, B)
    g = uniform_filter1d(g, size=L + 1, mode="wrap")
    return x * g[:, None]


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
    y = mid_cycle(y)
    return y - y.mean(axis=0)          # constant offset only, so the loop seam is untouched


# ---------------------------------------------------------------- arrangement
def render() -> np.ndarray:
    core = engine_core()
    rumble = engine_rumble()
    whine = turbine_whine()
    vent = vents()

    fx = np.zeros((L3, 2))       # events, mostly heard through the hall
    send = np.zeros((L3, 2))
    near = np.zeros((L3, 2))     # console chirps, closer and drier

    def hit(x, t, g, pan, wet=1.0, dry=0.25):
        place(fx, x, t, g * dry, pan)
        place(send, x, t, g * wet, pan)

    # clanks: (time, base Hz, dur, gain, pan)
    hit(clank(240, 1.1, 0.9, attack=0.0008), 0.0, 0.55, -0.35)          # loop-top clank
    hit(clank(310, 0.9), 3.70, 0.75, 0.45)                              # dropped tool...
    hit(clank(318, 0.6, 0.7), 3.93, 0.4, 0.5)                           # ...bounce
    hit(clank(325, 0.35, 0.5), 4.05, 0.18, 0.52)                        # ...settle
    for i in range(9):                                                  # chain rattle, far left
        tc = 7.9 + i * 0.055 + rng.uniform(-0.012, 0.012)
        hit(clank(rng.uniform(700, 1100), 0.18, 0.8), tc, 0.22 * rng.uniform(0.6, 1.0) * (1 - i / 14), -0.75)
    hit(clank(132, 2.4, 0.6, attack=0.003), 11.2, 1.0, 0.1, wet=1.3, dry=0.15)   # heavy bulkhead clang
    hit(clank(205, 1.2, 1.0), 15.6, 0.6, 0.7)
    hit(clank(280, 0.8), 17.95, 0.42, -0.6)
    hit(clank(276, 0.5, 0.6), 18.12, 0.22, -0.62)

    # machinery
    hit(servo(), 9.2, 0.55, 0.35, wet=0.8, dry=0.35)
    hit(pneumatic(), 13.6, 0.45, -0.5, wet=0.7, dry=0.3)

    # console chirps (closer: drier, small send)
    for x, t, g, p in ((chirp_trill(), 2.3, 0.22, 0.5), (chirp_burble(), 6.4, 0.17, -0.4),
                       (chirp_ack(), 12.6, 0.2, 0.6), (chirp_sweep(), 16.75, 0.15, -0.55)):
        place(near, x, t, g, p)
        place(send, x, t, g * 0.35, p)

    wet = convolve(send, hall_ir())
    wet = sos_filter(wet, "highpass", 150, order=4)
    near = sos_filter(near, "highpass", 400, order=2)

    low = (0.30 * core + 0.10 * rumble)
    low = sos_filter(low, "lowpass", 900, order=2)
    low = np.repeat(low[:, None], 2, axis=1)

    stems = {"core": low, "whine": 0.045 * whine, "vents": 0.07 * vent,
             "clank dry": fx, "hall": 0.5 * wet, "chirps": near}
    if DEBUG:
        for k, v in stems.items():
            print(f"  stem {k:10s} {integrated_lufs(mid_cycle(v)):6.1f} LUFS (pre-master)")
    mix = sum(stems.values())
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    side = sos_filter(side, "highpass", 250, order=8)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 20, order=2)
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
