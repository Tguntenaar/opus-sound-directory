/** Default lead-alert inbox: Olivier first, then Thomas. */
export const DEFAULT_NOTIFY_TO = [
  "olivierguntenaar@gmail.com",
  "thomas@guntenaar.org",
] as const;

/** Comma/semicolon list → trim, lowercase, dedupe, drop empties. Unset/empty → defaults. */
export function parseNotifyRecipients(raw?: string | null): string[] {
  const seen = new Set<string>();
  const recipients: string[] = [];
  for (const part of (raw ?? "").split(/[,;]/)) {
    const email = part.trim().toLowerCase();
    if (!email || seen.has(email)) continue;
    seen.add(email);
    recipients.push(email);
  }
  return recipients.length > 0 ? recipients : [...DEFAULT_NOTIFY_TO];
}
