/** Path + query for home browse URL sync (`?category=`, `?q=`). */
export function buildHomeBrowseHref(options: {
  category?: string;
  query?: string;
}): string {
  const params = new URLSearchParams();
  const category = options.category ?? "all";
  const query = options.query?.trim() ?? "";
  if (category !== "all") params.set("category", category);
  if (query) params.set("q", query);
  const qs = params.toString();
  return qs ? `/?${qs}` : "/";
}
