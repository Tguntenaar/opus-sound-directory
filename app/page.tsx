import { Suspense } from "react";
import { TrackedLink } from "@/components/tracked-link";
import { Plus } from "lucide-react";
import { getAllEntriesMerged } from "@/lib/entries";
import { slimEntriesForBrowse } from "@/lib/browse-catalog-payload";
import { getFeaturedEntry, FEATURED_CONTROL_SLUG } from "@/lib/featured";
import { sortEntries } from "@/lib/browse-sort";
import { homeCollectionPageJsonLd } from "@/lib/structured-data";
import { HomeBrowse } from "@/components/home-browse";
import { BrowseGrid } from "@/components/browse-grid";
import { JsonLd } from "@/components/json-ld";
import { isValidCategorySlug } from "@/lib/category-seo";

type HomePageProps = {
  searchParams?: Promise<{ q?: string; category?: string }>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const catalog = await getAllEntriesMerged();
  const slim = slimEntriesForBrowse(catalog);
  const featuredEntry = getFeaturedEntry(slim) ?? undefined;
  const featuredControl = slim.find((e) => e.slug === FEATURED_CONTROL_SLUG);
  const entries = sortEntries(slim, "popular", {}).slice(0, 18);
  const sp = searchParams ? await searchParams : {};
  const initialQuery = sp.q?.trim() ?? "";
  const initialCategory =
    sp.category && isValidCategorySlug(sp.category) ? sp.category : "all";

  return (
    <div className="flex flex-col gap-12">
      <JsonLd data={homeCollectionPageJsonLd(catalog)} />
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
        <TrackedLink event="add_sound_click" eventProperties={{ placement: "home_hero" }} href="/submit" className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-lg bg-violet-600 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-violet-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-violet-400">
          <Plus className="h-4 w-4" aria-hidden="true" />
          Add your sound
        </TrackedLink>
      </header>
      <Suspense
        fallback={
          <BrowseGrid
            entries={entries}
            catalogHref="/catalog/browse.json"
            featuredEntry={featuredEntry}
            featuredControl={featuredControl}
            syncCategoryToUrl
            syncQueryToUrl
            initialCategory={initialCategory}
            initialQuery={initialQuery}
          />
        }
      >
        <HomeBrowse
          entries={entries}
          catalogHref="/catalog/browse.json"
          featuredEntry={featuredEntry}
          featuredControl={featuredControl}
          initialQueryFromServer={initialQuery}
        />
      </Suspense>
    </div>
  );
}
