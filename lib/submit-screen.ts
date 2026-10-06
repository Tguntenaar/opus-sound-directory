import type { ScreeningFlags, SubmitEntryInput } from "@/lib/submit-types";

const BANNED_PATTERNS: { re: RegExp; label: string }[] = [
  { re: /\bos\.system\b/i, label: "os.system" },
  { re: /\bsubprocess\b/i, label: "subprocess" },
  { re: /\brequests\b/i, label: "requests" },
  { re: /\bsocket\b/i, label: "socket" },
  { re: /\beval\s*\(/i, label: "eval(" },
  { re: /\bexec\s*\(/i, label: "exec(" },
  { re: /\b__import__\s*\(/i, label: "__import__(" },
  { re: /\burllib\.request\b/i, label: "urllib.request" },
  { re: /\bhttpx\b/i, label: "httpx" },
  { re: /\bopen\s*\([^)]*["']wb["']/i, label: "binary write" },
];

const OPUS_CLAIM_RE =
  /\b(claude\s+opus|opus\s+5\.?5|generated\s+by\s+opus|made\s+by\s+opus)\b/i;

const SPAM_LINK_RE = /(https?:\/\/[^\s]+){6,}/i;

export type StaticScreenResult =
  | { ok: true; flags: ScreeningFlags }
  | { ok: false; reason: string; flags: ScreeningFlags };

export function staticScreenSubmission(input: SubmitEntryInput): StaticScreenResult {
  const flags: ScreeningFlags = { notes: [] };
  const code = resolveCode(input);
  const haystack = `${input.title}\n${input.prompt}\n${code ?? ""}`;

  const banned: string[] = [];
  for (const { re, label } of BANNED_PATTERNS) {
    if (re.test(haystack)) banned.push(label);
  }
  if (banned.length) flags.bannedPatterns = banned;

  const suspiciousClaims: string[] = [];
  if (OPUS_CLAIM_RE.test(haystack)) {
    suspiciousClaims.push("opus_attribution_claim");
  }
  if (suspiciousClaims.length) flags.suspiciousClaims = suspiciousClaims;

  if (SPAM_LINK_RE.test(input.prompt) || SPAM_LINK_RE.test(input.title)) {
    flags.spam = true;
    flags.notes?.push("excessive_links");
  }
  if (input.prompt.length > 8000 || input.title.length > 160) {
    return { ok: false, reason: "Field length exceeded", flags };
  }
  if (code && code.length > 100_000) {
    return { ok: false, reason: "Code exceeds 100 KB", flags };
  }
  if (code && /[\x00-\x08\x0e-\x1f]/.test(code)) {
    return { ok: false, reason: "Code must be text only", flags };
  }

  if (banned.length) {
    return {
      ok: false,
      reason: `Blocked patterns in submission: ${banned.join(", ")}`,
      flags,
    };
  }

  return { ok: true, flags };
}

export function resolveCode(input: SubmitEntryInput): string | undefined {
  if (input.code?.trim()) return input.code.trim();
  if (input.codeSnippet?.trim()) return input.codeSnippet.trim();
  return undefined;
}
