"""Point-and-click adventure title theme, take 1 (faithful): 2-operator FM, OPL-style, 9 channels.

Creative brief
--------------
An ORIGINAL 24-second title theme for a breezy, slightly mischievous island adventure game, written the
way an early-90s FM sound card would play it: every instrument is a 2-operator FM patch (one modulator
phase-modulating one carrier, optional modulator self-feedback), the whole arrangement lives on 9
monophonic channels (a new key-on on a channel cuts the note it was playing), envelopes move in
0.75 dB attenuation steps on a 1 ms envelope clock, and the vibrato is the chip's fixed 6.07 Hz / 14
cent kind. Key E Dorian (the raised 6th, C#, is the "island sunshine" colour). Every patch is rendered
4x oversampled and decimated, and the master is low-passed at 15.5 kHz, so nothing aliases.

Patches (carrier : modulator ratio, index behaviour):
- STEEL  steel drum      1 : 3.5, index 4.5 decaying in ~25 ms -> metallic "plink" that settles to a pure tone
- LEAD   marimba-flute   1 : 3, index spike (mallet "tock", 2nd+4th partials) decaying into a soft breathy
                         flute sustain (index 0.45), delayed chip vibrato
- BASS   plucky bass     1 : 1, index 3.0 decaying to 0.9 (2nd and 3rd harmonics for phone speakers)
- BRASS  2-op brass      1 : 1, index follows the amplitude envelope (the "blat"), scoop into pitch
- SKANK  offbeat chords  1 : 1, short clavinet-ish stabs; PAD = same channels, soft slow version
- TWINK  twinkle bell    1 : 5, index decaying -> glassy celesta
- HAT / SNARE / TOM      FM percussion (inharmonic ratios + noise for hat and snare, pitch-dropped tom)
Mix: tiny room (0.4 s RT60, 5 ms pre-delay), bass and toms dry and mono, sides high-passed at 120 Hz.

Channel map (exactly 9, like an OPL2): ch0 lead (steel/twinkle round-robin in bars 1 and 10),
ch1 brass (steel in bar 1, pad in bar 10), ch2 bass, ch3-5 skank chords, ch6 hat, ch7 snare, ch8 tom.

CUE SHEET  (grid: 100 BPM, 4/4, 1 beat = 18 frames at 30 fps, so 1 bar = 72 frames = 115200 samples;
positions below are in eighth notes, 1 eighth = 9 frames = 14400 samples)
bar | frame | chord | events
  1 |     0 | Em7   | cue f0 INTRO: steel-drum 16th arpeggio rising E4 G4 B4 D5 / G4 .. E5 / B4 .. G5 / D5 E5 G5 B5
  2 |    72 | Em7   | THEME A: lead B4 D5 E5 G5~ (3+3+2 tresillo, tied over the bar) ; bass E2 B2 E3 D3 on 1, &2, &3, &4 ; skank on every &
  3 |   144 | A7    | THEME A: lead ~G5 E5 C#5 E5 A5~ ; bass A2 E3 A2 C#3
  4 |   216 | Dmaj7 | THEME A: lead ~A5 F#5 E5 D5 C#5 D5 F#5~ ; bass D2 A2 D3 C#3
  5 |   288 | Bm7   | THEME A: lead ~F#5 D5 B4 (breath on beat 4) ; bass B1 F#2 B2 A2
  6 |   360 | Gmaj7 | THEME B: lead B5 A5 F#5 ; brass D4 F#4 G4 A4 B4 ; one-drop drums enter (hat 8ths, snare+tom on 3)
  7 |   432 | F#m7  | THEME B: lead A5 F#5 E5 ; brass C#5 A4 F#4 E4 A4 ; snare ghost on the last 16th
  8 |   504 | A7    | THEME B: lead G5 F#5 E5 C#5 ; brass G4 A4 C#5 E5 C#5 A4 ; tom fill (16ths, high -> low) from the &3
  9 |   576 | Em9   | CADENCE: tutti hit on 1 (all 9 channels), lead F#5 -> E5, brass G4, chord F#4 B4 D5, bass E2 B2 G2 F#2
 10 |   648 | Em9   | HELD CHORD (pad F#4 G4 B4 D5 over E2) + twinkling Em9 arpeggio E6 F#6 B6 D7 ... fading to silence
end |   720 |       | 24.000 s = 1152000 samples, last 0.9 s faded to digital silence

The code below reads the bar frames, the chords and the frames-per-beat from the table above, so the
music and the note-fit checks run on one clock.

usage: python3 take-1.py OUT.wav
"""
import re
import sys
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d

