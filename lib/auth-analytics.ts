export type SignInAttempt = {
  provider: "github" | "google";
  source: "submit" | "account";
  startedAt: number;
};

export const SIGN_IN_ATTEMPT_KEY = "opus:sign-in-attempt";

/** Only accept recent, known metadata; never retain OAuth codes or account details. */
export function parseSignInAttempt(value: string | null, now = Date.now()): SignInAttempt | null {
  if (!value) return null;
  try {
    const attempt = JSON.parse(value) as SignInAttempt;
    if (!attempt || !["github", "google"].includes(attempt.provider)
      || !["submit", "account"].includes(attempt.source)
      || typeof attempt.startedAt !== "number"
      || now < attempt.startedAt || now - attempt.startedAt > 60 * 60 * 1000) return null;
    return { provider: attempt.provider, source: attempt.source, startedAt: attempt.startedAt };
  } catch { return null; }
}
