import type { SubmitEntry } from "@/lib/submit-types";
import { CATEGORIES } from "@/lib/categories";
import { formatMood } from "@/lib/mood";
import { SITE_NAME } from "@/lib/site-url";

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

type MailEnv = {
  SPONSOR_SEND_EMAIL?: EmailSender;
  SPONSOR_MAIL_FROM?: string;
  SPONSOR_MAIL_TO?: string;
};

async function readMailEnv(): Promise<MailEnv> {
  try {
    const { env } = await import("cloudflare:workers");
    return env as MailEnv;
  } catch {
    return {
      SPONSOR_MAIL_FROM: process.env.SPONSOR_MAIL_FROM,
      SPONSOR_MAIL_TO: process.env.SPONSOR_MAIL_TO,
    };
  }
}

/** Best-effort alert; never throws. */
export async function notifySubmitEntry(entry: SubmitEntry): Promise<void> {
  try {
    const env = await readMailEnv();
    const sender = env.SPONSOR_SEND_EMAIL;
    const from = env.SPONSOR_MAIL_FROM?.trim();
    if (!sender || !from) return;

    const to = (env.SPONSOR_MAIL_TO?.trim() || DEFAULT_NOTIFY_TO).toLowerCase();
    const cat = CATEGORIES[entry.category]?.label ?? entry.category;
    const moods = entry.mood.map(formatMood).join(", ");
    const subject = `Sound submission: ${entry.title} [${entry.status}]`;
    const text = [
      `Directory submission (${entry.id}) — ${entry.status}`,
      entry.communitySlug ? `Live: /e/${entry.communitySlug}` : null,
      ``,
      `Title: ${entry.title}`,
      `Source: ${entry.source}`,
      `Category: ${cat}`,
      `Mood: ${moods}`,
      `Email: ${entry.email}`,
      entry.codeUrl ? `Code link: ${entry.codeUrl}` : null,
      entry.codeSnippet ? `Code snippet: ${entry.codeSnippet.length} chars (see KV)` : null,
      ``,
      `Prompt:`,
      entry.prompt,
      ``,
      `Submitted: ${entry.createdAt}`,
    ]
      .filter(Boolean)
      .join("\n");

    const html = `<pre style="font-family:ui-monospace,monospace;font-size:13px">${text.replace(/</g, "&lt;")}</pre>`;

    await sender.send({
      from: { email: from, name: SITE_NAME },
      to: [{ email: to }],
      replyTo: { email: entry.email },
      subject,
      text,
      html,
    });
  } catch (err) {
    console.error("submit notify email failed", err);
  }
}
