"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

export function SpectrogramImage({
  src,
  alt,
  className,
  width = 1200,
  height = 400,
}: {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
}) {
  const ref = useRef<HTMLImageElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mq.matches) {
      setVisible(true);
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true);
          io.disconnect();
        }
      },
      { rootMargin: "80px", threshold: 0.08 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <img
      ref={ref}
      src={src}
      alt={alt}
      width={width}
      height={height}
      loading="lazy"
      decoding="async"
      className={cn(
        "aspect-[3/1] w-full rounded-xl border border-zinc-800 bg-zinc-950 object-cover transition-[border-color] duration-200 hover:border-zinc-700",
        visible && "spectrogram-reveal",
        className,
      )}
      style={{ maxHeight: height }}
    />
  );
}
