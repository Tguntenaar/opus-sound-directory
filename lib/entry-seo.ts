import { CATEGORIES } from "./categories.ts";
import { formatMood } from "./mood.ts";
import type { SoundEntry } from "./entries-types.ts";
import { canonicalForPath, getSiteUrl } from "./site-url.ts";
import { pickMetaDescription, pickTitleSegment } from "./seo-limits.ts";

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
  guitar: "Guitar Sound",
  music: "Music Track",
  foley: "Foley Sound Effect",
};

/** Shorter nouns when the full title would exceed snippet limits. */
const SHORT_CATEGORY_NOUN: Record<string, string> = {
  "ad-beds": "Ad Bed",
  "ui-sounds": "UI SFX",
  "logo-stings": "Logo Sting",
  drops: "Whoosh SFX",
  risers: "Riser SFX",
  "chaos-calm": "Transition Bed",
  ambient: "Ambient Bed",
  meme: "Meme SFX",
  gaming: "Game SFX",
  cinematic: "Cinematic SFX",
  "retro-tech": "Retro Tech SFX",
  guitar: "Guitar",
  music: "Music Bed",
  foley: "Foley SFX",
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
  guitar: "intros, vlogs and warm, human-feeling edits",
  music: "underscores, explainers and classical-style edits",
  foley: "car spots, action cuts and realistic B-roll",
};

export function categoryNoun(category: string): string {
  return CATEGORY_NOUN[category] ?? "Sound Effect";
}

function shortCategoryNoun(category: string): string {
  return SHORT_CATEGORY_NOUN[category] ?? "SFX";
}

export function entryPageTitle(entry: SoundEntry): string {
  const noun = categoryNoun(entry.category);
  const shortNoun = shortCategoryNoun(entry.category);
  const title = entry.title;
  const custom = entry.seoTitle?.trim();
  const variants = [
    ...(custom ? [custom] : []),
    `${title} — Free ${noun} (WAV, MP3, CC0)`,
    `${title} — Free ${noun} (CC0)`,
    `${title} — Free ${noun}`,
    `${title} — Free ${shortNoun} (CC0)`,
    `${title} — Free ${shortNoun}`,
    title,
  ];
  return pickTitleSegment(variants);
}

export function entryMetaDescription(entry: SoundEntry): string {
  const dur = entry.timing.durationSec;
  const bpm = entry.timing.bpm;
  const moods = (entry.mood ?? []).slice(0, 3).map(formatMood).join(", ");
  const use = USE_CASE[entry.category] ?? "video";
  const cat = CATEGORIES[entry.category]?.label ?? entry.category;
  const moodPart = moods ? `${moods} · ` : "";
  const lufs = entry.metrics.lufs != null ? ` ${entry.metrics.lufs} LUFS.` : "";
  const bpmPart = bpm != null ? ` at ${bpm} BPM` : "";
  const footer = " Prompt, Python code, and spectrogram.";
  const shortUse = use.length > 36 ? "video edits" : use;

  const full = `Free ${cat.toLowerCase()} — ${entry.title}, ${dur}s${bpmPart}. ${moodPart}CC0 download for ${use}.${lufs}${footer}`;
  const noFooter = `Free ${cat.toLowerCase()} — ${entry.title}, ${dur}s${bpmPart}. ${moodPart}CC0 download for ${use}.${lufs}`;
  const noLufs = `Free ${cat.toLowerCase()} — ${entry.title}, ${dur}s${bpmPart}. ${moodPart}CC0 download for ${use}.`;
  const noMood = `Free ${cat.toLowerCase()} — ${entry.title}, ${dur}s${bpmPart}. CC0 download for ${use}.`;
  const noBpm = `Free ${cat.toLowerCase()} — ${entry.title}, ${dur}s. CC0 download for ${shortUse}.`;
  const compact = `Free ${categoryNoun(entry.category).toLowerCase()}: ${entry.title}. ${dur}s CC0 WAV/MP3 for ${shortUse}.`;

  return pickMetaDescription([full, noFooter, noLufs, noMood, noBpm, compact]);
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