SEED = 42
SR = 48000
N = 1152000
FPS = 30
SPF = SR // FPS                     # 1600 samples per video frame
OS = 4                              # oversampling for every FM operator
rng = np.random.default_rng(SEED)

# ------------------------------------------------------------------ the one clock: parse the cue sheet
F_BEAT = int(re.search(r"1 beat = (\d+) frames", __doc__).group(1))
F8 = F_BEAT // 2                    # frames per eighth note
CUE = [(int(m[1]), int(m[2]), m[3]) for m in
       re.finditer(r"^\s*(\d+) \|\s*(\d+) \| (\S+)\s*\|", __doc__, re.M)]
BAR_FRAME = {b: f for b, f, _ in CUE}
BAR_CHORD = {b: c for b, _, c in CUE}
NBARS = len(CUE)
assert all(BAR_FRAME[b] == (b - 1) * 8 * F8 for b in BAR_FRAME), "cue sheet frames off the grid"
assert (BAR_FRAME[NBARS] + 8 * F8) * SPF == N, "cue sheet does not end on the stated length"


def at(bar, pos8):
    """sample index of eighth-note position pos8 inside bar (pos8 may run past the barline)."""
    return int(round((BAR_FRAME[bar] + pos8 * F8) * SPF))


EIGHTH = F8 * SPF                   # 14400 samples

# ------------------------------------------------------------------ pitch + harmony helpers
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name):
    m = re.fullmatch(r"([A-G])([#b]?)(-?\d)", name)
    return 12 * (int(m[3]) + 1) + PC[m[1]] + {"#": 1, "b": -1, "": 0}[m[2]]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


QUAL = {"m7": (0, 3, 7, 10), "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11), "m9": (0, 3, 7, 10, 2),
        "6": (0, 4, 7, 9), "m": (0, 3, 7), "m7b5": (0, 3, 6, 10)}


def chord_pcs(sym):
    m = re.fullmatch(r"([A-G][#b]?)(.*)", sym)
    r = midi(m[1] + "4") % 12
    return {(r + i) % 12 for i in QUAL[m[2]]}


SCALE = {midi(n + "4") % 12 for n in "E F# G A B C# D".split()}      # E Dorian
SCALE_NAME = "E Dorian"


def scale_for_bar(bar):
    return SCALE


# ------------------------------------------------------------------ THE SCORE (note lists)
# "NOTE@pos:dur" with pos and dur in eighth notes inside the bar; durations may tie over the barline.
LEAD = {
    2: "B4@0:3 D5@3:3 E5@6:1 G5@7:3",
    3: "E5@2:1 C#5@3:3 E5@6:1 A5@7:3",
    4: "F#5@2:1 E5@3:1 D5@4:1 C#5@5:1 D5@6:1 F#5@7:3",
    5: "D5@2:1 B4@3:3",
    6: "B5@0:3 A5@3:1 F#5@4:4",
    7: "A5@0:3 F#5@3:1 E5@4:4",
    8: "G5@0:3 F#5@3:1 E5@4:2 C#5@6:2",
    9: "F#5@0:2 E5@2:6",
}
BRASS = {
    6: "D4@0:2 F#4@3:1 G4@4:1 A4@5:1 B4@6:2",
    7: "C#5@0:3 A4@3:1 F#4@4:2 E4@6:1 A4@7:1",
    8: "G4@0:2 A4@2:1 C#5@3:1 E5@4:2 C#5@6:1 A4@7:1",
    9: "G4@0:3",
}
BASS = {
    2: "E2@0:1.5 B2@3:1 E3@5:1 D3@7:1",
    3: "A2@0:1.5 E3@3:1 A2@5:1 C#3@7:1",
    4: "D2@0:1.5 A2@3:1 D3@5:1 C#3@7:1",
    5: "B1@0:1.5 F#2@3:1 B2@5:1 A2@7:1",
    6: "G2@0:1.5 D3@3:1 G2@5:1 F#2@7:1",
    7: "F#2@0:1.5 C#3@3:1 F#2@5:1 E2@7:1",
    8: "A2@0:1.5 E2@3:1 A2@5:1 G2@7:1",
    9: "E2@0:2 B2@3:1 G2@5:1 F#2@7:1",
    10: "E2@0:8",
}
STEEL = {1: "E4@0:.5 G4@.5:.5 B4@1:.5 D5@1.5:.5 G4@2:.5 B4@2.5:.5 D5@3:.5 E5@3.5:.5 "
            "B4@4:.5 D5@4.5:.5 E5@5:.5 G5@5.5:.5 D5@6:.5 E5@6.5:.5 G5@7:.5 B5@7.5:.5"}
