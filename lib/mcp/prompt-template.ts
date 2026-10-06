import { CATEGORIES, CATEGORY_ORDER } from "@/lib/categories";

const BASE_TEMPLATE = `Make a [DURATION_SEC] s [ROLE] for [VIDEO_CONTEXT] at [FPS] fps.
Output: one WAV, 48 kHz / 16-bit / stereo, exactly [SAMPLE_COUNT] samples.
Python + numpy/scipy only. Synthesise everything (no samples, no downloads). Fixed random seed [SEED].
Timing: [BPM] BPM (1 beat = [FRAMES_PER_BEAT] frames). Cues: frame [0] = [CUE_0]; …; last beat fades to exactly 0.
Sound: [CONCRETE DESCRIPTION — pitch, attack, decay, texture; styles not artist names].
Master: −14 LUFS integrated, true peak ≤ −1 dBTP.
You can't listen, so verify: measure loudness and peak with ffmpeg ebur128, check exact length, confirm cue frames, render a spectrogram. Fix and re-render until every check passes, then report the numbers.`;

export function getHousePromptTemplate(category?: string): {
  template: string;
  category?: string;
  categoryLabel?: string;
  constraints: string[];
} {
  const constraints = [
    "numpy/scipy synthesis only",
    "48 kHz stereo WAV",
    "target −14 LUFS integrated, true peak ≤ −1 dBTP",
    "cue frames tied to video fps",
    "fixed random seed in code",
  ];
  const cat = category && CATEGORIES[category] ? category : undefined;
  return {
    template: BASE_TEMPLATE,
    category: cat,
    categoryLabel: cat ? CATEGORIES[cat].label : undefined,
    constraints,
    categories: CATEGORY_ORDER,
  };
}
