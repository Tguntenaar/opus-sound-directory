import type { SponsorLead } from "./sponsor-types.ts";

export type SponsorLeadWebhookPayload = {
  id: string;
  companyName: string;
  website: string;
  contactName: string;
  email: string;
  packages: SponsorLead["packages"];
  budgetRange: string;
  message: string;
  ref?: string;
  createdAt: string;
};

export function sponsorLeadWebhookPayload(lead: SponsorLead): SponsorLeadWebhookPayload {
  return {
    id: lead.id,
    companyName: lead.companyName,
    website: lead.website,
    contactName: lead.contactName,
    email: lead.email,
    packages: lead.packages,
    budgetRange: lead.budgetRange,
    message: lead.message,
    ref: lead.ref,
    createdAt: lead.createdAt,
  };
}

export function sponsorLeadWebhookHeaders(key?: string | null): Record<string, string> {
  const headers: Record<string, string> = { "content-type": "application/json" };
  const token = key?.trim();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

/** Best-effort webhook; never throws. No-ops when URL is unset. */
export async function postSponsorLeadWebhook(
  lead: SponsorLead,
  env: { SPONSOR_NOTIFY_WEBHOOK_URL?: string; SPONSOR_NOTIFY_WEBHOOK_KEY?: string },
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  const url = env.SPONSOR_NOTIFY_WEBHOOK_URL?.trim();
  if (!url) return;
  try {
    const res = await fetchFn(url, {
      method: "POST",
      headers: sponsorLeadWebhookHeaders(env.SPONSOR_NOTIFY_WEBHOOK_KEY),
      body: JSON.stringify(sponsorLeadWebhookPayload(lead)),
    });
    if (!res.ok) {
      console.warn("sponsor notify webhook failed", { leadId: lead.id, status: res.status });
    }
  } catch (err) {
    console.warn("sponsor notify webhook failed", err);
  }
}
