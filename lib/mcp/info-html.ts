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
    .page { max-width: 32rem; margin: 0 auto; }
    .home {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      margin: 0 0 1rem;
      padding: 0.45rem 0.8rem;
      border: 1px solid #27272a;
      border-radius: 0.5rem;
      background: #18181b;
      color: #e4e4e7;
      font-size: 0.875rem;
      font-weight: 500;
      text-decoration: none;
    }
    .home:hover { background: #27272a; color: #fafafa; border-color: #3f3f46; }
    .home:focus-visible { outline: 2px solid rgb(139 92 246 / 0.6); outline-offset: 2px; }
    .card { border: 1px solid #27272a; border-radius: 0.75rem; padding: 1.5rem; background: #18181b; overflow: hidden; min-width: 0; }
    h1 { font-size: 1.5rem; margin: 0 0 0.5rem; }
    p { color: #a1a1aa; font-size: 0.875rem; line-height: 1.5; }
    code { font-family: ui-monospace, monospace; font-size: 0.75rem; }
    /* Page-local: /mcp is standalone HTML, not CodeViewer. Box must size to content. */
    pre {
      display: block;
      box-sizing: border-box;
      width: 100%;
      max-width: 100%;
      min-width: 0;
      margin: 0.75rem 0 0;
      padding: 0.75rem 1rem;
      overflow-x: auto;
      background: #09090b;
      border: 1px solid #27272a;
      border-radius: 0.5rem;
      line-height: 1.5;
      color: #d4d4d8;
      font-family: ui-monospace, monospace;
      font-size: 0.75rem;
      white-space: pre;
    }
    .endpoint { color: #c4b5fd; word-break: break-all; }
    section { margin-top: 1.25rem; padding-top: 1.25rem; border-top: 1px solid #27272a; }
    button { background: #3f3f46; color: #fafafa; border: 0; border-radius: 0.375rem; padding: 0.35rem 0.65rem; cursor: pointer; font-size: 0.75rem; }
    button:hover { background: #52525b; }
    .row { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
  </style>
</head>
<body>
  <div class="page">
    <a class="home" href="/">← Opus Sounds Directory</a>
    <div class="card">
      <h1>MCP server</h1>
      <p><a class="home" href="/agents">Install the skill and connect your agent →</a></p>
      <p>Public streamable HTTP endpoint for ${SITE_NAME}. Search and downloads are open to everyone. Sign in to submit sounds and follow their review.</p>
      <p>${MCP_SUBMIT_LICENSE_NOTE.replace(/</g, "&lt;")}</p>
      <p>For submissions, create a revocable agent token in <a href="/account" style="color:#c4b5fd">your account</a> and configure your MCP client with the HTTP header <code>Authorization: Bearer YOUR_TOKEN</code>. Keep tokens in your client’s private secret settings. Tokens allow submission and access to your own status; browser sign-in is separate.</p>
      <p class="endpoint"><code>${endpoint}</code></p>
      <section>
        <div class="row"><strong>Cursor (.cursor/mcp.json)</strong><button type="button" onclick="copy('c1')">Copy</button></div>
        <pre id="c1">${cursorJson.replace(/</g, "&lt;")}</pre>
      </section>
      <section>
        <div class="row"><strong>Claude Code</strong><button type="button" onclick="copy('c2')">Copy</button></div>
        <pre id="c2">${claudeCli.replace(/</g, "&lt;")}</pre>
      </section>
    </div>
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