TWINK = {10: "E6@0:.5 F#6@.5:.5 B6@1:.5 D7@1.5:.5 B6@2:.5 G6@2.5:.5 F#6@3:1 B6@4:1 E6@5:1 B5@6:2"}
# skank voicings (3 voices, between bass and lead); stabs on every offbeat eighth
VOICING = {2: "G4 B4 D5", 3: "G4 C#5 E5", 4: "F#4 A4 C#5", 5: "F#4 A4 D5",
           6: "F#4 B4 D5", 7: "E4 A4 C#5", 8: "E4 G4 C#5", 9: "F#4 B4 D5", 10: "F#4 B4 D5"}
SKANK = {b: " ".join(f"{n}@{p}:.35" for p in (1, 3, 5, 7) for n in VOICING[b].split()) for b in range(2, 9)}
SKANK[9] = " ".join(f"{n}@{p}:{d}" for p, d in ((0, 2), (3, .35), (5, .35)) for n in VOICING[9].split())
PAD = {10: VOICING[10].replace(" ", "@0:8 ") + "@0:8", }
PAD_G = {10: "G4@0:8"}               # the brass channel holds the Em9's 3rd under the twinkle
HAT = {b: " ".join(f"X@{p}:.5" for p in range(8)) for b in (6, 7, 8)}
HAT[9] = "X@0:2"
SNARE = {6: "X@4:1", 7: "X@4:1 X@7.5:.5", 8: "X@4:1", 9: "X@0:2"}
TOM = {6: "A2@4:1", 7: "A2@4:1", 8: "A2@4:1 G3@5:.5 G3@5.5:.5 D3@6:.5 D3@6.5:.5 A2@7:.5 A2@7.5:.5", 9: "A2@0:2"}


def parse(part):
    out = []
    for bar, s in part.items():
        for tok in s.split():
            n, rest = tok.split("@")
            p, d = rest.split(":")
            out.append((bar, float(p), float(d), n))
    return sorted(out, key=lambda e: (e[0], e[1]))


# ------------------------------------------------------------------ composition checks (printed)
def bars_spanned(bar, pos, dur):
    t0, t1 = (bar - 1) * 8 + pos, (bar - 1) * 8 + pos + dur
    return [b for b in range(1, NBARS + 1) if (b - 1) * 8 < t1 - 1e-9 and b * 8 > t0 + 1e-9]


def check_fit(name, notes):
    """every note must be a tone of every chord it sounds over; a non-chord scale tone is allowed only
    as a short (<= 1 eighth) passing/neighbour tone on a weak position (not beat 1 or 3), approached or
    left by step, and not crossing a barline."""
    bad, passing = [], []
    pitched = [e for e in notes if e[3] != "X"]
    for i, (bar, pos, dur, n) in enumerate(pitched):
        pc = midi(n) % 12
        spans = bars_spanned(bar, pos, dur)
        if all(pc in chord_pcs(BAR_CHORD[b]) for b in spans):
            continue
        prev_m = midi(pitched[i - 1][3]) if i > 0 else None
        next_m = midi(pitched[i + 1][3]) if i + 1 < len(pitched) else None
        step = any(m is not None and abs(m - midi(n)) <= 2 for m in (prev_m, next_m))
        weak = (pos % 4) != 0
        if pc in scale_for_bar(bar) and weak and dur <= 1 and len(spans) == 1 and step:
            passing.append(f"{n} bar {bar} pos {pos:g} over {BAR_CHORD[bar]}")
        else:
            bad.append(f"{n} bar {bar} pos {pos:g} dur {dur:g} over {[BAR_CHORD[b] for b in spans]}")
    print(f"  note-fit {name:6s}: {len(pitched):3d} notes, {len(pitched) - len(bad) - len(passing):3d} chord tones, "
          f"{len(passing)} passing{(' (' + '; '.join(passing) + ')') if passing else ''}, {len(bad)} WRONG")
    for b in bad:
        print("      WRONG:", b)
    return not bad


