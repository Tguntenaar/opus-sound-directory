/** Global single-playback coordinator for all <audio> elements. */

import { setLastPlayedEntryId } from "@/lib/playback-focus";

const elements = new Map<string, HTMLAudioElement>();
let currentId: string | null = null;
const listeners = new Set<(id: string | null) => void>();

export function registerAudioElement(id: string, el: HTMLAudioElement) {
  elements.set(id, el);
  return () => {
    elements.delete(id);
    if (currentId === id) currentId = null;
  };
}

export function subscribePlayback(listener: (id: string | null) => void) {
  listeners.add(listener);
  listener(currentId);
  return () => listeners.delete(listener);
}

function notify() {
  for (const l of listeners) l(currentId);
}

export function getPlayingId() {
  return currentId;
}

export async function requestPlay(id: string) {
  if (currentId && currentId !== id) {
    const prev = elements.get(currentId);
    if (prev) {
      prev.pause();
      prev.currentTime = 0;
    }
  }
  currentId = id;
  setLastPlayedEntryId(id);
  notify();
  const el = elements.get(id);
  if (el) await el.play();
}

export function requestPause(id: string) {
  const el = elements.get(id);
  if (el) {
    el.pause();
  }
  if (currentId === id) currentId = null;
  notify();
}

export function notifyEnded(id: string) {
  if (currentId === id) currentId = null;
  notify();
}
