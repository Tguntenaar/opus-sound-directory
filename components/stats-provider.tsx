"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { EntryStats, StatEvent, StatsMap } from "@/lib/stats-types";
import { EMPTY_STATS } from "@/lib/stats-types";
import { getPosthogWhenReady } from "@/lib/analytics-client";
import { PosthogPageviews } from "@/components/posthog-pageviews";

type StatsContextValue = {
  stats: StatsMap;
  rankingStats: StatsMap;
  track: (entryId: string, event: StatEvent) => void;
  getEntryStats: (entryId: string) => EntryStats;
};

const StatsContext = createContext<StatsContextValue | null>(null);

export function StatsProvider({ children }: { children: ReactNode }) {
  const trackedPlays = useRef(new Set<string>());
  const [stats, setStats] = useState<StatsMap>({});
  const [rankingStats, setRankingStats] = useState<StatsMap>({});

  useEffect(() => {
    void getPosthogWhenReady();
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/stats")
      .then((r) => (r.ok ? r.json() as Promise<{ stats: StatsMap }> : Promise.reject()))
      .then((data: { stats: StatsMap }) => {
        if (!cancelled) {
          setStats(data.stats ?? {});
          setRankingStats(data.stats ?? {});
        }
      })
      .catch(() => {
        if (!cancelled) setStats({});
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const track = useCallback((entryId: string, event: StatEvent) => {
    // Public popularity counts at most one play per sound per page session.
    if (event === "play") {
      if (trackedPlays.current.has(entryId)) return;
      trackedPlays.current.add(entryId);
    }
    setStats((prev) => {
      const cur = prev[entryId] ?? { ...EMPTY_STATS };
      return {
        ...prev,
        [entryId]: { ...cur, [event]: (cur[event] ?? 0) + 1 },
      };
    });
    void fetch("/api/stats", {
      method: "POST",
      keepalive: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: entryId, event }),
    })
      .then((r) => (r.ok ? r.json() as Promise<{ stats: EntryStats }> : null))
      .then((data) => {
        if (data?.stats) {
          setStats((prev) => ({
            ...prev,
            [entryId]: data.stats as EntryStats,
          }));
        }
      })
      .catch(() => {
        /* keep optimistic count */
      });
  }, []);

  const getEntryStats = useCallback(
    (entryId: string) => stats[entryId] ?? { ...EMPTY_STATS },
    [stats],
  );

  const value = useMemo(
    () => ({ stats, rankingStats, track, getEntryStats }),
    [stats, rankingStats, track, getEntryStats],
  );

  return (
    <StatsContext.Provider value={value}>
      <PosthogPageviews />
      {children}
    </StatsContext.Provider>
  );
}

export function useStats() {
  const ctx = useContext(StatsContext);
  if (!ctx) throw new Error("useStats must be used within StatsProvider");
  return ctx;
}
