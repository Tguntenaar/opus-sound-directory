"use client";

import { useSearchParams } from "next/navigation";
import type { SoundEntry } from "@/lib/entries";
import { BrowseGrid } from "@/components/browse-grid";
import { isValidCategorySlug } from "@/lib/category-seo";

type Props = {
  entries: SoundEntry[];
  catalogHref?: string;
  featuredEntry?: SoundEntry;
  featuredControl?: SoundEntry;
  /** From the server on first paint so the Suspense fallback matches. */
  initialQueryFromServer?: string;
};

export function HomeBrowse({
  entries,
  catalogHref,
  featuredEntry,
  featuredControl,
  initialQueryFromServer = "",
}: Props) {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("category");
  const initialCategory =
    fromUrl && isValidCategorySlug(fromUrl) ? fromUrl : "all";
  const fromUrlQuery = searchParams.get("q")?.trim() ?? "";
  const initialQuery = fromUrlQuery || initialQueryFromServer;

  return (
    <BrowseGrid
      entries={entries}
      catalogHref={catalogHref}
      featuredEntry={featuredEntry}
      featuredControl={featuredControl}
      syncCategoryToUrl
      syncQueryToUrl
      initialCategory={initialCategory}
      initialQuery={initialQuery}
    />
  );
}
