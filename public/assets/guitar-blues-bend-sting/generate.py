"""guitar-blues-bend-sting: Opus Sound Directory

A four-second singing blues-lead stinger in A minor pentatonic, played on a solid-body electric through a warm low-gain tube overdrive into a 1x12 open-back cab, with a short slapback and a small plate. From frame 0 a quick three-note slurred pickup climbs the G string: a picked A, a hammer-on to C and a slide up to D. It lands exactly on frame 30 (1.0 s) on a hard-picked E on the B string that is bent a full step and a half up to G. The bend is one continuous push that arrives a hair flat and settles in tune. The held note then gets a wide finger vibrato that starts slow and speeds up. A slight release-and-rebend dip follows, and then the note blooms into a soft octave-harmonic feedback swell that fades to silence by about 3.9 s. The strings are physically modelled. Each string is additive, with integrated-phase pitch so that bends, slides and vibrato stay continuous. The model adds stiffness inharmonicity, faster decay for higher partials, pick- and pickup-position combs, and a resonant pickup. The amp is 4x oversampled, and the cab rolls off everything above about 6 kHz, so the drive stays warm with no fizz.

Run:  python3 generate.py   -> writes out.wav next to this file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SAMPLE_RATE = 48000
SEED = 4030
DURATION_SEC = 4.0
BPM = None
KEY = "A minor pentatonic"
FPS = 30
CUE_FRAMES = (0, 30)           # frame 0: pickup starts, frame 30: struck 1.5-step bend
TARGET_LUFS = -14.0
TRUE_PEAK_CEILING_DBTP = -1.0

SR = SAMPLE_RATE
N = int(round(DURATION_SEC * SR))
OS = 4                         # oversampling factor for the drive stages
BEND_T = CUE_FRAMES[1] / FPS   # 1.0 s

rng = np.random.default_rng(SEED)
T = np.arange(N) / SR


# ---------------------------------------------------------------- utilities
def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def smooth01(x: np.ndarray) -> np.ndarray:
    """C2-continuous 0->1 ramp (smootherstep) of a clipped argument."""
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


def ramp(t0: float, t1: float) -> np.ndarray:
    """Smooth 0->1 transition between t0 and t1 over the whole timeline."""
    return smooth01((T - t0) / max(t1 - t0, 1e-9))


def bump(tc: float, width: float) -> np.ndarray:
    """Unit-area Gaussian pulse (per second) centred at tc."""
    return np.exp(-0.5 * ((T - tc) / width) ** 2) / (width * np.sqrt(2 * np.pi))


def sos_filter(x, kind, freq, order=2, fs=SR):
    sos = signal.butter(order, freq, btype=kind, fs=fs, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def biquad(kind: str, f0: float, q: float, gain_db: float = 0.0, fs: float = SR):
    """RBJ cookbook biquads: 'peak', 'lowpass', 'lowshelf', 'highshelf'."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / fs
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2 * q)
    if kind == "peak":
        b = [1 + alpha * a_, -2 * cw, 1 - alpha * a_]
        a = [1 + alpha / a_, -2 * cw, 1 - alpha / a_]
    elif kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "lowshelf":
        s = 2 * np.sqrt(a_) * alpha
        b = [a_ * ((a_ + 1) - (a_ - 1) * cw + s), 2 * a_ * ((a_ - 1) - (a_ + 1) * cw), a_ * ((a_ + 1) - (a_ - 1) * cw - s)]
        a = [(a_ + 1) + (a_ - 1) * cw + s, -2 * ((a_ - 1) + (a_ + 1) * cw), (a_ + 1) + (a_ - 1) * cw - s]
    elif kind == "highshelf":
        s = 2 * np.sqrt(a_) * alpha
        b = [a_ * ((a_ + 1) + (a_ - 1) * cw + s), -2 * a_ * ((a_ - 1) + (a_ + 1) * cw), a_ * ((a_ + 1) + (a_ - 1) * cw - s)]
        a = [(a_ + 1) - (a_ - 1) * cw + s, 2 * ((a_ - 1) - (a_ + 1) * cw), (a_ + 1) - (a_ - 1) * cw - s]
    else:
        raise ValueError(kind)
    return np.array(b) / a[0], np.array(a) / a[0]


def eq(x, kind, f0, q, gain_db=0.0, fs=SR):
    b, a = biquad(kind, f0, q, gain_db, fs)
    return signal.lfilter(b, a, x, axis=0)


