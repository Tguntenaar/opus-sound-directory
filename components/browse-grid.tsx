"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { ArrowDownAZ, Bookmark, Search, SlidersHorizontal, TrendingUp, X } from "lucide-react";
import { BrowseEmptyState } from "@/components/browse-empty-state";
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
import { buildHomeBrowseHref } from "@/lib/home-browse-url";

type Props = {
  entries: SoundEntry[];
  /** Home: hydrate the full catalog from a static asset instead of the RSC payload. */
  catalogHref?: string;
  /** Featured editorial pick when `entries` is only the first page (home). */
  featuredEntry?: SoundEntry;
  featuredControl?: SoundEntry;
  /** Lock grid to one category (category landing pages). */
  lockedCategory?: string;
  /** Sync ?category= on the home page without full navigation. */
  syncCategoryToUrl?: boolean;
  /** Sync ?q= on the home page (replaceState, debounced). */
  syncQueryToUrl?: boolean;
  initialCategory?: string;
  initialQuery?: string;
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
  entries: entriesProp,
  catalogHref,
  featuredEntry,
  featuredControl,
  lockedCategory,
  syncCategoryToUrl,
  syncQueryToUrl,
  initialCategory = "all",
  initialQuery = "",
}: Props) {
  const [entries, setEntries] = useState(entriesProp);

  useEffect(() => {
    setEntries(entriesProp);
  }, [entriesProp]);

  useEffect(() => {
    if (!catalogHref) return;
    let cancelled = false;
    fetch(catalogHref)
      .then((r) => (r.ok ? r.json() as Promise<SoundEntry[]> : Promise.reject()))
      .then((data) => {
        if (!cancelled && Array.isArray(data)) setEntries(data);
      })
      .catch(() => {
        /* Keep the first-page snapshot when the catalog asset is unavailable. */
      });
    return () => {
      cancelled = true;
    };
  }, [catalogHref]);
  // Freeze ranking to the loaded snapshot so playing a card never moves it.
  const { rankingStats: stats } = useStats();
  const [category, setCategory] = useState<string>(
    lockedCategory ?? initialCategory ?? "all",
  );
  const [mood, setMood] = useState<string>("all");
  const [query, setQuery] = useState(initialQuery);
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

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  const setCategoryWithUrl = useCallback(
    (next: string) => {
      if (next !== category) {
        captureEvent("filter_change", { filter: "category", value: next });
      }
      setCategory(next);
      if (syncCategoryToUrl && !lockedCategory) {
        const path = buildHomeBrowseHref({ category: next, query });
        window.history.pushState(null, "", path);
      }
    },
    [syncCategoryToUrl, lockedCategory, category, query],
  );

  const queryUrlDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (!syncQueryToUrl || lockedCategory) return;
    if (queryUrlDebounceRef.current) clearTimeout(queryUrlDebounceRef.current);
    queryUrlDebounceRef.current = setTimeout(() => {
      const path = buildHomeBrowseHref({ category, query });
      const current = `${window.location.pathname}${window.location.search}`;
      if (current !== path) window.history.replaceState(null, "", path);
    }, 300);
    return () => {
      if (queryUrlDebounceRef.current) clearTimeout(queryUrlDebounceRef.current);
    };
  }, [syncQueryToUrl, lockedCategory, category, query]);

  const homeSponsor = lockedCategory ? null : getHomeSponsor();
  const featured = useMemo(() => {
    if (lockedCategory || homeSponsor) return undefined;
    return featuredEntry ?? getFeaturedEntry(entries) ?? undefined;
  }, [entries, lockedCategory, homeSponsor, featuredEntry]);
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
  const [autoLoadMore, setAutoLoadMore] = useState(false);

  useEffect(() => {
    const enable = () => setAutoLoadMore(true);
    if (document.readyState === "complete") {
      const timer = window.setTimeout(enable, 800);
      return () => window.clearTimeout(timer);
    }
    window.addEventListener("load", enable, { once: true });
    return () => window.removeEventListener("load", enable);
  }, []);
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
    if (!autoLoadMore || !hasMore || !loadMoreRef.current || !("IntersectionObserver" in window)) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting) return;
      observer.disconnect();
      loadMore();
    }, { rootMargin: "0px 0px 400px 0px" });
    observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [autoLoadMore, hasMore, loadMore, visibleCount]);

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

  const sortLabel =
    sort === "popular"
      ? "Sorted by popularity (switch to newest)"
      : "Sorted by newest (switch to popular)";

  const clearFacets = useCallback(() => {
    if (!lockedCategory) setCategoryWithUrl("all");
    if (mood !== "all") captureEvent("filter_change", { filter: "mood", value: "all" });
    setMood("all");
  }, [lockedCategory, mood, setCategoryWithUrl]);

  const hasFacetFilters =
    (!lockedCategory && category !== "all") || mood !== "all";
  const hasQuery = query.trim().length > 0;

  return (
    <div className="flex flex-col gap-8">
      {featured && !bookmarksOnly && !lockedCategory && !homeSponsor ? <FeaturedSoundExperiment
        entry={featured}
        control={featuredControl ?? entries.find((entry) => entry.slug === FEATURED_CONTROL_SLUG)}
      /> : <FeaturedSlot
        entry={bookmarksOnly ? undefined : featured}
        placement={lockedCategory ? "category" : "home"}
        category={lockedCategory}
      />}

      <div
        className="sticky top-0 z-30 -mx-4 border-b border-zinc-800/70 bg-zinc-950/90 px-4 py-3 backdrop-blur-md supports-[backdrop-filter]:bg-zinc-950/75"
      >
        <div className="flex flex-col gap-3">
          <div className="flex flex-nowrap items-center gap-1.5 sm:gap-2">
            <label className="relative min-w-0 flex-1">
              <span className="sr-only">Search sounds</span>
              <Search
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500"
                aria-hidden
              />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search…"
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900/50 py-2 pl-9 pr-3 text-sm text-zinc-100 placeholder:text-zinc-600 transition-[border-color,box-shadow] duration-200 focus:border-violet-500/40 focus:outline-none focus:ring-2 focus:ring-violet-500/25"
              />
            </label>
            <div className="flex shrink-0 items-center gap-1 sm:gap-1.5">
              <IconButton
                label={bookmarksOnly ? "Show all sounds" : "Bookmarked only"}
                aria-pressed={bookmarksOnly}
                variant="outline"
                onClick={() => setBookmarksOnly((value) => !value)}
              >
                <Bookmark
                  className={`h-4 w-4 ${bookmarksOnly ? "fill-violet-400 text-violet-400" : ""}`}
                  aria-hidden
                />
              </IconButton>
              <IconButton
                label={sortLabel}
                onClick={cycleSort}
                variant="outline"
              >
                {sort === "popular" ? (
                  <TrendingUp className="h-4 w-4" aria-hidden />
                ) : (
                  <ArrowDownAZ className="h-4 w-4" aria-hidden />
                )}
              </IconButton>
              <span className="relative inline-flex">
                <IconButton
                  label={
                    filtersOpen
                      ? "Hide category and mood filters"
                      : "Category and mood filters"
                  }
                  aria-expanded={filtersOpen}
                  aria-controls={filtersId}
                  variant="outline"
                  onClick={() => setFiltersOpen((open) => !open)}
                  className={
                    filtersOpen || activeFilterCount > 0
                      ? "border-violet-500/35 bg-zinc-900/80"
                      : undefined
                  }
                >
                  <SlidersHorizontal className="h-4 w-4" aria-hidden />
                </IconButton>
                {activeFilterCount > 0 && (
                  <span
                    className="pointer-events-none absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-violet-500 px-1 text-[10px] font-medium leading-none text-white"
                    aria-hidden
                  >
                    {activeFilterCount}
                  </span>
                )}
              </span>
            </div>
          </div>
          {activeFilterCount > 0 && (
            <div className="pill-scroll flex flex-nowrap items-center gap-1.5 overflow-x-auto pb-0.5 text-xs text-zinc-400">
              {!lockedCategory && category !== "all" && (
                <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-violet-500/20 bg-violet-500/10 px-2.5 py-1 text-violet-200">
                  {categoryPills.find((option) => option.value === category)?.label}
                  <button
                    type="button"
                    className="rounded-full p-0.5 text-violet-300/80 transition-colors hover:bg-violet-500/20 hover:text-violet-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400"
                    aria-label="Remove category filter"
                    onClick={() => setCategoryWithUrl("all")}
                  >
                    <X className="h-3 w-3" aria-hidden />
                  </button>
                </span>
              )}
              {mood !== "all" && (
                <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-violet-500/20 bg-violet-500/10 px-2.5 py-1 text-violet-200">
                  {formatMood(mood)}
                  <button
                    type="button"
                    className="rounded-full p-0.5 text-violet-300/80 transition-colors hover:bg-violet-500/20 hover:text-violet-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400"
                    aria-label="Remove mood filter"
                    onClick={() => {
                      captureEvent("filter_change", { filter: "mood", value: "all" });
                      setMood("all");
                    }}
                  >
                    <X className="h-3 w-3" aria-hidden />
                  </button>
                </span>
              )}
              <IconButton label="Clear all filters" variant="ghost" size="sm" onClick={clearFacets}>
                <X className="h-3.5 w-3.5" aria-hidden />
              </IconButton>
            </div>
          )}
          <div id={filtersId} hidden={!filtersOpen}>
            {filtersOpen && (
              <div className="max-h-[50vh] space-y-4 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/30 p-3 sm:space-y-5 sm:p-5">
                {!lockedCategory && (
                  <section className="space-y-2">
                    <h2 className="text-[11px] font-medium uppercase tracking-wide text-zinc-500">
                      Category
                    </h2>
                    <FilterPillGroup
                      scrollable
                      aria-label="Category"
                      options={categoryPills}
                      value={category}
                      onChange={setCategoryWithUrl}
                      hrefForValue={(v) => (v === "all" ? "/" : `/c/${v}`)}
                    />
                  </section>
                )}
                {moodOptions.length > 0 && (
                  <section
                    className={`space-y-2 ${!lockedCategory ? "border-t border-zinc-800 pt-4" : ""}`}
                  >
                    <h2 className="text-[11px] font-medium uppercase tracking-wide text-zinc-500">
                      Mood
                    </h2>
                    <FilterPillGroup
                      scrollable
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
                  </section>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div ref={gridRef}>
        {filtered.length === 0 ? (
          <BrowseEmptyState
            bookmarksOnly={bookmarksOnly}
            hasQuery={hasQuery}
            hasFacetFilters={hasFacetFilters}
            onClearSearch={() => setQuery("")}
            onClearFacets={clearFacets}
            onShowAll={() => setBookmarksOnly(false)}
          />
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
        <p role="status" className="text-xs text-zinc-400">
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
