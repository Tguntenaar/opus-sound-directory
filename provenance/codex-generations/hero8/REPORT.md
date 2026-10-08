# Hero8 — 27 procedural sound takes

All audio was generated locally from NumPy/SciPy oscillators, noise, modal models and algorithmic effects. No samples, recordings, downloads or model APIs were used. Seeds are 42, 43 and 44.

## Validation

27/27 WAVs pass read-back checks: exact requested sample counts, 48,000 Hz, stereo, 16-bit PCM, non-silent, finite and unclipped. FFmpeg EBU R128 reports each take at its requested −14.0 or −17.0 LUFS. Highest 4× oversampled true peak is −1.293 dBTP. All scripts rendered in well under 60 seconds on this machine.

Silent tails, every UI slicing gap and the braam’s 40 ms vacuum were checked sample by sample. Riser joins were checked for value and slope discontinuities; their boundary steps are smaller than ordinary within-loop steps. Loop endpoints need not have identical values: adjacent samples should preserve the continuing waveform.

All 27 spectrograms were visually inspected in the three contact sheets. The plots show the expected boom decays, centered whoosh swells, eight separated UI events, rising octave lanes, staged modem timeline, specified fail contours, arcade sweeps, braam accents and coin intervals. No missing cue or unexpected full-band boundary stripe was found.

**Listening limitation:** no auditory review was performed. The descriptions and rankings below are provisional design assessments supported by source inspection, waveform measurements and spectrograms; they are not claims of having heard the files. Use `index.html` to choose by ear, especially for brass realism, repeat-listening comfort and loop illusion.

## Per-take measurements and assessment

| Slug | Take | Seconds | LUFS | True peak (dBTP, 4×) | Character / title fit |
|---|---:|---:|---:|---:|---|
| heavy-boom-meme | 1 | 1.50 | -14.0 | -2.379 | Sub-heavy impact with a ringing metallic body and diffuse dark decay; strong structural match to shock boom. |
| heavy-boom-meme | 2 | 1.50 | -14.0 | -2.212 | Round membrane body with a denser, darker feedback tail; fits the cinematic boom angle, less sharp than take 1. |
| heavy-boom-meme | 3 | 1.50 | -14.0 | -1.525 | Harmonic midrange impact with two separated dark echoes; best phone-oriented construction, more pitched than a neutral impact. |
| whoosh-pass-by | 1 | 1.20 | -14.0 | -2.632 | Airy midrange sweep with a distinct dropping tonal thread; matches pass-by, with the spectral apex at 0.6 s. |
| whoosh-pass-by | 2 | 1.20 | -14.0 | -2.172 | Broadband pass with a prominent low-mid Doppler body; matches the heavier-object angle. |
| whoosh-pass-by | 3 | 1.20 | -14.0 | -3.209 | Tightly concentrated bright turbulence burst with a broad stereo traverse; matches fast swish, least overtly tonal. |
| ui-cozy-sprite | 1 | 4.00 | -17.0 | -2.079 | Eight rounded, short tonal gestures with a clear noise-delete ending; fits cozy UI and all slicing gaps are silent. |
| ui-cozy-sprite | 2 | 4.00 | -17.0 | -1.607 | Eight woody/modal gestures with short upper-mode flashes; fits mallet UI, although the highest modes are brighter. |
| ui-cozy-sprite | 3 | 4.00 | -17.0 | -2.641 | Eight soft FM and bubble gestures; fits glassy UI, with more harmonic color than take 1. |
| endless-riser-shepard | 1 | 12.00 | -14.0 | -5.693 | Smooth ascending octave lanes over interleaved low pulses and ticks; structurally matches endless tension and passes seam checks. |
| endless-riser-shepard | 2 | 12.00 | -14.0 | -6.371 | Denser harmonic ascending lanes with warm low pulses; string-like synthesis, not a realistic sampled orchestra. |
| endless-riser-shepard | 3 | 12.00 | -14.0 | -5.589 | Bright rising harmonic lanes plus migrating random-phase bands and blips; fits electronic tension, with the busiest spectrum. |
| dialup-modem-56k | 1 | 12.00 | -14.0 | -1.475 | Dial tone, seven digits, ringback, answer tone, FSK, probing and training appear in order; recognizable modem construction, not a protocol emulator. |
| dialup-modem-56k | 2 | 12.00 | -14.0 | -5.823 | Narrower, saturated handset treatment with prominent probing and stuttered training; matches gritty retro-tech. |
| dialup-modem-56k | 3 | 12.00 | -14.0 | -4.050 | Two endpoint positions, short line echo and a negotiation hole; matches the two-ends angle while remaining largely centered. |
| wah-wah-fail | 1 | 2.80 | -14.0 | -5.047 | Three brass-like notes with a final minor-third droop and double plunger opening; matches original comic fail contour. |
| wah-wah-fail | 2 | 2.80 | -14.0 | -3.064 | Lower three-note brass phrase ending in pitch sag and lip-buzz noise; matches deflating tuba-like fail. |
| wah-wah-fail | 3 | 2.80 | -14.0 | -5.279 | Quick pickup pair, medium note and fluttering held droop; matches talking-mute fail, busiest of the three. |
| arcade-game-over | 1 | 1.80 | -14.0 | -2.032 | Eight visibly descending pulse sweeps then two low blips; strong structural match to the requested arcade loss effect. |
| arcade-game-over | 2 | 1.80 | -14.0 | -3.211 | Descending minor-mode pulse phrase with harmony, bass and a final noise thud; matches a melodic game-over jingle. |
| arcade-game-over | 3 | 1.80 | -14.0 | -2.578 | Wide falling vibrato spiral then three low blips and crunch; matches comic chip deflation. |
| trailer-braam-hit | 1 | 4.00 | -14.0 | -2.338 | Noise suck, clean vacuum, hard low chord and dark decay; strong structural match to a trailer braam. |
| trailer-braam-hit | 2 | 4.00 | -14.0 | -1.293 | Hard low chord with metallic modulation and stronger midrange distortion; matches aggressive braam, more abrasive. |
| trailer-braam-hit | 3 | 4.00 | -14.0 | -1.957 | Hard first chord plus a visible second swell at 2 s; matches double braam, leaves less negative space. |
| game-coin-pickup | 1 | 0.50 | -17.0 | -4.802 | Separated glass notes and scattered upper glints; matches collectible sparkle with a major-sixth main interval. |
| game-coin-pickup | 2 | 0.50 | -17.0 | -2.686 | Two struck-metal events and a short upward shimmer; strongest coin-like construction, uses a major third. |
| game-coin-pickup | 3 | 0.50 | -17.0 | -5.878 | Single fast rising portamento and stable bright ring; fits pickup, more electronic than metallic, uses a fifth. |

