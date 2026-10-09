import Link from "next/link";
import { GithubStars } from "@/components/github-stars";
import { Info, LayoutGrid, Plug, UserRound } from "lucide-react";
import { IconTooltip } from "@/components/icon-tooltip";
import { BrandMark } from "@/components/brand-mark";
import { GlobalSearch } from "@/components/global-search";

export function SiteHeader() {
  return (
    <header className="overflow-visible border-b border-zinc-800/60">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 overflow-visible px-4 py-5">
        <Link
          href="/"
          className="group inline-flex items-center gap-2.5 text-sm font-medium tracking-tight text-zinc-100 transition-colors hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
        >
          <BrandMark size={20} interactive />
          Opus Sounds Directory
        </Link>
        <nav className="ml-auto flex items-center gap-1 overflow-visible text-sm" aria-label="Main">
          <GlobalSearch />
          <IconTooltip label="Browse sounds" side="bottom">
            <Link
              href="/"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-400 transition-colors hover:bg-zinc-900/80 hover:text-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
              aria-label="Browse sounds"
            >
              <LayoutGrid className="h-4 w-4" aria-hidden />
            </Link>
          </IconTooltip>
          <IconTooltip label="Use with your agent" side="bottom">
            <Link
              href="/agents"
              prefetch={false}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-900/80 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
              aria-label="Use with your agent"
            >
              <Plug className="h-4 w-4" aria-hidden />
            </Link>
          </IconTooltip>
          <IconTooltip label="Your account" side="bottom">
            <Link href="/account" prefetch={false} aria-label="Your account" className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"><UserRound className="h-4 w-4" aria-hidden /></Link>
          </IconTooltip>
          <IconTooltip label="About" side="bottom">
            <Link
              href="/about"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-900/80 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
              aria-label="About"
            >
              <Info className="h-4 w-4" aria-hidden />
            </Link>
          </IconTooltip>
          <GithubStars />
        </nav>
      </div>
    </header>
  );
}
