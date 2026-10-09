import type { Metadata } from "next";
import { TrackedLink } from "@/components/tracked-link";
import { Plug, ArrowRight } from "lucide-react";
import { ManualSubmission } from "@/components/manual-submission";
import { canonicalForPath } from "@/lib/site-metadata";
import { DEFAULT_OG_IMAGE, SITE_NAME } from "@/lib/site-url";

const title = "Submit";
const description =
  "Propose a synthesised sound for the directory — prompt, synthesis code, and your contributor account.";

export const metadata: Metadata = {
  title,
  description,
  alternates: { canonical: canonicalForPath("/submit") },
  openGraph: {
    title: `${title} · ${SITE_NAME}`,
    description,
    url: "/submit",
    images: [{ url: DEFAULT_OG_IMAGE, width: 1200, height: 630 }],
  },
};

export default function SubmitPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">Add your sound</h1>
        <p className="text-sm text-zinc-400">Sign in first. Then submit with your agent or manually.</p>
      </header>

      <section className="space-y-5 rounded-2xl border border-violet-500/30 bg-violet-500/5 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-lg font-medium text-zinc-100"><Plug className="h-5 w-5 text-violet-300" aria-hidden="true" />Use your agent</h2>
          <span className="rounded-full bg-violet-500/15 px-3 py-1 text-xs font-medium text-violet-300">Quickest · MCP</span>
        </div>
        <p className="text-sm text-zinc-400">Let your agent send the prompt, code and sound details.</p>
        <ol className="space-y-3 text-sm text-zinc-300">
          <li className="flex items-center gap-3"><span className="text-xs text-violet-400">01</span>Sign in and create an agent token.</li>
          <li className="flex items-center gap-3"><span className="text-xs text-violet-400">02</span>Connect MCP with your token.</li>
          <li className="flex items-center gap-3"><span className="text-xs text-violet-400">03</span>Ask your agent to submit your sound.</li>
        </ol>
        <div className="flex flex-wrap items-center gap-4">
          <TrackedLink event="submit_agent_token_click" eventProperties={{ source: "submit_page" }} href="/account" className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-violet-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-violet-400">Get an agent token<ArrowRight className="h-4 w-4" aria-hidden="true" /></TrackedLink>
          <TrackedLink event="submit_agent_setup_click" eventProperties={{ source: "submit_page" }} href="/agents" className="text-sm text-zinc-400 transition-colors hover:text-zinc-100">MCP setup →</TrackedLink>
        </div>
      </section>

      <ManualSubmission />
      <p className="text-xs text-zinc-500">Submissions are reviewed before publishing.</p>
    </div>
  );
}
