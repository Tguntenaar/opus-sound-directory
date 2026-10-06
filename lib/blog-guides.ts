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

export function getRelatedGuideForCategory(category: string) {
  const slug = CATEGORY_GUIDE_SLUG[category];
  if (!slug) return undefined;
  return getBlogPostBySlug(slug);
}
