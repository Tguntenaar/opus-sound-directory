import type { SoundEntry } from "@/lib/entries-types";

/** Max prompt chars kept for client-side browse search (see `matchesSearch`). */
const BROWSE_PROMPT_PREFIX = 200;

/**
 * Strip catalog fields that inflate the home/category RSC payload but are not
 * needed for browse cards, filters, or search.
 */
export function slimEntriesForBrowse(entries: SoundEntry[]): SoundEntry[] {
  return entries.map((entry) => {
    const prompt =
      entry.prompt.length > BROWSE_PROMPT_PREFIX
        ? entry.prompt.slice(0, BROWSE_PROMPT_PREFIX)
        : entry.prompt;

    return {
      ...entry,
      prompt,
      notes: "",
      cues: undefined,
      seed: 0,
      master: { targetLufs: entry.master.targetLufs, truePeakDbTp: entry.master.truePeakDbTp },
      metrics: {
        lufs: null,
        truePeak: null,
        durationSec: entry.metrics.durationSec ?? entry.timing.durationSec,
        passedChecks: entry.metrics.passedChecks,
      },
      assets: {
        wav: entry.assets.wav,
        mp3: entry.assets.mp3,
        spectrogram: "",
        code: "",
      },
    };
  });
}
