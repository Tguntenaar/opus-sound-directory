import { algoliasearch } from "algoliasearch";

export async function getAlgoliaSearch() {
  let config: Record<string, unknown> = process.env;
  try {
    const { env } = await import("cloudflare:workers");
    config = { ...config, ...env };
  } catch {
    // Node development and tests use environment variables.
  }
  const appId = config.ALGOLIA_APP_ID;
  const apiKey = config.ALGOLIA_SEARCH_API_KEY;
  const indexName = typeof config.ALGOLIA_INDEX_NAME === "string" && config.ALGOLIA_INDEX_NAME ? config.ALGOLIA_INDEX_NAME : "opus_sounds";
  if (!appId && !apiKey) return null;
  if (typeof appId !== "string" || typeof apiKey !== "string" || !appId || !apiKey) throw new Error("Incomplete Algolia search configuration");
  return { client: algoliasearch(appId, apiKey), indexName };
}
