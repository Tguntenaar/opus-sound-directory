"use client";

import { useEffect, useRef } from "react";

const SOUND_PATHS = [
  "M8 5 21 2v15c0 2-2.2 3.5-4.4 3.5-2 0-3.1-1.1-2.6-2.7.5-1.8 2.8-3 5-2.8V8L10 10v9c0 2-2.2 3.5-4.4 3.5-2 0-3.1-1.1-2.6-2.7.5-1.8 2.8-3 5-2.8Z",
  "M10 2h2c.4 3 2 3.8 4.6 5.2 2.8 1.6 3.6 4.2 2.2 7.1-.2-3-2.9-4.5-6.8-5.1V19c0 2-2.4 3.6-4.8 3.6-2.2 0-3.5-1.3-2.8-3 .6-1.9 3.2-3.1 5.6-2.8Z",
  // Solid waveform and four-point spark, matching the flat note cutouts.
  "M1 10h3l2-6 4 12 4-14 4 14 2-6h3v3h-1l-4 10-4-13-4 13-4-11-1 1H1Z",
  "M12 1 15 9 23 12 15 15 12 23 9 15 1 12 9 9Z",
];
const COLORS = ["#c4b5fd", "#a78bfa", "#e9d5ff", "#818cf8"];

export function ClickNotes() {
  const layerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const layer = layerRef.current;
    if (!layer) return;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const previewMotion = process.env.NODE_ENV === "development"
      && new URLSearchParams(window.location.search).get("preview-motion") === "full";
    if (previewMotion) layer.dataset.previewMotion = "full";
    const live = new Map<SVGSVGElement, Animation>();
    let pointerType = "";

    function clear() {
      live.forEach((animation, note) => {
        animation.cancel();
        note.remove();
      });
      live.clear();
    }

    function rememberPointer(event: PointerEvent) {
      pointerType = event.pointerType;
    }

    function burst(event: MouseEvent) {
      if ((motion.matches && !previewMotion) || event.detail === 0 || event.button !== 0 || pointerType !== "mouse") return;

      const firstShape = Math.floor(Math.random() * SOUND_PATHS.length);
      const secondShape = (firstShape + 1 + Math.floor(Math.random() * (SOUND_PATHS.length - 1))) % SOUND_PATHS.length;
      for (let i = 0; i < 2; i++) {
        // Bound the work even when someone clicks repeatedly.
        if (live.size >= 32) {
          const oldest = live.keys().next().value!;
          live.get(oldest)!.cancel();
          oldest.remove();
          live.delete(oldest);
        }
        const note = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        note.setAttribute("viewBox", "0 0 24 24");
        note.setAttribute("fill", COLORS[i]);
        note.classList.add("click-note");
        note.style.left = `${event.clientX}px`;
        note.style.top = `${event.clientY}px`;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", SOUND_PATHS[i === 0 ? firstShape : secondShape]);
        note.appendChild(path);
        layer!.appendChild(note);

        const dx = (i - 0.5) * 18 + Math.random() * 8 - 4;
        const height = 20 + Math.random() * 12;
        const turn = (i - 0.5) * 12;
        const pose = (x: number, y: number, rotation: number, scale: number) =>
          `translate(-50%, -50%) translate(${x}px, ${y}px) rotate(${rotation}deg) scale(${scale})`;
        const animation = note.animate([
          { transform: pose(0, 0, 0, 0.35), opacity: 0, offset: 0 },
          { transform: pose(dx * 0.3, -height * 0.6, turn * 0.3, 1), opacity: 1, offset: 0.2 },
          { transform: pose(dx * 0.7, -height, turn * 0.7, 1), opacity: 0.9, offset: 0.55 },
          { transform: pose(dx, -height + 12, turn, 0.7), opacity: 0, offset: 1 },
        ], { duration: 650 + Math.random() * 150, easing: "ease-out", fill: "both" });
        live.set(note, animation);
        animation.onfinish = () => {
          live.delete(note);
          note.remove();
        };
      }
    }

    document.addEventListener("pointerdown", rememberPointer, { capture: true, passive: true });
    document.addEventListener("click", burst, { capture: true, passive: true });
    motion.addEventListener("change", clear);
    return () => {
      document.removeEventListener("pointerdown", rememberPointer, true);
      document.removeEventListener("click", burst, true);
      motion.removeEventListener("change", clear);
      clear();
    };
  }, []);

  return <div ref={layerRef} className="click-notes" aria-hidden="true" />;
}
