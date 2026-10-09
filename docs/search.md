# Sound search

Open search from the header on any page, or press ⌘K on Mac / Ctrl+K on Windows and Linux. Use the arrow keys and Enter to open a sound; Escape closes the dialog. Queries wait for a 250 ms pause and at least two characters before sending a request.

Play or pause a sound directly from its search result. Tab reaches the preview and open controls. Only one sound plays at a time; changing the query or closing search stops the preview. Audio loads only when you press play. Sounds without rendered audio have no preview button. Reindex after adding preview fields to an existing index.

The global dialog uses Algolia when configured. With no Algolia credentials, it searches the current public catalog on the server. Partial configuration or an Algolia outage produces a retry message. The existing browse field still filters the cards on its page.

## Connect Algolia

Create an Algolia application and use a dedicated index named `opus_sounds`.

Add these values to the ignored `.dev.vars` file for development and to the deployed Worker's environment variables/secrets for production:

```dotenv
ALGOLIA_APP_ID=your_application_id
ALGOLIA_SEARCH_API_KEY=your_search_only_key
ALGOLIA_INDEX_NAME=opus_sounds
```

Use a search-only key restricted to this index. Search runs on the server; no API keys are sent to the browser. Keep indexing credentials separate from the Worker and never commit them.

## Populate and refresh the index

The public `/api/search/catalog` feed includes visible bundled sounds and published community sounds. First deploy the feed, or start the local preview for development.

Validate the feed without changing Algolia:

```sh
npm run search:index -- --source https://opussounds.directory --dry-run
```

Store `ALGOLIA_APP_ID`, `ALGOLIA_INDEX_NAME`, and `ALGOLIA_WRITE_API_KEY` in an ignored `.env.algolia` file. The indexing key needs access to the target index and its temporary replacement indices, with the permissions required by Algolia's `setSettings` and `replaceAllObjects` methods.

```sh
node --env-file=.env.algolia scripts/index-algolia.mjs --source https://opussounds.directory
```

Use a separate index and a local source URL for preview data. Never point the production index at a local catalog: it may not contain published community sounds.

Run indexing after catalog deployments and after community publishing or unpublishing. This command replaces the index with the complete public snapshot, so removed sounds disappear too. Sync is manual; it is not scheduled automatically. Invalid, duplicate, or empty feeds stop the command before it writes to Algolia. Algolia's temporary-index replacement keeps the existing search available during indexing.

After indexing and configuring the Worker, verify a known query at `/api/search?q=chime`: the response should say `"provider":"algolia"`. The dialog then displays “Search by Algolia.”
