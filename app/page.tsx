import { Suspense } from "react";
import { TrackedLink } from "@/components/tracked-link";
import { Plus } from "lucide-react";
import { getAllEntriesMerged } from "@/lib/entries";
import { homeCollectionPageJsonLd } from "@/lib/structured-data";
import { HomeBrowse } from "@/components/home-browse";
import { BrowseGrid } from "@/components/browse-grid";
import { JsonLd } from "@/components/json-ld";

export default async function HomePage() {
  const entries = await getAllEntriesMerged();

  return (
    <div className="flex flex-col gap-12">
      <JsonLd data={homeCollectionPageJsonLd(entries)} />
      <header className="flex flex-wrap items-center justify-between gap-6">
        <div className="max-w-xl">
        <h1 className="text-2xl font-medium tracking-tight text-balance text-zinc-50">
          Your AI video looks great. Now make it sound right.
        </h1>
        <p className="mt-2 text-sm text-balance text-zinc-400">
          Royalty-free effects and music beds, each with the prompt and code that made it, so you
          can grab one or make your own.
        </p>
        </div>
        <TrackedLink event="add_sound_click" eventProperties={{ placement: "home_hero" }} href="/submit" className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-lg bg-violet-500 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-violet-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-violet-400">
          <Plus className="h-4 w-4" aria-hidden="true" />
          Add your sound
        </TrackedLink>
      </header>
      <Suspense fallback={<BrowseGrid entries={entries} />}>
        <HomeBrowse entries={entries} />
      </Suspense>
    </div>
  );
}
