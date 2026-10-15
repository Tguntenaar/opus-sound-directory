import fs from "node:fs";
import path from "node:path";

export type LoudnessTargetsConfig = {
  truePeakDbTpMax: number;
  integratedToleranceLu: number;
  momentaryToleranceLu: number;
  useMomentaryWhenDurationBelowSec: number;
  defaultIntegratedLufs: number;
  entryOverrides: Record<string, { integratedLufs?: number; note?: string }>;
  profiles: Array<{
    id: string;
    integratedLufs: number;
    categories: string[];
    maxDurationSec?: number;
    minDurationSec?: number;
    excludeEntryIds?: string[];
  }>;
};

export type CatalogEntryLike = {
  id: string;
  category: string;
  timing?: { durationSec?: number };
  master?: { targetLufs?: number; truePeakDbTp?: number };
};

const configPath = path.join(import.meta.dirname, "../config/loudness-targets.json");

let cached: LoudnessTargetsConfig | null = null;

export function loadLoudnessTargetsConfig(): LoudnessTargetsConfig {
  if (!cached) {
    cached = JSON.parse(fs.readFileSync(configPath, "utf8")) as LoudnessTargetsConfig;
  }
  return cached;
}

function profileMatches(entry: CatalogEntryLike, profile: LoudnessTargetsConfig["profiles"][0]): boolean {
  if (profile.excludeEntryIds?.includes(entry.id)) return false;
  if (!profile.categories.includes(entry.category)) return false;
  const dur = entry.timing?.durationSec ?? 999;
  if (profile.maxDurationSec !== undefined && dur > profile.maxDurationSec) return false;
  if (profile.minDurationSec !== undefined && dur < profile.minDurationSec) return false;
  return true;
}

export function expectedIntegratedLufs(
  entry: CatalogEntryLike,
  config = loadLoudnessTargetsConfig(),
): number {
  const override = config.entryOverrides[entry.id];
  if (override?.integratedLufs !== undefined) return override.integratedLufs;
  if (entry.master?.targetLufs !== undefined) return entry.master.targetLufs;
  for (const profile of config.profiles) {
    if (profileMatches(entry, profile)) return profile.integratedLufs;
  }
  return config.defaultIntegratedLufs;
}

export function truePeakCeiling(
  _entry: CatalogEntryLike,
  config = loadLoudnessTargetsConfig(),
): number {
  return config.truePeakDbTpMax;
}

export function usesMomentaryLoudness(
  entry: CatalogEntryLike,
  config = loadLoudnessTargetsConfig(),
): boolean {
  const dur = entry.timing?.durationSec ?? 999;
  return dur < config.useMomentaryWhenDurationBelowSec;
}

export type MeasuredLoudness = {
  lufs: number | null;
  truePeakDbTp: number | null;
  lufsMomentaryMax?: number | null;
};

export function checkLoudnessMetrics(
  entry: CatalogEntryLike,
  measured: MeasuredLoudness,
  config = loadLoudnessTargetsConfig(),
): { ok: boolean; reasons: string[] } {
  const reasons: string[] = [];
  const target = expectedIntegratedLufs(entry, config);
  const peakCeiling = truePeakCeiling(entry, config);

  if (measured.truePeakDbTp === null) {
    reasons.push("missing true peak");
  } else if (measured.truePeakDbTp > peakCeiling + 0.05) {
    reasons.push(`true peak ${measured.truePeakDbTp.toFixed(2)} dBTP > ${peakCeiling.toFixed(2)}`);
  }

  if (usesMomentaryLoudness(entry, config) && measured.lufsMomentaryMax != null) {
    if (Math.abs(measured.lufsMomentaryMax - target) > config.momentaryToleranceLu) {
      reasons.push(
        `momentary max ${measured.lufsMomentaryMax.toFixed(2)} LUFS vs target ${target.toFixed(2)}`,
      );
    }
  } else if (measured.lufs === null) {
    reasons.push("missing integrated LUFS");
  } else if (Math.abs(measured.lufs - target) > config.integratedToleranceLu) {
    reasons.push(`integrated ${measured.lufs.toFixed(2)} LUFS vs target ${target.toFixed(2)}`);
  }

  return { ok: reasons.length === 0, reasons };
}
