import { getAllEntriesMerged } from "@/lib/entries";
import { toSearchRecords } from "@/lib/search-records";

/** Public indexing feed, including published community sounds. */
export async function GET() {
  return Response.json({ records: toSearchRecords(await getAllEntriesMerged()) }, {
    headers: { "Cache-Control": "no-store" },
  });
}
