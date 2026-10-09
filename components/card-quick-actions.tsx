"use client";

import { useEffect, useRef, useState } from "react";
import { Bookmark, Check, Copy, Download } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { IconButton } from "@/components/icon-button";
import { toggleBookmark, useBookmarks } from "@/lib/use-bookmarks";
import { useBookmarkLogin } from "@/components/bookmark-login-provider";
import { useStats } from "@/components/stats-provider";
import { cn } from "@/lib/utils";
import { captureEvent } from "@/lib/analytics-client";
import { soundEventProps, type AnalyticsSource } from "@/lib/analytics";
import { entryWavDownloadPath } from "@/lib/wav-url";
import { isCommunityEntry } from "@/lib/community-types";

export function CardQuickActions({
  entry,
  className,
  source = "card",
}: {
  entry: SoundEntry;
  className?: string;
  source?: AnalyticsSource;
}) {
  const { track } = useStats();
  const [copied, setCopied] = useState(false);
  const [downloadStarted, setDownloadStarted] = useState(false);
  const downloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => {
    if (downloadTimer.current) clearTimeout(downloadTimer.current);
  }, []);
  const bookmarks = useBookmarks();
  const requestBookmark = useBookmarkLogin();
  const bookmarked = bookmarks.has(entry.id);

  async function copyPrompt(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(entry.prompt);
      track(entry.id, "copy");
      captureEvent("sound_copy_prompt", soundEventProps(entry, source));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  function downloadWav(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    track(entry.id, "download");
    captureEvent("sound_download", { ...soundEventProps(entry, source), format: "wav" });
    const a = document.createElement("a");
    a.href = isCommunityEntry(entry)
      ? entry.assets.wav
      : entryWavDownloadPath(entry.id);
    a.download = `${entry.title.replace(/\s+/g, "-").toLowerCase()}.wav`;
    a.click();
    setDownloadStarted(true);
    if (downloadTimer.current) clearTimeout(downloadTimer.current);
    downloadTimer.current = setTimeout(() => setDownloadStarted(false), 1600);
  }

  return (
    <div
      className={cn(
        "flex items-center gap-0.5 opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-within:opacity-100 motion-reduce:opacity-100",
        className,
      )}
    >
      <IconButton label={copied ? "Prompt copied" : "Copy prompt"} onClick={copyPrompt}>
        {copied ? (
          <Check className="icon-check-pop h-3.5 w-3.5 text-emerald-300" aria-hidden />
        ) : (
          <Copy className="h-3.5 w-3.5" aria-hidden />
        )}
      </IconButton>
      <IconButton label={downloadStarted ? "Download started" : "Download WAV"} onClick={downloadWav}>
        {downloadStarted ? (
          <Check className="icon-check-pop h-3.5 w-3.5 text-emerald-300" aria-hidden />
        ) : (
          <Download className="h-3.5 w-3.5" aria-hidden />
        )}
      </IconButton>
      <IconButton label={bookmarked ? "Remove bookmark" : "Bookmark sound"} aria-pressed={bookmarked}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          requestBookmark(entry.id, () => {
            const saved = toggleBookmark(entry.id);
            captureEvent("sound_bookmark", { ...soundEventProps(entry, source), saved });
          });
        }}>
        <Bookmark className={cn("h-3.5 w-3.5", bookmarked && "fill-violet-400 text-violet-400")} aria-hidden />
      </IconButton>
    </div>
  );
}
