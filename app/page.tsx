import { Suspense } from "react";
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
      <header className="max-w-xl">
        <h1 className="text-2xl font-medium tracking-tight text-balance text-zinc-50">
          Your AI video looks great. Now make it sound right.
        </h1>
        <p className="mt-2 text-sm text-balance text-zinc-400">
          Royalty-free effects and music beds, each with the prompt and code that made it, so you
          can grab one or make your own.
        </p>
      </header>
      <Suspense fallback={<BrowseGrid entries={entries} />}>
        <HomeBrowse entries={entries} />
      </Suspense>
    </div>
  );
}
