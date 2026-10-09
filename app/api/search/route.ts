import { getAlgoliaSearch } from "@/lib/algolia";
import { getAllEntriesMerged } from "@/lib/entries";
import { searchCatalog, toSearchRecords, type SearchRecord } from "@/lib/search-records";

export async function GET(request: Request) {
  const query = new URL(request.url).searchParams.get("q")?.trim() ?? "";
  if (query.length < 2 || query.length > 200) {
    return Response.json({ error: "Use between 2 and 200 characters." }, { status: 400 });
  }
  try {
    const algolia = await getAlgoliaSearch();
    if (!algolia) {
      const records = toSearchRecords(await getAllEntriesMerged());
      return Response.json(searchCatalog(records, query));
    }
    const result = await algolia.client.searchSingleIndex<SearchRecord>({
      indexName: algolia.indexName,
      searchParams: {
        query,
        hitsPerPage: 12,
        attributesToRetrieve: ["id", "modelId", "previewUrl", "slug", "title", "category", "tags", "mood", "description", "durationSec"],
        attributesToHighlight: [],
      },
    });
    return Response.json({ hits: result.hits, nbHits: result.nbHits ?? result.hits.length, provider: "algolia" }, {
      headers: { "Cache-Control": "public, max-age=30, s-maxage=60" },
    });
  } catch {
    console.error("Sound search failed");
    return Response.json({ error: "Search is temporarily unavailable. Please try again." }, { status: 503 });
  }
}
