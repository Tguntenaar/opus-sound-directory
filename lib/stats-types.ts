export type StatEvent = "copy" | "download";

export type EntryStats = {
  copy: number;
  download: number;
};

export type StatsMap = Record<string, EntryStats>;

export const EMPTY_STATS: EntryStats = { copy: 0, download: 0 };
