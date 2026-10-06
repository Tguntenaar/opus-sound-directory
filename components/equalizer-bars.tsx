"use client";

import { cn } from "@/lib/utils";

export function EqualizerBars({
  active,
  className,
  bars = 4,
}: {
  active: boolean;
  className?: string;
  bars?: number;
}) {
  return (
    <span
      className={cn("inline-flex items-end gap-[2px]", className)}
      aria-hidden
    >
      {Array.from({ length: bars }, (_, i) => (
        <span
          key={i}
          className={cn(
            "eq-bar w-[2px] rounded-full bg-violet-400",
            active ? "eq-bar--active" : "h-1 bg-zinc-600",
          )}
          style={active ? { animationDelay: `${i * 0.12}s` } : undefined}
        />
      ))}
    </span>
  );
}
