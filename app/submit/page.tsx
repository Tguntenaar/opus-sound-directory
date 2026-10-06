import type { Metadata } from "next";
import Link from "next/link";
import { SubmitEntryForm } from "@/components/submit-entry-form";
import { canonicalForPath } from "@/lib/site-metadata";
import { DEFAULT_OG_IMAGE, SITE_NAME } from "@/lib/site-url";

const title = "Submit";
const description =
  "Propose a synthesised sound for the directory — prompt, optional code, and contact details.";

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
    <div className="mx-auto max-w-lg">
      <h1 className="text-3xl font-semibold text-zinc-50">Submit an entry</h1>
      <p className="mt-2 text-sm text-zinc-500">
        Share a prompt and optional synthesis code. We store submissions securely and email the
        maintainers. For full control, you can also{" "}
        <Link
          href="https://github.com/Tguntenaar/opus-sound-directory"
          className="text-violet-400 hover:text-violet-300"
          target="_blank"
          rel="noopener noreferrer"
        >
          open a PR on GitHub
        </Link>
        .
      </p>

      <div className="mt-8">
        <SubmitEntryForm />
      </div>
    </div>
  );
}
