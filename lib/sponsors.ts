import sponsorsConfig from "@/content/sponsors.json";

export type ActiveSponsor = {
  name: string;
  logo: string;
  line: string;
  url: string;
  utm?: string;
};

type SponsorsFile = {
  blog?: {
    active?: ActiveSponsor | null;
    bySlug?: Record<string, ActiveSponsor>;
  };
};

const config = sponsorsConfig as SponsorsFile;

export function getBlogActiveSponsor(slug: string): ActiveSponsor | null {
  const blog = config.blog;
  if (!blog) return null;
  const perSlug = blog.bySlug?.[slug];
  if (perSlug) return perSlug;
  if (blog.active) return blog.active;
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
