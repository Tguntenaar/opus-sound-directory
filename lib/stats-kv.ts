import { ALL_ENTRIES } from "@/lib/entries.generated";
import type { EntryStats, StatEvent, StatsMap } from "@/lib/stats-types";
import { EMPTY_STATS } from "@/lib/stats-types";

const KEY_PREFIX = "stats:";

function key(entryId: string, event: StatEvent) {
  return `${KEY_PREFIX}${entryId}:${event}`;
}

type KvLike = {
  get(key: string): Promise<string | null>;
  put(key: string, value: string): Promise<void>;
};

const devMemory = new Map<string, string>();

function devKv(): KvLike {
  return {
    async get(k) {
      return devMemory.get(k) ?? null;
    },
    async put(k, v) {
      devMemory.set(k, v);
    },
  };
}

async function resolveKv(): Promise<KvLike | null> {
  try {
    const { env } = await import("cloudflare:workers");
    const kv = (env as { STATS_KV?: KvLike }).STATS_KV;
    if (kv) return kv;
  } catch {
    // not in workerd (e.g. plain node preview)
  }
  if (process.env.NODE_ENV === "development") return devKv();
  return devKv();
}

async function readCount(kv: KvLike, entryId: string, event: StatEvent): Promise<number> {
  const raw = await kv.get(key(entryId, event));
  const n = raw ? parseInt(raw, 10) : 0;
  return Number.isFinite(n) ? n : 0;
}

export async function getStatsForEntry(entryId: string): Promise<EntryStats> {
  const kv = await resolveKv();
  if (!kv) return { ...EMPTY_STATS };
  const [copy, download] = await Promise.all([
    readCount(kv, entryId, "copy"),
    readCount(kv, entryId, "download"),
  ]);
  return { copy, download };
}

export async function getAllStats(): Promise<StatsMap> {
  const kv = await resolveKv();
  const ids = ALL_ENTRIES.map((e) => e.id);
  const out: StatsMap = {};
  if (!kv) {
    for (const id of ids) out[id] = { ...EMPTY_STATS };
    return out;
  }
  await Promise.all(
    ids.map(async (id) => {
      out[id] = await getStatsForEntry(id);
    }),
  );
  return out;
}

export async function incrementStat(entryId: string, event: StatEvent): Promise<EntryStats> {
  const kv = await resolveKv();
  if (!kv) {
    return { ...EMPTY_STATS, [event]: 1 } as EntryStats;
  }
  const current = await readCount(kv, entryId, event);
  const next = current + 1;
  await kv.put(key(entryId, event), String(next));
  return getStatsForEntry(entryId);
}

export function isValidEntryId(id: string): boolean {
  return ALL_ENTRIES.some((e) => e.id === id);
}

export function isValidEvent(event: string): event is StatEvent {
  return event === "copy" || event === "download";
}
