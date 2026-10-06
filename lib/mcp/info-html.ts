import { MCP_SUBMIT_LICENSE_NOTE } from "@/lib/licenses";
import { getSiteUrl, SITE_NAME } from "@/lib/site-url";

export function mcpInfoHtml(): string {
  const endpoint = `${getSiteUrl()}/mcp`;
  const cursorJson = JSON.stringify(
    { mcpServers: { "opus-sounds": { url: endpoint } } },
    null,
    2,
  );
  const claudeCli = `claude mcp add --transport http opus-sounds ${endpoint}`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="index,follow" />
  <title>MCP · ${SITE_NAME}</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, sans-serif; background: #09090b; color: #e4e4e7; margin: 0; padding: 2rem 1rem; }
    .card { max-width: 32rem; margin: 0 auto; border: 1px solid #27272a; border-radius: 0.75rem; padding: 1.5rem; background: #18181b; }
    h1 { font-size: 1.5rem; margin: 0 0 0.5rem; }
    p { color: #a1a1aa; font-size: 0.875rem; line-height: 1.5; }
    code, pre { font-family: ui-monospace, monospace; font-size: 0.75rem; }
    .endpoint { color: #c4b5fd; word-break: break-all; }
    section { margin-top: 1.25rem; padding-top: 1.25rem; border-top: 1px solid #27272a; }
    button { background: #3f3f46; color: #fafafa; border: 0; border-radius: 0.375rem; padding: 0.35rem 0.65rem; cursor: pointer; font-size: 0.75rem; }
    button:hover { background: #52525b; }
    .row { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>MCP server</h1>
    <p>Public streamable HTTP endpoint for ${SITE_NAME}. Submissions are screened and AI-reviewed; safe entries auto-publish as community sounds.</p>
    <p>${MCP_SUBMIT_LICENSE_NOTE.replace(/</g, "&lt;")}</p>
    <p class="endpoint"><code>${endpoint}</code></p>
    <section>
      <div class="row"><strong>Cursor (.mcp.json)</strong><button type="button" onclick="copy('c1')">Copy</button></div>
      <pre id="c1">${cursorJson.replace(/</g, "&lt;")}</pre>
    </section>
    <section>
      <div class="row"><strong>Claude Code</strong><button type="button" onclick="copy('c2')">Copy</button></div>
      <pre id="c2">${claudeCli.replace(/</g, "&lt;")}</pre>
    </section>
  </div>
  <script>
    function copy(id) {
      const t = document.getElementById(id).textContent;
      navigator.clipboard.writeText(t);
    }
  </script>
</body>
</html>`;
}
