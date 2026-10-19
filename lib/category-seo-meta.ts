import { pickMetaDescription, pickTitleSegment } from "./seo-limits.ts";
import type { CategorySeoContent } from "./category-seo.ts";

/** Document `<title>` segment for a category hub (visual h1 stays unchanged). */
export function categoryPageTitle(seo: CategorySeoContent): string {
  const { h1 } = seo;
  const variants = [
    h1,
    h1.replace(/^Free Royalty-Free /, "Free "),
    h1.replace(/ Sound Effects/g, " SFX"),
    h1.replace(/ & /g, " and "),
    h1.replace(/ for Video$/, ""),
  ].filter((v, i, arr) => v.length > 0 && arr.indexOf(v) === i);
  return pickTitleSegment(variants);
}

export function categoryPageDescription(intro: string): string {
  return pickMetaDescription([intro]);
}
