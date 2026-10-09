"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { captureEvent } from "@/lib/analytics-client";
import { parseSignInAttempt, SIGN_IN_ATTEMPT_KEY } from "@/lib/auth-analytics";

/** Mounted independently of the collapsed manual form and signed-in account UI. */
export function AuthCallbackAnalytics() {
  const pathname = usePathname();
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const url = new URL(window.location.href);
    const outcome = url.searchParams.get("sign_in");
    if (outcome !== "returned" && outcome !== "failed") return;
    let attempt = null;
    try {
      attempt = parseSignInAttempt(sessionStorage.getItem(SIGN_IN_ATTEMPT_KEY));
      sessionStorage.removeItem(SIGN_IN_ATTEMPT_KEY);
    } catch { /* Storage restrictions must not prevent sign-in. */ }
    // Consume synchronously, before requests, to prevent duplicate callback counting.
    url.searchParams.delete("sign_in");
    url.searchParams.delete("error");
    url.searchParams.delete("error_description");
    window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
    if (outcome === "failed") setFailed(true);
    if (!attempt) return;
    const properties = { provider: attempt.provider, source: attempt.source, stage: "callback", duration_ms: Date.now() - attempt.startedAt };
    if (outcome === "failed") {
      captureEvent("auth_sign_in_failed", { ...properties, failure_reason: "provider_callback" });
      return;
    }
    void (async () => {
      try {
        const response = await fetch("/api/account", { cache: "no-store" });
        if (!response.ok) throw new Error("session_check_failed");
        const data = await response.json() as { user: { id: string } | null };
        if (data.user) captureEvent("auth_sign_in_succeeded", properties);
        else {
          captureEvent("auth_sign_in_failed", { ...properties, failure_reason: "missing_session" });
          setFailed(true);
        }
      } catch {
        captureEvent("auth_sign_in_failed", { ...properties, failure_reason: "session_check_failed" });
        setFailed(true);
      }
    })();
  }, [pathname]);
  return failed ? <p role="alert" className="mx-auto max-w-2xl px-4 pt-4 text-sm text-amber-300">Could not complete sign-in. Please try again.</p> : null;
}
