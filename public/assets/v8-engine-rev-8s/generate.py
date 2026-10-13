#!/usr/bin/env python3
"""V8 engine start, rev and shutdown -- take 3 (old big-block muscle car, passing the listener).

CREATIVE BRIEF
Same physical engine model as take 1 (rpm integrated into crank angle, one exhaust pulse per firing event, cross-
plane firing order 1-8-4-3-6-5-7-2, firing frequency rpm/60*4, left bank cyl 1-4 / right bank cyl 5-8 each into
its own pipe) tuned as an old big-block: duller, heavier blow-down pulses with low port rings, long log-style
primaries and long dual pipes, chambered mufflers (strong ~70 Hz body resonance, 2 kHz low-pass), more overrun
pops. Lopey idle from a big cam: overlap dilutes the charge so random cylinders fire weakly (32 % of idle
firings at 20-55 %), extra timing jitter, and the idle hunts (+-45 rpm noise + a 1.7 Hz lope).
The car idles 21 m up the road on the listener's left (7 m lateral offset). From frame 75 it launches and drives
past left -> right (closest ~7.1 m at 5.0 s), and is already receding when it upshifts at frame 180. The
pass-by is physical, applied to the rendered car signal:
  * Doppler: the listener at time t hears the emission time tau with tau + (r(tau) - r0)/c = t (the constant
    r0/c bulk delay is dropped, so everything before the launch lands on its frame); the signal is read at tau(t).
  * 1/r distance gain (7 m reference), a ground reflection off the asphalt (image source below the road, gain
    0.55) read through its own Doppler path -> the classic sweeping pass-by comb,
  * air absorption: a low-pass whose cutoff falls with distance (crossfaded filter bank), and an equal-power
    left -> right pan from the azimuth; the two banks only separate (stereo side) when the car is close.
  * All engine keyframes after the launch are written in HEARD frames and converted to emission time by
    inverting the propagation, so the stab and the upshift cut land on frames 75 and 180 for the listener.
Under the exhaust: intake roar with a throttle gulp, valvetrain tick, belt whine, whir, overrun pumping whoosh.
Outdoors: no room. Master: 25 Hz high-pass, mono below 120 Hz (side high-passed), a slow 2.5:1 fader ride so the
close pass is turned down smoothly, -14 LUFS, hold-type true-peak limiter at -1.35 dBTP (4x oversampled).

CUE SHEET (30 fps, 48 kHz, 1 frame = 1600 samples; frames are HEARD time). All times read from CUE / RPM_KEYS /
LOAD_KEYS / SPEED_KEYS.
 frame   time    event
   0    0.000 s  starter (22 m away): solenoid clack + geared starter whine, cranking ~210 rpm
  18    0.600 s  catch: misfiring first firings, flare to 1,800 rpm (frame 31)
  20    0.667 s  starter pinion disengages
  31-75          lopey 750 rpm idle (weak cylinders, hunting)
  75    2.500 s  THROTTLE STAB (cue) and launch: firing pulse phase-locked to 2.500 s, load 0.12 -> 1.0, gulp
  93    3.100 s  6,500 rpm; the car is rolling towards the listener (12 m/s by frame 120)
  95    3.167 s  lift-off: overrun burble, crackles and pops, coming closer
 150    5.000 s  second pull at full load right as the car passes the listener (closest, 7.1 m)
 180    6.000 s  7,000 rpm, IGNITION CUT for the upshift (cue), heard receding (17 m away, 19 m/s), 80 ms
 185    6.167 s  4,800 rpm, decaying to idle as the car rolls away (a few pops)
 225    7.500 s  key-off far away (~44 m): chuffs, last shudder
 230    7.667 s  cooling-metal tick 1 (far away, barely audible)
 235    7.833 s  cooling-metal tick 2 (far away, barely audible)
 240    8.000 s  end, true silence (384000 samples)

 RPM_KEYS and LOAD_KEYS: as take 1 (see the tables below in the code).
 SPEED_KEYS (frame, m/s), linear: 0:0  75:0  120:12  150:12.5  180:19  195:20  225:16  240:15
"""
import sys
import wave

import numpy as np
from scipy import signal
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 48000
FPS = 30
N = 384000
SEED = 44
TARGET_LUFS = -14.0
rng = np.random.default_rng(SEED)

CUE = {"starter": 0, "catch": 18, "disengage": 20, "flare_top": 31, "stab": 75, "stab_top": 93, "lift": 95,
       "pull2": 150, "cut": 180, "cut_end": 182.4, "settle": 185, "keyoff": 225, "tick1": 230, "tick2": 235,
       "end": 240}
