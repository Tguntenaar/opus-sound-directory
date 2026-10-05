import type { Metadata } from "next";
import { SponsorInterestForm } from "@/components/sponsor-interest-form";
import { SPONSOR_PACKAGES } from "@/lib/sponsor-packages";
import { DEFAULT_OG_IMAGE, SITE_NAME } from "@/lib/site-url";

const title = "Sponsor";
const description =
  "Featured placements and brand partnerships on the Opus Sound Directory — homepage slots, category takeovers, and model packs.";

export const metadata: Metadata = {
  title,
  description,
  openGraph: {
    title: `${title} · ${SITE_NAME}`,
    description,
    url: "/sponsor",
    images: [{ url: DEFAULT_OG_IMAGE, width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: `${title} · ${SITE_NAME}`,
    description,
    images: [DEFAULT_OG_IMAGE],
  },
};

export default function SponsorPage() {
  return (
    <div className="space-y-14">
      <section className="max-w-2xl">
        <p className="text-sm font-medium uppercase tracking-wider text-violet-400">Partnerships</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-50 sm:text-4xl">
          Put your brand next to Opus-generated sound
        </h1>
        <p className="mt-4 text-zinc-400 leading-relaxed">
          Editors and producers browse here before they commit beds and SFX to a timeline. Sponsorship
          works like paid directory inventory — featured slots, category shelves, and co-built sound
          packs — not display ads. Tell us what you want; we reply with availability and an invoice
          (no checkout on this page).
        </p>
      </section>

      <section aria-labelledby="packages-heading">
        <h2 id="packages-heading" className="text-xl font-semibold text-zinc-100">
          Packages
        </h2>
        <p className="mt-2 text-sm text-zinc-500">
          Mix and match — most partners start with one slot and expand after the first month.
        </p>
        <ul className="mt-6 grid gap-4 sm:grid-cols-2">
          {SPONSOR_PACKAGES.map((pkg) => (
            <li
              key={pkg.id}
              className="flex flex-col rounded-xl border border-zinc-800 bg-zinc-900/30 p-5"
            >
              <h3 className="font-medium text-zinc-50">{pkg.name}</h3>
              <p className="mt-1 text-sm text-violet-300/90">{pkg.tagline}</p>
              <ul className="mt-4 flex-1 space-y-2 text-sm text-zinc-400">
                {pkg.bullets.map((b) => (
                  <li key={b} className="flex gap-2">
                    <span className="text-violet-500" aria-hidden>·</span>
                    {b}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </section>

      <section
        className="relative rounded-2xl border border-zinc-800 bg-zinc-900/20 p-6 sm:p-8"
        aria-labelledby="inquiry-heading"
      >
        <h2 id="inquiry-heading" className="text-xl font-semibold text-zinc-100">
          Company inquiry
        </h2>
        <p className="mt-2 text-sm text-zinc-500">
          Share your goals and we&apos;ll follow up with inventory, pricing, and a simple insertion order.
        </p>
        <div className="mt-8">
          <SponsorInterestForm />
        </div>
      </section>
    </div>
  );
}
