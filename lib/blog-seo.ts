import type { BlogPost } from "./blog-types.ts";
import { pickTitleSegment } from "./seo-limits.ts";

export function blogPageTitle(post: BlogPost): string {
  const custom = post.seoTitle?.trim();
  const variants = custom ? [custom, post.title] : [post.title];
  return pickTitleSegment(variants);
}
