"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { IconTooltip } from "@/components/icon-tooltip";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  children: ReactNode;
  variant?: "ghost" | "outline";
  size?: "sm" | "md";
};

export function IconButton({
  label,
  children,
  className,
  variant = "ghost",
  size = "sm",
  ...props
}: Props) {
  const dim = size === "sm" ? "h-8 w-8" : "h-9 w-9";
  return (
    <IconTooltip label={label}>
      <button
        type="button"
        aria-label={label}
        title={label}
        className={cn(
          "inline-flex items-center justify-center rounded-lg transition-[color,background-color,border-color,transform] duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60 active:scale-95 motion-reduce:active:scale-100",
          dim,
          variant === "ghost" &&
            "text-zinc-400 hover:bg-zinc-800/80 hover:text-zinc-100",
          variant === "outline" &&
            "border border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:bg-zinc-900 hover:text-zinc-100",
          className,
        )}
        {...props}
      >
        {children}
      </button>
    </IconTooltip>
  );
}
