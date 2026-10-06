import { getEntryById, getEntryBySlug } from "@/lib/entries";
import { getCommunityCode, getCommunityEntryBySlug } from "@/lib/community-kv";
import type { SoundEntry } from "@/lib/entries-types";
import { getSiteUrl } from "@/lib/site-url";
import { isCommunityEntry } from "@/lib/community-types";
import { entryWavDownloadUrl } from "@/lib/wav-url";

const MAX_INLINE_CODE = 20_000;

async function loadStaticCode(assetPath: string): Promise<string | null> {
  if (!assetPath.startsWith("/assets/")) return null;
  const base = getSiteUrl();
  try {
    const res = await fetch(`${base}${assetPath}`);
    if (!res.ok) return null;
    return await res.text();
  } catch {
    return null;
  }
}

export async function resolveSoundEntry(idOrSlug: string): Promise<SoundEntry | null> {
  const bySlug = getEntryBySlug(idOrSlug) ?? (await getCommunityEntryBySlug(idOrSlug));
  if (bySlug) return bySlug;
  const byId = getEntryById(idOrSlug);
  if (byId) return byId;
  return null;
}

export async function getSoundDetail(id: string) {
  const entry = await resolveSoundEntry(id);
  if (!entry) return null;
  const base = getSiteUrl();
  let codeInline: string | undefined;
  let codeUrl: string | undefined;

  if (isCommunityEntry(entry)) {
    const code = await getCommunityCode(entry.slug);
    if (code) {
      if (code.length <= MAX_INLINE_CODE) codeInline = code;
      else codeUrl = `${base}${entry.codeApiPath}`;
    }
  } else {
    const inline = await loadStaticCode(entry.assets.code);
    if (inline) {
      if (inline.length <= MAX_INLINE_CODE) codeInline = inline;
      else codeUrl = `${base}${entry.assets.code}`;
    } else {
      codeUrl = `${base}${entry.assets.code}`;
    }
  }

  return {
    entry,
    pageUrl: `${base}/e/${entry.slug}`,
    assets: {
      mp3: entry.assets.mp3.startsWith("http")
        ? entry.assets.mp3
        : entry.assets.mp3
          ? `${base}${entry.assets.mp3}`
          : "",
      wav: isCommunityEntry(entry)
        ? entry.assets.wav.startsWith("http")
          ? entry.assets.wav
          : entry.assets.wav
            ? `${base}${entry.assets.wav}`
            : ""
        : entryWavDownloadUrl(entry.id, base),
      spectrogram: entry.assets.spectrogram
        ? entry.assets.spectrogram.startsWith("http")
          ? entry.assets.spectrogram
          : `${base}${entry.assets.spectrogram}`
        : "",
      codeUrl,
      codeInline,
    },
  };
}
