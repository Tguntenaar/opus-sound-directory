"""Cozy UI kit, 8-sound sprite (ui-cozy-sprite), take 2: wooden mallets.

Creative brief:
A 4.0-second UI sound sprite, 192,000 samples at 48 kHz stereo, eight sounds each starting exactly on
frames 0, 15, 30, 45, 60, 75, 90, 105 at 30 fps (every 0.5 s) and each fully silent before the next
slot, so each can be sliced: 1 tap, 2 toggle-on, 3 toggle-off, 4 bubble pop, 5 success, 6 error,
7 notification, 8 delete swoosh. Cozy, rounded and bubbly; all pitched material in F major pentatonic
(F G A C D) so the set feels like one product. Each sound <= 300 ms: soft bodies with a 1-2 ms
transient, gentle pitch glides (up for positive actions, down for toggle-off and delete), a felt-like
low-passed error (two notes falling a minor third), and a pop built from a fast-rising resonant
band-pass blip. Nothing above 9 kHz, nothing harsh, pleasant on the hundredth repeat; low end mono.
Roughly equal perceived loudness per slot. About -17 LUFS integrated, true peak <= -1 dBTP.
Prints a JSON cue map (slot, name, start sample, end sample) to stdout.

Take angle 2 (wooden mallets): every pitched sound is modal mallet synthesis. Marimba-like tuned bars
(modes 1 : 3.99 : 9.83) and kalimba/free-bar tines (1 : 2.76 : 5.40) ring as decaying sines whose upper
modes die much faster; each strike is convolved with a 0.6-2 ms felt contact pulse, which is both the
soft transient and the felt low-pass. Marimba notes get a slow-blooming resonator-tube fundamental.
  1 tap           a tiny wooden 'tock': C5 free-bar modes, 0.5 ms contact, short knock
  2 toggle-on     marimba C5 -> F5 two-stroke flam, each bar bending up into pitch
  3 toggle-off    marimba F5 -> C5, second stroke softer, bars drooping slightly
  4 bubble pop    felt-mallet pulse into a resonant band-pass shooting D5 -> D6, a small wooden cup ring
  5 success       marimba F5-A5-C6-F6 rising roll, last bar ringing
  6 error         heavy-felt low marimba F4 -> D4 (falling minor third), low-passed, centred
  7 notification  kalimba tines A5 -> D6
  8 delete swoosh descending marimba roll F6-D6-C6-A5-G5-F5 sweeping right to left over a soft brown-noise
                  swoosh falling 2 kHz -> 400 Hz

usage: python take-2.py OUT.wav
"""

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")
import json
import sys
import wave

import numpy as np
from scipy import signal

SR = 48000
N_TOTAL = 192000          # 4.0 s
SLOT = 24000              # 0.5 s = 15 frames at 30 fps
MAX_LEN = 14400           # 300 ms per sound
SEED = 43
rng = np.random.default_rng(SEED)

# F major pentatonic, equal temperament (A4 = 440)
NOTE = {n: 440.0 * 2 ** (k / 12) for n, k in {
    "F3": -16, "G3": -14, "A3": -12, "C4": -9, "D4": -7, "F4": -4, "G4": -2, "A4": 0, "C5": 3, "D5": 5,
    "F5": 8, "G5": 10, "A5": 12, "C6": 15, "D6": 17, "F6": 20, "G6": 22, "A6": 24}.items()}

t = np.arange(MAX_LEN) / SR
HP = signal.butter(2, 25, "highpass", fs=SR, output="sos")
LP = signal.butter(8, 7500, "lowpass", fs=SR, output="sos")
XO = signal.butter(4, 250, "highpass", fs=SR, output="sos")


def smooth01(u):
    u = np.clip(u, 0.0, 1.0)
    return 0.5 - 0.5 * np.cos(np.pi * u)


def env(start=0.0, attack=0.0015, tau=0.06):
    tt = t - start
    a = np.where(tt < 0, 0.0, smooth01(tt / attack))
    return a * np.exp(-np.maximum(tt - attack, 0.0) / tau)


