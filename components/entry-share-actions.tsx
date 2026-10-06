"use client";

import { ShareButton } from "@/components/share-button";

export function EntryShareActions({ slug, title }: { slug: string; title: string }) {
  const url =
    typeof window !== "undefined"
      ? `${window.location.origin}/e/${slug}`
      : `/e/${slug}`;
  return <ShareButton url={url} title={title} />;
}
