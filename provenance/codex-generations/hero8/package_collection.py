"""Write the evidence-based report and offline comparison page, then zip assets."""
from pathlib import Path
import json, html, zipfile
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text())
rows=json.loads((ROOT/'measurements.json').read_text())
renders=json.loads((ROOT/'render-results.json').read_text())
notes={
'heavy-boom-meme':[
'Sub-heavy impact with a ringing metallic body and diffuse dark decay; strong structural match to shock boom.',
'Round membrane body with a denser, darker feedback tail; fits the cinematic boom angle, less sharp than take 1.',
'Harmonic midrange impact with two separated dark echoes; best phone-oriented construction, more pitched than a neutral impact.'],
'whoosh-pass-by':[
'Airy midrange sweep with a distinct dropping tonal thread; matches pass-by, with the spectral apex at 0.6 s.',
'Broadband pass with a prominent low-mid Doppler body; matches the heavier-object angle.',
'Tightly concentrated bright turbulence burst with a broad stereo traverse; matches fast swish, least overtly tonal.'],
'ui-cozy-sprite':[
'Eight rounded, short tonal gestures with a clear noise-delete ending; fits cozy UI and all slicing gaps are silent.',
'Eight woody/modal gestures with short upper-mode flashes; fits mallet UI, although the highest modes are brighter.',
'Eight soft FM and bubble gestures; fits glassy UI, with more harmonic color than take 1.'],
'endless-riser-shepard':[
'Smooth ascending octave lanes over interleaved low pulses and ticks; structurally matches endless tension and passes seam checks.',
'Denser harmonic ascending lanes with warm low pulses; string-like synthesis, not a realistic sampled orchestra.',
'Bright rising harmonic lanes plus migrating random-phase bands and blips; fits electronic tension, with the busiest spectrum.'],
'dialup-modem-56k':[
'Dial tone, seven digits, ringback, answer tone, FSK, probing and training appear in order; recognizable modem construction, not a protocol emulator.',
'Narrower, saturated handset treatment with prominent probing and stuttered training; matches gritty retro-tech.',
'Two endpoint positions, short line echo and a negotiation hole; matches the two-ends angle while remaining largely centered.'],
'wah-wah-fail':[
'Three brass-like notes with a final minor-third droop and double plunger opening; matches original comic fail contour.',
'Lower three-note brass phrase ending in pitch sag and lip-buzz noise; matches deflating tuba-like fail.',
'Quick pickup pair, medium note and fluttering held droop; matches talking-mute fail, busiest of the three.'],
'arcade-game-over':[
'Eight visibly descending pulse sweeps then two low blips; strong structural match to the requested arcade loss effect.',
'Descending minor-mode pulse phrase with harmony, bass and a final noise thud; matches a melodic game-over jingle.',
'Wide falling vibrato spiral then three low blips and crunch; matches comic chip deflation.'],
'trailer-braam-hit':[
'Noise suck, clean vacuum, hard low chord and dark decay; strong structural match to a trailer braam.',
'Hard low chord with metallic modulation and stronger midrange distortion; matches aggressive braam, more abrasive.',
'Hard first chord plus a visible second swell at 2 s; matches double braam, leaves less negative space.'],
'game-coin-pickup':[
'Separated glass notes and scattered upper glints; matches collectible sparkle with a major-sixth main interval.',
'Two struck-metal events and a short upward shimmer; strongest coin-like construction, uses a major third.',
'Single fast rising portamento and stable bright ring; fits pickup, more electronic than metallic, uses a fifth.']}
ranks={
'heavy-boom-meme':([2,1,3],'Membrane weight first; choose take 3 for phone playback.'),
'whoosh-pass-by':([1,3,2],'Balanced pass first, tight whip second, heavy object third.'),
'ui-cozy-sprite':([1,2,3],'Simplest rounded palette first for frequent UI repetition.'),
'endless-riser-shepard':([1,2,3],'Cleanest illusion first; richer harmonics and electronic density are alternatives.'),
'dialup-modem-56k':([1,3,2],'Clearest staged sequence first; handset grit is a deliberate coloration.'),
'wah-wah-fail':([2,1,3],'Low deflation has the clearest comic gesture on paper.'),
'arcade-game-over':([1,3,2],'Requested sweep construction first; spiral second, musical jingle third.'),
'trailer-braam-hit':([1,2,3],'Single clean hit first; choose aggression or a second accent as needed.'),
'game-coin-pickup':([2,1,3],'Struck-metal model best fits a coin; glass and electronic glide offer distinct alternatives.')}
lines=['# Hero8 — 27 procedural sound takes','',
'All audio was generated locally from NumPy/SciPy oscillators, noise, modal models and algorithmic effects. No samples, recordings, downloads or model APIs were used. Seeds are 42, 43 and 44.','',
'## Validation','',
'27/27 WAVs pass read-back checks: exact requested sample counts, 48,000 Hz, stereo, 16-bit PCM, non-silent, finite and unclipped. FFmpeg EBU R128 reports each take at its requested −14.0 or −17.0 LUFS. Highest 4× oversampled true peak is −1.293 dBTP. All scripts rendered in well under 60 seconds on this machine.','',
'Silent tails, every UI slicing gap and the braam’s 40 ms vacuum were checked sample by sample. Riser joins were checked for value and slope discontinuities; their boundary steps are smaller than ordinary within-loop steps. Loop endpoints need not have identical values: adjacent samples should preserve the continuing waveform.','',
'All 27 spectrograms were visually inspected in the three contact sheets. The plots show the expected boom decays, centered whoosh swells, eight separated UI events, rising octave lanes, staged modem timeline, specified fail contours, arcade sweeps, braam accents and coin intervals. No missing cue or unexpected full-band boundary stripe was found.','',
'**Listening limitation:** no auditory review was performed. The descriptions and rankings below are provisional design assessments supported by source inspection, waveform measurements and spectrograms; they are not claims of having heard the files. Use `index.html` to choose by ear, especially for brass realism, repeat-listening comfort and loop illusion.','',
'## Per-take measurements and assessment','',
'| Slug | Take | Seconds | LUFS | True peak (dBTP, 4×) | Character / title fit |',
'|---|---:|---:|---:|---:|---|']
for r in rows: lines.append(f"| {r['slug']} | {r['take']} | {r['duration']:.2f} | {r['lufs']:.1f} | {r['true_peak_dbtp']:.3f} | {notes[r['slug']][r['take']-1]} |")
lines+=['','## Provisional ranking','']
for entry in manifest:
    order,reason=ranks[entry['slug']]
    lines.append(f"- **{entry['slug']}: {' > '.join(map(str,order))}. {reason}")
