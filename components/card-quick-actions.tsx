"use client";

import { useState } from "react";
import { Check, Copy, Download } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { IconButton } from "@/components/icon-button";
import { ShareButton } from "@/components/share-button";
import { useStats } from "@/components/stats-provider";
import { cn } from "@/lib/utils";
import { captureEvent } from "@/lib/analytics-client";
import { soundEventProps, type AnalyticsSource } from "@/lib/analytics";

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
  const shareUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/e/${entry.slug}`
      : `/e/${entry.slug}`;

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
    a.href = entry.assets.wav;
    a.download = `${entry.title.replace(/\s+/g, "-").toLowerCase()}.wav`;
    a.click();
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
      <IconButton label="Download WAV" onClick={downloadWav}>
        <Download className="h-3.5 w-3.5" aria-hidden />
      </IconButton>
      <ShareButton url={shareUrl} title={entry.title} entry={entry} source={source} />
    </div>
  );
}