RPM_KEYS = [(0, 0), (1, 190), (18, 215), (20, 520), (24, 1300), (28, 1750), (31, 1800), (38, 1350), (48, 830),
            (54, 690), (60, 780), (66, 745), (75, 750), (78, 1500), (84, 3700), (90, 5800), (93, 6500),
            (95, 6480), (99, 5700), (108, 4200), (120, 2900), (135, 1800), (150, 1200), (156, 1900),
            (165, 3700), (174, 5700), (180, 7000), (182.4, 6000), (185, 4800), (192, 3700), (204, 2000),
            (213, 1150), (220, 820), (225, 750), (229.5, 0)]
LOAD_KEYS = [(0, 0), (18, 0), (18.3, 0.65), (26, 0.45), (34, 0.18), (48, 0.12), (74.97, 0.12), (75, 1.0),
             (94.4, 1.0), (95, 0.0), (149.9, 0.0), (150, 1.0), (179.97, 1.0), (180, 0.0), (182.3, 0.0), (182.4, 0.5), (186, 0.35),
             (200, 0.12), (225, 0.12), (225.2, 0.0), (240, 0.0)]
FIRING_ORDER = [1, 8, 4, 3, 6, 5, 7, 2]
BANK = {1: 0, 2: 0, 3: 0, 4: 0, 5: 1, 6: 1, 7: 1, 8: 1}       # 0 = left bank/channel, 1 = right
DEG_PER_FIRING = 90.0                                        # 720 deg / 8 cylinders
POP_WINDOWS = [(96, 148, 1.4), (186, 198, 0.6)]              # (from frame, to frame, density) overrun pops

# pass-by geometry (metres, m/s). The car idles X0 up the road to the left, launches on the stab and drives
# past left -> right at LATERAL metres, closest at 5.0 s, and is receding when it upshifts at frame 180.
X0, LATERAL, H_SRC, H_LIS, C_AIR, R_REF = -21.0, 7.0, 0.35, 1.6, 343.0, 7.0
SPEED_KEYS = [(0, 0), (75, 0), (120, 12.0), (150, 12.5), (180, 19.0), (195, 20.0), (225, 16.0), (240, 15.0)]
GROUND_R = 0.55                                                # asphalt reflection at grazing incidence

t = np.arange(N) / SR

# trajectory in emission time; arrival time t_out = tau + (r - r0)/c (the constant r0/c bulk delay is dropped,
# so everything before the launch is heard exactly on its frame)
speed = np.interp(t, [f / FPS for f, _ in SPEED_KEYS], [v for _, v in SPEED_KEYS])
pos_x = X0 + np.cumsum(speed) / SR
r_dir = np.sqrt(pos_x ** 2 + LATERAL ** 2 + (H_LIS - H_SRC) ** 2)
r_gnd = np.sqrt(pos_x ** 2 + LATERAL ** 2 + (H_LIS + H_SRC) ** 2)
r0 = r_dir[0]
t_arr = t + (r_dir - r0) / C_AIR
t_arr_g = t + (r_gnd - r0) / C_AIR


def T(fr):
    """Emission time of an event that must be HEARD on frame `fr` (inverts the propagation delay)."""
    return float(np.interp(fr / FPS, t_arr, t))



# ----------------------------------------------------------------------------------------------- helpers
def bp_sos(fc, q, order=2):
    bw = fc / q
    return signal.butter(order, [max(20, fc - bw / 2), min(23000, fc + bw / 2)], "bandpass", fs=SR, output="sos")


def scatter(dst, start_idx, kernels):
    """Add a (n_events, K) kernel matrix into dst at integer start indices (vectorised)."""
    K = kernels.shape[1]
    idx = start_idx[:, None] + np.arange(K)[None, :]
    ok = (idx >= 0) & (idx < len(dst))
    dst += np.bincount(idx[ok], weights=kernels[ok], minlength=len(dst))[:len(dst)]


def frac_time(times, K):
    n0 = np.floor(times * SR).astype(int)
    fr = times * SR - n0
    tt = (np.arange(K)[None, :] - fr[:, None]) / SR
    return n0, np.maximum(tt, 0.0), (tt >= 0)


def smooth(x, sec):
    return uniform_filter1d(x, max(1, int(sec * SR)), mode="nearest")


# ----------------------------------------------------------------------------------------------- clock
rpm = PchipInterpolator([T(f) for f, _ in RPM_KEYS], [r for _, r in RPM_KEYS])(t)
rpm = np.maximum(rpm, 0.0)
load = np.interp(t, [T(f) for f, _ in LOAD_KEYS], [v for _, v in LOAD_KEYS])

