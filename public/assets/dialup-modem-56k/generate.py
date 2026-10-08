"""56k modem handshake, take 2 (gritty handset).

Creative brief:
A 12-second 56k dial-up modem connection, 576,000 samples, 30 fps, everything band-limited to a
300-3,400 Hz telephone line with faint line hiss and slight 2nd-harmonic distortion. Timeline:
0-1.0 s off-hook dial tone (350 + 440 Hz); 1.0-2.4 s seven DTMF digits (standard row/column pairs,
100 ms tone / 100 ms gap); 2.6-3.6 s one ringback burst (440 + 480 Hz); 3.8-6.0 s answer tone
2,100 Hz with 180 degree phase reversals every 450 ms and 15 Hz amplitude modulation; 6.0-7.0 s
V.21-style FSK bursts (1,650/1,850 Hz at 300 baud, random bits) answered by the other side;
7.0-9.0 s V.34-style line probing: a comb of tones every 150 Hz from 150 to 3,750 Hz with phase
reversals (the "bong" chirps), then 9.0-12.0 s loud scrambled training noise in rhythmic bursts
with a rising hiss, cutting to dead silence through a 3 ms fade ending exactly on frame 360
("connected"). Mono-centred with slight width. Tame 2-3 kHz harshness.

Take angle 2 (gritty handset): same protocol timeline, heard through an old handset: carbon-mic-
style nonlinearity, a slightly narrower line (400-3,200 Hz), a little 60 Hz-free crackle, and extra
emphasis on the V.34 probing 'bongs' and the warbling V.8 / V.90 negotiation between 7 and 9 s; the
training section is grainier with stuttering bursts. (The carbon-mic asymmetry supplies the 2nd-
harmonic distortion.) Original synthesis from the protocol description; no recording is sampled.

usage: python take-2.py OUT.wav
"""

import os as _os
OUT_DEFAULT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out.wav")
import sys
import wave

import numpy as np
from scipy import ndimage, signal

SR = 48000
N = 576000
SEED = 43
rng = np.random.default_rng(SEED)
t = np.arange(N) / SR


def idx(sec):
    return int(round(sec * SR))


def gate(t0, t1, ramp=0.004):
    """1 inside [t0, t1), raised-cosine ramps of `ramp` s inside the window, 0 elsewhere."""
    e = np.zeros(N)
    i0, i1 = idx(t0), min(idx(t1), N)
    e[i0:i1] = 1.0
    r = idx(ramp)
    if r > 0:
        w = 0.5 - 0.5 * np.cos(np.pi * np.arange(r) / r)
        e[i0:i0 + r] *= w
        if idx(t1) <= N:
            e[i1 - r:i1] *= w[::-1]
    return e


def tone(f, phase=0.0):
    return np.sin(2 * np.pi * f * t + phase)


def fsk(t0, t1, f_mark, f_space, baud=300, amp=1.0):
    """Phase-continuous binary FSK with random bits between t0 and t1."""
    i0, i1 = idx(t0), idx(t1)
    n = i1 - i0
    spb = SR // baud
    bits = rng.integers(0, 2, n // spb + 2)
    f = np.where(np.repeat(bits, spb)[:n] == 1, f_mark, f_space)
    ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 2 * np.pi)
    out = np.zeros(N)
    out[i0:i1] = amp * np.sin(ph)
    return out * gate(t0, t1, 0.003)


def lufs(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    p = np.cumsum(np.concatenate([np.zeros((1, y.shape[1])), y ** 2]), axis=0)
    starts = np.arange(0, len(y) - blk + 1, hop)
    z = ((p[starts + blk] - p[starts]) / blk).sum(axis=1)
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lk > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return -0.691 + 10 * np.log10(z2.mean())


def true_peak_db(x):
    return 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)


def peaking(f0, gain_db, q):
    a = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    al = np.sin(w0) / (2 * q)
    b = [1 + al * a, -2 * np.cos(w0), 1 - al * a]
    aa = [1 + al / a, -2 * np.cos(w0), 1 - al / a]
    return np.array(b) / aa[0], np.array(aa) / aa[0]


# ---------------------------------------------------------------- 0-1.0 s: dial tone
line = 0.26 * (tone(350) + tone(440)) * gate(0.0, 1.0, 0.010)

# ---------------------------------------------------------------- 1.0-2.4 s: 7 DTMF digits
ROWS = [697, 770, 852, 941]
COLS = [1209, 1336, 1477]
KEYS = {"1": (0, 0), "2": (0, 1), "3": (0, 2), "4": (1, 0), "5": (1, 1), "6": (1, 2),
        "7": (2, 0), "8": (2, 1), "9": (2, 2), "0": (3, 1)}
digits = "".join(rng.choice(list("1234567890"), 7))
for k, d in enumerate(digits):
    r, c = KEYS[d]
    t0 = 1.0 + 0.2 * k
    line += gate(t0, t0 + 0.1, 0.003) * (0.22 * tone(ROWS[r]) + 0.26 * tone(COLS[c]))

