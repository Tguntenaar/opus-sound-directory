import Link from "next/link";
import { getRelatedGuideForCategory } from "@/lib/blog-guides";

export function RelatedGuideLink({ category }: { category: string }) {
  const guide = getRelatedGuideForCategory(category);
  if (!guide) return null;
  return (
    <p className="text-xs text-zinc-600">
      Related guide:{" "}
      <Link
        href={`/blog/${guide.slug}`}
        className="text-violet-400/90 underline-offset-2 hover:text-violet-300 hover:underline"
      >
        {guide.title}
      </Link>
    </p>
  );
}
