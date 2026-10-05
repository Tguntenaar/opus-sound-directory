export type SponsorPackageId =
  | "featured-home"
  | "category-takeover"
  | "model-pack"
  | "newsletter-social"
  | "custom";

export type SponsorPackage = {
  id: SponsorPackageId;
  name: string;
  tagline: string;
  bullets: string[];
};

export const SPONSOR_PACKAGES: SponsorPackage[] = [
  {
    id: "featured-home",
    name: "Featured homepage",
    tagline: "Logo, one-liner, and link above the browse grid.",
    bullets: [
      "Prime placement on the directory home",
      "Short brand blurb (≤ 120 characters)",
      "Tracked outbound link",
      "Monthly refresh on copy or creative",
    ],
  },
  {
    id: "category-takeover",
    name: "Category takeover",
    tagline: "Own a shelf — Ad beds, Chaos→Calm, UI sounds, and more.",
    bullets: [
      "Banner + logo in one category section",
      "Optional “Presented by” on every card in category",
      "Co-branded runner prompt pack (offline delivery)",
    ],
  },
  {
    id: "model-pack",
    name: "Model pack",
    tagline: "Sponsor a batch of Opus-generated sounds with your brief.",
    bullets: [
      "We publish 8–16 entries under your creative direction",
      "Full prompts, code, and metrics on the directory",
      "You get first rights to use in campaigns",
    ],
  },
  {
    id: "newsletter-social",
    name: "Newsletter & X shout",
    tagline: "Paid mention when our audience updates go out (inventory as available).",
    bullets: [
      "Featured partner line in directory newsletter drops",
      "Coordinated X post when a pack or category launches",
      "Bundled with homepage or category slots when booked together",
    ],
  },
  {
    id: "custom",
    name: "Custom / takeover",
    tagline: "Event, seasonal moment, or full directory partnership.",
    bullets: [
      "Multi-category or seasonal placements",
      "Custom categories or tagged collections",
      "Volume discounts for annual partners",
    ],
  },
];

export const BUDGET_RANGES = [
  { value: "under-1k", label: "Under $1k / month" },
  { value: "1k-3k", label: "$1k – $3k / month" },
  { value: "3k-10k", label: "$3k – $10k / month" },
  { value: "10k-plus", label: "$10k+ / month" },
  { value: "project", label: "One-off project (not monthly)" },
  { value: "exploring", label: "Exploring / not sure yet" },
] as const;
