import { authUnavailable, sessionContributor } from "@/lib/auth";
import { listOwnedSubmissions } from "@/lib/submit-kv";
import { submissionReviewUrl } from "@/lib/submit-pipeline";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    const user = await sessionContributor(request);
    if (!user) return Response.json({ error: "Sign in to view your submissions." }, { status: 401 });
    const entries = await listOwnedSubmissions(user.id);
    return Response.json({ submissions: entries.map(entry => ({
      id: entry.id, title: entry.title, status: entry.status, createdAt: entry.createdAt,
      reviewUrl: submissionReviewUrl(entry), reviewerNote: entry.reviewerNote,
    })) }, { headers: { "Cache-Control": "no-store" } });
  } catch { return authUnavailable(); }
}
