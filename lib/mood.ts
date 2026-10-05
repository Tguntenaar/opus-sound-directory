/** Browseable mood / style facets (orthogonal tags per entry). */
export const MOOD_FACETS: Record<string, string> = {
  upbeat: "Upbeat",
  slow: "Slow",
  happy: "Happy",
  sad: "Sad",
  energetic: "Energetic",
  calm: "Calm",
  bright: "Bright",
  dark: "Dark",
};

export type MoodSlug = keyof typeof MOOD_FACETS;

export const TEMPO_LABELS: Record<string, string> = {
  slow: "Slow tempo",
  medium: "Mid tempo",
  fast: "Fast tempo",
};

export type TempoSlug = keyof typeof TEMPO_LABELS;

export function formatMood(slug: string): string {
  return MOOD_FACETS[slug as MoodSlug] ?? slug;
}
