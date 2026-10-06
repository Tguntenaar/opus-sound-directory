import type { Metadata } from "next";
import Link from "next/link";
import { getSiteUrl } from "@/lib/site-url";

export const metadata: Metadata = {
  title: "Not found",
  alternates: { canonical: getSiteUrl() },
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center">
      <p className="text-5xl font-light text-zinc-700" aria-hidden>404</p>
      <h1 className="text-xl font-medium text-zinc-100">Page not found</h1>
      <p className="text-sm text-zinc-500">
        That URL isn&apos;t in the directory. Head back to browse sounds.
      </p>
      <Link
        href="/"
        className="mt-2 rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:border-violet-500/50 hover:text-violet-200"
      >
        Back home
      </Link>
    </div>
  );
}
