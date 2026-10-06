import { handleMcpRequest } from "@/lib/mcp/handler";
import { mcpInfoHtml } from "@/lib/mcp/info-html";

export const runtime = "edge";

export async function GET(request: Request) {
  const accept = request.headers.get("accept") ?? "";
  const isBrowser =
    accept.includes("text/html") &&
    !accept.includes("application/json") &&
    request.headers.get("mcp-session-id") == null;
  if (isBrowser) {
    return new Response(mcpInfoHtml(), {
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  }
  return handleMcpRequest(request);
}

export async function POST(request: Request) {
  return handleMcpRequest(request);
}

export async function DELETE(request: Request) {
  return handleMcpRequest(request);
}

export async function OPTIONS(request: Request) {
  return handleMcpRequest(request);
}
