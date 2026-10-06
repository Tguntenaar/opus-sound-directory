"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { usePrefersReducedMotion } from "@/lib/use-prefers-reduced-motion";

export type PillOption = { value: string; label: string };

type Props = {
  options: PillOption[];
  value: string;
  onChange: (value: string) => void;
  "aria-label": string;
};

export function FilterPillGroup({ options, value, onChange, "aria-label": ariaLabel }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const reduced = usePrefersReducedMotion();
  const [indicator, setIndicator] = useState({ left: 0, width: 0, top: 0, height: 0, ready: false });

  const measure = useCallback(() => {
    const root = containerRef.current;
    if (!root) return;
    const active = root.querySelector<HTMLElement>(`[data-pill-value="${CSS.escape(value)}"]`);
    if (!active) return;
    const cr = root.getBoundingClientRect();
    const br = active.getBoundingClientRect();
    setIndicator({
      left: br.left - cr.left + root.scrollLeft,
      width: br.width,
      top: br.top - cr.top + root.scrollTop,
      height: br.height,
      ready: true,
    });
  }, [value]);

  useLayoutEffect(() => {
    measure();
  }, [measure, options]);

  useEffect(() => {
    const root = containerRef.current;
    if (!root) return;
    const ro = new ResizeObserver(() => measure());
    ro.observe(root);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [measure]);

  const chip =
    "relative z-[1] rounded-full px-3 py-1 text-xs transition-colors duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60";
  const chipIdle = "text-zinc-500 hover:text-zinc-300";
  const chipActive = "text-violet-100";

  return (
    <div
      ref={containerRef}
      className="relative flex flex-wrap gap-1.5"
      role="group"
      aria-label={ariaLabel}
    >
      {!reduced && indicator.ready && (
        <span
          className="pointer-events-none absolute z-0 rounded-full bg-violet-500/15 ring-1 ring-violet-500/20 transition-[left,width,top,height] duration-300 ease-out motion-reduce:transition-none"
          style={{
            left: indicator.left,
            width: indicator.width,
            top: indicator.top,
            height: indicator.height,
          }}
          aria-hidden
        />
      )}
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            data-pill-value={opt.value}
            onClick={() => onChange(opt.value)}
            className={cn(
              chip,
              active ? chipActive : chipIdle,
              reduced && active && "bg-violet-500/15 text-violet-200",
            )}
            aria-pressed={active}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
