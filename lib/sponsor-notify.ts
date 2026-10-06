import type { SponsorLead } from "@/lib/sponsor-types";
import { BUDGET_RANGES, SPONSOR_PACKAGES } from "@/lib/sponsor-packages";
import { SITE_NAME } from "@/lib/site-url";
import { sponsorNotifySkipReason } from "@/lib/sponsor-notify-skip";

const DEFAULT_NOTIFY_TO = "thomas@guntenaar.org";

type EmailSender = {
  send: (message: {
    from: { email: string; name?: string };
    to: { email: string }[];
    subject: string;
    text: string;
    html?: string;
    replyTo?: { email: string; name?: string };
  }) => Promise<unknown>;
};

type SponsorMailEnv = {
  SPONSOR_SEND_EMAIL?: EmailSender;
  SPONSOR_MAIL_FROM?: string;
  SPONSOR_MAIL_TO?: string;
};

async function readMailEnv(): Promise<SponsorMailEnv> {
  try {
    const { env } = await import("cloudflare:workers");
    return env as SponsorMailEnv;
  } catch {
    return {
      SPONSOR_MAIL_FROM: process.env.SPONSOR_MAIL_FROM,
      SPONSOR_MAIL_TO: process.env.SPONSOR_MAIL_TO,
    };
  }
}

function packageLabels(ids: string[]): string {
  const map = new Map(SPONSOR_PACKAGES.map((p) => [p.id, p.name]));
  return ids.map((id) => map.get(id) ?? id).join(", ");
}

function budgetLabel(value: string): string {
  return BUDGET_RANGES.find((b) => b.value === value)?.label ?? value;
}

/** Best-effort alert; never throws. Skips when send binding or FROM address is missing. */
export async function notifySponsorLead(lead: SponsorLead): Promise<void> {
  try {
    const env = await readMailEnv();
    const skip = sponsorNotifySkipReason(env);
    if (skip) {
      console.warn("sponsor notify skipped", { leadId: lead.id, reason: skip });
      return;
    }
    const sender = env.SPONSOR_SEND_EMAIL;
    const from = env.SPONSOR_MAIL_FROM?.trim();
    if (!sender || !from) return;

    const to = (env.SPONSOR_MAIL_TO?.trim() || DEFAULT_NOTIFY_TO).toLowerCase();
    const subject = `Sponsor lead: ${lead.companyName}`;
    const text = [
      `New sponsor inquiry (${lead.id})`,
      ``,
      `Company: ${lead.companyName}`,
      `Website: ${lead.website}`,
      `Contact: ${lead.contactName}`,
      `Email: ${lead.email}`,
      `Packages: ${packageLabels(lead.packages)}`,
      `Budget: ${budgetLabel(lead.budgetRange)}`,
      lead.ref ? `Ref: ${lead.ref}` : null,
      lead.logoUrl ? `Logo: ${lead.logoUrl}` : null,
      ``,
      lead.message,
      ``,
      `Submitted: ${lead.createdAt}`,
    ]
      .filter(Boolean)
      .join("\n");

    const html = `<pre style="font-family:ui-monospace,monospace;font-size:13px">${text.replace(/</g, "&lt;")}</pre>`;

    await sender.send({
      from: { email: from, name: SITE_NAME },
      to: [{ email: to }],
      replyTo: { email: lead.email, name: lead.contactName },
      subject,
      text,
      html,
    });
  } catch (err) {
    console.error("sponsor notify email failed", err);
  }
}
