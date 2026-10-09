"use client";

import { useMemo, useSyncExternalStore } from "react";

const KEY = "opus-sounds:bookmarks";
const EVENT = "opus-sounds:bookmarks-changed";
let fallback = "[]";
let memoryOnly = false;

function snapshot() {
  if (memoryOnly) return fallback;
  try { return localStorage.getItem(KEY) ?? fallback; } catch { return fallback; }
}

function subscribe(notify: () => void) {
  const onStorage = (event: StorageEvent) => {
    if (event.key === KEY || event.key === null) notify();
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(EVENT, notify);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(EVENT, notify);
  };
}

function parse(raw: string): string[] {
  try {
    const value: unknown = JSON.parse(raw);
    return Array.isArray(value) ? value.filter((id): id is string => typeof id === "string") : [];
  } catch { return []; }
}

export function toggleBookmark(id: string): boolean {
  const ids = new Set(parse(snapshot()));
  const saved = !ids.has(id);
  if (saved) ids.add(id); else ids.delete(id);
  fallback = JSON.stringify([...ids]);
  try { localStorage.setItem(KEY, fallback); } catch { memoryOnly = true; }
  window.dispatchEvent(new Event(EVENT));
  return saved;
}

export function useBookmarks() {
  const raw = useSyncExternalStore(subscribe, snapshot, () => "[]");
  return useMemo(() => new Set(parse(raw)), [raw]);
}
