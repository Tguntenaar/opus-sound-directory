"use client";

import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

type Props = {
  label: string;
  children: ReactNode;
  className?: string;
  side?: "top" | "bottom";
};

/** Render outside card clipping and keep the label inside the viewport. */
export function IconTooltip({ label, children, className, side = "top" }: Props) {
  const anchor = useRef<HTMLSpanElement>(null);
  const tooltip = useRef<HTMLSpanElement>(null);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [position, setPosition] = useState<{ left: number; top: number } | null>(null);
  const open = (hovered || focused) && !dismissed;

  useLayoutEffect(() => {
    if (!open) { setPosition(null); return; }
    function place() {
      if (!anchor.current || !tooltip.current) return;
      const rect = anchor.current.getBoundingClientRect();
      const tip = tooltip.current.getBoundingClientRect();
      const margin = 8;
      const gap = 6;
      let top = side === "top" ? rect.top - tip.height - gap : rect.bottom + gap;
      if (top < margin) top = rect.bottom + gap;
      if (top + tip.height > window.innerHeight - margin) top = rect.top - tip.height - gap;
      setPosition({
        left: Math.max(margin, Math.min(rect.left + (rect.width - tip.width) / 2, window.innerWidth - tip.width - margin)),
        top: Math.max(margin, Math.min(top, window.innerHeight - tip.height - margin)),
      });
    }
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [open, side, label]);

  useEffect(() => {
    if (!open) return;
    const dismiss = (event: KeyboardEvent) => { if (event.key === "Escape") setDismissed(true); };
    document.addEventListener("keydown", dismiss);
    return () => document.removeEventListener("keydown", dismiss);
  }, [open]);

  return <span ref={anchor} className={cn("inline-flex", className)}
    onMouseEnter={() => { setHovered(true); setDismissed(false); }}
    onMouseLeave={() => setHovered(false)}
    onFocus={() => { setFocused(true); setDismissed(false); }}
    onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setFocused(false); }}>
    {children}
    {open && createPortal(<span ref={tooltip} role="tooltip"
      className="pointer-events-none fixed z-[100] max-w-[calc(100vw-16px)] break-words rounded-md bg-zinc-800 px-2 py-1 text-xs font-medium text-zinc-200 shadow-lg ring-1 ring-zinc-700/80"
      style={{ left: position?.left ?? 0, top: position?.top ?? 0, visibility: position ? "visible" : "hidden" }}>
      {label}
    </span>, document.body)}
  </span>;
}
