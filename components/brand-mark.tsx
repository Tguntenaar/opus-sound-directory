"use client";

import { cn } from "@/lib/utils";

type Props = {
  className?: string;
  size?: number;
  /** Enable one-shot pulse arc sweep on group hover (header wordmark). */
  interactive?: boolean;
};

export function BrandMark({ className, size = 18, interactive = false }: Props) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      fill="none"
      width={size}
      height={size}
      className={cn("shrink-0", interactive && "brand-mark-interactive", className)}
      aria-hidden
    >
      <circle cx="32" cy="32" r="20" stroke="#52525b" strokeWidth="1.5" opacity="0.85" />
      <circle cx="32" cy="32" r="14" stroke="#fafafa" strokeWidth="2.25" />
      <g className={cn(interactive && "brand-mark-arc-group")}>
        <path
          d="M32 12a20 20 0 0 1 17.32 10"
          stroke="#8b5cf6"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </g>
      <circle cx="32" cy="32" r="4" fill="#8b5cf6" />
    </svg>
  );
}
