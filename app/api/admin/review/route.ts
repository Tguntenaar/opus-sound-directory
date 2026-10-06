import { NextResponse } from "next/server";
import { unpublishCommunityEntry } from "@/lib/community-kv";
import { publishSubmissionAsCommunity } from "@/lib/submit-pipeline";
import { isReviewAuthorized } from "@/lib/review-auth";
import { listSubmitEntries, updateSubmitEntry } from "@/lib/submit-kv";

export async function GET(request: Request) {
  if (!(await isReviewAuthorized(request))) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const submissions = await listSubmitEntries(150);
  return NextResponse.json({ submissions });
}

export async function POST(request: Request) {
  if (!(await isReviewAuthorized(request))) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }
  const b = body as Record<string, unknown>;
  const action = b.action;
  const submissionId = typeof b.submissionId === "string" ? b.submissionId : "";
  const note = typeof b.note === "string" ? b.note.slice(0, 2000) : "";

  if (action === "reject" && submissionId) {
    await updateSubmitEntry(submissionId, {
      status: "rejected",
      reviewerNote: note || "Rejected by admin",
    });
    return NextResponse.json({ ok: true });
  }

  if (action === "approve" && submissionId) {
    const slug = await publishSubmissionAsCommunity(submissionId);
    if (!slug) {
      return NextResponse.json({ error: "Submission not found" }, { status: 404 });
    }
    await updateSubmitEntry(submissionId, {
      reviewerNote: note || "Approved and published by admin",
    });
    return NextResponse.json({ ok: true, communitySlug: slug });
  }

  if (action === "unpublish" && typeof b.communitySlug === "string") {
    await unpublishCommunityEntry(b.communitySlug);
    return NextResponse.json({ ok: true });
  }

  return NextResponse.json({ error: "Unknown action" }, { status: 400 });
}
