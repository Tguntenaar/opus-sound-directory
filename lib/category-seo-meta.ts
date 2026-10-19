import { pickMetaDescription, pickTitleSegment } from "./seo-limits.ts";
import type { CategorySeoContent } from "./category-seo.ts";

/** Document `<title>` segment for a category hub (visual h1 stays unchanged). */
export function categoryPageTitle(seo: CategorySeoContent): string {
  const { h1, titleSegment } = seo;
  const variants = [
    ...(titleSegment ? [titleSegment] : []),
    h1,
    h1.replace(/^Free Royalty-Free /, "Free "),
    h1.replace(/ Sound Effects/g, " SFX"),
    h1.replace(/ & /g, " and "),
    h1.replace(/ for Video$/, ""),
  ].filter((v, i, arr) => v.length > 0 && arr.indexOf(v) === i);
  return pickTitleSegment(variants);
}

export function categoryPageDescription(seo: CategorySeoContent): string {
  const variants = [seo.intro];
  if (seo.introShort) variants.push(seo.introShort);
  return pickMetaDescription(variants);
}
