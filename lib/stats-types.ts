export type StatEvent = "copy" | "download" | "play";

export type EntryStats = {
  play: number;
  copy: number;
  download: number;
};

export type StatsMap = Record<string, EntryStats>;

export const EMPTY_STATS: EntryStats = { play: 0, copy: 0, download: 0 };