# ------------------------------------------------------------------ chip envelope generator
TICK = 48                           # 1 ms envelope clock
STEP_DB = 0.75                      # OPL attenuation step


def ma(x, n):
    c = np.concatenate([[0.0], np.cumsum(np.concatenate([np.zeros(n), x]))])
    return (c[n:n + len(x)] - c[:len(x)]) / n


def chip_env(n, gate, ar, dr, sl, rr, sustain=True):
    """OPL-style EG. ar attack time (s); dr decay rate (dB/s) down to sl (dB of attenuation);
    sustain=True holds sl while the key is down, False keeps falling at rr (percussive EG type);
    after key-off (gate samples) it falls at rr dB/s. Quantised to 0.75 dB on a 1 ms clock."""
    nt = n // TICK + 2
    t = np.arange(nt) * TICK / SR
    a = 1 - (1 - np.clip(t / max(ar, 1e-4), 0, 1)) ** 3
    att = -20 * np.log10(np.maximum(a, 1e-6))
    t1 = np.maximum(t - ar, 0)
    dec = np.minimum(t1 * dr, sl)
    if not sustain:
        t_sl = sl / dr
        dec = np.where(t1 > t_sl, sl + (t1 - t_sl) * rr, dec)
    att = np.where(t < ar, att, dec)
    g = gate / SR
    lg = np.interp(g, t, att)
    att = np.where(t >= g, lg + (t - g) * rr, att)
    q = np.ceil(att / STEP_DB - 1e-9) * STEP_DB
    amp = np.where(q < 96, 10 ** (-q / 20), 0.0)
    return ma(np.repeat(amp, TICK)[:n], 24)          # 0.5 ms smoothing of each step (no zipper clicks)


