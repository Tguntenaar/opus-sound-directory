"use client";

import Link from "next/link";
import { getRelatedGuideForCategory } from "@/lib/blog-guides";
import { captureEvent } from "@/lib/analytics-client";

export function RelatedGuideLink({ category }: { category: string }) {
  const guide = getRelatedGuideForCategory(category);
  if (!guide) return null;
  return (
    <p className="text-xs text-zinc-600">
      Related guide:{" "}
      <Link
        href={`/blog/${guide.slug}`}
        className="text-violet-400/90 underline-offset-2 hover:text-violet-300 hover:underline"
        onClick={() =>
          captureEvent("blog_related_guide_click", {
            category,
            guide_slug: guide.slug,
          })
        }
      >
        {guide.title}
      </Link>
    </p>
  );
}
