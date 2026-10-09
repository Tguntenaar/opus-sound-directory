import { getKvBinding } from "@/lib/kv-client";
import { HERO8_VOTING_ENTRY_IDS, isValidTakeForEntry } from "@/lib/hero8-takes";
import type { TakeVoteMap } from "@/lib/take-selection";

const COUNT_PREFIX = "takevote:";
const VOTER_PREFIX = "takevote:voter:";
const RATE_PREFIX = "takevote:rate:";
const RATE_WINDOW_MS = 60 * 60 * 1000;
const MAX_VOTES_PER_WINDOW = 60;

function countKey(entryId: string, takeId: string) {
  return `${COUNT_PREFIX}${entryId}:${takeId}`;
}

function voterKey(voterId: string, entryId: string, takeId: string) {
  return `${VOTER_PREFIX}${voterId}:${entryId}:${takeId}`;
}

function rateKey(fingerprint: string) {
  return `${RATE_PREFIX}${fingerprint}`;
}

async function readCount(kv: Awaited<ReturnType<typeof getKvBinding>>, entryId: string, takeId: string) {
  const raw = await kv.get(countKey(entryId, takeId));
  const n = raw ? parseInt(raw, 10) : 0;
  return Number.isFinite(n) ? n : 0;
}

export async function getTakeVotesForEntry(entryId: string): Promise<TakeVoteMap> {
  if (!HERO8_VOTING_ENTRY_IDS.includes(entryId)) return {};
  const kv = await getKvBinding("STATS_KV");
  const out: TakeVoteMap = {};
  for (const takeId of ["opus", "codex-1", "codex-2", "codex-3"]) {
    if (!isValidTakeForEntry(entryId, takeId)) continue;
    out[takeId] = await readCount(kv, entryId, takeId);
  }
  return out;
}

export async function getAllTakeVotes(): Promise<Record<string, TakeVoteMap>> {
  const out: Record<string, TakeVoteMap> = {};
  await Promise.all(
    HERO8_VOTING_ENTRY_IDS.map(async (id) => {
      out[id] = await getTakeVotesForEntry(id);
    }),
  );
  return out;
}

export async function checkTakeVoteRateLimit(fingerprint: string): Promise<boolean> {
  const kv = await getKvBinding("STATS_KV");
  const raw = await kv.get(rateKey(fingerprint));
  if (!raw) return true;
  try {
    const { count, ts } = JSON.parse(raw) as { count: number; ts: number };
    if (!Number.isFinite(ts) || Date.now() - ts >= RATE_WINDOW_MS) return true;
    return (count ?? 0) < MAX_VOTES_PER_WINDOW;
  } catch {
    return true;
  }
}

async function touchTakeVoteRateLimit(kv: Awaited<ReturnType<typeof getKvBinding>>, fingerprint: string) {
  const raw = await kv.get(rateKey(fingerprint));
  let count = 0;
  let ts = Date.now();
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as { count: number; ts: number };
      if (Number.isFinite(parsed.ts) && Date.now() - parsed.ts < RATE_WINDOW_MS) {
        count = parsed.count ?? 0;
        ts = parsed.ts;
      }
    } catch {
      /* reset */
    }
  }
  await kv.put(rateKey(fingerprint), JSON.stringify({ count: count + 1, ts }));
}

export type CastTakeVoteResult =
  | { ok: true; votes: TakeVoteMap; alreadyVoted?: boolean }
  | { ok: false; error: string; status: number };

export async function castTakeVote(
  entryId: string,
  takeId: string,
  voterId: string,
  fingerprint: string,
): Promise<CastTakeVoteResult> {
  if (!isValidTakeForEntry(entryId, takeId)) {
    return { ok: false, error: "Invalid entry or take", status: 400 };
  }
  const allowed = await checkTakeVoteRateLimit(fingerprint);
  if (!allowed) {
    return { ok: false, error: "Too many votes — try again later.", status: 429 };
  }

  const kv = await getKvBinding("STATS_KV");
  const dup = await kv.get(voterKey(voterId, entryId, takeId));
  if (dup) {
    const votes = await getTakeVotesForEntry(entryId);
    return { ok: true, votes, alreadyVoted: true };
  }

  const current = await readCount(kv, entryId, takeId);
  await kv.put(countKey(entryId, takeId), String(current + 1));
  await kv.put(voterKey(voterId, entryId, takeId), "1");
  await touchTakeVoteRateLimit(kv, fingerprint);

  const votes = await getTakeVotesForEntry(entryId);
  return { ok: true, votes };
}