def freq_track(f1, start=0.0, f0=None, glide=0.03, curve="cos"):
    """log-frequency glide f0 -> f1 over `glide` seconds from note start, then hold"""
    if f0 is None:
        return np.full(MAX_LEN, float(f1))
    u = np.clip((t - start) / glide, 0, 1)
    s = smooth01(u) if curve == "cos" else 1 - (1 - u) ** 3
    return f0 * (f1 / f0) ** s


def phase(freq, start=0.0):
    on = (t >= start).astype(float)
    return 2 * np.pi * np.cumsum(freq * on) / SR


def tri(ph, bright=1.0):
    """band-limited soft triangle (first three odd harmonics)"""
    return (np.sin(ph) - bright * np.sin(3 * ph) / 9 + bright * np.sin(5 * ph) / 25) / 1.15


def note(f1, start=0.0, tau=0.06, attack=0.0015, f0=None, glide=0.03, kind="sine", bright=1.0, curve="cos"):
    ph = phase(freq_track(f1, start, f0, glide, curve), start)
    w = np.sin(ph) if kind == "sine" else tri(ph, bright)
    return w * env(start, attack, tau)


def tick(start=0.0, dur=0.0015, lp=3500, amp=1.0):
    """1-2 ms soft noise transient, low-passed"""
    x = np.zeros(MAX_LEN)
    i, k = int(start * SR), int(dur * SR)
    x[i:i + k] = rng.standard_normal(k) * np.hanning(k + 2)[1:-1]
    return amp * signal.sosfilt(signal.butter(2, lp, "lowpass", fs=SR, output="sos"), x)


def tv_bandpass(x, fc, q, block=24):
    """time-varying resonant band-pass (RBJ, 0 dB peak), coefficients updated every `block` samples"""
    y = np.zeros_like(x)
    zi = np.zeros(2)
    for s in range(0, len(x), block):
        w0 = 2 * np.pi * fc[s] / SR
        al = np.sin(w0) / (2 * q)
        b = np.array([al, 0.0, -al]) / (1 + al)
        a = np.array([1.0, -2 * np.cos(w0) / (1 + al), (1 - al) / (1 + al)])
        y[s:s + block], zi = signal.lfilter(b, a, x[s:s + block], zi=zi)
    return y


def place(x, pan=0.0):
    """stereo placement: the low end stays mono, only the band above ~250 Hz is panned (constant power)"""
    high = signal.sosfilt(XO, x)
    low = x - high
    th = (np.asarray(pan) + 1) * np.pi / 4
    gl, gr = np.cos(th) * np.sqrt(2), np.sin(th) * np.sqrt(2)
    return np.stack([low + high * gl, low + high * gr], axis=1)


def finish(st, fade=0.05):
    """DC/HF clean-up and a hard guarantee of silence from 300 ms on"""
    st = signal.sosfilt(LP, signal.sosfilt(HP, st, axis=0), axis=0)
    w = np.zeros(MAX_LEN)                           # fade done by 295 ms: margin for the final band-limit
    e = MAX_LEN - int(0.005 * SR)
    k = int(fade * SR)
    w[:e - k] = 1.0
    w[e - k:e] = 0.5 + 0.5 * np.cos(np.pi * np.arange(1, k + 1) / k)
    return st * w[:, None]


# ---------------------------------------------------------------- the eight sounds
MARIMBA = ((1.0, 1.0), (3.99, 0.55), (9.83, 0.16))
TINE = ((1.0, 1.0), (2.76, 0.40), (5.40, 0.14))


def contact(x, dur):
    """felt mallet contact: convolve the modal ring with a Hann force pulse of `dur` seconds"""
    k = max(3, int(dur * SR))
    p = np.hanning(k + 2)[1:-1]
    return np.convolve(x, p / p.sum())[:MAX_LEN]


