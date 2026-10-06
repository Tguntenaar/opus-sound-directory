import type { Metadata } from "next";
import Link from "next/link";
import {
  BookOpen,
  FileCode2,
  GitBranch,
  HeartHandshake,
  LayoutGrid,
  Music2,
  Scale,
  Wrench,
} from "lucide-react";
import { canonicalForPath } from "@/lib/site-metadata";
import { DEFAULT_OG_IMAGE, SITE_NAME } from "@/lib/site-url";
import { LICENSE_MIT_URL, LICENSE_SOUNDS_URL, REPO_GITHUB } from "@/lib/licenses";
import { BrandMark } from "@/components/brand-mark";
import { IconTooltip } from "@/components/icon-tooltip";
import { OwnerProfileLinks } from "@/components/owner-profile-links";
import { cn } from "@/lib/utils";

const title = "About";

export const metadata: Metadata = {
  title,
  alternates: { canonical: canonicalForPath("/about") },
  openGraph: {
    title: `${title} · ${SITE_NAME}`,
    url: "/about",
    images: [{ url: DEFAULT_OG_IMAGE, width: 1200, height: 630 }],
  },
  twitter: {
    title: `${title} · ${SITE_NAME}`,
    images: [DEFAULT_OG_IMAGE],
  },
};

const rows = [
  {
    icon: Music2,
    text: "WAV & MP3 previews, the prompt, Python synth code, and loudness metrics per entry.",
  },
  {
    icon: Wrench,
    text: "Synthesised in Python with verification (length, LUFS/peak) and fixed seeds for reproducibility.",
  },
] as const;

const links = [
  { href: "/", label: "Browse", icon: LayoutGrid },
  { href: "/submit", label: "Submit", icon: FileCode2 },
  { href: "/sponsor", label: "Sponsor", icon: HeartHandshake },
  {
    href: REPO_GITHUB,
    label: "Source on GitHub",
    icon: GitBranch,
    external: true,
  },
  { href: "/blog", label: "Blog", icon: BookOpen },
] as const;

export default function AboutPage() {
  return (
    <div className="page-enter mx-auto flex max-w-xl justify-center px-1 sm:max-w-2xl">
      <div
        className={cn(
          "about-card sound-card w-full max-w-[36rem] rounded-lg border border-zinc-800/80 bg-zinc-900/20 p-8 sm:p-10",
          "transition-[transform,box-shadow,border-color,background-color] duration-200 ease-out",
          "hover:-translate-y-0.5 hover:border-zinc-600/90 hover:bg-zinc-900/45 hover:shadow-[0_8px_30px_-12px_rgb(0_0_0/0.55)]",
          "motion-reduce:transition-none motion-reduce:hover:translate-y-0",
        )}
        style={{ animationDelay: "0ms" }}
      >
        <div
          className="about-card-section flex flex-col items-center gap-3 text-center"
          style={{ animationDelay: "45ms" }}
        >
          <BrandMark size={48} />
          <h1 className="text-lg font-medium tracking-tight text-zinc-50">{SITE_NAME}</h1>
        </div>

        <p
          className="about-card-section mt-6 text-center text-sm leading-relaxed text-balance text-zinc-400"
          style={{ animationDelay: "90ms" }}
        >
          Opus Sounds Directory helps creators and developers add sound to AI-made videos. It offers
          royalty-free effects and music beds cut to common video lengths. Every sound comes with the
          prompt, code and loudness numbers behind it, so you can use it as is or have an AI model
          make your own version.
        </p>

        <ul className="mt-8 flex flex-col gap-4" aria-label="Highlights">
          <li
            className="about-card-section flex items-start gap-3 text-sm text-zinc-400"
            style={{ animationDelay: "135ms" }}
          >
            <IconTooltip label="Code MIT · Sounds CC0">
              <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-zinc-800/80 bg-zinc-950/50 text-violet-400/90">
                <Scale className="h-4 w-4" aria-hidden />
              </span>
            </IconTooltip>
            <span className="leading-relaxed">
              <a
                href={LICENSE_MIT_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-300 underline-offset-2 hover:text-violet-200 hover:underline"
              >
                Code MIT
              </a>
              {" · "}
              <a
                href={LICENSE_SOUNDS_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-300 underline-offset-2 hover:text-violet-200 hover:underline"
              >
                Sounds CC0
              </a>
              , free for any use, no credit needed
            </span>
          </li>
          {rows.map((row, index) => (
            <li
              key={row.text.slice(0, 24)}
              className="about-card-section flex items-start gap-3 text-sm text-zinc-400"
              style={{ animationDelay: `${180 + index * 45}ms` }}
            >
              <IconTooltip label={row.text}>
                <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-zinc-800/80 bg-zinc-950/50 text-violet-400/90">
                  <row.icon className="h-4 w-4" aria-hidden />
                </span>
              </IconTooltip>
              <span className="leading-relaxed">{row.text}</span>
            </li>
          ))}
        </ul>

        <nav
          className="about-card-section mt-10 flex flex-wrap items-center justify-center gap-2 border-t border-zinc-800/60 pt-8"
          aria-label="Site links"
          style={{ animationDelay: "270ms" }}
        >
          {links.map((item) => {
            const Icon = item.icon;
            const className =
              "inline-flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-900/80 hover:text-zinc-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60";
            if ("external" in item && item.external) {
              return (
                <IconTooltip key={item.href} label={item.label}>
                  <a
                    href={item.href}
                    className={className}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={item.label}
                  >
                    <Icon className="h-4 w-4" aria-hidden />
                  </a>
                </IconTooltip>
              );
            }
            return (
              <IconTooltip key={item.href} label={item.label}>
                <Link href={item.href} className={className} aria-label={item.label}>
                  <Icon className="h-4 w-4" aria-hidden />
                </Link>
              </IconTooltip>
            );
          })}
          <OwnerProfileLinks />
        </nav>
      </div>
    </div>
  );
}