# lumpy idle: slow hunting of the idle speed (only where the engine idles)
idle_w = np.clip((1300 - rpm) / 500, 0, 1) * (t > T(CUE["flare_top"])) * (t < T(CUE["keyoff"]))
hunt = smooth(rng.standard_normal(N), 0.25)
hunt /= np.abs(hunt).max() + 1e-12
lope = np.sin(2 * np.pi * 1.7 * t + 0.6 * np.sin(2 * np.pi * 0.45 * t))  # big-cam lope: idle hunts
rpm = rpm + (45 * hunt + 55 * lope) * idle_w

# cranking: compression strokes slow the crank (two passes: angle -> compression -> rpm -> angle)
crank_zone = t < T(CUE["catch"]) + 0.03
for _ in range(2):
    A = np.cumsum(np.maximum(rpm, 1e-3)) * 6.0 / SR             # crank angle in degrees (rpm*6 deg/s)
    phi0 = np.interp(T(CUE["stab"]), t, A) % DEG_PER_FIRING
    comp = (0.5 + 0.5 * np.cos(np.deg2rad(4 * (A - phi0)))) ** 3   # 1 at each compression TDC
    rpm_c = np.where(crank_zone, rpm * (1 - 0.32 * comp), rpm)
A = np.cumsum(np.maximum(rpm_c, 1e-3)) * 6.0 / SR
rpm = rpm_c
phi0 = np.interp(T(CUE["stab"]), t, A) % DEG_PER_FIRING
# phase-lock the last firing before the cut to just before the cue: a tiny (<15 rpm) smooth trim of the second
# pull so that a firing angle lands CUT_LEAD seconds before frame 180 (the stab stays locked to frame 75)
CUT_LEAD = 0.0015
t_last = T(CUE["cut"]) - CUT_LEAD
need = (phi0 - np.interp(t_last, t, A)) % DEG_PER_FIRING          # degrees still to go to the next firing
need = need - DEG_PER_FIRING if need > DEG_PER_FIRING / 2 else need
win = np.clip((t - T(CUE["pull2"])) / (t_last - T(CUE["pull2"])), 0, 1)
win_rate = np.sin(np.pi * win) ** 2 * ((t > T(CUE["pull2"])) & (t < t_last))
rpm = rpm + need / (6.0 * win_rate.sum() / SR) * win_rate
A = np.cumsum(np.maximum(rpm, 1e-3)) * 6.0 / SR
comp = (0.5 + 0.5 * np.cos(np.deg2rad(4 * (A - phi0)))) ** 3
k_stab = int(round((np.interp(T(CUE["stab"]), t, A) - phi0) / DEG_PER_FIRING))