def bar(f, start=0.0, modes=MARIMBA, tau=0.12, hard=0.001, vel=1.0, bend_cents=0.0, bend_t=0.03, tube=0.0):
    """one mallet stroke: decaying modes (upper modes die ~ ratio^-1.1 faster), optional pitch bend
    from `bend_cents` into pitch, optional marimba resonator-tube bloom"""
    tt = t - start
    on = tt >= 0
    bend = 2 ** (bend_cents / 1200 * (1 - smooth01(tt / bend_t)))
    x = np.zeros(MAX_LEN)
    for r, a in modes:
        if f * r > 7000:
            continue
        ph = phase(f * r * bend, start)
        x += a * np.sin(ph) * np.exp(-np.maximum(tt, 0) / (tau / r ** 1.1)) * on
    if tube:
        x += tube * np.sin(phase(f * bend, start)) * env(start, 0.008, tau * 1.3)
    return vel * contact(x, hard)


def s_tap():
    x = bar(NOTE["C5"], modes=TINE, tau=0.05, hard=0.0005)
    x += tick(0.0, 0.001, lp=1800, amp=0.25)                        # dry knock of the wood
    return place(x)


def s_toggle_on():
    out = place(bar(NOTE["C5"], 0.0, tau=0.1, hard=0.0009, vel=0.75, bend_cents=-30, tube=0.3), -0.1)
    out += place(bar(NOTE["F5"], 0.05, tau=0.12, hard=0.0009, bend_cents=-30, tube=0.3), 0.15)
    return out


def s_toggle_off():
    out = place(bar(NOTE["F5"], 0.0, tau=0.1, hard=0.0011, bend_cents=25, tube=0.3), 0.1)
    out += place(bar(NOTE["C5"], 0.05, tau=0.11, hard=0.0013, vel=0.7, bend_cents=25, tube=0.3), -0.15)
    return out


def s_bubble_pop():
    exc = contact(np.r_[1.0, np.zeros(MAX_LEN - 1)], 0.0008)
    fc = NOTE["D5"] * (NOTE["D6"] / NOTE["D5"]) ** (1 - (1 - np.clip(t / 0.02, 0, 1)) ** 2)
    x = tv_bandpass(exc, fc, q=200)
    x = x / np.abs(x).max() * np.exp(-t / 0.12)
    x += 0.3 * bar(NOTE["D6"], 0.012, modes=TINE, tau=0.05, hard=0.001)  # small wooden cup answering
    return place(x, 0.05)


def s_success():
    out = np.zeros((MAX_LEN, 2))
    for n, st, v, p in (("F5", 0.0, 0.75, -0.25), ("A5", 0.055, 0.8, -0.08),
                        ("C6", 0.11, 0.88, 0.08), ("F6", 0.165, 1.0, 0.25)):
        out += place(bar(NOTE[n], st, tau=0.12 if n != "F6" else 0.16, hard=0.0008, vel=v, tube=0.25), p)
    return out


def s_error():
    felt = signal.butter(2, 1200, "lowpass", fs=SR, output="sos")
    x = bar(NOTE["F4"], 0.0, tau=0.13, hard=0.002, tube=0.5)
    x += bar(NOTE["D4"], 0.12, tau=0.15, hard=0.002, vel=0.95, tube=0.5)
    x += tick(0.0, 0.002, lp=500, amp=0.3) + tick(0.12, 0.002, lp=500, amp=0.3)   # felt thumps
    return place(signal.sosfilt(felt, x))


def s_notification():
    out = place(bar(NOTE["A5"], 0.0, modes=TINE, tau=0.13, hard=0.0007, vel=0.85), -0.12)
    out += place(bar(NOTE["D6"], 0.09, modes=TINE, tau=0.16, hard=0.0007), 0.12)
    return out


