import { NextResponse } from "next/server";
import { scheduleBackground } from "@/lib/schedule-background";
import {
  checkSubmitRateLimit,
  saveSubmitEntry,
  touchSubmitRateLimit,
} from "@/lib/submit-kv";
import { notifySubmitEntry } from "@/lib/submit-notify";
import { isSubmitHoneypotDiscard, validateSubmitPayload } from "@/lib/submit-validate";

function clientFingerprint(request: Request): string {
  const ip =
    request.headers.get("cf-connecting-ip") ??
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "unknown";
  return ip.slice(0, 120);
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON" }, { status: 400 });
  }

  const result = validateSubmitPayload(body);
  if (!result.ok) {
    return NextResponse.json({ ok: false, error: result.error }, { status: 400 });
  }

  if (isSubmitHoneypotDiscard(result.data)) {
    return NextResponse.json({ ok: true });
  }

  const fingerprint = clientFingerprint(request);
  const allowed = await checkSubmitRateLimit(fingerprint);
  if (!allowed) {
    return NextResponse.json(
      { ok: false, error: "Too many submissions — try again in an hour." },
      { status: 429 },
    );
  }

  const entry = await saveSubmitEntry(result.data, "web");
  await touchSubmitRateLimit(fingerprint);
  const { runSubmissionPipeline } = await import("@/lib/submit-pipeline");
  scheduleBackground(runSubmissionPipeline(entry.id));

  return NextResponse.json({
    ok: true,
    id: entry.id,
    submissionId: entry.id,
    status: entry.status,
  });
}
