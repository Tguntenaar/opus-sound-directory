"use client";

import Link from "next/link";
import { ArrowUpRight, Megaphone } from "lucide-react";
import { getBlogActiveSponsor, withSponsorUtm } from "@/lib/sponsors";
import { cn } from "@/lib/utils";
import { captureEvent } from "@/lib/analytics-client";

type Props = {
  slug: string;
};

function trackBlogSponsorCta(slug: string, sponsored: boolean) {
  captureEvent("sponsor_cta_click", {
    placement: "blog",
    slug,
    sponsored,
  });
}

export function BlogSponsorCard({ slug }: Props) {
  const active = getBlogActiveSponsor(slug);
  const sponsorPageHref = `/sponsor?ref=blog-${encodeURIComponent(slug)}`;

  if (active) {
    const href = withSponsorUtm(active.url, active.utm);
    return (
      <aside
        className={cn(
          "not-prose mt-10 rounded-lg border border-zinc-800/90 bg-zinc-900/15 p-4 ring-1 ring-violet-500/15",
        )}
        aria-label="Sponsored"
      >
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1 rounded-full bg-violet-500/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-violet-200 ring-1 ring-violet-500/25">
            Sponsored
          </span>
          <img
            src={active.logo}
            alt=""
            className="h-6 w-auto max-w-[5rem] object-contain object-left"
          />
          <p className="min-w-0 flex-1 text-sm text-zinc-300">{active.line}</p>
          <a
            href={href}
            target="_blank"
            rel="sponsored noopener"
            className="inline-flex items-center gap-1 text-sm font-medium text-violet-300 transition-colors hover:text-violet-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
            onClick={() => trackBlogSponsorCta(slug, true)}
          >
            {active.name}
            <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
          </a>
        </div>
      </aside>
    );
  }

  return (
    <aside className="not-prose mt-10" aria-label="Sponsor this guide">
      <Link
        href={sponsorPageHref}
        className={cn(
          "group flex items-center justify-between gap-3 rounded-lg border border-zinc-800/90 bg-zinc-900/10 px-4 py-3",
          "text-sm text-zinc-400 ring-1 ring-violet-500/10 transition-colors",
          "hover:border-zinc-700 hover:bg-zinc-900/25 hover:text-zinc-200",
          "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60",
        )}
        onClick={() => trackBlogSponsorCta(slug, false)}
      >
        <span className="flex min-w-0 items-center gap-2.5">
          <span
            className="inline-flex shrink-0 items-center gap-1 rounded-full border border-zinc-700/80 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-500 ring-1 ring-violet-500/20"
            aria-hidden
          >
            <Megaphone className="h-3 w-3 text-violet-400/80" />
          </span>
          <span className="leading-snug">
            Sponsor this guide: reach creators adding sound to AI video
          </span>
        </span>
        <ArrowUpRight
          className="h-4 w-4 shrink-0 text-zinc-600 transition-colors group-hover:text-violet-400"
          aria-hidden
        />
      </Link>
    </aside>
  );
}
