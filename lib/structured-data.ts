import type { BlogPost } from "@/lib/blog-types";
import type { SoundEntry } from "@/lib/entries-types";
import { modelAttribution } from "@/lib/model-display";
import { getSiteUrl, SITE_NAME, DEFAULT_SITE_DESCRIPTION } from "@/lib/site-url";
import { entryShareDescription } from "@/lib/site-metadata";
import { CC0_LICENSE_URL } from "@/lib/licenses";
import { OWNER_SAME_AS } from "@/lib/owner-profiles";
import { entryWavDownloadPath } from "@/lib/wav-url";

export function iso8601Duration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) return "PT0S";
  const whole = Math.floor(seconds);
  const frac = seconds - whole;
  const h = Math.floor(whole / 3600);
  const m = Math.floor((whole % 3600) / 60);
  const s = whole % 60;
  let out = "PT";
  if (h) out += `${h}H`;
  if (m) out += `${m}M`;
  if (s || (!h && !m)) out += `${frac > 0 ? seconds.toFixed(3) : s}S`;
  else if (frac > 0) out += `${frac.toFixed(3)}S`;
  return out.replace(/(\d)\.(\d+)S$/, (_, a, b) => `${a}.${b}S`);
}

function absoluteUrl(path: string): string {
  const base = getSiteUrl();
  if (path.startsWith("http")) return path;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

function recordingCreator(entry: SoundEntry) {
  const attr = modelAttribution(entry.modelId, entry.targetModelId);
  if (attr.isLocalSynth) {
    return {
      "@type": "SoftwareApplication",
      name: "Local numpy synth runner",
      description: "Verification pipeline synthesis (not an Anthropic API generation)",
    };
  }
  return {
    "@type": "Organization",
    name: "Anthropic",
    description: attr.primary.replace(/^Made with /, ""),
  };
}

export function entryAudioObjectJsonLd(entry: SoundEntry) {
  const url = absoluteUrl(`/e/${entry.slug}`);
  const contentUrl = absoluteUrl(entryWavDownloadPath(entry.id));
  const dur =
    entry.metrics.durationSec ?? entry.timing.durationSec;
  return {
    "@context": "https://schema.org",
    "@type": "AudioObject",
    "@id": `${url}#audio`,
    name: entry.title,
    description: entryShareDescription(entry),
    contentUrl,
    encodingFormat: "audio/wav",
    duration: iso8601Duration(dur),
    url,
    license: CC0_LICENSE_URL,
    creator: recordingCreator(entry),
    ...(entry.modelId !== "local-synth"
      ? { generator: { "@type": "SoftwareApplication", name: entry.modelId } }
      : {}),
  };
}

export function entryListItemJsonLd(entry: SoundEntry, position: number) {
  const url = absoluteUrl(`/e/${entry.slug}`);
  const contentUrl = absoluteUrl(entryWavDownloadPath(entry.id));
  const dur =
    entry.metrics.durationSec ?? entry.timing.durationSec;
  return {
    "@type": "ListItem",
    position,
    item: {
      "@type": "MusicRecording",
      name: entry.title,
      url,
      contentUrl,
      encodingFormat: "audio/wav",
      duration: iso8601Duration(dur),
      creator: recordingCreator(entry),
      ...(entry.modelId !== "local-synth"
        ? { recordedUsing: entry.modelId }
        : { additionalProperty: { "@type": "PropertyValue", name: "modelId", value: entry.modelId } }),
    },
  };
}

export function homeCollectionPageJsonLd(entries: SoundEntry[]) {
  const siteUrl = getSiteUrl();
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "@id": `${siteUrl}/#collection`,
    name: SITE_NAME,
    description: DEFAULT_SITE_DESCRIPTION,
    url: siteUrl,
    mainEntity: {
      "@type": "ItemList",
      numberOfItems: entries.length,
      itemListElement: entries.map((e, i) => entryListItemJsonLd(e, i + 1)),
    },
  };
}

export function rootWebSiteJsonLd() {
  const siteUrl = getSiteUrl();
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": `${siteUrl}/#website`,
    name: SITE_NAME,
    description: DEFAULT_SITE_DESCRIPTION,
    url: siteUrl,
    publisher: organizationJsonLd(),
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${siteUrl}/?q={search_term_string}`,
      },
      "query-input": "required name=search_term_string",
    },
  };
}

export function organizationJsonLd() {
  const siteUrl = getSiteUrl();
  return {
    "@type": "Organization",
    "@id": `${siteUrl}/#organization`,
    name: SITE_NAME,
    url: siteUrl,
    description: DEFAULT_SITE_DESCRIPTION,
    sameAs: [...OWNER_SAME_AS],
    founder: {
      "@type": "Person",
      name: "Thomas Guntenaar",
      sameAs: [...OWNER_SAME_AS],
    },
  };
}

export function blogPostingJsonLd(post: BlogPost) {
  const siteUrl = getSiteUrl();
  const url = `${siteUrl}/blog/${post.slug}`;
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.description,
    datePublished: post.date,
    dateModified: post.date,
    mainEntityOfPage: { "@type": "WebPage", "@id": url },
    url,
    keywords: post.keywords.join(", "),
    author: organizationJsonLd(),
    publisher: organizationJsonLd(),
    image: absoluteUrl("/og-default.png"),
  };
}

export function breadcrumbListJsonLd(
  items: { name: string; path: string }[],
) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: absoluteUrl(item.path),
    })),
  };
}

export function categoryFaqPageJsonLd(
  category: string,
  faq: { q: string; a: string }[],
) {
  const url = absoluteUrl(`/c/${category}`);
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    url,
    mainEntity: faq.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: { "@type": "Answer", text: item.a },
    })),
  };
}

export function faqPageJsonLd(post: BlogPost) {
  if (!post.faq.length) return null;
  const siteUrl = getSiteUrl();
  const url = `${siteUrl}/blog/${post.slug}`;
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: post.faq.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.a,
      },
    })),
    url,
  };
}
