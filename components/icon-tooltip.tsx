"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = {
  label: string;
  children: ReactNode;
  className?: string;
  side?: "top" | "bottom";
};

/** Accessible icon affordance: visible `title` tooltip + guaranteed aria-label on child control. */
export function IconTooltip({ label, children, className, side = "top" }: Props) {
  return (
    <span className={cn("group/tip relative inline-flex", className)}>
      <span
        role="tooltip"
        className={cn(
          "pointer-events-none absolute left-1/2 z-50 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-zinc-800 px-2 py-1 text-xs font-medium text-zinc-200 shadow-lg ring-1 ring-zinc-700/80 group-hover/tip:flex group-focus-within/tip:flex motion-reduce:transition-none",
          side === "top" ? "bottom-full mb-1.5" : "top-full mt-1.5",
        )}
      >
        {label}
      </span>
      {children}
    </span>
  );
}
