"use client";

import { Copy, Download } from "lucide-react";
import { useStats } from "@/components/stats-provider";
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
      <span className="inline-flex items-center gap-1" title="Prompt copies">
        <Copy className="h-3 w-3 opacity-70" aria-hidden />
        {compact ? copy : `${copy.toLocaleString()} ${copy === 1 ? "copy" : "copies"}`}
      </span>
      <span className="inline-flex items-center gap-1" title="Audio downloads">
        <Download className="h-3 w-3 opacity-70" aria-hidden />
        {compact
          ? download
          : `${download.toLocaleString()} ${download === 1 ? "download" : "downloads"}`}
      </span>
    </div>
  );
}
