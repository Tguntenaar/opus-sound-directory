export const CATEGORIES: Record<
  string,
  { label: string; description: string }
> = {
  "chaos-calm": {
    label: "Chaos → calm",
    description: "Tension releases into breathable beds, timed to video frames.",
  },
  "ad-beds": {
    label: "Ad beds by length",
    description: "Upbeat and narrative beds at common ad durations.",
  },
  drops: {
    label: "Drops & transitions",
    description: "Impacts, whooshes, and cut helpers.",
  },
  risers: {
    label: "Risers",
    description: "Builds that land on a frame.",
  },
  "ui-sounds": {
    label: "UI & app sounds",
    description: "Short feedback tones for product surfaces.",
  },
  "logo-stings": {
    label: "Logo stings",
    description: "Brand moments in a few seconds.",
  },
  ambient: {
    label: "Ambient beds",
    description: "Background textures and loop-friendly pads.",
  },
};

export const CATEGORY_ORDER = [
  "chaos-calm",
  "ad-beds",
  "drops",
  "risers",
  "ui-sounds",
  "logo-stings",
  "ambient",
] as const;
