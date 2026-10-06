"use client";

import { IconTooltip } from "@/components/icon-tooltip";
import { CC0_LICENSE_URL } from "@/lib/licenses";
import { cn } from "@/lib/utils";

type Props = {
  className?: string;
};

export function Cc0Badge({ className }: Props) {
  return (
    <IconTooltip label="CC0 1.0 — public domain. Use freely, no credit required.">
      <a
        href={CC0_LICENSE_URL}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "inline-flex h-8 items-center rounded-md border border-zinc-700/80 bg-zinc-950/60 px-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 transition-colors hover:border-violet-500/40 hover:text-violet-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60",
          className,
        )}
        aria-label="Licensed under CC0 1.0 public domain"
      >
        CC0
      </a>
    </IconTooltip>
  );
}