## Provisional ranking

- **heavy-boom-meme: 2 > 1 > 3. Membrane weight first; choose take 3 for phone playback.
- **whoosh-pass-by: 1 > 3 > 2. Balanced pass first, tight whip second, heavy object third.
- **ui-cozy-sprite: 1 > 2 > 3. Simplest rounded palette first for frequent UI repetition.
- **endless-riser-shepard: 1 > 2 > 3. Cleanest illusion first; richer harmonics and electronic density are alternatives.
- **dialup-modem-56k: 1 > 3 > 2. Clearest staged sequence first; handset grit is a deliberate coloration.
- **wah-wah-fail: 2 > 1 > 3. Low deflation has the clearest comic gesture on paper.
- **arcade-game-over: 1 > 3 > 2. Requested sweep construction first; spiral second, musical jingle third.
- **trailer-braam-hit: 1 > 2 > 3. Single clean hit first; choose aggression or a second accent as needed.
- **game-coin-pickup: 2 > 1 > 3. Struck-metal model best fits a coin; glass and electronic glide offer distinct alternatives.

## Implementation choices and limits

The modem is a designed evocation of the specified protocol stages, not a standards-compliant V.90 implementation. The orchestral riser uses additive string-like harmonics, not instrument recordings. The electronic riser’s noise texture is a dense random-phase oscillator bank so its octave handoff stays periodic. Dynamic filters use overlapping spectral windows. Band limits are practical filter roll-offs, not ideal brick-wall cutoffs.

The UI error uses F5→D5: a falling minor third entirely inside F major pentatonic. Per-slot energy is normalized before mastering; subjective loudness can still differ by timbre. The more specific take contours govern the fail’s final pitch bends.

Every script carries its brief in its module docstring, is self-contained and accepts `python take-N.py OUT.wav`. With no argument, it writes next to itself. Synthesis needs only Python, NumPy and SciPy. FFmpeg is optional and automatically verifies integrated loudness when available; the built-in 48 kHz BS.1770 meter is always used for mastering. Matplotlib is used only by the collection verification tool.

## Files

- Each slug folder: three standalone Python scripts, three WAVs, three spectrogram PNGs, render logs and FFmpeg meter summaries.
- `index.html`: offline listening comparison; risers loop in the player. Open after extracting the ZIP.
- `manifest.json`, `measurements.json`, `render-results.json`: briefs, measurements and render timings.
- `build_collection.py`, `verify_collection.py`, `package_collection.py`: reproducible collection tooling.
- `REQUEST.txt`: original sound-generation request.
- `contact-sheet-1.png` through `contact-sheet-3.png`: visual review overview.
