const ALLOWED_HOST_SUFFIXES = [
  "opussounds.directory",
  "githubusercontent.com",
  "raw.githubusercontent.com",
  "cdn.jsdelivr.net",
  "files.catbox.moe",
  "0x0.st",
];

const MAX_AUDIO_BYTES = 10 * 1024 * 1024;

export function isAllowedAudioUrl(url: string): boolean {
  try {
    const u = new URL(url);
    if (u.protocol !== "https:") return false;
    const path = u.pathname.toLowerCase();
    if (!path.endsWith(".mp3") && !path.endsWith(".wav")) return false;
    const host = u.hostname.toLowerCase();
    return ALLOWED_HOST_SUFFIXES.some(
      (suffix) => host === suffix || host.endsWith(`.${suffix}`),
    );
  } catch {
    return false;
  }
}

/** Best-effort HEAD check for size; returns false when uncertain in dev. */
export async function validateAudioUrlSize(url: string): Promise<boolean> {
  if (!isAllowedAudioUrl(url)) return false;
  try {
    const res = await fetch(url, { method: "HEAD", redirect: "follow" });
    if (!res.ok) return false;
    const len = res.headers.get("content-length");
    if (!len) return true;
    const n = Number.parseInt(len, 10);
    return Number.isFinite(n) && n > 0 && n <= MAX_AUDIO_BYTES;
  } catch {
    return true;
  }
}

export function audioExtension(url: string): "mp3" | "wav" | null {
  const path = new URL(url).pathname.toLowerCase();
  if (path.endsWith(".mp3")) return "mp3";
  if (path.endsWith(".wav")) return "wav";
  return null;
}
