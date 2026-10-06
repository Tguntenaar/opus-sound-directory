import { getKvBinding } from "@/lib/kv-client";
import type { CommunitySoundEntry } from "@/lib/community-types";

const INDEX_KEY = "community:index";
const ENTRY_PREFIX = "community:entry:";
const CODE_PREFIX = "community:code:";

function entryKey(slug: string) {
  return `${ENTRY_PREFIX}${slug}`;
}

function codeKey(slug: string) {
  return `${CODE_PREFIX}${slug}`;
}

export async function saveCommunityEntry(
  entry: CommunitySoundEntry,
  code: string,
): Promise<void> {
  const kv = await getKvBinding("SPONSOR_KV");
  await kv.put(entryKey(entry.slug), JSON.stringify(entry));
  await kv.put(codeKey(entry.slug), code);
  const rawIndex = await kv.get(INDEX_KEY);
  const slugs: string[] = rawIndex ? JSON.parse(rawIndex) : [];
  if (!slugs.includes(entry.slug)) {
    slugs.unshift(entry.slug);
    await kv.put(INDEX_KEY, JSON.stringify(slugs));
  }
}

export async function getCommunityCode(slug: string): Promise<string | null> {
  const kv = await getKvBinding("SPONSOR_KV");
  return kv.get(codeKey(slug));
}

export async function getCommunityEntryBySlug(
  slug: string,
): Promise<CommunitySoundEntry | null> {
  const kv = await getKvBinding("SPONSOR_KV");
  const raw = await kv.get(entryKey(slug));
  if (!raw) return null;
  return JSON.parse(raw) as CommunitySoundEntry;
}

export async function listCommunityEntries(): Promise<CommunitySoundEntry[]> {
  const kv = await getKvBinding("SPONSOR_KV");
  const rawIndex = await kv.get(INDEX_KEY);
  const slugs: string[] = rawIndex ? JSON.parse(rawIndex) : [];
  const out: CommunitySoundEntry[] = [];
  for (const slug of slugs) {
    const e = await getCommunityEntryBySlug(slug);
    if (e) out.push(e);
  }
  return out;
}

export async function unpublishCommunityEntry(slug: string): Promise<boolean> {
  const kv = await getKvBinding("SPONSOR_KV");
  const rawIndex = await kv.get(INDEX_KEY);
  const slugs: string[] = rawIndex ? JSON.parse(rawIndex) : [];
  const next = slugs.filter((s) => s !== slug);
  await kv.put(INDEX_KEY, JSON.stringify(next));
  if (kv.delete) {
    await kv.delete(entryKey(slug));
    await kv.delete(codeKey(slug));
  }
  return true;
}
