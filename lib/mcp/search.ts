import { getAllEntries } from "@/lib/entries";
import type { SoundEntry } from "@/lib/entries-types";
import { listCommunityEntries } from "@/lib/community-kv";
import { getSiteUrl } from "@/lib/site-url";
import { modelAttribution } from "@/lib/model-display";
import { scoreEntry } from "@/lib/mcp/search-scoring";
import { entryWavDownloadUrl } from "@/lib/wav-url";
import { isCommunityEntry } from "@/lib/community-types";

export type SoundSearchHit = {
  id: string;
  title: string;
  category: string;
  mood: string[];
  tempo?: string;
  durationSec: number;
  modelId: string;
  modelLabel: string;
  url: string;
  mp3: string;
  wav: string;
  lufs: number | null;
  score: number;
};

export { scoreEntry } from "@/lib/mcp/search-scoring";

export async function searchSounds(options: {
  query?: string;
  category?: string;
  mood?: string;
  tempo?: string;
  maxDurationSec?: number;
  limit?: number;
}): Promise<SoundSearchHit[]> {
  const staticEntries = getAllEntries();
  const community = await listCommunityEntries();
  const merged = [...staticEntries, ...community];
  const query = options.query ?? "";
  const limit = Math.min(Math.max(options.limit ?? 20, 1), 50);
  const base = getSiteUrl();

  const hits: SoundSearchHit[] = [];
  for (const entry of merged) {
    const s = scoreEntry(entry, query, options);
    if (s <= 0) continue;
    const attr = modelAttribution(entry.modelId, entry.targetModelId);
    const modelLabel =
      entry.modelId === "community"
        ? "Community submission"
        : attr.isLocalSynth
          ? "local-synth"
          : entry.modelId;
    hits.push({
      id: entry.id,
      title: entry.title,
      category: entry.category,
      mood: entry.mood,
      tempo: entry.tempo,
      durationSec: entry.metrics.durationSec ?? entry.timing.durationSec,
      modelId: entry.modelId,
      modelLabel,
      url: `${base}/e/${entry.slug}`,
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
      lufs: entry.metrics.lufs,
      score: s,
    });
  }

  hits.sort((a, b) => b.score - a.score || a.title.localeCompare(b.title));
  return hits.slice(0, limit);
}

export async function listCategoryCounts(): Promise<
  { id: string; label: string; count: number; moods: Record<string, number> }[]
> {
  const staticEntries = getAllEntries();
  const community = await listCommunityEntries();
  const merged = [...staticEntries, ...community];
  const { CATEGORIES, CATEGORY_ORDER } = await import("@/lib/categories");
  return CATEGORY_ORDER.map((id) => {
    const inCat = merged.filter((e) => e.category === id);
    const moods: Record<string, number> = {};
    for (const e of inCat) {
      for (const m of e.mood) moods[m] = (moods[m] ?? 0) + 1;
    }
    return {
      id,
      label: CATEGORIES[id].label,
      count: inCat.length,
      moods,
    };
  });
}