lines+=['','## Implementation choices and limits','',
'The modem is a designed evocation of the specified protocol stages, not a standards-compliant V.90 implementation. The orchestral riser uses additive string-like harmonics, not instrument recordings. The electronic riser’s noise texture is a dense random-phase oscillator bank so its octave handoff stays periodic. Dynamic filters use overlapping spectral windows. Band limits are practical filter roll-offs, not ideal brick-wall cutoffs.','',
'The UI error uses F5→D5: a falling minor third entirely inside F major pentatonic. Per-slot energy is normalized before mastering; subjective loudness can still differ by timbre. The more specific take contours govern the fail’s final pitch bends.','',
'Every script carries its brief in its module docstring, is self-contained and accepts `python take-N.py OUT.wav`. With no argument, it writes next to itself. Synthesis needs only Python, NumPy and SciPy. FFmpeg is optional and automatically verifies integrated loudness when available; the built-in 48 kHz BS.1770 meter is always used for mastering. Matplotlib is used only by the collection verification tool.','',
'## Files','',
'- Each slug folder: three standalone Python scripts, three WAVs, three spectrogram PNGs, render logs and FFmpeg meter summaries.',
'- `index.html`: offline listening comparison; risers loop in the player. Open after extracting the ZIP.',
'- `manifest.json`, `measurements.json`, `render-results.json`: briefs, measurements and render timings.',
'- `build_collection.py`, `verify_collection.py`, `package_collection.py`: reproducible collection tooling.',
'- `REQUEST.txt`: original sound-generation request.',
'- `contact-sheet-1.png` through `contact-sheet-3.png`: visual review overview.','']
(ROOT/'REPORT.md').write_text('\n'.join(lines))
page=['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hero8 · Listening room</title>
<style>body{margin:0;background:#101416;color:#e8eee9;font:16px/1.5 system-ui}main{max-width:1160px;margin:auto;padding:40px 24px}h1{font-size:48px;margin:0}h2{font-size:23px}p{color:#aebcb5}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}article{background:#1b2323;padding:20px;border-radius:12px;border:1px solid #35413d}section{margin:42px 0}audio{width:100%;margin:14px 0}img{width:100%}a{color:#b3e6c8}small{color:#adc0b4}summary{cursor:pointer}label{display:block;margin-top:12px}select{font:inherit;padding:6px;background:#26322c;color:white;border:1px solid #708776;border-radius:5px}@media(max-width:760px){.grid{grid-template-columns:1fr}h1{font-size:36px}}</style>
<main><small>PROCEDURAL SOUND STUDIES · 48 kHz / PCM16</small><h1>Hero8 listening room</h1><p>Nine sounds. Three takes each. Play one at a time and choose by ear. Risers loop automatically.</p><p><a href="REPORT.md">Read the report</a> · Rankings are provisional; technical and visual checks are complete, auditory review is yours.</p>''']
for entry in manifest:
    slug=entry['slug']; page.append(f'<section><h2>{html.escape(slug.replace("-"," ").title())}</h2><p>{entry["duration"]:g} s · {entry["target_lufs"]} LUFS</p><div class="grid">')
    for take in range(1,4):
        r=next(r for r in rows if r['slug']==slug and r['take']==take)
        base=f'{slug}/take-{take}'; loop='loop' if slug=='endless-riser-shepard' else ''
        page.append(f'<article><strong>Take {take}</strong><p>{html.escape(entry["angles"][take-1])}</p><audio controls preload="none" {loop} src="{base}.wav"></audio><small>{r["true_peak_dbtp"]:.2f} dBTP · seed {41+take}</small><p><a href="{base}.wav" download>WAV</a> · <a href="{base}.py" download>Python</a></p><details><summary>Spectrogram</summary><img loading="lazy" src="{base}.png" alt="Waveform and spectrogram of {slug} take {take}"></details></article>')
    page.append('</div></section>')
page.append('''</main><script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})))</script></html>''')
(ROOT/'index.html').write_text('\n'.join(page))
out=ROOT.parent/'hero8.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts: z.write(p,p.relative_to(ROOT.parent))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for suffix in ['.wav','.png','.py']:
        assert sum(n.endswith(suffix) and '/take-' in n for n in z.namelist())==27
print(f'{out}: {out.stat().st_size/1024/1024:.1f} MiB, ZIP verified')
