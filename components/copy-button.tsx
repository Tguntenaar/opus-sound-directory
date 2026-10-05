"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useStats } from "@/components/stats-provider";

export function CopyButton({
  text,
  entryId,
  label = "Copy prompt",
}: {
  text: string;
  entryId: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);
  const { track } = useStats();

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      track(entryId, "copy");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <Button type="button" variant="outline" size="sm" onClick={copy} aria-label={label}>
      {copied ? <Check className="h-4 w-4" aria-hidden /> : <Copy className="h-4 w-4" aria-hidden />}
      {copied ? "Copied" : label}
    </Button>
  );
}