# firing events from crank angle
k_all = np.arange(0, int(A[-1] // DEG_PER_FIRING) + 1)
ang = phi0 + k_all * DEG_PER_FIRING
k_all, ang = k_all[ang < A[-1]], ang[ang < A[-1]]
ev_t = np.interp(ang, A, t)
ev_rpm = np.interp(ev_t, t, rpm)
ev_load = np.interp(ev_t, t, load)
cyl = np.array(FIRING_ORDER)[(k_all - k_stab) % 8]
bank = np.array([BANK[c] for c in cyl])
keep = ev_rpm > 25
ev_t, ev_rpm, ev_load, cyl, bank, k_all = ev_t[keep], ev_rpm[keep], ev_load[keep], cyl[keep], bank[keep], k_all[keep]
in_cut = (ev_t >= T(CUE["cut"]) - 0.0003) & (ev_t < T(CUE["cut_end"]))
fired = (ev_t >= T(CUE["catch"])) & (ev_t < T(CUE["keyoff"]) + 0.001) & ~in_cut
is_cue = np.abs(ev_t - T(CUE["stab"])) < 1e-6

# ----------------------------------------------------------------------------------------------- exhaust pulses
n_ev = len(ev_t)
cyl_amp = {1: 1.06, 2: 0.93, 3: 1.0, 4: 1.1, 5: 0.95, 6: 1.08, 7: 0.9, 8: 1.02}     # runner/port differences
cyl_res = {1: 1.0, 2: 1.07, 3: 0.95, 4: 1.03, 5: 0.97, 6: 1.05, 7: 0.93, 8: 1.01}
e_idle = np.clip((1300 - ev_rpm) / 500, 0, 1)
jit_sd = 0.00012 + 0.0009 * e_idle * fired
ev_tj = ev_t + rng.normal(0, 1, n_ev) * jit_sd * (~is_cue)
amp = (0.1 + 0.9 * ev_load) ** 1.25 * (0.6 + 0.4 * np.clip(ev_rpm / 6500, 0, 1.1))
amp *= np.array([cyl_amp[c] for c in cyl]) * (1 + rng.normal(0, 1, n_ev) * (0.07 + 0.10 * e_idle) * ~is_cue)
# cam overlap at idle: some cylinders randomly get a diluted charge and fire weakly (the lope)
weak = (rng.random(n_ev) < 0.32 * e_idle) & (ev_t > T(CUE["flare_top"]))
amp = np.where(weak, amp * rng.uniform(0.2, 0.55, n_ev), amp)
# the first few firings after the catch stutter (misfires)
first = fired & (ev_t < T(CUE["catch"]) + 0.09)
amp = np.where(first, amp * rng.choice([0.15, 0.6, 1.2], n_ev, p=[0.35, 0.3, 0.35]), amp)
amp = np.where(fired, amp, np.where(in_cut, 0.02, 0.045 * np.clip(ev_rpm / 200, 0, 1.5)))  # unfired: chuffs
bright = np.where(fired, np.clip(0.12 + 0.88 * ev_load, 0, 1) * (0.75 + 0.25 * np.clip(ev_rpm / 7000, 0, 1)), 0.0)
amp[is_cue] *= 1.35                                     # first full charge: the bark

K = int(0.032 * SR)
n0, tt, on = frac_time(ev_tj, K)
taper = np.clip((0.032 - tt) / 0.006, 0, 1)
b = bright[:, None]
tau = 2.2e-3 - 1.5e-3 * b
attack = 1 - np.exp(-tt / 0.00012)
# blow-down gas flow q(t) = (t/tau)^2 exp(2(1 - t/tau)); a pipe end radiates the pressure p ~ dq/dt, i.e. a sharp
# compression followed by a rarefaction (zero mean, so nothing steps or rings when the firing stops)
u = tt / tau
bump = u * (1 - u) * np.exp(2 * (1 - u)) / 0.853
fr_ring = (130 + 600 * b) * np.array([cyl_res[c] for c in cyl])[:, None]
ring = np.sin(2 * np.pi * fr_ring * tt) * np.exp(-tt / (16e-3 * (1 - b) ** 3 + 1.1e-3))
fr_hi = (750 + 1300 * b) * np.array([cyl_res[c] for c in cyl])[:, None]
ring2 = np.sin(2 * np.pi * fr_hi * tt) * np.exp(-tt / 0.9e-3) * (0.05 + 0.65 * b)
turb = rng.standard_normal((n_ev, K)) * np.exp(-tt / (0.9e-3 - 0.3e-3 * b)) * (0.03 + 0.52 * b)
kern = amp[:, None] * attack * (bump + 0.55 * ring + ring2 + turb) * on * taper
bus = np.zeros((2, N))
for bk in (0, 1):
    m = bank == bk
    scatter(bus[bk], n0[m], kern[m])

# ----------------------------------------------------------------------------------------------- overrun pops
pop_bus = np.zeros((2, N))
for f_a, f_b, dens in POP_WINDOWS:
    cand = np.where((ev_t > T(f_a)) & (ev_t < T(f_b)))[0]
    if len(cand) == 0:
        continue
    prog = (ev_t[cand] - T(f_a)) / (T(f_b) - T(f_a))
    p = dens * 0.075 * (1 - 0.8 * prog) * np.clip(ev_rpm[cand] / 3000, 0.4, 1.6)
    sel = cand[rng.random(len(cand)) < p]
    for i in sel:                                    # a few dozen events: per-event loop is short
        t0 = ev_t[i] + rng.uniform(0.6e-3, 3e-3)    # unburnt charge lights off after the valve opens
        bk = bank[i]
        kind = rng.random()
        L = int(0.04 * SR)
        x = np.arange(L) / SR
        if kind < 0.45:                              # bang
            a = rng.uniform(0.4, 0.75)
            k1 = a * ((x / 0.25e-3) * np.exp(1 - x / 0.25e-3) - (x / 1e-3) * np.exp(1 - x / 1e-3) / 4)
            k1 += a * 0.9 * rng.standard_normal(L) * np.exp(-x / 1.6e-3)
            k1 += a * 0.5 * np.sin(2 * np.pi * rng.uniform(90, 140) * x) * np.exp(-x / 0.012)
        else:                                        # crackle cluster
            k1 = np.zeros(L)
            for _ in range(rng.integers(3, 7)):
                o = rng.uniform(0, 0.028)
                xx = np.clip(x - o, 0, None)
                k1 += (x >= o) * rng.uniform(0.15, 0.45) * rng.standard_normal(L) * np.exp(-xx / 0.35e-3)
        s = int(t0 * SR)
        e = min(N, s + L)
        pop_bus[bk, s:e] += k1[:e - s]


# ----------------------------------------------------------------------------------------------- exhaust model
def pipe_ir(header_m, pipe_m, refl_h=-0.2, refl_p=-0.26, c=520.0, n_trips=5):
    """Exhaust waveguide as an impulse response: direct wave, inverting open-end reflections from the collector
    (header length) and the tailpipe (pipe length). Each round trip is low-passed and smeared a little more
    (perforated muffler tubes and wall losses make the reflections diffuse rather than a clean comb)."""
    L = int(0.08 * SR)
    h = np.zeros(L)
    h[0] = 1.0
    x = np.arange(L) / SR
    for length, refl in ((header_m, refl_h), (pipe_m, refl_p)):
        d = 2 * length / c
        for n in range(1, n_trips + 1):
            width = 0.00025 * length + 0.00012 * n * length   # Gaussian smear = frequency-dependent open-end reflection:
            #                                          low frequencies reflect, high frequencies radiate
            g = np.exp(-0.5 * ((x - n * d) / width) ** 2)
            g *= 1 + 0.6 * rng.standard_normal(L) * (n > 1)
            g /= g.sum() + 1e-12
            h += (refl ** n) * g
    return h


def peak_ba(f0, q, gain_db):
    A_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    al = np.sin(w0) / (2 * q)
    b_ = [1 + al * A_, -2 * np.cos(w0), 1 - al * A_]
    a_ = [1 + al / A_, -2 * np.cos(w0), 1 - al / A_]
    return np.array(b_) / a_[0], np.array(a_) / a_[0]


def muffler(x, chamber_ms, fc, body_hz):
    D = int(chamber_ms * 1e-3 * SR)
    y = x.copy()
    y[D:] += 0.4 * x[:-D]                            # expansion chamber reflection
    y = signal.lfilter(*peak_ba(body_hz, 3.0, 6.5), y)   # big chambered can: Helmholtz body resonance
    return signal.sosfilt(signal.butter(2, fc, "low", fs=SR, output="sos"), y)


HEADER_LEN = (0.92, 1.08)     # big-block log-style primaries into the collector
PIPE_LEN = (2.95, 3.25)       # long dual pipes to the rear bumper
CHAMBER = (1.7, 2.05)         # old chambered mufflers
BODY_HZ = (72, 65)
JET_LEVEL = 0.6
GULP = 0.5
WHIR = 0.10
PUMP = 0.25


def jet_env(hold=0.030, tau_d=0.016):
    """Tailpipe jet-noise envelope after the X-pipe crossover (both banks' gas merges there): each blow-down
    drives the gas jet until the next exhaust event (sample-and-hold of the pulse energy, decaying, at most `hold`
    long). When the ignition is cut the next blow-down is a weak unfired one, so the jet collapses within one
    firing interval."""
    te, ve = ev_tj, amp * (0.55 + 0.45 * bright)
    idx = np.searchsorted(te, t, side="right") - 1
    ok = idx >= 0
    age = np.where(ok, t - te[np.maximum(idx, 0)], 1.0)
    env = np.where(ok & (age < hold), ve[np.maximum(idx, 0)] * np.exp(-age / tau_d), 0.0)
    return uniform_filter1d(env, int(0.0003 * SR))


jet_shape = signal.butter(2, [380, 5200], "bandpass", fs=SR, output="sos")
JET_ENV = jet_env()
ex = np.zeros((2, N))
for bk in (0, 1):
    y = signal.fftconvolve(bus[bk] + 0.5 * pop_bus[bk], pipe_ir(HEADER_LEN[bk], PIPE_LEN[bk]))[:N]
    y = muffler(y, CHAMBER[bk], 2000, BODY_HZ[bk])
    jet = signal.sosfilt(jet_shape, rng.standard_normal(N)) * JET_ENV
    y += JET_LEVEL * jet / (np.abs(jet).max() + 1e-12) * np.abs(y).max()
    y += 0.55 * signal.sosfilt(signal.butter(2, 6000, "low", fs=SR, output="sos"), pop_bus[bk])  # crack at the tip
    ex[bk] = y
ex /= np.abs(ex).max()
drive = 1.2
ex = signal.resample_poly(np.tanh(drive * signal.resample_poly(ex, 2, 1, axis=-1)), 1, 2, axis=-1) / np.tanh(drive)  # 2x OS

# ----------------------------------------------------------------------------------------------- intake roar
# throttle = pedal, load = combustion. Through the 80 ms ignition cut the pedal is part-lifted for the shift.
THROTTLE_IN_CUT = 0.15
thr_raw = np.interp(t, [T(f) for f, _ in LOAD_KEYS], [v for _, v in LOAD_KEYS])
in_cut_t = (t >= T(CUE["cut"])) & (t < T(CUE["cut_end"]))
thr = smooth(np.where(in_cut_t, THROTTLE_IN_CUT, thr_raw) * (t >= T(CUE["catch"])), 0.004)
thr = np.concatenate([np.full(int(0.002 * SR), thr[0]), thr[:-int(0.002 * SR)]])   # causal: opens ON the cue
# induction pulsation follows the intake valves (crank angle), with or without combustion
pulse_env = (0.5 + 0.5 * np.cos(np.deg2rad(4 * (A - phi0) + 40))) ** 2
centers = np.array([260, 420, 680, 1100, 1750, 2800])
fc_t = 280 + 2300 * thr * np.clip(rpm / 7000, 0, 1)
pos = np.interp(np.log(fc_t), np.log(centers), np.arange(len(centers)))
noise = rng.standard_normal(N)
intake = np.zeros(N)
for i, fc in enumerate(centers):
    w = np.clip(1 - np.abs(pos - i), 0, 1)
    intake += w * signal.sosfilt(bp_sos(fc, 1.3), noise)
intake *= (0.05 + thr) * (0.15 + 0.85 * np.clip(rpm / 7000, 0, 1)) * (0.55 + 0.9 * pulse_env)
intake *= 0.55 / (np.abs(intake).max() + 1e-12)
# throttle-opening gulp: the plenum fills with a rush of air the instant the butterfly snaps open
for name, a in (("stab", 1.0), ("pull2", 0.6)):
    tg = t - T(CUE[name])
    gulp = signal.sosfilt(bp_sos(700, 0.9), rng.standard_normal(N))
    intake += GULP * a * gulp / np.abs(gulp).max() * (tg >= 0) * (1 - np.exp(-np.maximum(tg, 0) / 0.0015)) \
        * np.exp(-np.maximum(tg, 0) / 0.11)

# ----------------------------------------------------------------------------------------------- valvetrain + belt
kv = np.arange(0, int(A[-1] // 45) + 1)
v_ang = phi0 + kv * 45.0
v_ang = v_ang[v_ang < A[-1]]
v_t = np.interp(v_ang, A, t)
v_r = np.interp(v_t, t, rpm)
v_t, v_r, kv = v_t[v_r > 40], v_r[v_r > 40], np.arange(len(v_ang))[v_r > 40]
Kv = int(0.002 * SR)
vn0, vtt, von = frac_time(v_t + rng.normal(0, 4e-5, len(v_t)), Kv)
v_amp = (0.012 + 0.005 * rng.random(len(v_t))) * np.where(kv % 16 == 5, 2.4, 1.0)
v_f = rng.uniform(3800, 7200, len(v_t))[:, None]
vk = v_amp[:, None] * von * np.exp(-vtt / 0.22e-3) * (np.sin(2 * np.pi * v_f * vtt) + 0.6 * rng.standard_normal((len(v_t), Kv)))
valve = np.zeros(N)
scatter(valve, vn0, vk)
belt_ph = 2 * np.pi * np.cumsum(12 * rpm / 60) / SR
belt = 0.006 * (np.sin(belt_ph) + 0.4 * np.sin(2 * belt_ph)) * np.clip(rpm / 2000, 0, 1) * (rpm * 12 / 60 < 7000)

# ----------------------------------------------------------------------------------------------- starter motor
st = np.zeros(N)
t_dis = T(CUE["disengage"])
crank_rpm = np.minimum(rpm, 260)
f_st = 185 * crank_rpm / 210
f_st = np.where(t < t_dis, f_st, np.interp(t_dis, t, f_st) * np.exp(-(t - t_dis) / 0.09))
ph = 2 * np.pi * np.cumsum(f_st) / SR
st_env = np.clip(t / 0.012, 0, 1) * np.where(t < t_dis, 1.0, np.exp(-(t - t_dis) / 0.06))
st_env *= (0.75 + 0.5 * np.where(crank_zone, comp, 0)) * (t < t_dis + 0.4)
zone = t < t_dis + 0.4
for k in range(1, 70):
    fk = k * f_st[zone]
    a_k = (1 / k ** 1.3) * (1 + 4.0 * np.exp(-((k * 185 - 1480) / 380) ** 2))
    st[zone] += a_k * np.sin(k * ph[zone] + 0.7 * k) * (fk < 15000)
brush = signal.sosfilt(bp_sos(4500, 1.5), rng.standard_normal(N)) * (1 + np.sin(9 * ph)) * 0.6
st = (st / (np.abs(st[zone]).max() + 1e-12) + 0.25 * brush) * st_env


def clack(t0, a, freqs, dec):
    L = int(max(0.06, 6 * max(dec)) * SR)
    x = np.arange(L) / SR
    k = sum(np.sin(2 * np.pi * f * x) * np.exp(-x / d) for f, d in zip(freqs, dec))
    k = k / len(freqs) + 0.8 * rng.standard_normal(L) * np.exp(-x / 0.0015)
    k *= np.sin(0.5 * np.pi * np.clip(x / 0.0003, 0, 1)) * np.clip((x[-1] - x) / (0.2 * x[-1]), 0, 1)
    out = np.zeros(N)
    s = int(round(t0 * SR))
    out[s:s + L] = a * k[:N - s]
    return out


st = 0.55 * st / (np.abs(st).max() + 1e-12)
st += clack(T(CUE["starter"]), 0.6, [1900, 3350, 5200], [0.012, 0.008, 0.004])
st += clack(t_dis, 0.35, [1500, 2700, 4400], [0.01, 0.006, 0.004])

# ----------------------------------------------------------------------------------------------- key-off shudder + ticks
mech = np.zeros(N)
L = int(0.15 * SR)
x = np.arange(L) / SR
for dt_, a in [(0.055, 1.0), (0.115, 0.55)]:
    s = int((T(CUE["keyoff"]) + dt_) * SR)
    th = sum(np.sin(2 * np.pi * h * 46 * x) / h ** 1.2 for h in (1, 2, 3)) * np.exp(-x / 0.035)
    th *= np.clip(x / 0.004, 0, 1)
    rattle = sum((x > o) * rng.standard_normal(L) * np.exp(-np.clip(x - o, 0, None) / 0.0008)
                 for o in rng.uniform(0.002, 0.04, 5)) * 0.12
    mech[s:s + L] += a * (0.5 * th + rattle) * np.clip((x[-1] - x) / 0.03, 0, 1)
for name, a in [("tick1", 0.10), ("tick2", 0.075)]:
    mech += clack(T(CUE[name]), a, [2950, 4620, 7330, 10150], [0.03, 0.022, 0.014, 0.009])

# ----------------------------------------------------------------------------------------------- mix
cross = 0.28
mix = np.zeros((2, N))
mix[0] = ex[0] + cross * ex[1]
mix[1] = ex[1] + cross * ex[0]
in_l = intake
in_r = np.roll(intake, 23)
mix[0] += 0.42 * in_l
mix[1] += 0.42 * in_r
# rotating-assembly whir: broadband block noise that follows rpm (fills the gaps between idle pulses)
running = smooth(((t > T(CUE["catch"])) & (t < T(CUE["keyoff"]) + 0.05)).astype(float), 0.03)
whir = signal.sosfilt(signal.butter(2, [130, 1100], "bandpass", fs=SR, output="sos"), rng.standard_normal(N))
whir *= WHIR * running * (0.4 + 0.6 * np.clip(rpm / 7000, 0, 1)) / np.abs(whir).max()
# overrun pumping: with no combustion the pistons still shove air through the pipes -> a broadband whoosh that
# grows with rpm whenever the load is off (lift-off, the ignition cut)
# (it starts with the first unfired blow-down, ~3 ms after the spark is cut)
off = np.roll(smooth(np.clip(1 - load, 0, 1) * running, 0.002), int(0.003 * SR)) * np.clip(rpm / 7000, 0, 1) ** 1.5
pump = signal.sosfilt(signal.butter(2, [300, 7000], "bandpass", fs=SR, output="sos"), rng.standard_normal(N))
pump *= PUMP * off / np.abs(pump).max()
mech_c = valve + belt + whir + pump
mix += np.array([1.0, 0.9])[:, None] * mech_c
mix += np.array([0.9, 1.0])[:, None] * st * 0.6
mix += mech * 0.8

# ----------------------------------------------------------------------------------------------- pass-by
# outdoors: no room. The car is a point source with a narrow bank spread; the listener hears it through
#  * Doppler: the signal is read at the emission time tau(t) that arrives at t (direct and ground paths),
#  * 1/r spreading, * a ground reflection (sweeping comb, the classic pass-by flange),
#  * air absorption: a low-pass whose cutoff falls with distance, * an equal-power left -> right pan.
src = mix
src_mid, src_side = 0.5 * (src[0] + src[1]), 0.5 * (src[0] - src[1])
idx = np.arange(N, dtype=float)


def heard(t_arrival, r_path):
    tau = np.interp(t, t_arrival, t)                           # emission time heard at t
    m = np.interp(tau * SR, idx, src_mid)
    sd = np.interp(tau * SR, idx, src_side)
    g = R_REF / np.interp(tau, t, r_path)
    return m * g, sd * g, tau


mid_d, side_d, tau_d = heard(t_arr, r_dir)
mid_g, _, _ = heard(t_arr_g, r_gnd)
y_mid = mid_d + GROUND_R * mid_g
r_now = np.interp(tau_d, t, r_dir)
x_now = np.interp(tau_d, t, pos_x)

# air absorption: crossfade a bank of low-passes by distance (cutoff ~ 18 kHz at 3 m, ~4 kHz at 40 m)
fc_now = np.clip(18000 * (3.0 / r_now) ** 0.55, 2500, 18000)
lp_fc = np.array([2500, 4000, 6500, 10500, 18000])
pos_lp = np.interp(np.log(fc_now), np.log(lp_fc), np.arange(len(lp_fc)))


def air(x):
    out = np.zeros(N)
    for i, fc in enumerate(lp_fc):
        w = np.clip(1 - np.abs(pos_lp - i), 0, 1)
        out += w * signal.sosfilt(signal.butter(2, min(fc, 20000), "low", fs=SR, output="sos"), x)
    return out


y_mid = air(y_mid)
side = air(side_d) * 0.3 * np.clip(8.0 / r_now, 0, 1)         # the two banks only separate up close
az = np.arctan2(x_now, LATERAL)                                # -90 deg (left) .. +90 deg (right)
pan = 0.5 + 0.5 * np.sin(az)
mix = np.stack([np.cos(0.5 * np.pi * pan) * y_mid * np.sqrt(2) + side,
                np.sin(0.5 * np.pi * pan) * y_mid * np.sqrt(2) - side])


# ----------------------------------------------------------------------------------------------- master
def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=-1), axis=-1)


def lufs(x):
    y = k_weight(x) ** 2
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    cs = np.concatenate([np.zeros((2, 1)), np.cumsum(y, axis=1)], axis=1)
    st_ = np.arange(0, y.shape[1] - blk + 1, hop)
    z = ((cs[:, st_ + blk] - cs[:, st_]) / blk).sum(axis=0)
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return -0.691 + 10 * np.log10(z2.mean())


def true_peak(x):
    return np.abs(signal.resample_poly(x, 4, 1, axis=-1)).max()


def limiter(x, ceil_db):
    c = 10 ** (ceil_db / 20)
    os_ = np.abs(signal.resample_poly(x, 4, 1, axis=-1)).max(axis=0)
    p = os_[:N * 4].reshape(N, 4).max(axis=1)
    greq = np.minimum(1.0, c / (p + 1e-12))
    W = int(0.004 * SR)               # look-ahead / gain smoothing
    R = int(0.045 * SR)               # hold: the gain does not recover inside short gaps (keeps the cut a cut)
    gc = minimum_filter1d(greq, R + W + 1)                     # window [n-R, n+W] after the shift below
    k = (R - W) // 2
    gc = np.concatenate([np.full(k, gc[0]), gc[:-k]])
    g = uniform_filter1d(gc, 2 * W + 1)
    return x * np.minimum(g, 1.0)


sos_hp = signal.butter(2, 25, "high", fs=SR, output="sos")
mix = signal.sosfilt(sos_hp, mix, axis=-1)
# mono below 120 Hz: high-pass only the side signal (the mid path stays unfiltered, so nothing rings on the cut)
mid, side = 0.5 * (mix[0] + mix[1]), 0.5 * (mix[0] - mix[1])
side = signal.sosfilt(signal.butter(4, 120, "high", fs=SR, output="sos"), side)
mix = np.stack([mid + side, mid - side])

# fader ride: a slow 2.5:1 compressor on the 300 ms level, so the close pass is turned down smoothly instead of
# being chopped by the peak limiter (the 1/r swing stays audible, just not 15 dB of it)
lev = 10 * np.log10(uniform_filter1d((mix ** 2).sum(axis=0), int(0.3 * SR)) + 1e-12)
loud = lev > lev.max() - 30
thr_db = np.percentile(lev[loud], 55)
ride_db = uniform_filter1d(-(1 - 1 / 2.5) * np.maximum(0, lev - thr_db), int(0.15 * SR))
mix *= 10 ** (ride_db / 20)
fade = np.clip((CUE["end"] / FPS - t) / 0.06, 0, 1)
mix *= fade
pre_master = mix.copy()
gain = 10 ** ((TARGET_LUFS - lufs(mix)) / 20)
for _ in range(8):                                             # gain into the limiter until the OUTPUT hits target
    out_ = limiter(mix * gain, -1.35)
    gain *= 10 ** ((TARGET_LUFS - lufs(out_)) / 20)
mix = limiter(mix * gain, -1.35)
tp = true_peak(mix)
if tp > 10 ** (-1.1 / 20):
    mix *= 10 ** (-1.1 / 20) / tp
assert np.all(np.isfinite(mix))

out = np.clip(np.round(mix.T * 32767), -32768, 32767).astype("<i2")
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "take-1.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(out.tobytes())
print(f"wrote {out.shape[0]} samples, {lufs(mix):.2f} LUFS, TP {20*np.log10(true_peak(mix)):.2f} dBTP, "
      f"{int(fired.sum())} firings, {n_ev} crank events")
