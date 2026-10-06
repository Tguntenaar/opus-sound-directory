"use client";

import { ShareButton } from "@/components/share-button";
import type { SoundEntry } from "@/lib/entries";

export function EntryShareActions({
  slug,
  title,
  entry,
}: {
  slug: string;
  title: string;
  entry?: Pick<SoundEntry, "id" | "category" | "mood" | "modelId">;
}) {
  const url =
    typeof window !== "undefined"
      ? `${window.location.origin}/e/${slug}`
      : `/e/${slug}`;
  return <ShareButton url={url} title={title} entry={entry} source="detail" />;
}
