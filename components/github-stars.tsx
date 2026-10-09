"use client";

import { useEffect, useState } from "react";
import { Star } from "lucide-react";
import { IconTooltip } from "@/components/icon-tooltip";

export function GithubStars() {
  const [stars, setStars] = useState<number | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/github-stars", { signal: controller.signal }).then(async response => {
      if (!response.ok) return;
      const data = await response.json() as { stars?: number };
      if (Number.isSafeInteger(data.stars) && data.stars! >= 0) setStars(data.stars!);
    }).catch(() => { /* Keep the repository link available when the count is unavailable. */ });
    return () => controller.abort();
  }, []);

  return <IconTooltip label="Star on GitHub" side="bottom">
    <a href="https://github.com/Tguntenaar/opus-sound-directory" target="_blank" rel="noopener noreferrer"
      aria-label={stars === null ? "Star Opus Sounds on GitHub" : `Star Opus Sounds on GitHub (${stars} stars)`}
      className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg px-2 text-zinc-400 transition-colors hover:bg-zinc-900/80 hover:text-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-400">
      <Star className="h-4 w-4" aria-hidden="true" />
      <span className="min-w-2 text-xs tabular-nums">{stars === null ? "" : new Intl.NumberFormat("en", { notation: "compact" }).format(stars)}</span>
    </a>
  </IconTooltip>;
}
