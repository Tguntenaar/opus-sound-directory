"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { IconButton } from "@/components/icon-button";
import { useStats } from "@/components/stats-provider";
import { cn } from "@/lib/utils";
import { captureEvent } from "@/lib/analytics-client";
import { soundEventProps, type AnalyticsSource } from "@/lib/analytics";
import type { SoundEntry } from "@/lib/entries";

export function CopyButton({
  text,
  entryId,
  label = "Copy prompt",
  iconOnly = false,
  entry,
  source = "detail",
  copyKind = "prompt",
}: {
  text: string;
  entryId: string;
  label?: string;
  iconOnly?: boolean;
  entry?: Pick<SoundEntry, "id" | "category" | "mood" | "modelId">;
  source?: AnalyticsSource;
  copyKind?: "prompt" | "code";
}) {
  const [copied, setCopied] = useState(false);
  const { track } = useStats();

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      track(entryId, "copy");
      if (entry) {
        const base = soundEventProps(entry, source);
        captureEvent(copyKind === "code" ? "sound_copy_code" : "sound_copy_prompt", base);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  if (iconOnly) {
    return (
      <IconButton
        label={copied ? "Copied" : label}
        onClick={copy}
        variant="outline"
        className={cn(copied && "border-emerald-500/40 text-emerald-200")}
      >
        {copied ? (
          <Check className="icon-check-pop h-4 w-4" aria-hidden />
        ) : (
          <Copy className="h-4 w-4" aria-hidden />
        )}
      </IconButton>
    );
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={copy}
      aria-label={label}
      className={cn(copied && "border-emerald-500/40 text-emerald-200")}
    >
      {copied ? (
        <Check className="icon-check-pop h-4 w-4" aria-hidden />
      ) : (
        <Copy className="h-4 w-4" aria-hidden />
      )}
      <span className="sr-only">{copied ? "Copied" : label}</span>
    </Button>
  );
}