def smooth_noise(n: int, cutoff: float, fs: float = SR) -> np.ndarray:
    """Seeded, band-limited random drift with unit RMS (for human pitch/level wander)."""
    w = sos_filter(rng.standard_normal(n + 4000), "lowpass", cutoff, order=2, fs=fs)[4000:]
    return w / (np.sqrt(np.mean(w ** 2)) + 1e-12)


def place(bus: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0) -> None:
    s = int(round(t * SR))
    e = min(len(bus), s + len(x))
    if s < e:
        bus[s:e] += gain * x[: e - s]


# ---------------------------------------------------------------- the string model
SCALE_CM = 64.8              # scale length
PICKUP_CM = 15.5             # neck pickup, distance from the bridge
PICK_CM = 8.0                # where the pick hits, distance from the bridge
F_MAX = 9500.0               # partials stop here (the drive and cab do the rest, oversampled)


class String:
    """One guitar string as a bank of additive partials with integrated phase.

    fret(t) and bend(t) (cents) are smooth per-sample tracks, so hammer-ons, slides,
    bends and vibrato are all continuous pitch motion of the same vibrating string.
    Each excitation (pick, hammer, slide) adds amplitude to every partial and decays at
    a per-partial rate b1 + b3 f^2 (highs die first). A damping track adds loss for
    finger mutes and the energy a hammer/slide takes away. The magnetic pickup samples
    the string at a fixed distance from the bridge, so its comb moves with the fret.
    """

    def __init__(self, open_midi: float, b0: float = 1.4e-5):
        self.open_midi = open_midi
        self.b0 = b0
        self.fret = np.zeros(N)
        self.bend = np.zeros(N)
        self.damp = np.zeros(N)       # extra loss rate (1/s), all partials
        self.exc = []                 # (sample, amp per partial fn(n, f0, p_pluck), attack samples)
        self.extra = {}               # partial -> extra amplitude track (feedback)
        self.extra_rate = {}          # partial -> extra loss-rate track
        self.start = 0

    def set_fret(self, f0: float, changes):
        """changes: list of (t0, t1, new_fret); fret steps are quantised by the frets
        themselves on a slide (smoothed staircase), a hammer/pull is a ~3 ms step."""
        fr = np.full(N, float(f0))
        cur = f0
        for t0, t1, new in changes:
            steps = int(abs(new - cur))
            d = np.sign(new - cur)
            for k in range(steps):
                a = t0 + (t1 - t0) * k / steps
                b = t0 + (t1 - t0) * (k + 1) / steps
                fr += d * ramp(a, b)
            cur = new
        self.fret = fr

    def render(self) -> np.ndarray:
        L = SCALE_CM * 2 ** (-self.fret / 12)                    # vibrating length
        ffret = hz(self.open_midi) * 2 ** (self.fret / 12)
        f0 = ffret * 2 ** (self.bend / 1200)
        B = self.b0 * (SCALE_CM / L) ** 2                        # stiffness rises as the string shortens
        p_pu = PICKUP_CM / L
        s0 = self.start
        out = np.zeros(N)
        nmax = int(F_MAX // f0.min()) + 1
        for n in range(1, nmax + 1):
            fn = n * f0 * np.sqrt(1 + B * n * n)
            band = np.clip((F_MAX - fn) / 1500.0, 0.0, 1.0)      # fade partials out below F_MAX
            if band.max() <= 0:
                break
            ph = np.zeros(N)
            ph[s0:] = 2 * np.pi * np.cumsum(fn[s0:]) / SR - 2 * np.pi * fn[s0] / SR
            rate = 0.32 + 0.9e-6 * fn ** 2 + self.damp + self.extra_rate.get(n, 0.0)
            R = np.cumsum(rate) / SR
            amp = np.zeros(N)
            for s, spec, na in self.exc:                     # na: attack length (samples)
                a_n = spec(n, f0[s], PICK_CM / L[s])
                if a_n == 0:
                    continue
                env = np.zeros(N)
                env[s:] = np.exp(-(R[s:] - R[s]))
                env[s:s + na] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
                amp += a_n * env
            if n in self.extra:
                amp += self.extra[n]
            comb = np.abs(np.sin(n * np.pi * p_pu))
            out += amp * comb * band * np.sin(ph)
        return out


def pick_spec(vel: float, hard: float = 5200.0):
    """Plectrum: velocity-pickup spectrum ~ sin(n pi p)/n, softened by pick hardness."""
    def spec(n, f0, p):
        return vel * abs(np.sin(n * np.pi * p)) / n * np.exp(-n * f0 / hard) * 2.2
    return spec


def finger_spec(vel: float, soft: float = 2200.0):
    """Hammer-on / slide re-excitation: duller, from the fretting finger."""
    def spec(n, f0, p):
        return vel / n ** 1.2 * np.exp(-n * f0 / soft)
    return spec


def pick_scrape(dur: float = 0.006, f_lo=1800.0, f_hi=6500.0) -> np.ndarray:
    """The plectrum dragging over the wound/plain string just before release."""
    t = np.arange(int(dur * SR)) / SR
    y = sos_filter(rng.standard_normal(len(t)), "bandpass", [f_lo, f_hi], order=2)
    env = np.sin(np.pi * t / dur) ** 2 * np.exp(-t / 0.002)
    return y * env


# ---------------------------------------------------------------- the performance
def perform() -> tuple[np.ndarray, np.ndarray]:
    """Return (string signal at the pickup, small finger/pick noises) at SR."""
    # --- pickup on the G string (open G3 = MIDI 55): A4 (14) -> hammer C5 (17) -> slide D5 (19)
    g = String(55, b0=1.6e-5)
    t_ham = 0.285 + rng.uniform(-0.008, 0.008)
    t_sld = 0.585 + rng.uniform(-0.008, 0.008)
    g.set_fret(14, [(t_ham, t_ham + 0.004, 17), (t_sld, t_sld + 0.048, 19)])
    g.start = 0
    g.exc = [(0, pick_spec(0.62, hard=4600.0), 24),                 # 0.5 ms pick attack
             (int(t_ham * SR), finger_spec(0.30), 110),               # ~2.3 ms fingertip hammer
             (int((t_sld + 0.048) * SR), finger_spec(0.04), 240)]
    # energy the fretting finger takes on hammer and slide; finger mute before the bend
    g.damp = (np.log(1 / 0.62) * bump(t_ham + 0.002, 0.003)
              + np.log(1 / 0.80) * bump(t_sld + 0.03, 0.012)
              + 55.0 * ramp(0.935, 0.975))
    # a breath of vibrato on the D before the mute
    vphase = 2 * np.pi * np.cumsum(5.2 * np.ones(N)) / SR
    g.bend = 9.0 * ramp(0.70, 0.82) * (1 - np.cos(vphase - vphase[int(0.70 * SR)])) / 2 * -1
    g.bend += 2.0 * smooth_noise(N, 3.0)
    sig = g.render()

    # --- the bend on the B string (open B3 = MIDI 59): E5 at fret 17 bent +300 cents to G5
    b = String(59, b0=1.2e-5)
    b.set_fret(17, [])
    s_b = int(round(BEND_T * SR))
    b.start = s_b
    b.exc = [(s_b, pick_spec(1.0, hard=6200.0), 20)]

    # pitch: struck, then one continuous push that lands slightly flat and settles
    t_up0, t_up1 = BEND_T + 0.014, BEND_T + 0.150
    up = 286.0 * ramp(t_up0, t_up1) + 14.0 * ramp(t_up1 - 0.02, t_up1 + 0.17)
    # wide finger vibrato under the target (a bent note is vibrato'd by releasing),
    # rate accelerates 3.9 -> 6.4 Hz, depth opens to ~65 cents; skewed so the push
    # back up is a little quicker than the release.
    v_rate = 3.9 + 2.5 * ramp(1.40, 2.20)
    v_ph = 2 * np.pi * np.cumsum(v_rate) / SR
    v_ph -= v_ph[int(1.33 * SR)]
    v_depth = 65.0 * ramp(1.33, 1.72) * (1 - ramp(2.20, 2.30)) + 22.0 * ramp(2.62, 2.80) * (1 - ramp(3.05, 3.40))
    shape = (1 - np.cos(v_ph + 0.28 * np.sin(v_ph))) / 2
    vib = -v_depth * shape
    # release-and-rebend dip: relax ~1 semitone, push back up
    dip = -105.0 * ramp(2.27, 2.40) * (1 - ramp(2.43, 2.60))
    drift = 3.0 * smooth_noise(N, 2.5)
    b.bend = up + vib + dip + drift * ramp(1.0, 1.2)

    # octave-harmonic feedback bloom: partial 2 swells, the fundamental and upper
    # partials give way to it, then the player lets it go to silence
    fb_env = 0.46 * ramp(2.52, 3.10) * (1 - ramp(3.22, 3.80))
    fb_env *= 1 + 0.06 * smooth_noise(N, 4.0)
    b.extra = {2: fb_env, 4: 0.05 * fb_env}
    give = 2.8 * ramp(2.55, 3.05)
    for n in (1, 3, 5, 6, 7, 8, 9, 10, 11, 12):
        b.extra_rate[n] = give
    b.damp = 9.0 * ramp(3.30, 3.75)
    sig += b.render()

    # --- small mechanical noises (all pre-amp, so the drive colours them)
    noises = np.zeros(N)
    place(noises, pick_scrape(0.005), 0.0 + 0.0004, 0.05)
    place(noises, pick_scrape(0.007, 2200, 7000), BEND_T + 0.0004, 0.10)
    # fingertip squeak on the two-fret slide
    sd = 0.06
    sq = sos_filter(rng.standard_normal(int(sd * SR)), "bandpass", [1400, 3800], order=2)
    sq *= np.sin(np.pi * np.arange(len(sq)) / len(sq)) ** 2
    place(noises, sq, t_sld - 0.005, 0.012)
    # string rubbing on the fret while it is pushed: noise follows |d(bend)/dt|
    db = np.abs(np.gradient(b.bend) * SR) / 2500.0
    rub = sos_filter(rng.standard_normal(N), "bandpass", [900, 3200], order=2) * np.clip(db, 0, 1)
    noises += 0.006 * uniform_filter1d(rub, 96)
    return sig, noises


# ---------------------------------------------------------------- amp, cab, effects
def pickup_and_amp(x: np.ndarray) -> np.ndarray:
    """Resonant pickup -> low-gain two-stage asymmetric tube-style overdrive at 4x -> tone
    stack -> 1x12 open-back cab. Returns a mono signal at SR."""
    x = eq(x, "lowpass", 4100.0, 2.2)                       # pickup inductance/cable resonance
    x = x / (np.max(np.abs(x)) + 1e-12)
    up = signal.resample_poly(x, OS, 1)
    fs = SR * OS
    # stage 1: mid-humped low-gain drive (cut lows before clipping keeps it tight)
    y = sos_filter(up, "highpass", 180.0, order=1, fs=fs)
    y = eq(y, "peak", 780.0, 0.7, 5.0, fs)
    g1, b1 = 3.4, 0.18
    y = np.tanh(g1 * (y + b1 * 0.25)) - np.tanh(g1 * b1 * 0.25)
    y = sos_filter(y, "lowpass", 6500.0, order=1, fs=fs)
    # stage 2: preamp tube, gentler and opposite asymmetry
    y = eq(y, "lowshelf", 220.0, 0.7, 3.0, fs)
    g2, b2 = 1.7, -0.22
    y = (np.tanh(g2 * (y + b2)) - np.tanh(g2 * b2)) / np.tanh(g2)
    y = sos_filter(y, "highpass", 25.0, order=2, fs=fs)
    y = sos_filter(y, "lowpass", 9000.0, order=4, fs=fs)
    y = signal.resample_poly(y, 1, OS)[:N]
    # tone stack: warm, slightly scooped low-mids, rounded treble
    y = eq(y, "lowshelf", 160.0, 0.7, 1.5)
    y = eq(y, "peak", 420.0, 0.9, -1.5)
    y = eq(y, "peak", 1250.0, 0.8, 1.5)
    y = eq(y, "highshelf", 3500.0, 0.7, -2.0)
    # 1x12 open-back cab: soft low bump, cone presence peaks, steep roll-off (no fizz >7 kHz)
    y = sos_filter(y, "highpass", 85.0, order=2)
    y = eq(y, "peak", 115.0, 1.3, 1.5)
    y = eq(y, "peak", 2300.0, 1.6, 2.5)
    y = eq(y, "peak", 3400.0, 3.0, -2.0)
    y = eq(y, "lowpass", 5000.0, 1.0)
    y = sos_filter(y, "lowpass", 5600.0, order=4)
    y = sos_filter(y, "lowpass", 7200.0, order=4)
    return y


def plate(x: np.ndarray, rt60: float = 0.95, predelay: float = 0.014) -> np.ndarray:
    """Small plate: decorrelated stereo noise IR with a quick density build-up."""
    t = np.arange(int(rt60 * 1.2 * SR)) / SR
    env = np.exp(-6.9 * t / rt60) * (1 - np.exp(-t / 0.004))
    irs = []
    for _ in range(2):
        ir = sos_filter(rng.standard_normal(len(t)), "bandpass", [350, 6500], order=2) * env
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack([signal.fftconvolve(x, irs[0])[:N], signal.fftconvolve(x, irs[1])[:N]], axis=1)


def slapback(x: np.ndarray) -> np.ndarray:
    """Tape-style slapback: one dark repeat at 112 ms plus a faint second, slightly off-centre."""
    y = sos_filter(x, "lowpass", 3000.0, order=2)
    y = sos_filter(y, "highpass", 250.0, order=2)
    out = np.zeros((N, 2))
    for d, gl, gr in ((0.112, 0.20, 0.30), (0.224, 0.07, 0.05)):
        s = int(d * SR)
        out[s:, 0] += gl * y[:N - s]
        out[s:, 1] += gr * y[:N - s]
    return out


# ---------------------------------------------------------------- loudness / peak (BS.1770)
def k_weight(x: np.ndarray) -> np.ndarray:
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def integrated_lufs(x: np.ndarray) -> float:
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def true_peak_dbtp(x: np.ndarray) -> float:
    return float(20 * np.log10(np.max(np.abs(signal.resample_poly(x, 4, 1, axis=0))) + 1e-20))


def soft_limiter(x: np.ndarray, ceiling_db: float, look_ms: float = 2.0, rel_ms: float = 120.0) -> np.ndarray:
    """Look-ahead gain limiter driven by the 4x true peak; held, one-pole release, edge-safe smoothing."""
    ceil = 10 ** (ceiling_db / 20)
    os_ = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = os_[: len(x) * 4].reshape(len(x), 4).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    L = int(look_ms * 1e-3 * SR)
    held = minimum_filter1d(need, size=2 * L + 1, mode="nearest")
    rc = np.exp(-1.0 / (rel_ms * 1e-3 * SR))
    g = np.empty_like(held)
    prev = 1.0
    for n, h in enumerate(held.tolist()):
        prev = min(h, prev * rc + (1 - rc))
        g[n] = prev
    g = uniform_filter1d(g, size=L + 1, mode="nearest")
    return x * g[:, None]


def master(mix: np.ndarray) -> np.ndarray:
    gain_db = TARGET_LUFS - integrated_lufs(mix)
    ceiling = TRUE_PEAK_CEILING_DBTP - 0.3
    for _ in range(12):
        y = soft_limiter(mix * 10 ** (gain_db / 20), ceiling)
        err = TARGET_LUFS - integrated_lufs(y)
        if abs(err) < 0.03:
            break
        gain_db += err
    return y


# ---------------------------------------------------------------- mix
def render() -> np.ndarray:
    strings, noises = perform()
    gtr = pickup_and_amp(strings + noises)
    gtr = gtr / (np.max(np.abs(gtr)) + 1e-12)

    dry = np.stack([gtr, gtr], axis=1)               # one mic on the cab, centred
    slap = slapback(gtr)
    send = gtr + 0.6 * slap.mean(axis=1)
    wet = plate(sos_filter(send, "highpass", 300.0, order=2)) * 0.17
    mix = dry + slap + wet

    # keep the low end mono: steep high-pass on the side channel
    mid, side = (mix[:, 0] + mix[:, 1]) / 2, (mix[:, 0] - mix[:, 1]) / 2
    # (zero-phase, so the skirt is twice as steep; the side holds only slap + plate)
    side = signal.sosfiltfilt(signal.butter(8, 700.0, "highpass", fs=SR, output="sos"), side)
    mix = np.stack([mid + side, mid - side], axis=1)
    mix = sos_filter(mix, "highpass", 22.0, order=2)

    # the tail is already gone by ~3.8 s; make the last stretch exactly silent
    fade = 1 - ramp(3.62, 3.92)
    mix *= fade[:, None]
    return mix


def main() -> None:
    mix = render()
    y = master(mix)
    y = y - y.mean()                                # common-mode constant DC trim (keeps the side clean)
    dither = (rng.uniform(-0.5, 0.5, y.shape) + rng.uniform(-0.5, 0.5, y.shape)) / 32768
    dither *= (1 - ramp(3.90, 3.95))[:, None]
    pcm = np.round(np.clip((y + dither) * 32767, -32768, 32767)).astype(np.int16)
    assert pcm.shape == (N, 2)
    out = Path(__file__).resolve().parent / "out.wav"
    wavfile.write(out, SR, pcm)
    f = pcm.astype(np.float64) / 32768
    print(f"wrote {out}  samples={len(pcm)}  LUFS={integrated_lufs(f):.2f}  TP={true_peak_dbtp(f):.2f} dBTP")


if __name__ == "__main__":
    main()
