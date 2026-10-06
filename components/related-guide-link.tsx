"use client";

import Link from "next/link";
import { getRelatedGuideForEntry } from "@/lib/blog-guides";
import { captureEvent } from "@/lib/analytics-client";

export function RelatedGuideLink({
  entryId,
  category,
}: {
  entryId: string;
  category: string;
}) {
  const guide = getRelatedGuideForEntry(entryId, category);
  if (!guide) return null;
  return (
    <p className="text-xs text-zinc-400">
      Related guide:{" "}
      <Link
        href={`/blog/${guide.slug}`}
        className="text-violet-400 underline-offset-2 hover:text-violet-300 hover:underline"
        onClick={() =>
          captureEvent("blog_related_guide_click", {
            category,
            entry_id: entryId,
            guide_slug: guide.slug,
          })
        }
      >
        {guide.title}
      </Link>
    </p>
  );
}
