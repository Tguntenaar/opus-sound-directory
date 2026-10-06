import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-zinc-800/60">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-5">
        <Link href="/" className="text-sm font-medium tracking-tight text-zinc-100">
          Opus Sound Directory
        </Link>
        <nav className="flex items-center gap-4 text-sm" aria-label="Main">
          <Link href="/" className="text-zinc-400 hover:text-zinc-100">
            Browse
          </Link>
          <Link href="/about" className="text-zinc-500 hover:text-zinc-300">
            About
          </Link>
        </nav>
      </div>
    </header>
  );
}
