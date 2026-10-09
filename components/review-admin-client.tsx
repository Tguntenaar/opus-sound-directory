"use client";

import { useCallback, useState } from "react";
import { Button } from "@/components/ui/button";

type Submission = {
  id: string;
  title: string;
  status: string;
  source: string;
  createdAt: string;
  category: string;
  screening?: { spam?: boolean; bannedPatterns?: string[]; suspiciousClaims?: string[] };
  aiReview?: { verdict: string; quality: number; reasons: string[] };
  communitySlug?: string;
  reviewerNote?: string;
  ownerId?: string;
  notification?: { status: string };
};

export function ReviewAdminClient() {
  const [token, setToken] = useState("");
  const [items, setItems] = useState<Submission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/review", {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = (await res.json()) as { submissions?: Submission[]; error?: string };
      if (!res.ok) {
        setError(data.error ?? "Unauthorized");
        setItems([]);
        return;
      }
      setItems(data.submissions ?? []);
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  }, [token]);

  async function act(
    action: "reject" | "approve" | "unpublish",
    submissionId: string,
    communitySlug?: string,
  ) {
    const note =
      action === "reject"
        ? window.prompt("Rejection note (optional)") ?? ""
        : "";
    await fetch("/api/admin/review", {
      method: "POST",
      credentials: "include",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action, submissionId, communitySlug, note }),
    });
    await load();
  }

  return (
    <div className="mt-6 flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        <input
          type="password"
          placeholder="REVIEW_ADMIN_TOKEN"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="min-w-[12rem] flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200"
        />
        <Button type="button" onClick={() => void load()} disabled={loading}>
          {loading ? "Loading…" : "Load queue"}
        </Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <ul className="flex flex-col gap-3">
        {items.map((s) => (
          <li
            key={s.id}
            className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 text-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium text-zinc-100">{s.title}</p>
                <p className="text-xs text-zinc-500">
                  {s.status} · {s.source} · {s.category} · {new Date(s.createdAt).toLocaleString()}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {s.status === "pending_review" && (
                  <>
                    <Button type="button" size="sm" onClick={() => void act("approve", s.id)}>
                      Approve note
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => void act("reject", s.id)}
                    >
                      Reject
                    </Button>
                  </>
                )}
                {s.communitySlug && (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => void act("unpublish", s.id, s.communitySlug)}
                  >
                    Unpublish
                  </Button>
                )}
              </div>
            </div>
            {s.aiReview && (
              <p className="mt-2 text-xs text-zinc-400">
                AI: {s.aiReview.verdict} · quality {s.aiReview.quality} —{" "}
                {s.aiReview.reasons.join("; ")}
              </p>
            )}
            {s.screening?.suspiciousClaims?.length ? (
              <p className="mt-1 text-xs text-amber-500/90">
                Flags: {s.screening.suspiciousClaims.join(", ")}
              </p>
            ) : null}
            <p className="mt-1 text-xs text-zinc-500">Account: {s.ownerId || "Legacy submission"} · Warning email: {s.notification?.status || "Not sent"}</p>
            {s.reviewerNote && (
              <p className="mt-1 text-xs text-zinc-500">Note: {s.reviewerNote}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
