"use client";

import { Copy, Download } from "lucide-react";
import { useStats } from "@/components/stats-provider";
import { AnimatedNumber } from "@/components/animated-number";
import { cn } from "@/lib/utils";

export function UsageBadges({
  entryId,
  className,
  compact = false,
}: {
  entryId: string;
  className?: string;
  compact?: boolean;
}) {
  const { getEntryStats } = useStats();
  const { copy, download } = getEntryStats(entryId);

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500",
        className,
      )}
      aria-label={`${copy} prompt copies, ${download} audio downloads`}
    >
      <span className="inline-flex items-center gap-1 tabular-nums" title="Prompt copies">
        <Copy className="h-3 w-3 opacity-70" aria-hidden />
        {compact ? (
          <AnimatedNumber value={copy} />
        ) : (
          <>
            <AnimatedNumber value={copy} />
            {` ${copy === 1 ? "copy" : "copies"}`}
          </>
        )}
      </span>
      <span className="inline-flex items-center gap-1 tabular-nums" title="Audio downloads">
        <Download className="h-3 w-3 opacity-70" aria-hidden />
        {compact ? (
          <AnimatedNumber value={download} />
        ) : (
          <>
            <AnimatedNumber value={download} />
            {` ${download === 1 ? "download" : "downloads"}`}
          </>
        )}
      </span>
    </div>
  );
}
