"use client";

import Link from "next/link";
import { Megaphone, Sparkles } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { EntryCard } from "@/components/entry-card";
import { cn } from "@/lib/utils";

type Props = {
  entry: SoundEntry;
};

export function FeaturedSlot({ entry }: Props) {
  return (
    <section
      className="flex flex-col gap-3 rounded-xl border border-violet-500/20 bg-gradient-to-br from-violet-500/[0.07] to-zinc-900/30 p-4 sm:p-5"
      aria-labelledby="featured-heading"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span
            className="inline-flex items-center gap-1 rounded-full bg-violet-500/15 px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-violet-200 ring-1 ring-violet-500/25"
          >
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
            "inline-flex items-center gap-1.5 rounded-full border border-zinc-700/80 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide text-zinc-500 transition-colors hover:border-zinc-500 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60",
          )}
          title="Sponsor the homepage featured slot"
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
