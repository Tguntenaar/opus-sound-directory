"use client";

import { Pause, Play } from "lucide-react";
import { cn } from "@/lib/utils";

export function PlayPauseIcon({
  playing,
  className,
  size = "md",
}: {
  playing: boolean;
  className?: string;
  size?: "sm" | "md";
}) {
  const dim = size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4";
  return (
    <span className={cn("relative inline-flex shrink-0", dim, className)} aria-hidden>
      <Play
        className={cn(
          dim,
          "absolute inset-0 transition-all duration-200 ease-out",
          playing ? "scale-75 opacity-0" : "scale-100 opacity-100",
        )}
      />
      <Pause
        className={cn(
          dim,
          "absolute inset-0 transition-all duration-200 ease-out",
          playing ? "scale-100 opacity-100" : "scale-75 opacity-0",
        )}
      />
    </span>
  );
}