def up(a, n4):
    a = np.broadcast_to(np.asarray(a, dtype=float), (n4 // OS,)) if np.ndim(a) == 0 else a
    return np.interp(np.arange(n4) / OS, np.arange(len(a)), a)


def fm(f0, n, env, rc=1.0, rm=1.0, index=0.0, fb=0.0, pitch=1.0):
    """2-op FM rendered at 4x and decimated. env/index/pitch: arrays at 48 kHz (or scalars)."""
    n4 = n * OS
    f = f0 * up(pitch, n4)
    ph = 2 * np.pi * np.cumsum(f) / (SR * OS)
    pm = ph * rm
    mod = np.sin(pm + fb * np.sin(pm))
    y = np.sin(ph * rc + up(index, n4) * mod) * up(env, n4)
    return signal.resample_poly(y, 1, OS)[:n]


def tsec(n):
    return np.arange(n) / SR


def chip_vibrato(n, delay=0.22, cents=14.0, rate=6.07):
    t = tsec(n)
    return 2 ** (cents / 1200 * np.sin(2 * np.pi * rate * t) * np.clip((t - delay) / 0.15, 0, 1))


# ------------------------------------------------------------------ instruments  (f0, gate, nmax) -> sig, env
def i_steel(f0, gate, nmax, vel):
    n = min(int(1.6 * SR), nmax)
    env = chip_env(n, n, 0.001, 60, 8, 16, sustain=False)
    idx = 4.5 * np.exp(-tsec(n) / 0.025) + 0.12
    return vel * fm(f0, n, env, 1.0, 3.5, idx), env


def i_lead(f0, gate, nmax, vel):
    n = min(gate + int(0.5 * SR), nmax)
    env = chip_env(n, gate, 0.004, 45, 6, 70)
    t = tsec(n)
    idx = 2.6 * np.exp(-t / 0.018) + 0.45
    y = fm(f0, n, env, 1.0, 3.0, idx, fb=0.2, pitch=chip_vibrato(n))
    br = signal.sosfilt(BREATH_SOS, rng.standard_normal(n)) * env * 0.05   # a breath of air (flute half)
    return vel * (y + br), env


def i_bass(f0, gate, nmax, vel):
    n = min(gate + int(0.25 * SR), nmax)
    env = chip_env(n, gate, 0.002, 16, 15, 90)
    idx = 2.1 * np.exp(-tsec(n) / 0.06) + 0.9
    return vel * fm(f0, n, env, 1.0, 1.0, idx, fb=0.15), env


def i_brass(f0, gate, nmax, vel):
    n = min(gate + int(0.4 * SR), nmax)
    env = chip_env(n, gate, 0.035, 12, 4, 60)
    t = tsec(n)
    scoop = 2 ** (-0.35 / 12 * np.exp(-t / 0.025))
    vib = chip_vibrato(n, delay=0.3, cents=10)
    idx = 0.35 + 3.0 * env ** 1.6                        # index follows the envelope: the "blat"
    return vel * fm(f0, n, env, 1.0, 1.0, idx, fb=0.35, pitch=scoop * vib), env


def i_skank(f0, gate, nmax, vel):
    n = min(gate + int(0.3 * SR), nmax)
    env = chip_env(n, gate, 0.002, 35, 10, 110)
    idx = 2.4 * np.exp(-tsec(n) / 0.03) + 0.7
    return vel * fm(f0, n, env, 1.0, 1.0, idx, fb=0.25), env


def i_pad(f0, gate, nmax, vel):
    n = min(int(3.0 * SR), nmax)
    env = chip_env(n, n, 0.09, 6, 4, 13, sustain=False)
    return vel * fm(f0, n, env, 1.0, 1.0, 0.7 * env + 0.2, pitch=chip_vibrato(n, 0.4, 7)), env


def i_twink(f0, gate, nmax, vel):
    n = min(int(1.2 * SR), nmax)
    env = chip_env(n, n, 0.001, 40, 10, 22, sustain=False)
    idx = 1.4 * np.exp(-tsec(n) / 0.06) + 0.15
    return vel * fm(f0, n, env, 1.0, 5.0, idx), env


def i_hat(f0, gate, nmax, vel):
    n = min(int(0.25 * SR), nmax)
    env = chip_env(n, n, 0.0005, 160, 20, 90, sustain=False)
    ring = fm(6200.0, n, 1.0, 1.0, 1.47, 2.6)
    nz = signal.sosfilt(HAT_SOS, rng.standard_normal(n))
    return vel * env * (0.5 * ring + 0.9 * nz), env


def i_snare(f0, gate, nmax, vel):
    n = min(int(0.4 * SR), nmax)
    env = chip_env(n, n, 0.0008, 70, 12, 45, sustain=False)
    t = tsec(n)
    body = fm(196.0, n, env * np.exp(-t / 0.07), 1.0, 1.6, 2.0 * np.exp(-t / 0.03),
              pitch=1 + 0.15 * np.exp(-t / 0.02))
    nz = signal.sosfilt(SNARE_SOS, rng.standard_normal(n)) * env
    return vel * (0.8 * body + 0.6 * nz), env


def i_tom(f0, gate, nmax, vel):
    n = min(int(0.5 * SR), nmax)
    env = chip_env(n, n, 0.001, 40, 10, 26, sustain=False)
    t = tsec(n)
    return vel * fm(f0, n, env, 1.0, 1.0, 1.4 * np.exp(-t / 0.02), pitch=1 + 0.5 * np.exp(-t / 0.035)), env


BREATH_SOS = signal.butter(2, [1800, 5000], "bandpass", fs=SR, output="sos")
HAT_SOS = signal.butter(4, [7000, 12500], "bandpass", fs=SR, output="sos")
SNARE_SOS = signal.butter(2, [1800, 8000], "bandpass", fs=SR, output="sos")

# part: (notes, instrument, channel(s), gain, pan(s), gate fraction or seconds, tag)
PARTS = [
    ("steel", STEEL, i_steel, [0, 1, 3, 4], 0.30, [-0.35, 0.35, -0.15, 0.15], None),
    ("lead", LEAD, i_lead, [0], 0.42, [0.05], 0.92),
    ("brass", BRASS, i_brass, [1], 0.24, [-0.3], 0.88),
    ("bass", BASS, i_bass, [2], 0.40, [0.0], 0.8),
    ("skank", SKANK, i_skank, [3, 4, 5], 0.10, [-0.4, 0.1, 0.4], 0.11),
    ("pad", PAD, i_pad, [3, 4, 5], 0.075, [-0.4, 0.1, 0.4], None),
    ("padG", PAD_G, i_pad, [1], 0.07, [-0.3], None),
    ("twink", TWINK, i_twink, [0, 6, 7, 8], 0.16, [0.45, -0.45, 0.25, -0.25], None),
    ("hat", HAT, i_hat, [6], 0.24, [0.3], None),
    ("snare", SNARE, i_snare, [7], 0.28, [-0.08], None),
    ("tom", TOM, i_tom, [8], 0.33, [0.0], None),
]
DRY_MONO = {"bass", "tom"}


def velocity(part, bar, pos):
    if part == "steel":
        return 0.6 + 0.4 * pos / 8                           # crescendo up the arpeggio
    if part == "twink":
        return 1.0 - 0.75 * pos / 8                          # fading twinkle
    if part == "hat":
        return 1.0 if pos % 1 else 0.55 + 0.1 * (pos % 2)    # offbeat accents, light on the beats
    if part == "snare":
        return 0.45 if pos % 1 else (1.2 if bar == 9 else 1.0)
    if part in ("skank", "lead") and bar == 9 and pos == 0:
        return 1.2                                           # the cadence hit
    return 1.0


def build_events():
    ev = []
    for name, part, inst, chans, gain, pans, gate in PARTS:
        notes = parse(part)
        if name in ("skank", "pad"):                         # 3-note chords: voice k -> channel k
            groups = {}
            for e in notes:
                groups.setdefault((e[0], e[1]), []).append(e)
            for key, g in groups.items():
                for k, e in enumerate(sorted(g, key=lambda e: midi(e[3]))):
                    ev.append(dict(part=name, inst=inst, note=e, ch=chans[k], gain=gain, pan=pans[k], gatef=gate))
        else:
            for k, e in enumerate(notes):
                c = k % len(chans)
                ev.append(dict(part=name, inst=inst, note=e, ch=chans[c], gain=gain, pan=pans[c], gatef=gate))
    for e in ev:
        bar, pos, dur, n = e["note"]
        e["on"] = at(bar, pos)
        d = dur * EIGHTH
        e["gate"] = int(d * e["gatef"]) if isinstance(e["gatef"], float) and e["gatef"] <= 1 else int(d)
        if e["part"] == "skank":
            e["gate"] = int(0.11 * SR) if dur < 1 else int(d * 0.9)
        e["f0"] = hz(midi(n)) if n != "X" else 0.0
        e["vel"] = velocity(e["part"], bar, pos)
    # monophonic channels: the next key-on on the same channel cuts the current note
    by_ch = {}
    for e in ev:
        by_ch.setdefault(e["ch"], []).append(e)
    for lst in by_ch.values():
        lst.sort(key=lambda e: e["on"])
        for a, b in zip(lst, lst[1:] + [None]):
            a["nmax"] = (b["on"] if b else N) - a["on"]
            assert a["nmax"] > 0, ("two notes start together on channel", a["ch"], a["note"], b["note"])
    return ev


def pan_gains(p):
    th = (p + 1) * np.pi / 4
    return np.cos(th) * np.sqrt(2), np.sin(th) * np.sqrt(2)


def render(ev):
    upper = np.zeros((N, 2))
    low = np.zeros(N)
    voices = np.zeros(N + 1, dtype=int)
    for e in ev:
        sig, env = e["inst"](e["f0"], e["gate"], e["nmax"], e["vel"])
        n = min(len(sig), N - e["on"])
        sig = sig[:n] * e["gain"]
        if len(env) >= e["nmax"]:                          # cut by the next key-on: 2 ms chip-style ramp
            k = min(96, n)
            sig[-k:] *= np.cos(np.linspace(0, np.pi / 2, k)) ** 2
        alive = np.nonzero(env[:n] > env.max() * 1e-3)[0]
        end = e["on"] + (alive[-1] + 1 if len(alive) else 0)
        voices[e["on"]] += 1
        voices[end] -= 1
        if e["part"] in DRY_MONO:
            low[e["on"]:e["on"] + n] += sig
        else:
            gl, gr = pan_gains(e["pan"])
            upper[e["on"]:e["on"] + n, 0] += sig * gl
            upper[e["on"]:e["on"] + n, 1] += sig * gr
    return upper, low, np.cumsum(voices)[:N]


# ------------------------------------------------------------------ room, master, loudness
def room_ir(rt60=0.4, length=0.55, predelay=0.005):
    n = int(length * SR)
    t = tsec(n)
    ir = rng.standard_normal((n, 2)) * np.exp(-6.91 * t / rt60)[:, None]
    ir = signal.sosfilt(signal.butter(2, 6500, "lowpass", fs=SR, output="sos"), ir, axis=0)
    for d, g in ((0.007, 0.5), (0.011, -0.38), (0.017, 0.3), (0.023, -0.22)):    # a small room's early bounces
        ir[int(d * SR), 0] += g
        ir[int((d + 0.0013) * SR), 1] += g
    ir /= np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True))
    pd = int(predelay * SR)
    return np.vstack([np.zeros((pd, 2)), ir])


