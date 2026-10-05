import Link from "next/link";

const links = [
  { href: "/", label: "Browse" },
  { href: "/about", label: "About" },
  { href: "/submit", label: "Submit" },
];

export function SiteHeader() {
  return (
    <header className="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
        <Link href="/" className="group flex flex-col gap-0.5">
          <span className="text-lg font-semibold tracking-tight text-zinc-50">
            Opus Sound Directory
          </span>
          <span className="text-xs text-zinc-500 group-hover:text-zinc-400">
            Synthesised beds & SFX — human taste still required
          </span>
        </Link>
        <nav className="flex items-center gap-1 sm:gap-2" aria-label="Main">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="rounded-md px-3 py-2 text-sm text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
