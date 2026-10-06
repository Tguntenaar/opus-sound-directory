import type { SoundEntry } from "@/lib/entries-types";

/** UI SFX shorter than 1 s — integrated LUFS is not a reliable loudness readout. */
export function isShortUiEntry(
  entry: Pick<SoundEntry, "category" | "timing">,
): boolean {
  return entry.category === "ui-sounds" && entry.timing.durationSec < 1;
}

/** Truthful pass/fail from measured metrics vs entry master + timing spec. */
export function entryMetricsPassed(
  entry: Pick<SoundEntry, "metrics" | "timing" | "master" | "category">,
): boolean {
  const { metrics, timing, master } = entry;
  if (metrics.truePeak == null || metrics.durationSec == null) {
    return false;
  }

  const peakOk = metrics.truePeak <= master.truePeakDbTp;

  const expectedSamples = timing.samples;
  const measuredSamples = Math.round(metrics.durationSec * timing.sampleRate);
  const samplesOk = measuredSamples === expectedSamples;

  const durationOk = Math.abs(metrics.durationSec - timing.durationSec) < 0.001;

  if (isShortUiEntry(entry)) {
    return peakOk && samplesOk && durationOk;
  }

  if (metrics.lufs == null) return false;

  const lufsOk = Math.abs(metrics.lufs - master.targetLufs) <= 1;

  return lufsOk && peakOk && samplesOk && durationOk;
}
