"use client";

import { useState } from "react";
import { Check, Download } from "lucide-react";
import { useStats } from "@/components/stats-provider";
import { IconButton } from "@/components/icon-button";
import { Cc0Badge } from "@/components/cc0-badge";
import { cn } from "@/lib/utils";

type Props = {
  entryId: string;
  wav: string;
  mp3: string;
  title: string;
};

export function DownloadLinks({ entryId, wav, mp3, title }: Props) {
  const { track } = useStats();
  const [lastFormat, setLastFormat] = useState<"wav" | "mp3" | null>(null);

  const base = title.replace(/\s+/g, "-").toLowerCase();

  function triggerDownload(href: string, filename: string, format: "wav" | "mp3") {
    track(entryId, "download");
    setLastFormat(format);
    const a = document.createElement("a");
    a.href = href;
    a.download = filename;
    a.click();
    window.setTimeout(() => setLastFormat(null), 1600);
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <IconButton
        label={lastFormat === "wav" ? "WAV download started" : "Download WAV"}
        variant="outline"
        onClick={() => triggerDownload(wav, `${base}.wav`, "wav")}
        className={cn(lastFormat === "wav" && "border-emerald-500/40 text-emerald-200")}
      >
        {lastFormat === "wav" ? (
          <Check className="icon-check-pop h-4 w-4" aria-hidden />
        ) : (
          <Download className="h-4 w-4" aria-hidden />
        )}
      </IconButton>
      <IconButton
        label={lastFormat === "mp3" ? "MP3 download started" : "Download MP3"}
        variant="outline"
        onClick={() => triggerDownload(mp3, `${base}.mp3`, "mp3")}
        className={cn(lastFormat === "mp3" && "border-emerald-500/40 text-emerald-200")}
      >
        {lastFormat === "mp3" ? (
          <Check className="icon-check-pop h-4 w-4" aria-hidden />
        ) : (
          <Download className="h-4 w-4" aria-hidden />
        )}
      </IconButton>
      <span className="text-xs text-zinc-600" aria-hidden>WAV · MP3</span>
      <Cc0Badge />
    </div>
  );
}
