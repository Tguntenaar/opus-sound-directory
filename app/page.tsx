import { getAllEntries } from "@/lib/entries";
import { homeCollectionPageJsonLd } from "@/lib/structured-data";
import { BrowseGrid } from "@/components/browse-grid";
import { JsonLd } from "@/components/json-ld";

export default function HomePage() {
  const entries = getAllEntries();

  return (
    <div className="flex flex-col gap-12">
      <JsonLd data={homeCollectionPageJsonLd(entries)} />
      <header className="max-w-xl">
        <h1 className="text-2xl font-medium tracking-tight text-zinc-50">Synthesised sounds</h1>
        <p className="mt-2 text-sm text-zinc-500">Beds and SFX for video — browse and preview.</p>
      </header>
      <BrowseGrid entries={entries} />
    </div>
  );
}
