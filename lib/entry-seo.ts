import { CATEGORIES } from "@/lib/categories";
import { formatMood } from "@/lib/mood";
import type { SoundEntry } from "@/lib/entries-types";
import { canonicalForPath } from "@/lib/site-metadata";
import { getSiteUrl } from "@/lib/site-url";

const CATEGORY_NOUN: Record<string, string> = {
  "ad-beds": "Ad Music Bed",
  "ui-sounds": "UI Sound Effect",
  "logo-stings": "Logo Sting",
  drops: "Whoosh Sound Effect",
  risers: "Riser Sound Effect",
  "chaos-calm": "Transition Bed",
  ambient: "Ambient Bed",
  meme: "Meme Sound Effect",
  gaming: "Game Sound Effect",
  cinematic: "Cinematic Sound Effect",
  "retro-tech": "Retro Tech Sound Effect",
};

const USE_CASE: Record<string, string> = {
  "ad-beds": "TikTok, Reels, and Shorts ads",
  "ui-sounds": "app demos and product videos",
  "logo-stings": "intros and brand reveals",
  drops: "cuts and transitions",
  risers: "hooks and reveal moments",
  "chaos-calm": "story arc edits",
  ambient: "underscoring and B-roll",
  meme: "reaction edits and comedy beats",
  gaming: "games, streams and gaming edits",
  cinematic: "trailers and big reveals",
  "retro-tech": "nostalgia edits and throwback intros",
};

export function categoryNoun(category: string): string {
  return CATEGORY_NOUN[category] ?? "Sound Effect";
}

export function entryPageTitle(entry: SoundEntry): string {
  const noun = categoryNoun(entry.category);
  return `${entry.title} — Free ${noun} (WAV, MP3, CC0)`;
}

export function entryMetaDescription(entry: SoundEntry): string {
  const dur = entry.timing.durationSec;
  const bpm = entry.timing.bpm;
  const moods = (entry.mood ?? []).slice(0, 3).map(formatMood).join(", ");
  const use = USE_CASE[entry.category] ?? "video";
  const cat = CATEGORIES[entry.category]?.label ?? entry.category;
  const moodPart = moods ? `${moods} · ` : "";
  const lufs =
    entry.metrics.lufs != null ? ` ${entry.metrics.lufs} LUFS.` : "";
  const bpmPart = bpm != null ? ` at ${bpm} BPM` : "";
  return `Free ${cat.toLowerCase()} — ${entry.title}, ${dur}s${bpmPart}. ${moodPart}CC0 download for ${use}.${lufs} Prompt, Python code, and spectrogram.`;
}

export function spectrogramAlt(entry: SoundEntry): string {
  const noun = categoryNoun(entry.category).toLowerCase();
  const bpmPart =
    entry.timing.bpm != null ? ` and ${entry.timing.bpm} BPM` : "";
  return `Spectrogram of ${entry.title}, a free ${noun} at ${entry.timing.durationSec}s${bpmPart}`;
}

export function entryAudioUrls(entry: SoundEntry) {
  const base = getSiteUrl();
  const mp3 = `${base}${entry.assets.mp3}`;
  const canonical = canonicalForPath(`/e/${entry.slug}`);
  return { mp3, canonical };
}

export function relatedEntries(entry: SoundEntry, all: SoundEntry[], limit = 3): SoundEntry[] {
  const sameCategory = all.filter(
    (e) => e.id !== entry.id && e.category === entry.category,
  );
  const moodSet = new Set(entry.mood ?? []);
  const scored = sameCategory.map((e) => {
    const overlap = (e.mood ?? []).filter((m) => moodSet.has(m)).length;
    return { e, score: overlap };
  });
  scored.sort((a, b) => b.score - a.score || a.e.title.localeCompare(b.e.title));
  const picked = scored.slice(0, limit).map((s) => s.e);
  if (picked.length >= limit) return picked;
  for (const e of sameCategory) {
    if (picked.length >= limit) break;
    if (!picked.find((p) => p.id === e.id)) picked.push(e);
  }
  return picked.slice(0, limit);
}
