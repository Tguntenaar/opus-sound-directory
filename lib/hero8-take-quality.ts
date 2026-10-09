/** Loudness / peak gate for Codex hero8 candidates (from measurements.json). */

export function passesTakeQuality(m: {
  lufs: number;
  truePeakDbTp: number;
}): boolean {
  const target14 = Math.abs(m.lufs - -14) <= 0.6;
  const target17 = Math.abs(m.lufs - -17) <= 0.6;
  const lufsOk = target14 || target17;
  const peakOk = m.truePeakDbTp <= -1.0;
  return lufsOk && peakOk;
}
