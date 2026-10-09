import { TrackedLink } from "@/components/tracked-link";
import type { Viewport } from "next";
import "./globals.css";
import { SiteHeader } from "@/components/site-header";
import { StatsProvider } from "@/components/stats-provider";
import { PlaybackShortcuts } from "@/components/playback-shortcuts";
import { LandingSting } from "@/components/landing-sting";
import { rootSiteMetadata } from "@/lib/site-metadata";
import { rootWebSiteJsonLd, organizationJsonLd } from "@/lib/structured-data";
import { JsonLd } from "@/components/json-ld";
import { FileUp, HeartHandshake, Info } from "lucide-react";
import { IconTooltip } from "@/components/icon-tooltip";
import { OwnerProfileLinks } from "@/components/owner-profile-links";
import { PosthogProvider } from "@/components/posthog-provider";
import { ClickNotes } from "@/components/click-notes";

export const metadata = rootSiteMetadata();

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f4f5" },
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 antialiased">
        <ClickNotes />
        <JsonLd data={[rootWebSiteJsonLd(), organizationJsonLd()]} />
        <PosthogProvider>
          <StatsProvider>
          <PlaybackShortcuts />
          <LandingSting />
          <SiteHeader />
          <main className="page-enter mx-auto max-w-6xl px-4 py-12 sm:py-16">{children}</main>
          <footer className="border-t border-zinc-900/80 py-8">
            <nav
              className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-3 px-4 text-xs text-zinc-400"
              aria-label="Footer"
            >
              <IconTooltip label="Submit a sound">
                <TrackedLink
                  event="add_sound_click"
                  eventProperties={{ placement: "footer" }}
                  href="/submit"
                  className="inline-flex h-10 w-10 items-center justify-center rounded-lg transition-colors hover:bg-zinc-900/60 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
                  aria-label="Submit a sound"
                >
                  <FileUp className="h-4 w-4" aria-hidden />
                </TrackedLink>
              </IconTooltip>
              <IconTooltip label="Sponsor">
                <a
                  href="/sponsor"
                  className="inline-flex h-10 w-10 items-center justify-center rounded-lg transition-colors hover:bg-zinc-900/60 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
                  aria-label="Sponsor"
                >
                  <HeartHandshake className="h-4 w-4" aria-hidden />
                </a>
              </IconTooltip>
              <IconTooltip label="About">
                <a
                  href="/about"
                  className="inline-flex h-10 w-10 items-center justify-center rounded-lg transition-colors hover:bg-zinc-900/60 hover:text-zinc-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
                  aria-label="About"
                >
                  <Info className="h-4 w-4" aria-hidden />
                </a>
              </IconTooltip>
              <span className="text-zinc-800" aria-hidden>
                ·
              </span>
              <OwnerProfileLinks variant="footer" />
            </nav>
          </footer>
          </StatsProvider>
        </PosthogProvider>
      </body>
    </html>
  );
}
