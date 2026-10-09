import { algoliasearch } from "algoliasearch";
import { z } from "zod";

// Run against the site's public feed so community sounds are included too.
const sourceIndex = process.argv.indexOf("--source");
const source = sourceIndex >= 0 ? process.argv[sourceIndex + 1] : undefined;
const dryRun = process.argv.includes("--dry-run");
if (!source || source.startsWith("--")) {
  throw new Error("Provide --source https://your-site.example (or a local preview URL).");
}
const url = new URL("/api/search/catalog", source);
if (!['http:', 'https:'].includes(url.protocol)) throw new Error("Use an HTTP or HTTPS source.");
const response = await fetch(url, { signal: AbortSignal.timeout(30_000), cache: "no-store" });
if (!response.ok) throw new Error(`Catalog request failed (${response.status}); index left unchanged.`);
const recordSchema = z.object({
  objectID: z.string().min(1), slug: z.string().min(1), title: z.string().min(1),
  id: z.string().min(1), modelId: z.string(), previewUrl: z.string().nullable(),
  category: z.string(), tags: z.array(z.string()), mood: z.array(z.string()),
  description: z.string(), durationSec: z.number().nonnegative(),
});
const { records } = z.object({ records: z.array(recordSchema).min(1) }).parse(await response.json());
if (new Set(records.map((record) => record.objectID)).size !== records.length) {
  throw new Error("Catalog contains duplicate object IDs; index left unchanged.");
}
const indexName = process.env.ALGOLIA_INDEX_NAME || "opus_sounds";
if (dryRun) {
  console.log(`Validated ${records.length} public sounds for ${indexName}. No Algolia writes performed.`);
} else {
  const appId = process.env.ALGOLIA_APP_ID;
  const apiKey = process.env.ALGOLIA_WRITE_API_KEY;
  if (!appId || !apiKey) throw new Error("Set ALGOLIA_APP_ID and ALGOLIA_WRITE_API_KEY in your local environment.");
  const client = algoliasearch(appId, apiKey);
  const indexSettings = {
    searchableAttributes: ["title", "tags", "mood", "category", "description"],
    attributesForFaceting: ["category", "mood", "tags"],
    attributesToHighlight: [],
  };
  let currentSettings;
  try {
    currentSettings = await client.getSettings({ indexName });
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  if (!currentSettings || Object.entries(indexSettings).some(([key, value]) => JSON.stringify(currentSettings[key]) !== JSON.stringify(value))) {
    const settings = await client.setSettings({ indexName, indexSettings });
    await client.waitForTask({ indexName, taskID: settings.taskID, maxRetries: 60 });
  }
  console.log(`Uploading ${records.length} public sounds to ${indexName}…`);
  // Algolia uploads to a temporary index before swapping it into place.
  // Replacing the full snapshot removes withdrawn sounds and stale records.
  await client.replaceAllObjects({ indexName, objects: records });
  console.log(`Indexed ${records.length} public sounds in ${indexName}.`);
}