# ---------------------------------------------------------------- 2.6-3.6 s: one ringback burst
line += 0.17 * (tone(440) + tone(480)) * gate(2.6, 3.6, 0.010)

# ---------------------------------------------------------------- 3.8-6.0 s: answer tone
rev = np.floor(np.maximum(t - 3.8, 0) / 0.45)                    # 180 deg reversal every 450 ms
ans = np.sin(2 * np.pi * 2100 * t + np.pi * rev) * (1.0 + 0.2 * np.sin(2 * np.pi * 15 * t))
line += 0.40 * ans * gate(3.8, 6.0, 0.008)

# ---------------------------------------------------------------- 6.0-7.0 s: V.21 FSK exchange
for a, b in [(6.00, 6.26), (6.52, 6.74)]:
    line += fsk(a, b, 1650, 1850, amp=0.40)
for a, b in [(6.30, 6.48), (6.78, 6.99)]:                        # the other side, V.21 low channel
    line += fsk(a, b, 980, 1180, amp=0.34)

# ---------------------------------------------------------------- 7.0-9.0 s: probing + warbling negotiation
ks = np.arange(1, 26)                                            # 150 ... 3,750 Hz comb
comb = np.zeros(N)
for k in ks:
    comb += np.sin(2 * np.pi * 150 * k * t + np.pi * k ** 2 / len(ks))
comb /= np.sqrt(len(ks) / 2)


def bong(t0, t1, rev_period, amp):
    """Emphasised probing 'bong': comb burst, 180 deg phase reversals, hard struck envelope."""
    sgn = np.where(np.floor(np.maximum(t - t0, 0) / rev_period) % 2 == 0, 1.0, -1.0)
    strike = 0.45 + 0.55 * np.exp(-np.maximum(t - t0, 0) / 0.07)
    return amp * comb * sgn * strike * gate(t0, t1, 0.003)


def warble(t0, t1, fc, dev, rate, amp):
    """V.8 / V.90-style warbling negotiation tone: FM with a wobbling rate."""
    tl = np.maximum(t - t0, 0)
    inst = fc + dev * np.sin(2 * np.pi * rate * tl + 0.6 * np.sin(2 * np.pi * 1.7 * tl))
    ph = 2 * np.pi * np.cumsum(inst) / SR
    return amp * np.sin(ph) * gate(t0, t1, 0.004)


def chirpy(t0, t1, fa, fb, step, amp):
    """V.90-style rapid two-tone alternation with short glides between the tones."""
    tl = np.maximum(t - t0, 0)
    tri = np.abs(((tl / step) % 2) - 1)                          # 1..0..1 triangle
    sq = np.clip((tri - 0.5) * 6 + 0.5, 0, 1)                    # near-square with glides
    inst = fa + (fb - fa) * sq
    return amp * np.sin(2 * np.pi * np.cumsum(inst) / SR) * gate(t0, t1, 0.004)


line += bong(7.00, 7.16, 0.160, 0.56)
line += warble(7.18, 7.34, 1400, 320, 11.0, 0.40)
line += bong(7.36, 7.52, 0.160, 0.56)
line += chirpy(7.54, 8.00, 1150, 1900, 0.028, 0.36)
line += warble(7.54, 8.00, 2600, 180, 7.0, 0.14)
line += bong(8.02, 8.18, 0.160, 0.54)
line += warble(8.20, 8.36, 1250, 380, 9.0, 0.40)
line += bong(8.38, 8.54, 0.160, 0.54)
line += bong(8.56, 8.98, 0.060, 0.42)                            # long L2-style probe, fast reversals
line += warble(8.56, 8.98, 1750, 260, 13.0, 0.16)

# ---------------------------------------------------------------- 9.0-12.0 s: grainy, stuttering training
baud, sps = 3200, SR // 3200
nsym = int(3.1 * baud)
sym = (rng.choice([-3, -1, 1, 3], nsym) + 1j * rng.choice([-3, -1, 1, 3], nsym)) / 3.0
up = np.zeros(nsym * sps, complex)
up[::sps] = sym
bb = signal.lfilter(signal.firwin(161, 1700, fs=SR), 1, up)
qam = np.real(bb * np.exp(2j * np.pi * 1829 * np.arange(len(bb)) / SR))
qam /= np.sqrt(np.mean(qam ** 2))
train = np.zeros(N)
i9 = idx(9.0)
train[i9:] = qam[:N - i9]
bursts = [(9.00, 9.40), (9.48, 9.88), (9.96, 10.36), (10.44, 10.84), (10.92, 11.32), (11.40, 12.5)]
env = np.full(N, 0.10) * gate(9.0, 12.5, 0.004)
for j, (a, b) in enumerate(bursts):
    env += (0.70 + 0.06 * j) * gate(a, b, 0.006)
