import type { Metadata } from "next";
import { ReviewAdminClient } from "@/components/review-admin-client";

export const metadata: Metadata = {
  title: "Review",
  robots: { index: false, follow: false },
};

export default function ReviewAdminPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold text-zinc-50">Submission review</h1>
      <p className="mt-2 text-sm text-zinc-500">
        Protected queue for web and MCP submissions. Auto-published community entries can be
        unpublished here. Token via <code className="text-zinc-400">?token=</code> or Bearer header.
      </p>
      <ReviewAdminClient />
    </div>
  );
}