def lufs(x):
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    p = np.cumsum(np.concatenate([[0.0], (y ** 2).sum(axis=1)]))
    st = np.arange(0, len(y) - blk + 1, hop)
    z = (p[st + blk] - p[st]) / blk
    z1 = z[-0.691 + 10 * np.log10(z + 1e-20) > -70]
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[-0.691 + 10 * np.log10(z1) > rel]
    return -0.691 + 10 * np.log10(z2.mean())


def true_peak(x):
    return np.abs(signal.resample_poly(x, 4, 1, axis=0)).reshape(len(x), 4, 2).max(axis=(1, 2))


def limit(x, ceil_db):
    c = 10 ** (ceil_db / 20)
    req = np.minimum(1.0, c / np.maximum(true_peak(x), 1e-9))
    W = 960                                                # 20 ms look-ahead / release
    g = minimum_filter1d(req, 2 * W + 1)
    g = np.convolve(g, np.ones(W + 1) / (W + 1), mode="same")
    return x * np.minimum(g, req.max())[:, None]


def master(upper, low, target=-14.0):
    ir = room_ir()
    send = signal.sosfilt(signal.butter(2, 220, "highpass", fs=SR, output="sos"),
                          upper + 0.15 * low[:, None], axis=0)
    wet = signal.fftconvolve(send, ir, axes=0)[:N] * 0.22
    hp_up = signal.butter(2, 110, "highpass", fs=SR, output="sos")
    x = signal.sosfilt(hp_up, upper, axis=0) + wet + low[:, None]
    m, s = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    s = signal.sosfilt(signal.butter(4, 120, "highpass", fs=SR, output="sos"), s)   # mono below 120 Hz
    x = np.stack([m + s, m - s], axis=1)
    x = signal.sosfilt(signal.butter(2, 25, "highpass", fs=SR, output="sos"), x, axis=0)
    x = signal.sosfilt(signal.butter(8, 15500, "lowpass", fs=SR, output="sos"), x, axis=0)
    fade = np.ones(N)                                     # last 0.9 s fall to digital silence
    nf = int(0.9 * SR)
    fade[-nf:] = np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
    fade[-480:] = 0
    x *= fade[:, None]
    for _ in range(4):
        x *= 10 ** ((target - lufs(x)) / 20)
        x = limit(x, -1.4)
    tp = 20 * np.log10(true_peak(x).max())
    if tp > -1.1:
        x *= 10 ** ((-1.1 - tp) / 20)
    return x


