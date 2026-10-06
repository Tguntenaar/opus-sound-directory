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
          <main className="mx-auto max-w-6xl px-4 py-12 sm:py-16">{children}</main>
          <footer className="border-t border-zinc-900/80 py-8">
            <nav
              className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-5 gap-y-1 px-4 text-xs text-zinc-600"
              aria-label="Footer"
            >
              <a href="/submit" className="hover:text-zinc-400">Submit</a>
              <span className="text-zinc-800" aria-hidden>·</span>
              <a href="/sponsor" className="hover:text-zinc-400">Sponsor</a>
              <span className="text-zinc-800" aria-hidden>·</span>
              <a href="/about" className="hover:text-zinc-400">About</a>
            </nav>
          </footer>
        </StatsProvider>
      </body>
    </html>
  );
}