def s_delete():
    out = np.zeros((MAX_LEN, 2))
    seq = ("F6", "D6", "C6", "A5", "G5", "F5")
    for i, n in enumerate(seq):
        out += place(bar(NOTE[n], 0.028 * i, tau=0.06, hard=0.0009, vel=1.0 - 0.1 * i), 0.4 - 0.16 * i)
    brown = np.cumsum(rng.standard_normal(MAX_LEN))
    brown = signal.sosfilt(signal.butter(2, 150, "highpass", fs=SR, output="sos"), brown)
    fc = 2000 * (400 / 2000) ** smooth01(t / 0.2)
    air = tv_bandpass(brown, fc, q=1.2)
    air *= env(0.0, 0.002, 0.07) / (np.abs(air[:4800]).max() + 1e-9) * 0.35
    pan = 0.4 - 0.8 * smooth01(t / 0.2)
    return out + place(air, pan)


SOUNDS = [("tap", s_tap), ("toggle-on", s_toggle_on), ("toggle-off", s_toggle_off),
          ("bubble pop", s_bubble_pop), ("success", s_success), ("error", s_error),
          ("notification", s_notification), ("delete swoosh", s_delete)]


# ---------------------------------------------------------------- loudness helpers (BS.1770)
def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs_integrated(x):
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[s:s + blk] ** 2, axis=0).sum() for s in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean()))


def slot_momentary(st):
    """K-weighted level of one slot over a 400 ms window from its onset (BS.1770 momentary)"""
    y = k_weight(np.concatenate([st, np.zeros((SLOT, 2))]))
    return float(-0.691 + 10 * np.log10(np.sum(y[:int(0.4 * SR)] ** 2) / (0.4 * SR) + 1e-20))


def true_peak_db(x):
    return float(20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12))


def soft_ceiling(x, ceil, knee=0.85):
    """transparent below knee*ceil; above it a tanh shoulder that never exceeds ceil (rounds the 1-2 ms
    attack peaks of the shortest sounds instead of turning the whole sprite down)"""
    k = knee * ceil
    a = np.abs(x)
    y = np.where(a > k, k + (ceil - k) * np.tanh((a - k) / (ceil - k)), a)
    return np.sign(x) * y


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT
    slots = [finish(fn()) for _, fn in SOUNDS]
    ref = -20.0
    slots = [s * 10 ** ((ref - slot_momentary(s)) / 20) for s in slots]
    mix = np.zeros((N_TOTAL, 2))
    for i, s in enumerate(slots):
        mix[i * SLOT:i * SLOT + MAX_LEN] = s
    def master(g):                                  # gain, soft ceiling, re-band-limit what the shoulder made
        return signal.sosfilt(LP, soft_ceiling(mix * g, 10 ** (-1.45 / 20)), axis=0)
    g = 1.0
    for _ in range(5):                              # converge on -17 LUFS integrated
        g *= 10 ** ((-17.0 - lufs_integrated(master(g))) / 20)
    mix = master(g)
    tp = true_peak_db(mix)
    if tp > -1.3:                                   # stay safely under -1 dBTP after 16-bit rounding
        mix *= 10 ** ((-1.3 - tp) / 20)
    assert np.all(np.isfinite(mix))
    pcm = np.clip(np.round(mix * 32767), -32768, 32767).astype("<i2")
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    cues = []
    for i, (name, _) in enumerate(SOUNDS):
        s0 = i * SLOT
        nz = np.nonzero(np.abs(pcm[s0:s0 + SLOT].astype(int)).max(axis=1))[0]
        cues.append({"slot": i + 1, "name": name, "frame": 15 * i, "start_sample": s0,
                     "end_sample": int(s0 + nz[-1] + 1)})
    print(json.dumps(cues, indent=1))
    x = pcm.astype(float) / 32768
    lv = [slot_momentary(x[i * SLOT:i * SLOT + MAX_LEN]) for i in range(8)]
    print(f"{out_path}: {lufs_integrated(x):.2f} LUFS, {true_peak_db(x):.2f} dBTP, slot LUFS-M "
          + " ".join(f"{v:.1f}" for v in lv), file=sys.stderr)


if __name__ == "__main__":
    main()
