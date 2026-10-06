"use client";

import { Copy, Download, Play } from "lucide-react";
import { useStats } from "@/components/stats-provider";
import { AnimatedNumber } from "@/components/animated-number";
import { NewStatBadge } from "@/components/new-stat-badge";
import type { EntryStats } from "@/lib/stats-types";
import {
  isPublicStatCountVisible,
  shouldShowNewStatBadge,
} from "@/lib/stats-display";
import { cn } from "@/lib/utils";

function publicUsageCounts(stats: EntryStats): number[] {
  const counts = [stats.copy, stats.download];
  const play = (stats as EntryStats & { play?: number }).play;
  if (typeof play === "number") counts.push(play);
  return counts;
}

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
  const stats = getEntryStats(entryId);
  const { copy, download } = stats;
  const play = (stats as EntryStats & { play?: number }).play;
  const counts = publicUsageCounts(stats);
  const showNew = shouldShowNewStatBadge(counts);
  const showCopy = isPublicStatCountVisible(copy);
  const showDownload = isPublicStatCountVisible(download);
  const showPlay = typeof play === "number" && isPublicStatCountVisible(play);

  const ariaLabel = showNew
    ? "Recently added — usage counts still growing"
    : [
        showPlay && typeof play === "number" ? `${play} plays` : null,
        showCopy ? `${copy} prompt copies` : null,
        showDownload ? `${download} audio downloads` : null,
      ]
        .filter(Boolean)
        .join(", ");

  if (!showNew && !showCopy && !showDownload && !showPlay) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500",
        className,
      )}
      aria-label={ariaLabel}
    >
      {showNew && <NewStatBadge />}
      {showPlay && typeof play === "number" && (
        <span className="inline-flex items-center gap-1 tabular-nums" title="Plays">
          <Play className="h-3 w-3 opacity-70" aria-hidden />
          {compact ? (
            <AnimatedNumber value={play} />
          ) : (
            <>
              <AnimatedNumber value={play} />
              {` ${play === 1 ? "play" : "plays"}`}
            </>
          )}
        </span>
      )}
      {showCopy && (
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
      )}
      {showDownload && (
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
      )}
    </div>
  );
}
