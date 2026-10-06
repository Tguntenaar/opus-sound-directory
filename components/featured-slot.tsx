"use client";

import Link from "next/link";
import { useRef } from "react";
import { ArrowUpRight, Megaphone, Sparkles } from "lucide-react";
import { captureEvent } from "@/lib/analytics-client";
import type { SoundEntry } from "@/lib/entries";
import { EntryCard } from "@/components/entry-card";
import { cn } from "@/lib/utils";
import {
  getCategorySponsor,
  getHomeSponsor,
  withSponsorUtm,
  type ActiveSponsor,
} from "@/lib/sponsors";
import {
  useSponsorImpression,
  type SponsorSlotPlacement,
} from "@/lib/use-sponsor-impression";

type Props = {
  entry?: SoundEntry | null;
  placement: SponsorSlotPlacement;
  category?: string;
};

function trackSponsorClick(placement: SponsorSlotPlacement, category?: string) {
  captureEvent("sponsor_click", {
    placement,
    ...(category ? { category } : {}),
  });
}

function PaidSponsorSlot({
  sponsor,
  placement,
  category,
}: {
  sponsor: ActiveSponsor;
  placement: SponsorSlotPlacement;
  category?: string;
}) {
  const ref = useRef<HTMLElement>(null);
  useSponsorImpression(ref, true, { placement, category });
  const href = withSponsorUtm(sponsor.url, sponsor.utm);

  return (
    <section
      ref={ref}
      className="flex flex-col gap-3 rounded-xl border border-violet-500/20 bg-gradient-to-br from-violet-500/[0.07] to-zinc-900/30 p-4 sm:p-5"
      aria-labelledby="sponsor-slot-heading"
    >
      <h2
        id="sponsor-slot-heading"
        className="inline-flex w-fit items-center gap-1 rounded-full bg-violet-500/15 px-2.5 py-0.5 text-xs font-medium uppercase tracking-wider text-violet-200 ring-1 ring-violet-500/25"
      >
        <Megaphone className="h-3 w-3" aria-hidden />
        Sponsored
      </h2>
      <a
        href={href}
        target="_blank"
        rel="sponsored noopener"
        className="flex flex-wrap items-center gap-4 rounded-lg outline-offset-4 transition-colors hover:text-violet-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
        onClick={() => trackSponsorClick(placement, category)}
      >
        {sponsor.logo ? (
          <img
            src={sponsor.logo}
            alt=""
            className="h-10 w-auto max-w-[8rem] object-contain object-left"
          />
        ) : null}
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-medium text-zinc-100">{sponsor.name}</span>
          <span className="mt-0.5 block text-sm text-zinc-400">{sponsor.line}</span>
        </span>
        <ArrowUpRight className="h-4 w-4 shrink-0 text-violet-300" aria-hidden />
      </a>
    </section>
  );
}

export function FeaturedSlot({ entry, placement, category }: Props) {
  const sponsor =
    placement === "category" && category
      ? getCategorySponsor(category)
      : placement === "home"
        ? getHomeSponsor()
        : null;

  if (sponsor) {
    return <PaidSponsorSlot sponsor={sponsor} placement={placement} category={category} />;
  }

  if (!entry) return null;

  return (
    <section
      className="flex flex-col gap-3 rounded-xl border border-violet-500/20 bg-gradient-to-br from-violet-500/[0.07] to-zinc-900/30 p-4 sm:p-5"
      aria-labelledby="featured-heading"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-full bg-violet-500/15 px-2.5 py-0.5 text-xs font-medium uppercase tracking-wider text-violet-200 ring-1 ring-violet-500/25">
            <Sparkles className="h-3 w-3" aria-hidden />
            Featured
          </span>
          <h2 id="featured-heading" className="text-sm text-zinc-400">
            Editor&apos;s pick
          </h2>
        </div>
        <Link
          href="/sponsor"
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border border-zinc-700/80 px-2.5 py-1 text-xs font-medium uppercase tracking-wide text-zinc-500 transition-colors hover:border-zinc-500 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60",
          )}
          title="Sponsor the homepage featured slot"
          onClick={() => captureEvent("sponsor_cta_click", { placement: "featured_slot" })}
        >
          <Megaphone className="h-3 w-3" aria-hidden />
          <span>Sponsored slot</span>
        </Link>
      </div>
      <div className="max-w-md">
        <EntryCard entry={entry} featured />
      </div>
    </section>
  );
}
