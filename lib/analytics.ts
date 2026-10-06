import type { SoundEntry } from "@/lib/entries-types";

export type AnalyticsSource = "card" | "detail" | "featured" | "blog_embed";

export type SoundEventProps = {
  sound_id: string;
  category: string;
  mood: string;
  model_id: string;
  source: AnalyticsSource;
};

export function soundEventProps(
  entry: Pick<SoundEntry, "id" | "category" | "mood" | "modelId">,
  source: AnalyticsSource,
): SoundEventProps {
  return {
    sound_id: entry.id,
    category: entry.category,
    mood: (entry.mood ?? []).join(","),
    model_id: entry.modelId,
    source,
  };
}

export type OutboundDestination = "github" | "x" | "profile";
