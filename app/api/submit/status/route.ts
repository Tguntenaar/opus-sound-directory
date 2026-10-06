import { NextResponse } from "next/server";
import { getSubmitEntry } from "@/lib/submit-kv";
import { submissionReviewUrl } from "@/lib/submit-pipeline";

export async function GET(request: Request) {
  const id = new URL(request.url).searchParams.get("id")?.trim();
  if (!id) {
    return NextResponse.json({ error: "id required" }, { status: 400 });
  }
  const entry = await getSubmitEntry(id);
  if (!entry) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }
  return NextResponse.json({
    submissionId: entry.id,
    status: entry.status,
    reviewUrl: submissionReviewUrl(entry),
    reviewerNote: entry.reviewerNote,
  });
}
