"use client";

import { useSearchParams } from "next/navigation";
import type { SoundEntry } from "@/lib/entries";
import { BrowseGrid } from "@/components/browse-grid";
import { isValidCategorySlug } from "@/lib/category-seo";

export function HomeBrowse({ entries }: { entries: SoundEntry[] }) {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("category");
  const initialCategory =
    fromUrl && isValidCategorySlug(fromUrl) ? fromUrl : "all";

  return (
    <BrowseGrid
      entries={entries}
      syncCategoryToUrl
      initialCategory={initialCategory}
    />
  );
}