# stutter: random 15-60 ms drop-outs inside the bursts (none in the final 0.25 s before the cut)
stut = np.ones(N)
tc = 9.05
while tc < 11.7:
    on = rng.uniform(0.04, 0.16)
    off = rng.uniform(0.015, 0.06)
    stut -= 0.85 * gate(tc + on, tc + on + off, 0.002)
    tc += on + off
# grain: 4 ms grains with random gain (granular roughness)
gsz = idx(0.004)
grain = np.repeat(rng.uniform(0.45, 1.0, N // gsz + 1), gsz)[:N]
grain = ndimage.uniform_filter1d(grain, 48)
line += 0.58 * train * env * stut * grain

hn = rng.standard_normal(N)                                       # rising hiss
hiss_lo = signal.sosfilt(signal.butter(2, [900, 1800], "bandpass", fs=SR, output="sos"), hn)
hiss_hi = signal.sosfilt(signal.butter(2, [2000, 3100], "bandpass", fs=SR, output="sos"), hn)
ramp = np.clip((t - 9.0) / 3.0, 0, 1)
rise = (1 - ramp) * hiss_lo + ramp * hiss_hi
rise /= np.sqrt(np.mean(rise[i9:] ** 2)) + 1e-12
line += 0.20 * rise * (10 ** (-20 * (1 - ramp) / 20)) * gate(9.0, 12.5, 0.05)

# ---------------------------------------------------------------- old handset
# carbon-mic nonlinearity: asymmetric soft saturation, granule noise riding the signal, slow
# packing drift of the sensitivity (+-1 dB)
envs = np.sqrt(np.maximum(ndimage.uniform_filter1d(line ** 2, idx(0.005)), 0))
drift = 10 ** (1.0 * np.sin(2 * np.pi * 0.37 * t + 1.1) * np.sin(2 * np.pi * 2.3 * t) / 20)
y = line * drift
y = np.tanh(1.5 * y + 0.35 * y ** 2) / 1.5
y = y - ndimage.uniform_filter1d(y, idx(0.004))                  # no DC thumps from the asymmetry
y += 0.05 * envs * rng.standard_normal(N)                        # granule noise
line = y

# crackle (no hum): sparse tiny decaying bursts, a few clustered
nclk = 70
ct = np.sort(rng.uniform(0.05, 11.9, nclk))
crk = np.zeros(N)
for c0 in ct:
    i0 = idx(c0)
    L = rng.integers(20, 120)
    crk[i0:i0 + L] += rng.uniform(0.01, 0.05) * rng.standard_normal(L) * np.exp(-np.arange(L) / (L / 4))
line += crk

# narrow 400-3,200 Hz line
bp = np.vstack([signal.ellip(8, 0.3, 65, 3200, "lowpass", fs=SR, output="sos"),
                signal.butter(6, 400, "highpass", fs=SR, output="sos")])
line = signal.sosfilt(bp, line)
h = signal.sosfilt(bp, rng.standard_normal((N, 2)), axis=0)
hiss = np.column_stack([h[:, 0], 0.75 * h[:, 0] + 0.66 * h[:, 1]])
hiss *= 0.005 / np.sqrt(np.mean(hiss ** 2))

b, a = peaking(2500, -4.0, 0.9)                                  # tame 2-3 kHz harshness
line = signal.lfilter(b, a, line)
hiss = signal.lfilter(b, a, hiss, axis=0)

hp1k = signal.sosfilt(signal.butter(2, 1000, "highpass", fs=SR, output="sos"), line)
d = idx(0.0007)
side = 0.10 * np.concatenate([np.zeros(d), hp1k[:-d]])
x = np.column_stack([line + side, line - side]) + hiss

# DC removal (~25 Hz high-pass)
x = signal.sosfilt(signal.butter(2, 25, "highpass", fs=SR, output="sos"), x, axis=0)
x *= gate(0.0, 13.0, 0.010)[:, None]                             # smooth start from silence

# ---------------------------------------------------------------- master
x *= 10 ** ((-14.0 - lufs(x)) / 20)
thr = 10 ** (-2.0 / 20)
pk = ndimage.maximum_filter1d(np.abs(x).max(axis=1), 97)
g = np.minimum(1.0, thr / np.maximum(pk, 1e-9))
g = ndimage.uniform_filter1d(ndimage.minimum_filter1d(g, 97), 97)
x *= g[:, None]
tp = true_peak_db(x)
if tp > -1.3:
    x *= 10 ** ((-1.3 - tp) / 20)

# ---------------------------------------------------------------- cut: 3 ms fade ending on frame 360
# raised-cosine in the dB domain (0 -> -100 dB over 3 ms), last sample exactly zero
r = idx(0.003)
u = np.arange(1, r + 1) / r
fade = 10 ** (-100 * (0.5 - 0.5 * np.cos(np.pi * u)) / 20)
fade[-1] = 0.0
x[-r:] *= fade[:, None]

assert x.shape == (N, 2) and np.all(np.isfinite(x))
pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
with wave.open(sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"digits {digits}  LUFS {lufs(x):.2f}  TP {true_peak_db(x):.2f} dBTP")
