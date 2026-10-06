import type { BlogBlock, BlogTocItem } from "@/lib/blog-markdown";
import { getEntryById } from "@/lib/entries";
import { BlogEntryEmbed } from "@/components/blog-entry-embed";

type Props = {
  blocks: BlogBlock[];
  toc: BlogTocItem[];
  showToc: boolean;
};

export function BlogArticleBody({ blocks, toc, showToc }: Props) {
  return (
    <div className="blog-article flex flex-col gap-0">
      {showToc ? (
        <nav
          aria-label="Table of contents"
          className="not-prose mb-8 rounded-lg border border-zinc-800/80 bg-zinc-900/20 px-4 py-3 text-sm"
        >
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">On this page</p>
          <ol className="flex flex-col gap-1.5 text-zinc-400">
            {toc.map((item) => (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  className="text-violet-400/90 transition-colors hover:text-violet-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
                >
                  {item.text}
                </a>
              </li>
            ))}
          </ol>
        </nav>
      ) : null}
      {blocks.map((block, i) => {
        if (block.type === "entry") {
          const entry = getEntryById(block.entryId);
          if (!entry) {
            return (
              <p key={i} className="text-sm text-zinc-500">
                Sound entry not found: {block.entryId}
              </p>
            );
          }
          return <BlogEntryEmbed key={i} entry={entry} />;
        }
        return (
          <div
            key={i}
            className="blog-prose"
            dangerouslySetInnerHTML={{ __html: block.html }}
          />
        );
      })}
    </div>
  );
}
