import { getKvBinding } from "@/lib/kv-client";
import type { SubmitEntry, SubmitEntryInput, SubmissionSource } from "@/lib/submit-types";
import { resolveCode } from "@/lib/submit-screen";

import { getAccountEnv } from "@/lib/auth";
import { ownedSubmissionInput, type SubmissionOwner } from "@/lib/submission-access";

const INDEX_KEY = "submit:index";
const ENTRY_PREFIX = "submit:entry:";
const RATE_WINDOW_MS = 60 * 60 * 1000;

function entryKey(id: string) {
  return `${ENTRY_PREFIX}${id}`;
}

export async function saveSubmitEntry(
  input: SubmitEntryInput,
  source: SubmissionSource,
  owner: SubmissionOwner,
): Promise<SubmitEntry> {
  const data = ownedSubmissionInput(input, owner);
  const { ACCOUNTS_DB: db } = await getAccountEnv();
  const entry: SubmitEntry = {
    ...data,
    id: crypto.randomUUID(),
    ownerId: owner.id,
    createdAt: new Date().toISOString(),
    source,
    status: "scanning",
    storedCode: resolveCode(data),
  };
  // D1's atomic conditional insert also enforces the per-account cooldown.
  const result = await db.prepare(`INSERT INTO submission (id, ownerId, createdAt, payload)
    SELECT ?, ?, ?, ? WHERE NOT EXISTS (
      SELECT 1 FROM submission WHERE ownerId = ? AND createdAt > ?
    )`).bind(entry.id, owner.id, entry.createdAt, JSON.stringify(entry), owner.id,
      new Date(Date.now() - RATE_WINDOW_MS).toISOString()).run();
  if (!result.meta.changes) throw new SubmissionRateLimitError();
  return entry;
}

export class SubmissionRateLimitError extends Error {}

export async function listOwnedSubmissions(ownerId: string): Promise<SubmitEntry[]> {
  const { ACCOUNTS_DB: db } = await getAccountEnv();
  const result = await db.prepare("SELECT payload FROM submission WHERE ownerId = ? ORDER BY createdAt DESC LIMIT 100")
    .bind(ownerId).all<{ payload: string }>();
  return result.results.map(row => JSON.parse(row.payload) as SubmitEntry);
}

export async function getSubmitEntry(id: string): Promise<SubmitEntry | null> {
  const { ACCOUNTS_DB: db } = await getAccountEnv();
  const row = await db.prepare("SELECT payload FROM submission WHERE id = ?").bind(id).first<{ payload: string }>();
  if (row) return JSON.parse(row.payload) as SubmitEntry;
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
  const { ACCOUNTS_DB: db } = await getAccountEnv();
  const result = await db.prepare("UPDATE submission SET payload = ? WHERE id = ?")
    .bind(JSON.stringify(next), id).run();
  if (!result.meta.changes) {
    const kv = await getKvBinding("SPONSOR_KV");
    await kv.put(entryKey(id), JSON.stringify(next));
  }
  return next;
}

export async function listSubmitEntries(limit = 100): Promise<SubmitEntry[]> {
  const kv = await getKvBinding("SPONSOR_KV");
  const rawIndex = await kv.get(INDEX_KEY);
  const ids: string[] = rawIndex ? JSON.parse(rawIndex) : [];
  const { ACCOUNTS_DB: db } = await getAccountEnv();
  const rows = await db.prepare("SELECT payload FROM submission ORDER BY createdAt DESC LIMIT ?")
    .bind(Math.min(limit, 500)).all<{ payload: string }>();
  const out = rows.results.map(row => JSON.parse(row.payload) as SubmitEntry);
  for (const id of ids.slice(0, limit)) {
    const e = await getSubmitEntry(id);
    if (e) out.push(e);
  }
  return out.sort((a, b) => b.createdAt.localeCompare(a.createdAt)).slice(0, limit);
}
