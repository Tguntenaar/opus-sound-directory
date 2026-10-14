"use client";

import { useSearchParams } from "next/navigation";
import type { SoundEntry } from "@/lib/entries";
import { BrowseGrid } from "@/components/browse-grid";
import { isValidCategorySlug } from "@/lib/category-seo";

type Props = {
  entries: SoundEntry[];
  /** From the server on first paint so the Suspense fallback matches. */
  initialQueryFromServer?: string;
};

export function HomeBrowse({ entries, initialQueryFromServer = "" }: Props) {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("category");
  const initialCategory =
    fromUrl && isValidCategorySlug(fromUrl) ? fromUrl : "all";
  const fromUrlQuery = searchParams.get("q")?.trim() ?? "";
  const initialQuery = fromUrlQuery || initialQueryFromServer;

  return (
    <BrowseGrid
      entries={entries}
      syncCategoryToUrl
      syncQueryToUrl
      initialCategory={initialCategory}
      initialQuery={initialQuery}
    />
  );
}
