import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, BookOpen } from "lucide-react";
import { getAllBlogPosts } from "@/lib/blog";
import { canonicalForPath } from "@/lib/site-metadata";
import { DEFAULT_OG_IMAGE, SITE_NAME } from "@/lib/site-url";

const title = "Blog";

export const metadata: Metadata = {
  title,
  description: "Notes on synthesised audio, prompts, and video workflows.",
  alternates: { canonical: canonicalForPath("/blog") },
  openGraph: {
    title: `${title} · ${SITE_NAME}`,
    description: "Notes on synthesised audio, prompts, and video workflows.",
    url: "/blog",
    images: [{ url: DEFAULT_OG_IMAGE, width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: `${title} · ${SITE_NAME}`,
    images: [DEFAULT_OG_IMAGE],
  },
};

function formatDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function BlogIndexPage() {
  const posts = getAllBlogPosts();

  return (
    <div className="page-enter mx-auto max-w-[42rem]">
      <header className="mb-10 flex flex-col gap-3">
        <Link
          href="/"
          className="inline-flex w-fit items-center gap-1.5 text-sm text-violet-400 transition-colors hover:text-violet-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Browse
        </Link>
        <div className="flex items-center gap-2 text-zinc-50">
          <BookOpen className="h-5 w-5 text-violet-400/80" aria-hidden />
          <h1 className="text-2xl font-medium tracking-tight">Blog</h1>
        </div>
        <p className="text-sm text-zinc-500">Short notes — prompts, synth, and video timing.</p>
      </header>

      {posts.length === 0 ? (
        <p className="text-sm text-zinc-600">No posts yet.</p>
      ) : (
        <ul className="flex flex-col gap-6">
          {posts.map((post) => (
            <li key={post.slug}>
              <article className="group border-b border-zinc-800/60 pb-6 last:border-0">
                <time
                  dateTime={post.date}
                  className="text-xs tabular-nums text-zinc-600"
                >
                  {formatDate(post.date)}
                </time>
                <h2 className="mt-1 text-lg font-medium text-zinc-100 transition-colors group-hover:text-white">
                  <Link
                    href={`/blog/${post.slug}`}
                    className="focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
                  >
                    {post.title}
                  </Link>
                </h2>
                <p className="mt-1.5 text-sm leading-relaxed text-zinc-500">{post.description}</p>
              </article>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
