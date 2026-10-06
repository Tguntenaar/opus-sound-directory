import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { getAllBlogPosts, getBlogPostBySlug } from "@/lib/blog";
import { renderBlogBody } from "@/lib/blog-markdown";
import { canonicalForPath } from "@/lib/site-metadata";
import { DEFAULT_OG_IMAGE, SITE_NAME } from "@/lib/site-url";
import { blogPostingJsonLd, faqPageJsonLd } from "@/lib/structured-data";
import { BlogArticleBody } from "@/components/blog-article-body";
import { JsonLd } from "@/components/json-ld";

type Props = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  return getAllBlogPosts().map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = getBlogPostBySlug(slug);
  if (!post) return { title: "Not found" };
  return {
    title: post.title,
    description: post.description,
    keywords: post.keywords,
    alternates: { canonical: canonicalForPath(`/blog/${post.slug}`) },
    openGraph: {
      type: "article",
      title: post.title,
      description: post.description,
      url: `/blog/${post.slug}`,
      publishedTime: post.date,
      images: [{ url: DEFAULT_OG_IMAGE, width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title: `${post.title} · ${SITE_NAME}`,
      description: post.description,
      images: [DEFAULT_OG_IMAGE],
    },
  };
}

function formatDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  const post = getBlogPostBySlug(slug);
  if (!post) notFound();

  const { blocks, toc, showToc } = renderBlogBody(post.body);
  const faqLd = faqPageJsonLd(post);
  const jsonLd = faqLd ? [blogPostingJsonLd(post), faqLd] : blogPostingJsonLd(post);

  return (
    <article className="page-enter mx-auto max-w-[42rem]">
      <JsonLd data={jsonLd} />
      <header className="mb-8 flex flex-col gap-3">
        <Link
          href="/blog"
          className="inline-flex w-fit items-center gap-1.5 text-sm text-violet-400 transition-colors hover:text-violet-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Blog
        </Link>
        <time dateTime={post.date} className="text-xs tabular-nums text-zinc-600">
          {formatDate(post.date)}
        </time>
        <h1 className="text-2xl font-medium tracking-tight text-zinc-50 sm:text-3xl">
          {post.title}
        </h1>
        {post.description ? (
          <p className="text-sm leading-relaxed text-zinc-500">{post.description}</p>
        ) : null}
      </header>
      <BlogArticleBody blocks={blocks} toc={toc} showToc={showToc} />
      {post.faq.length > 0 ? (
        <section className="not-prose mt-12 border-t border-zinc-800/80 pt-8">
          <h2 className="text-sm font-medium text-zinc-300">FAQ</h2>
          <dl className="mt-4 flex flex-col gap-4">
            {post.faq.map((item) => (
              <div key={item.q}>
                <dt className="text-sm font-medium text-zinc-200">{item.q}</dt>
                <dd className="mt-1 text-sm text-zinc-500">{item.a}</dd>
              </div>
            ))}
          </dl>
        </section>
      ) : null}
    </article>
  );
}