def write_wav(path, x):
    d = (rng.random(x.shape) - rng.random(x.shape)) / 32768.0    # TPDF dither
    d[:8] = 0
    d[-480:] = 0
    q = np.clip(np.round((x + d) * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(q.tobytes())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "take-1.wav"
    print(f"composition checks ({SCALE_NAME}; chords per bar from the cue sheet: "
          + " | ".join(BAR_CHORD[b] for b in range(1, NBARS + 1)) + ")")
    ok = True
    for name, part in (("lead", LEAD), ("brass", BRASS), ("bass", BASS), ("steel", STEEL), ("twink", TWINK),
                       ("skank", SKANK), ("pad", {10: PAD[10] + " " + PAD_G[10]})):
        ok &= check_fit(name, parse(part))
    assert ok, "a note does not fit its chord"
    ev = build_events()
    upper, low, voices = render(ev)
    vmax = voices.max()
    where = np.nonzero(voices == vmax)[0]
    print(f"  voices: max {vmax} simultaneous (limit 9), first reached at {where[0] / SR:.2f} s, "
          f"{len(where) / SR * 1000:.0f} ms in total at the max; {len(ev)} notes on {len({e['ch'] for e in ev})} channels")
    assert vmax <= 9
    x = master(upper, low)
    assert np.all(np.isfinite(x))
    print(f"  master: {lufs(x):.2f} LUFS, {20 * np.log10(true_peak(x).max()):.2f} dBTP")
    write_wav(out, x)
    print("wrote", out)


if __name__ == "__main__":
    main()
