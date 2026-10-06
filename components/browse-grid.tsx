"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownAZ, Search, SlidersHorizontal, TrendingUp } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { CATEGORY_ORDER, CATEGORIES } from "@/lib/categories";
import { MOOD_FACETS, formatMood } from "@/lib/mood";
import { EntryCard } from "@/components/entry-card";
import { FilterPillGroup, type PillOption } from "@/components/filter-pill-group";
import { FeaturedSlot } from "@/components/featured-slot";
import { getFeaturedEntry } from "@/lib/featured";
import { matchesSearch, sortEntries, type SortMode } from "@/lib/browse-sort";
import { useStats } from "@/components/stats-provider";
import { IconButton } from "@/components/icon-button";
import { captureEvent } from "@/lib/analytics-client";

type Props = {
  entries: SoundEntry[];
  /** Lock grid to one category (category landing pages). */
  lockedCategory?: string;
  /** Sync ?category= on the home page without full navigation. */
  syncCategoryToUrl?: boolean;
  initialCategory?: string;
};

function moodsInCatalog(entries: SoundEntry[]): string[] {
  const set = new Set<string>();
  for (const e of entries) {
    for (const m of e.mood ?? []) set.add(m);
  }
  return Object.keys(MOOD_FACETS).filter((k) => set.has(k));
}

export function BrowseGrid({
  entries,
  lockedCategory,
  syncCategoryToUrl,
  initialCategory = "all",
}: Props) {
  const { stats } = useStats();
  const [category, setCategory] = useState<string>(
    lockedCategory ?? initialCategory ?? "all",
  );
  const [mood, setMood] = useState<string>("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortMode>("popular");
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (lockedCategory) {
      setCategory(lockedCategory);
      return;
    }
    if (initialCategory) setCategory(initialCategory);
  }, [lockedCategory, initialCategory]);

  const setCategoryWithUrl = useCallback(
    (next: string) => {
      if (next !== category) {
        captureEvent("filter_change", { filter: "category", value: next });
      }
      setCategory(next);
      if (syncCategoryToUrl && !lockedCategory) {
        const path =
          next === "all" ? "/" : `/?category=${encodeURIComponent(next)}`;
        window.history.pushState(null, "", path);
      }
    },
    [syncCategoryToUrl, lockedCategory, category],
  );

  const featured = useMemo(() => {
    if (lockedCategory) return undefined;
    return getFeaturedEntry(entries);
  }, [entries, lockedCategory]);
  const moodOptions = useMemo(() => moodsInCatalog(entries), [entries]);

  const categoryPills: PillOption[] = useMemo(() => {
    const items: PillOption[] = [{ value: "all", label: "All" }];
    for (const id of CATEGORY_ORDER) {
      const count = entries.filter((e) => e.category === id).length;
      if (count === 0) continue;
      items.push({ value: id, label: CATEGORIES[id].label });
    }
    return items;
  }, [entries]);

  const moodPills: PillOption[] = useMemo(
    () => [
      { value: "all", label: "Any mood" },
      ...moodOptions.map((id) => ({ value: id, label: formatMood(id) })),
    ],
    [moodOptions],
  );

  const filtered = useMemo(() => {
    const base = entries.filter((e) => {
      if (featured && e.id === featured.id) return false;
      if (category !== "all" && e.category !== category) return false;
      if (mood !== "all" && !(e.mood ?? []).includes(mood)) return false;
      if (!matchesSearch(e, query)) return false;
      return true;
    });
    return sortEntries(base, sort, stats);
  }, [entries, category, mood, query, sort, stats, featured]);

  const filterKey = `${category}-${mood}-${query}-${sort}`;

  const cycleSort = useCallback(() => {
    setSort((s) => {
      const next = s === "popular" ? "new" : "popular";
      captureEvent("sort_change", { sort: next });
      return next;
    });
  }, []);

  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSearchEventRef = useRef("");

  useEffect(() => {
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    searchDebounceRef.current = setTimeout(() => {
      const q = query.trim();
      if (q.length < 2) return;
      const key = `${q}:${filtered.length}`;
      if (key === lastSearchEventRef.current) return;
      lastSearchEventRef.current = key;
      captureEvent("search", { query: q, result_count: filtered.length });
    }, 450);
    return () => {
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, [query, filtered.length]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      const cards = Array.from(
        gridRef.current?.querySelectorAll<HTMLElement>("[data-sound-card]") ?? [],
      );
      if (cards.length === 0) return;
      const idx = cards.findIndex((c) => c === document.activeElement);
      const col = window.innerWidth >= 1024 ? 3 : window.innerWidth >= 640 ? 2 : 1;
      let next = idx;
      if (e.key === "ArrowRight") next = idx < 0 ? 0 : Math.min(cards.length - 1, idx + 1);
      if (e.key === "ArrowLeft") next = idx < 0 ? 0 : Math.max(0, idx - 1);
      if (e.key === "ArrowDown") next = idx < 0 ? 0 : Math.min(cards.length - 1, idx + col);
      if (e.key === "ArrowUp") next = idx < 0 ? 0 : Math.max(0, idx - col);
      if (next !== idx && next >= 0) {
        e.preventDefault();
        cards[next]?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [filterKey]);

  const sortLabel = sort === "popular" ? "Sort: Popular" : "Sort: Newest";

  return (
    <div className="flex flex-col gap-8">
      {featured && <FeaturedSlot entry={featured} />}

      <div
        className="sticky top-0 z-30 -mx-4 border-b border-zinc-800/70 bg-zinc-950/90 px-4 py-3 backdrop-blur-md supports-[backdrop-filter]:bg-zinc-950/75"
      >
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <label className="relative min-w-[12rem] flex-1">
              <span className="sr-only">Search sounds</span>
              <Search
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500"
                aria-hidden
              />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search title, mood, tags…"
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900/50 py-2 pl-9 pr-3 text-sm text-zinc-100 placeholder:text-zinc-600 transition-colors focus:border-violet-500/40 focus:outline-none focus:ring-2 focus:ring-violet-500/25"
              />
            </label>
            <IconButton
              label={sortLabel}
              onClick={cycleSort}
              variant="outline"
              className="shrink-0"
            >
              {sort === "popular" ? (
                <TrendingUp className="h-4 w-4" aria-hidden />
              ) : (
                <ArrowDownAZ className="h-4 w-4" aria-hidden />
              )}
            </IconButton>
            <span className="hidden items-center gap-1 text-[10px] uppercase tracking-wide text-zinc-600 sm:inline-flex">
              <SlidersHorizontal className="h-3 w-3" aria-hidden />
              Filters
            </span>
          </div>
          {!lockedCategory && (
            <FilterPillGroup
              aria-label="Category"
              options={categoryPills}
              value={category}
              onChange={setCategoryWithUrl}
              hrefForValue={(v) => (v === "all" ? "/" : `/c/${v}`)}
            />
          )}
          {moodOptions.length > 0 && (
            <FilterPillGroup
              aria-label="Mood"
              options={moodPills}
              value={mood}
              onChange={(next) => {
                if (next !== mood) {
                  captureEvent("filter_change", { filter: "mood", value: next });
                }
                setMood(next);
              }}
            />
          )}
        </div>
      </div>

      <div ref={gridRef}>
        {filtered.length === 0 ? (
          <p className="animate-fade-in py-16 text-center text-sm text-zinc-600">
            No sounds match these filters.
          </p>
        ) : (
          <div
            key={filterKey}
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {filtered.map((entry, index) => (
              <EntryCard key={entry.id} entry={entry} staggerIndex={index} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
