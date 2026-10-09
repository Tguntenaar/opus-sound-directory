import type { SubmitEntry } from "@/lib/submit-types";
import { getSiteUrl, SITE_NAME } from "@/lib/site-url";

export function submissionWarningText(entry: SubmitEntry): string {
  return [
    `Sound submission needs attention: ${entry.title}`,
    `Submission: ${entry.id}`,
    `Status: ${entry.status}`,
    `Account: ${entry.ownerId || "legacy submission without an account"}`,
    `Contact: ${entry.email}`,
    `Review: ${getSiteUrl()}/admin/review`,
    `Reason: ${entry.reviewerNote || "Review required"}`,
    ...(entry.aiReview?.reasons || []),
    ...(entry.aiReview?.rightsConcerns || []).map(reason => `Rights concern: ${reason}`),
    ...(entry.screening?.bannedPatterns || []).map(reason => `Code flag: ${reason}`),
    ...(entry.screening?.suspiciousClaims || []).map(reason => `Claim flag: ${reason}`),
    "Automated flags are review signals, not a determination of illegality.",
    "", "Submitted prompt (untrusted content):", entry.prompt,
  ].join("\n");
}

/** Reports delivery state so missing configuration never looks like a delivered warning. */
export async function notifySubmitEntry(entry: SubmitEntry): Promise<NonNullable<SubmitEntry["notification"]>> {
  const attemptedAt = new Date().toISOString();
  try {
    const { env } = await import("cloudflare:workers");
    const config = env as typeof env & { SUBMIT_MAIL_TO?: string; SUBMIT_MAIL_FROM?: string; SPONSOR_MAIL_FROM?: string };
    const sender = config.SPONSOR_SEND_EMAIL;
    const from = config.SUBMIT_MAIL_FROM || config.SPONSOR_MAIL_FROM;
    const to = config.SUBMIT_MAIL_TO;
    if (!sender || !from || !to) return { status: "unconfigured", attemptedAt };
    const result = await sender.send({
      from: { email: from, name: SITE_NAME }, to: to.split(/[,;]/).map(value => value.trim()).filter(Boolean),
      subject: `Submission needs review [${entry.status}]: ${entry.title.replace(/[\r\n]/g, " ").slice(0, 120)}`,
      text: submissionWarningText(entry),
    });
    if (!result?.messageId) return { status: "failed", attemptedAt };
    return { status: "sent", attemptedAt };
  } catch {
    console.error("Submission warning delivery failed", { submissionId: entry.id });
    return { status: "failed", attemptedAt };
  }
}
