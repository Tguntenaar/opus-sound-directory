"use client";

import { useEffect } from "react";
import { getPlayingId, subscribePlayback } from "@/lib/audio-controller";

const STING_SRC = "/assets/logo-sting-deep-bass/out.mp3";
const PLAYED_KEY = "opus:landing-sting";
const VOLUME = 0.45;

/**
 * The site's audio logo: plays the deep bass sting once per browser session.
 * Tries on landing (allowed when the browser permits autoplay); otherwise waits for the
 * visitor's first click, tap or key press. Never plays over, or before, a sound the
 * visitor starts themselves.
 */
export function LandingSting() {
  useEffect(() => {
    try {
      if (sessionStorage.getItem(PLAYED_KEY)) return;
    } catch {
      // storage blocked: fall through and play at most once per page load
    }

    const audio = new Audio(STING_SRC);
    audio.preload = "auto";
    audio.volume = VOLUME;
    let done = false;
    const gestures = ["pointerdown", "keydown"] as const;

    function finish() {
      if (done) return;
      done = true;
      try {
        sessionStorage.setItem(PLAYED_KEY, "1");
      } catch {
        // ignore
      }
      for (const g of gestures) window.removeEventListener(g, onGesture, true);
    }

    function play() {
      if (done || getPlayingId()) return finish();
      audio.play().then(finish, () => {
        // autoplay blocked: keep waiting for a gesture
      });
    }

    function onGesture(e: Event) {
      const t = e.target instanceof Element ? e.target : null;
      // The visitor is going for a sound (or typing): don't put the sting in front of it.
      if (t?.closest("[data-audio-player], [data-sound-card], input, textarea, select, [contenteditable]")) return;
      if (e instanceof KeyboardEvent && (e.code === "Space" || e.metaKey || e.ctrlKey || e.altKey)) return;
      play();
    }

    const unsubscribe = subscribePlayback((id) => {
      if (!id) return;
      if (!audio.paused) audio.pause();
      finish();
    });

    for (const g of gestures) window.addEventListener(g, onGesture, true);
    play();

    return () => {
      for (const g of gestures) window.removeEventListener(g, onGesture, true);
      unsubscribe();
      audio.pause();
    };
  }, []);

  return null;
}
