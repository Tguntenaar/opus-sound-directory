import type { Metadata } from "next";
import "./globals.css";
import { SiteHeader } from "@/components/site-header";
import { StatsProvider } from "@/components/stats-provider";

export const metadata: Metadata = {
  title: "Opus Sound Directory",
  description:
    "Browsable directory of Claude Opus–generated synthesised audio: prompts, code, spectrograms, and measured loudness.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 antialiased">
        <StatsProvider>
          <SiteHeader />
          <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
          <footer className="border-t border-zinc-900 py-8 text-center text-xs text-zinc-600">
            Sounds are synthesised for video timing — not realistic instruments or vocals.
            Royalty-free stubs; verify in your mix.
          </footer>
        </StatsProvider>
      </body>
    </html>
  );
}
