import { authUnavailable, sessionContributor, sameOriginMutation } from "@/lib/auth";
import { SubmissionRateLimitError } from "@/lib/submit-kv";
import { NextResponse } from "next/server";
import { scheduleBackground } from "@/lib/schedule-background";
import {
  saveSubmitEntry,
} from "@/lib/submit-kv";
import { isSubmitHoneypotDiscard, validateSubmitPayload } from "@/lib/submit-validate";
import { captureServerEvent, hashDistinctSuffix } from "@/lib/posthog-server";

function clientFingerprint(request: Request): string {
  const ip =
    request.headers.get("cf-connecting-ip") ??
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "unknown";
  return ip.slice(0, 120);
}

export async function POST(request: Request) {
  if (!sameOriginMutation(request)) return NextResponse.json({ error: "Invalid origin" }, { status: 403 });
  let owner;
  try { owner = await sessionContributor(request); } catch { return authUnavailable(); }
  if (!owner) return NextResponse.json({ error: "Sign in to submit a sound." }, { status: 401 });
  if (!owner.emailVerified) return NextResponse.json({ error: "Verify your email with your sign-in provider before submitting." }, { status: 403 });
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON" }, { status: 400 });
  }

  const result = validateSubmitPayload({ ...(body && typeof body === "object" ? body : {}), email: owner.email });
  if (!result.ok) {
    return NextResponse.json({ ok: false, error: result.error }, { status: 400 });
  }

  if (isSubmitHoneypotDiscard(result.data)) {
    return NextResponse.json({ ok: true });
  }

  const fingerprint = clientFingerprint(request);
  let entry;
  try { entry = await saveSubmitEntry(result.data, "web", owner); }
  catch (error) {
    if (error instanceof SubmissionRateLimitError) return NextResponse.json({ error: "Too many submissions — try again in an hour." }, { status: 429 });
    return authUnavailable();
  }
  const { runSubmissionPipeline } = await import("@/lib/submit-pipeline");
  scheduleBackground(runSubmissionPipeline(entry.id));

  scheduleBackground(
    hashDistinctSuffix(fingerprint).then((suffix) =>
      captureServerEvent({
        distinctId: `submit:${suffix}`,
        event: "submit_form_submit",
        properties: {
          submission_id: entry.id,
          source: "web",
          category: entry.category,
          mood_count: entry.mood.length,
        },
      }),
    ),
  );

  return NextResponse.json({
    ok: true,
    id: entry.id,
    submissionId: entry.id,
    status: entry.status,
  });
}
