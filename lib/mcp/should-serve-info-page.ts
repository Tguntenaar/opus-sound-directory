/** Human-facing GETs (browser nav, Next/vinext RSC prefetch) — not MCP stream clients. */
export function shouldServeMcpInfoPage(request: Request): boolean {
  if (request.method !== "GET") return false;
  if (request.headers.get("mcp-session-id")) return false;

  const protocol =
    request.headers.get("MCP-Protocol-Version") ??
    request.headers.get("mcp-protocol-version");
  if (protocol) return false;

  const url = new URL(request.url);
  if (url.searchParams.has("_rsc")) return true;

  const accept = request.headers.get("accept") ?? "";
  if (accept.includes("text/x-component")) return true;
  if (request.headers.has("next-router-prefetch")) return true;
  if (request.headers.get("purpose") === "prefetch") return true;

  if (accept.includes("text/event-stream")) return false;

  return (
    accept.includes("text/html") &&
    !accept.includes("application/json")
  );
}
