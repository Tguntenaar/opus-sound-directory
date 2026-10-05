import "./globals.css";
import { SiteHeader } from "@/components/site-header";
import { StatsProvider } from "@/components/stats-provider";
import { rootSiteMetadata } from "@/lib/site-metadata";

export const metadata = rootSiteMetadata();

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 antialiased">
        <StatsProvider>
          <SiteHeader />
          <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
          <footer className="border-t border-zinc-900 py-10 text-center text-xs text-zinc-600">
            <p className="mb-4">
              <a
                href="/sponsor"
                className="inline-flex items-center justify-center rounded-lg border border-violet-500/40 bg-violet-500/10 px-4 py-2 text-sm font-medium text-violet-200 hover:border-violet-400/60 hover:bg-violet-500/15"
              >
                Sponsor the directory
              </a>
            </p>
            <nav className="mb-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2" aria-label="Footer">
              <a href="/about" className="text-zinc-500 hover:text-zinc-300">About</a>
              <a href="/submit" className="text-zinc-500 hover:text-zinc-300">Submit</a>
              <a href="/sponsor" className="text-zinc-500 hover:text-zinc-300">Sponsors</a>
            </nav>
            Sounds are synthesized for video timing — not realistic instruments or vocals.
            Royalty-free stubs; verify in your mix.
          </footer>
        </StatsProvider>
      </body>
    </html>
  );
}
