export type ActiveSponsor = {
  name: string;
  logo: string;
  line: string;
  url: string;
  utm?: string;
};

export type SponsorsFile = {
  blog?: {
    active?: ActiveSponsor | null;
    bySlug?: Record<string, ActiveSponsor | null>;
  };
  home?: ActiveSponsor | null;
  categories?: Record<string, ActiveSponsor | null>;
};

export function isActiveSponsor(value: unknown): value is ActiveSponsor {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.name === "string" &&
    v.name.trim().length > 0 &&
    typeof v.url === "string" &&
    v.url.trim().length > 0 &&
    typeof v.line === "string" &&
    typeof v.logo === "string" &&
    (v.utm === undefined || typeof v.utm === "string")
  );
}

export function resolveHomeSponsor(file: SponsorsFile): ActiveSponsor | null {
  return isActiveSponsor(file.home) ? file.home : null;
}

export function resolveCategorySponsor(
  file: SponsorsFile,
  category: string,
): ActiveSponsor | null {
  if (!category) return null;
  const raw = file.categories?.[category];
  return isActiveSponsor(raw) ? raw : null;
}

export function resolveBlogSponsor(file: SponsorsFile, slug: string): ActiveSponsor | null {
  const blog = file.blog;
  if (!blog) return null;
  const perSlug = blog.bySlug?.[slug];
  if (isActiveSponsor(perSlug)) return perSlug;
  if (isActiveSponsor(blog.active)) return blog.active;
  return null;
}

/** Append optional UTM query string to a destination URL. */
export function withSponsorUtm(url: string, utm?: string): string {
  if (!utm?.trim()) return url;
  const extra = new URLSearchParams(utm.startsWith("?") ? utm.slice(1) : utm);
  const qs = extra.toString();
  if (!qs) return url;
  return `${url}${url.includes("?") ? "&" : "?"}${qs}`;
}
