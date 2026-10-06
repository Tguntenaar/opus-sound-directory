import Link from "next/link";
import { AudioLines, BookOpen, Info, LayoutGrid } from "lucide-react";
import { IconTooltip } from "@/components/icon-tooltip";

export function SiteHeader() {
  return (
    <header className="border-b border-zinc-800/60">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-5">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-medium tracking-tight text-zinc-100 transition-colors hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
        >
          <AudioLines className="h-4 w-4 text-violet-400/90" aria-hidden />
          Opus Sound Directory
        </Link>
        <nav className="flex items-center gap-1 text-sm" aria-label="Main">
          <IconTooltip label="Browse sounds">
            <Link
              href="/"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-400 transition-colors hover:bg-zinc-900/80 hover:text-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
              aria-label="Browse sounds"
            >
              <LayoutGrid className="h-4 w-4" aria-hidden />
            </Link>
          </IconTooltip>
          <IconTooltip label="Blog">
            <Link
              href="/blog"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-900/80 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
              aria-label="Blog"
            >
              <BookOpen className="h-4 w-4" aria-hidden />
            </Link>
          </IconTooltip>
          <IconTooltip label="About">
            <Link
              href="/about"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-900/80 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
              aria-label="About"
            >
              <Info className="h-4 w-4" aria-hidden />
            </Link>
          </IconTooltip>
        </nav>
      </div>
    </header>
  );
}
