export type SponsorNotifyMailProbe = {
  SPONSOR_SEND_EMAIL?: unknown;
  SPONSOR_MAIL_FROM?: string;
};

/** Why an alert was skipped. Null means send can proceed. */
export function sponsorNotifySkipReason(env: SponsorNotifyMailProbe): string | null {
  if (!env.SPONSOR_SEND_EMAIL) return "missing SPONSOR_SEND_EMAIL binding";
  if (!env.SPONSOR_MAIL_FROM?.trim()) return "missing SPONSOR_MAIL_FROM";
  return null;
}
