import { handleMcpRequest } from "@/lib/mcp/handler";
import { mcpInfoHtml } from "@/lib/mcp/info-html";
import { shouldServeMcpInfoPage } from "@/lib/mcp/should-serve-info-page";

export const runtime = "edge";

export async function GET(request: Request) {
  if (shouldServeMcpInfoPage(request)) {
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
