import { getKvBinding } from "@/lib/kv-client";
import type { SubmitEntry, SubmitEntryInput, SubmissionSource } from "@/lib/submit-types";
import { resolveCode } from "@/lib/submit-screen";

const INDEX_KEY = "submit:index";
const ENTRY_PREFIX = "submit:entry:";
const RATE_PREFIX = "submit:rate:";
const MAX_INDEX = 500;
const RATE_WINDOW_MS = 60 * 60 * 1000;

function entryKey(id: string) {
  return `${ENTRY_PREFIX}${id}`;
}

function rateKey(fingerprint: string) {
  return `${RATE_PREFIX}${fingerprint}`;
}

export async function checkSubmitRateLimit(fingerprint: string): Promise<boolean> {
  const kv = await getKvBinding("SPONSOR_KV");
  const raw = await kv.get(rateKey(fingerprint));
  if (!raw) return true;
  const ts = Number.parseInt(raw, 10);
  if (!Number.isFinite(ts)) return true;
  return Date.now() - ts >= RATE_WINDOW_MS;
}

export async function touchSubmitRateLimit(fingerprint: string): Promise<void> {
  const kv = await getKvBinding("SPONSOR_KV");
  await kv.put(rateKey(fingerprint), String(Date.now()));
}

export async function saveSubmitEntry(
  input: SubmitEntryInput,
  source: SubmissionSource,
): Promise<SubmitEntry> {
  const kv = await getKvBinding("SPONSOR_KV");
  const id = crypto.randomUUID();
  const storedCode = resolveCode(input);
  const entry: SubmitEntry = {
    id,
    createdAt: new Date().toISOString(),
    source,
    status: "scanning",
    storedCode,
    ...input,
  };
  await kv.put(entryKey(id), JSON.stringify(entry));

  const rawIndex = await kv.get(INDEX_KEY);
  const ids: string[] = rawIndex ? JSON.parse(rawIndex) : [];
  ids.unshift(id);
  await kv.put(INDEX_KEY, JSON.stringify(ids.slice(0, MAX_INDEX)));

  return entry;
}

export async function getSubmitEntry(id: string): Promise<SubmitEntry | null> {
  const kv = await getKvBinding("SPONSOR_KV");
  const raw = await kv.get(entryKey(id));
  if (!raw) return null;
  return JSON.parse(raw) as SubmitEntry;
}

export async function updateSubmitEntry(
  id: string,
  patch: Partial<SubmitEntry>,
): Promise<SubmitEntry | null> {
  const existing = await getSubmitEntry(id);
  if (!existing) return null;
  const next = { ...existing, ...patch };
  const kv = await getKvBinding("SPONSOR_KV");
  await kv.put(entryKey(id), JSON.stringify(next));
  return next;
}

export async function listSubmitEntries(limit = 100): Promise<SubmitEntry[]> {
  const kv = await getKvBinding("SPONSOR_KV");
  const rawIndex = await kv.get(INDEX_KEY);
  const ids: string[] = rawIndex ? JSON.parse(rawIndex) : [];
  const out: SubmitEntry[] = [];
  for (const id of ids.slice(0, limit)) {
    const e = await getSubmitEntry(id);
    if (e) out.push(e);
  }
  return out;
}
