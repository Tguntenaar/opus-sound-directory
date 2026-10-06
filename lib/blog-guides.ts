import { getBlogPostBySlug } from "@/lib/blog";

/** Most relevant published guide per sound category (internal linking). */
const CATEGORY_GUIDE_SLUG: Record<string, string> = {
  "ad-beds": "royalty-free-sound-effects-and-music-for-tiktok-reels-shorts-ads",
  "ui-sounds": "how-to-write-a-sound-effect-prompt",
  "logo-stings": "how-to-make-an-audio-logo",
  drops: "whoosh-and-transition-sound-effects-for-video-editing",
  risers: "how-to-add-sound-and-music-to-ai-generated-videos",
  "chaos-calm": "how-to-add-sound-and-music-to-ai-generated-videos",
  ambient: "how-to-add-sound-and-music-to-ai-generated-videos",
};

/** Entry-specific guide overrides (takes precedence over category map). */
const ENTRY_GUIDE_SLUG: Record<string, string> = {
  "podcast-intro-10s": "podcast-intro-music",
  "meditation-bowls-40s": "seamless-ambient-loops-and-meditation-sounds",
  "ocean-shore-loop": "seamless-ambient-loops-and-meditation-sounds",
  "sci-fi-hangar-loop": "seamless-ambient-loops-and-meditation-sounds",
  "heartbeat-tension-12s": "horror-and-tension-sound-effects",
  "logo-sting-dark-cinematic": "horror-and-tension-sound-effects",
  "tape-stop-transition": "glitch-tape-stop-and-countdown-sound-effects",
  "glitch-transition-digital": "glitch-tape-stop-and-countdown-sound-effects",
  "countdown-10-to-0": "glitch-tape-stop-and-countdown-sound-effects",
  "synthwave-drive-20s": "synthwave-and-8-bit-music-for-videos",
  "game-coin-pickup": "synthwave-and-8-bit-music-for-videos",
  "game-level-up": "synthwave-and-8-bit-music-for-videos",
};

export function getRelatedGuideForCategory(category: string) {
  const slug = CATEGORY_GUIDE_SLUG[category];
  if (!slug) return undefined;
  return getBlogPostBySlug(slug);
}

export function getRelatedGuideForEntry(entryId: string, category: string) {
  const entrySlug = ENTRY_GUIDE_SLUG[entryId];
  if (entrySlug) {
    const guide = getBlogPostBySlug(entrySlug);
    if (guide) return guide;
  }
  return getRelatedGuideForCategory(category);
}
