"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { ArrowDownAZ, Bookmark, ChevronDown, Search, SlidersHorizontal, TrendingUp } from "lucide-react";
import { useBookmarks } from "@/lib/use-bookmarks";
import type { SoundEntry } from "@/lib/entries";
import { CATEGORY_ORDER, CATEGORIES } from "@/lib/categories";
import { MOOD_FACETS, formatMood } from "@/lib/mood";
import { EntryCard } from "@/components/entry-card";
import { FilterPillGroup, type PillOption } from "@/components/filter-pill-group";
import { FeaturedSlot } from "@/components/featured-slot";
import { getFeaturedEntry, FEATURED_CONTROL_SLUG } from "@/lib/featured";
import { FeaturedSoundExperiment } from "@/components/featured-sound-experiment";
import { getHomeSponsor } from "@/lib/sponsors";
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

const PAGE_SIZE = 18;

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
  // Freeze ranking to the loaded snapshot so playing a card never moves it.
  const { rankingStats: stats } = useStats();
  const [category, setCategory] = useState<string>(
    lockedCategory ?? initialCategory ?? "all",
  );
  const [mood, setMood] = useState<string>("all");
  const [query, setQuery] = useState("");
  const bookmarks = useBookmarks();
  const [bookmarksOnly, setBookmarksOnly] = useState(false);
  const [sort, setSort] = useState<SortMode>("popular");
  const gridRef = useRef<HTMLDivElement>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const filtersId = useId();
  const activeFilterCount = Number(!lockedCategory && category !== "all") + Number(mood !== "all");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("opus-sounds:sort");
      if (saved === "popular" || saved === "new") setSort(saved);
    } catch { /* Storage can be unavailable in private browsing. */ }
  }, []);

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

  const homeSponsor = lockedCategory ? null : getHomeSponsor();
  const featured = useMemo(() => {
    if (lockedCategory || homeSponsor) return undefined;
    return getFeaturedEntry(entries) ?? undefined;
  }, [entries, lockedCategory, homeSponsor]);
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
      if (featured && e.id === featured.id && !bookmarksOnly) return false;
      if (bookmarksOnly && !bookmarks.has(e.id)) return false;
      if (category !== "all" && e.category !== category) return false;
      if (mood !== "all" && !(e.mood ?? []).includes(mood)) return false;
      if (!matchesSearch(e, query)) return false;
      return true;
    });
    return sortEntries(base, sort, stats);
  }, [entries, category, mood, query, sort, stats, featured, bookmarksOnly, bookmarks]);

  const filterKey = JSON.stringify([category, mood, query, sort, bookmarksOnly]);
  const [pagination, setPagination] = useState({ key: filterKey, count: PAGE_SIZE });
  const loadMoreRef = useRef<HTMLDivElement>(null);
  // Reset in the same render so a new search never flashes the previous page count.
  if (pagination.key !== filterKey) setPagination({ key: filterKey, count: PAGE_SIZE });
  const visibleCount = pagination.key === filterKey ? pagination.count : PAGE_SIZE;
  const visibleEntries = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;
  const loadMore = useCallback(() => {
    setPagination(current => ({
      key: filterKey,
      count: Math.min(filtered.length, (current.key === filterKey ? current.count : PAGE_SIZE) + PAGE_SIZE),
    }));
  }, [filterKey, filtered.length]);

  useEffect(() => {
    if (!hasMore || !loadMoreRef.current || !("IntersectionObserver" in window)) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting) return;
      observer.disconnect();
      loadMore();
    }, { rootMargin: "0px 0px 400px 0px" });
    observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadMore, visibleCount]);

  const cycleSort = useCallback(() => {
    const next = sort === "popular" ? "new" : "popular";
    setSort(next);
    captureEvent("sort_change", { sort: next });
    try { localStorage.setItem("opus-sounds:sort", next); } catch { /* Optional preference. */ }
  }, [sort]);

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
      {featured && !lockedCategory && !homeSponsor ? <FeaturedSoundExperiment
        entry={featured}
        control={entries.find((entry) => entry.slug === FEATURED_CONTROL_SLUG)}
      /> : <FeaturedSlot
        entry={featured}
        placement={lockedCategory ? "category" : "home"}
        category={lockedCategory}
      />}

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
            <IconButton label={bookmarksOnly ? "Show all sounds" : "Show bookmarked sounds"}
              aria-pressed={bookmarksOnly} variant="outline" onClick={() => setBookmarksOnly(value => !value)}>
              <Bookmark className={`h-4 w-4 ${bookmarksOnly ? "fill-violet-400 text-violet-400" : ""}`} aria-hidden />
            </IconButton>
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
            <button type="button" aria-expanded={filtersOpen} aria-controls={filtersId}
              onClick={() => setFiltersOpen(open => !open)}
              className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-zinc-800 px-3 text-sm text-zinc-300 transition-colors hover:border-zinc-600 hover:bg-zinc-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400">
              <SlidersHorizontal className="h-4 w-4" aria-hidden />
              Filters
              {activeFilterCount > 0 && <span className="rounded-full bg-violet-500/15 px-1.5 text-xs text-violet-300">{activeFilterCount}</span>}
              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${filtersOpen ? "rotate-180" : ""}`} aria-hidden />
            </button>
          </div>
          {activeFilterCount > 0 && <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-400">
            {!lockedCategory && category !== "all" && <span className="rounded-md bg-violet-500/10 px-2 py-1 text-violet-300">{categoryPills.find(option => option.value === category)?.label}</span>}
            {mood !== "all" && <span className="rounded-md bg-violet-500/10 px-2 py-1 text-violet-300">{formatMood(mood)}</span>}
            <button type="button" className="rounded px-2 py-1 hover:text-zinc-100 focus-visible:outline-violet-400" onClick={() => {
              if (!lockedCategory) setCategoryWithUrl("all");
              if (mood !== "all") captureEvent("filter_change", { filter: "mood", value: "all" });
              setMood("all");
            }}>Clear filters</button>
          </div>}
          <div id={filtersId} hidden={!filtersOpen}>
            {filtersOpen && <div className="max-h-[50vh] space-y-5 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 sm:p-5">
              {!lockedCategory && <section className="space-y-2">
                <h2 className="text-xs font-medium uppercase tracking-wide text-zinc-500">Category</h2>
                <FilterPillGroup aria-label="Category" options={categoryPills} value={category} onChange={setCategoryWithUrl}
                  hrefForValue={(v) => (v === "all" ? "/" : `/c/${v}`)} />
              </section>}
              {moodOptions.length > 0 && <section className={`space-y-2 ${!lockedCategory ? "border-t border-zinc-800 pt-4" : ""}`}>
                <h2 className="text-xs font-medium uppercase tracking-wide text-zinc-500">Mood</h2>
                <FilterPillGroup aria-label="Mood" options={moodPills} value={mood} onChange={(next) => {
                  if (next !== mood) captureEvent("filter_change", { filter: "mood", value: next });
                  setMood(next);
                }} />
              </section>}
            </div>}
          </div>
        </div>
      </div>

      <div ref={gridRef}>
        {filtered.length === 0 ? (
          <p className="animate-fade-in py-16 text-center text-sm text-zinc-600">
            {bookmarksOnly ? "No bookmarked sounds match these filters." : "No sounds match these filters."}
          </p>
        ) : (
          <div
            key={filterKey}
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {visibleEntries.map((entry, index) => (
              <EntryCard key={entry.id} entry={entry} staggerIndex={index % PAGE_SIZE} />
            ))}
          </div>
        )}
      </div>
      {filtered.length > 0 && <div ref={loadMoreRef} className="flex flex-col items-center gap-3 py-4">
        <p role="status" className="text-xs text-zinc-500">
          {visibleEntries.length} of {filtered.length} sounds
        </p>
        {hasMore && <button type="button" onClick={loadMore}
          className="rounded-lg border border-zinc-800 px-4 py-2 text-sm text-zinc-400 transition-colors hover:border-zinc-600 hover:text-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400">
          Load more
        </button>}
      </div>}
    </div>
  );
}
