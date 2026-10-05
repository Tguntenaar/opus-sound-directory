"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { EntryStats, StatEvent, StatsMap } from "@/lib/stats-types";
import { EMPTY_STATS } from "@/lib/stats-types";

type StatsContextValue = {
  stats: StatsMap;
  track: (entryId: string, event: StatEvent) => void;
  getEntryStats: (entryId: string) => EntryStats;
};

const StatsContext = createContext<StatsContextValue | null>(null);

export function StatsProvider({ children }: { children: ReactNode }) {
  const [stats, setStats] = useState<StatsMap>({});

  useEffect(() => {
    let cancelled = false;
    fetch("/api/stats")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data: { stats: StatsMap }) => {
        if (!cancelled) setStats(data.stats ?? {});
      })
      .catch(() => {
        if (!cancelled) setStats({});
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const track = useCallback((entryId: string, event: StatEvent) => {
    setStats((prev) => {
      const cur = prev[entryId] ?? { ...EMPTY_STATS };
      return {
        ...prev,
        [entryId]: { ...cur, [event]: cur[event] + 1 },
      };
    });
    void fetch("/api/stats", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: entryId, event }),
    })
      .then((r) => (r.ok ? r.json() : null))
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
    () => ({ stats, track, getEntryStats }),
    [stats, track, getEntryStats],
  );

  return <StatsContext.Provider value={value}>{children}</StatsContext.Provider>;
}

export function useStats() {
  const ctx = useContext(StatsContext);
  if (!ctx) throw new Error("useStats must be used within StatsProvider");
  return ctx;
}
