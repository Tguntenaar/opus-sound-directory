"use client";

import { useEffect } from "react";
import {
  getPlayingId,
  requestPause,
  requestPlay,
} from "@/lib/audio-controller";
import { getPlaybackShortcutTarget } from "@/lib/playback-focus";

export function PlaybackShortcuts() {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.code !== "Space" || e.repeat) return;
      const t = e.target;
      if (
        t instanceof HTMLInputElement ||
        t instanceof HTMLTextAreaElement ||
        t instanceof HTMLSelectElement ||
        (t instanceof HTMLElement && t.isContentEditable)
      ) {
        return;
      }
      if (document.activeElement?.closest("[data-audio-player]")) return;

      const card = document.activeElement?.closest<HTMLElement>("[data-sound-card]");
      const entryId = card?.dataset.entryId ?? getPlaybackShortcutTarget();
      if (!entryId) return;

      e.preventDefault();
      if (getPlayingId() === entryId) {
        requestPause(entryId);
      } else {
        void requestPlay(entryId);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return null;
}
