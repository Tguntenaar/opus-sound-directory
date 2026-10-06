"use client";

import { useState } from "react";
import { Check, Share2 } from "lucide-react";
import { IconButton } from "@/components/icon-button";

export function ShareButton({
  url,
  title,
  className,
}: {
  url: string;
  title: string;
  className?: string;
}) {
  const [done, setDone] = useState(false);

  async function share(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    try {
      if (navigator.share) {
        await navigator.share({ title, url });
      } else {
        await navigator.clipboard.writeText(url);
        setDone(true);
        window.setTimeout(() => setDone(false), 1600);
      }
    } catch {
      /* cancelled */
    }
  }

  return (
    <IconButton
      label={done ? "Link copied" : "Share"}
      onClick={share}
      className={className}
    >
      {done ? (
        <Check className="icon-check-pop h-3.5 w-3.5 text-emerald-300" aria-hidden />
      ) : (
        <Share2 className="h-3.5 w-3.5" aria-hidden />
      )}
    </IconButton>
  );
}
