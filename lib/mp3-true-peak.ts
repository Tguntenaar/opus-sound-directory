import { execFileSync, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

/** Decoded-programme true peak ceiling for shipped MP3 previews (dBTP / ffmpeg ebur128). */
export const MP3_TRUE_PEAK_CEILING_DBTP = -1.0;

export function ffmpegAvailable(): boolean {
  try {
    execFileSync("ffmpeg", ["-version"], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

export type Ebur128Summary = {
  lufs: number | null;
  truePeakDbTp: number | null;
  lufsMomentaryMax: number | null;
};

export function measureEbur128(filePath: string): Ebur128Summary {
  const { stderr, status, error } = spawnSync(
    "ffmpeg",
    ["-hide_banner", "-i", filePath, "-af", "ebur128=peak=true", "-f", "null", "-"],
    { encoding: "utf8", maxBuffer: 16 * 1024 * 1024 },
  );
  if (error || status !== 0 || !stderr) {
    return { lufs: null, truePeakDbTp: null, lufsMomentaryMax: null };
  }
  let lufs: number | null = null;
  let truePeakDbTp: number | null = null;
  let lufsMomentaryMax: number | null = null;
  for (const line of stderr.split("\n")) {
    const iMatch = line.match(/\bI:\s*([-0-9.]+)\s*LUFS/);
    if (iMatch) {
      const v = Number(iMatch[1]);
      if (v > -70) lufs = v;
    }
    const mMatch = line.match(/\bM:\s*([-0-9.]+)/);
    if (mMatch) {
      const v = Number(mMatch[1]);
      if (v > -70) {
        lufsMomentaryMax =
          lufsMomentaryMax === null ? v : Math.max(lufsMomentaryMax, v);
      }
    }
    if (line.includes("Peak:") && line.includes("dBFS")) {
      const peakPart = line.split("Peak:")[1]?.split("dBFS")[0]?.trim();
      if (peakPart) truePeakDbTp = Number(peakPart);
    }
  }
  return { lufs, truePeakDbTp, lufsMomentaryMax };
}

export function listPublicMp3Files(publicRoot: string): string[] {
  const out: string[] = [];
  const assetsDir = path.join(publicRoot, "assets");
  if (!fs.existsSync(assetsDir)) return out;
  const walk = (dir: string) => {
    for (const name of fs.readdirSync(dir)) {
      const full = path.join(dir, name);
      const st = fs.statSync(full);
      if (st.isDirectory()) walk(full);
      else if (name.endsWith(".mp3")) out.push(full);
    }
  };
  walk(assetsDir);
  return out.sort();
}

export function mp3PassesTruePeakCeiling(truePeakDbTp: number | null): boolean {
  return truePeakDbTp !== null && truePeakDbTp <= MP3_TRUE_PEAK_CEILING_DBTP;
}
