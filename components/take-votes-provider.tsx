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
import type { TakeVoteMap } from "@/lib/take-selection";

type TakeVotesContextValue = {
  votesByEntry: Record<string, TakeVoteMap>;
  voteForTake: (entryId: string, takeId: string) => void;
  getVotes: (entryId: string) => TakeVoteMap;
};

const TakeVotesContext = createContext<TakeVotesContextValue | null>(null);

export function TakeVotesProvider({ children }: { children: ReactNode }) {
  const [votesByEntry, setVotesByEntry] = useState<Record<string, TakeVoteMap>>({});

  useEffect(() => {
    let cancelled = false;
    fetch("/api/take-votes")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data: { votes: Record<string, TakeVoteMap> }) => {
        if (!cancelled) setVotesByEntry(data.votes ?? {});
      })
      .catch(() => {
        if (!cancelled) setVotesByEntry({});
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const voteForTake = useCallback((entryId: string, takeId: string) => {
    setVotesByEntry((prev) => {
      const cur = prev[entryId] ?? {};
      return {
        ...prev,
        [entryId]: { ...cur, [takeId]: (cur[takeId] ?? 0) + 1 },
      };
    });
    void fetch("/api/take-votes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entryId, takeId }),
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.votes) {
          setVotesByEntry((prev) => ({
            ...prev,
            [entryId]: data.votes as TakeVoteMap,
          }));
        }
      })
      .catch(() => {
        /* keep optimistic */
      });
  }, []);

  const getVotes = useCallback(
    (entryId: string) => votesByEntry[entryId] ?? {},
    [votesByEntry],
  );

  const value = useMemo(
    () => ({ votesByEntry, voteForTake, getVotes }),
    [votesByEntry, voteForTake, getVotes],
  );

  return <TakeVotesContext.Provider value={value}>{children}</TakeVotesContext.Provider>;
}

export function useTakeVotes() {
  const ctx = useContext(TakeVotesContext);
  if (!ctx) throw new Error("useTakeVotes must be used within TakeVotesProvider");
  return ctx;
}
