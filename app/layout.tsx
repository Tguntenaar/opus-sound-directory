import "./globals.css";
import { SiteHeader } from "@/components/site-header";
import { StatsProvider } from "@/components/stats-provider";
import { PlaybackShortcuts } from "@/components/playback-shortcuts";
import { rootSiteMetadata } from "@/lib/site-metadata";
import { rootWebSiteJsonLd, organizationJsonLd } from "@/lib/structured-data";
import { JsonLd } from "@/components/json-ld";
import { FileUp, HeartHandshake, Info } from "lucide-react";
import { IconTooltip } from "@/components/icon-tooltip";

export const metadata = rootSiteMetadata();

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 antialiased">
        <JsonLd data={[rootWebSiteJsonLd(), organizationJsonLd()]} />
        <StatsProvider>
          <PlaybackShortcuts />
          <SiteHeader />
          <main className="page-enter mx-auto max-w-6xl px-4 py-12 sm:py-16">{children}</main>
          <footer className="border-t border-zinc-900/80 py-8">
            <nav
              className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-3 px-4 text-xs text-zinc-600"
              aria-label="Footer"
            >
              <IconTooltip label="Submit a sound">
                <a
                  href="/submit"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-zinc-900/60 hover:text-zinc-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
                  aria-label="Submit a sound"
                >
                  <FileUp className="h-4 w-4" aria-hidden />
                </a>
              </IconTooltip>
              <IconTooltip label="Sponsor">
                <a
                  href="/sponsor"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-zinc-900/60 hover:text-zinc-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
                  aria-label="Sponsor"
                >
                  <HeartHandshake className="h-4 w-4" aria-hidden />
                </a>
              </IconTooltip>
              <IconTooltip label="About">
                <a
                  href="/about"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-zinc-900/60 hover:text-zinc-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
                  aria-label="About"
                >
                  <Info className="h-4 w-4" aria-hidden />
                </a>
              </IconTooltip>
            </nav>
          </footer>
        </StatsProvider>
      </body>
    </html>
  );
}
