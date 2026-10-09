import { authUnavailable, sessionContributor } from "@/lib/auth";
import { ownsSubmission } from "@/lib/submission-access";
import { NextResponse } from "next/server";
import { getSubmitEntry } from "@/lib/submit-kv";
import { submissionReviewUrl } from "@/lib/submit-pipeline";

export async function GET(request: Request) {
  let owner;
  try { owner = await sessionContributor(request); } catch { return authUnavailable(); }
  if (!owner) return NextResponse.json({ error: "Sign in to view your submissions." }, { status: 401 });
  const id = new URL(request.url).searchParams.get("id")?.trim();
  if (!id) {
    return NextResponse.json({ error: "id required" }, { status: 400 });
  }
  const entry = await getSubmitEntry(id);
  if (!entry || !ownsSubmission(entry.ownerId, owner.id)) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }
  return NextResponse.json({
    submissionId: entry.id,
    status: entry.status,
    reviewUrl: submissionReviewUrl(entry),
    reviewerNote: entry.reviewerNote,
  }, { headers: { "Cache-Control": "no-store" } });
}
