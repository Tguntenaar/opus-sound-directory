import { getKvBinding } from "@/lib/kv-client";
import type { SponsorLead, SponsorLeadInput } from "@/lib/sponsor-types";

const INDEX_KEY = "sponsor:index";
const LEAD_PREFIX = "sponsor:lead:";
const MAX_INDEX = 200;

function leadKey(id: string) {
  return `${LEAD_PREFIX}${id}`;
}

export async function saveSponsorLead(input: SponsorLeadInput): Promise<SponsorLead> {
  const kv = await getKvBinding("SPONSOR_KV");
  const id = crypto.randomUUID();
  const lead: SponsorLead = {
    id,
    createdAt: new Date().toISOString(),
    ...input,
  };
  await kv.put(leadKey(id), JSON.stringify(lead));

  const rawIndex = await kv.get(INDEX_KEY);
  const ids: string[] = rawIndex ? JSON.parse(rawIndex) : [];
  ids.unshift(id);
  await kv.put(INDEX_KEY, JSON.stringify(ids.slice(0, MAX_INDEX)));

  return lead;
}

export async function listSponsorLeads(limit = 50): Promise<SponsorLead[]> {
  const kv = await getKvBinding("SPONSOR_KV");
  const rawIndex = await kv.get(INDEX_KEY);
  if (!rawIndex) return [];
  const ids: string[] = JSON.parse(rawIndex);
  const leads: SponsorLead[] = [];
  for (const id of ids.slice(0, limit)) {
    const raw = await kv.get(leadKey(id));
    if (raw) leads.push(JSON.parse(raw) as SponsorLead);
  }
  return leads;
}
