/** Canonical path for full-quality WAV download (R2 with static fallback). */
export function entryWavDownloadPath(entryId: string): string {
  return `/audio/${entryId}/out.wav`;
}

export function entryWavDownloadUrl(entryId: string, siteOrigin: string): string {
  const base = siteOrigin.replace(/\/$/, "");
  return `${base}${entryWavDownloadPath(entryId)}`;
}
