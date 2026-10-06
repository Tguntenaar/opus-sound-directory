import sponsorsConfig from "@/content/sponsors.json";
import {
  resolveBlogSponsor,
  resolveCategorySponsor,
  resolveHomeSponsor,
  type ActiveSponsor,
  type SponsorsFile,
} from "@/lib/sponsor-resolve";

export type { ActiveSponsor, SponsorsFile };
export {
  isActiveSponsor,
  resolveBlogSponsor,
  resolveCategorySponsor,
  resolveHomeSponsor,
  withSponsorUtm,
} from "@/lib/sponsor-resolve";

const config = sponsorsConfig as SponsorsFile;

export function getHomeSponsor(): ActiveSponsor | null {
  return resolveHomeSponsor(config);
}

export function getCategorySponsor(category: string): ActiveSponsor | null {
  return resolveCategorySponsor(config, category);
}

export function getBlogActiveSponsor(slug: string): ActiveSponsor | null {
  return resolveBlogSponsor(config, slug);
}
