import { createMcpHandler } from "agents/mcp/server";
import { getRequestExecutionContext } from "vinext/shims/request-context";
import { createOpusMcpServer } from "@/lib/mcp/server";

const mcpHandler = createMcpHandler(
  (request: Request) => createOpusMcpServer(request),
  {
    route: "/mcp",
    corsOptions: {
      origin: "*",
      methods: "GET, POST, DELETE, OPTIONS",
      headers: "Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version",
      maxAge: 86400,
    },
  },
);

export async function handleMcpRequest(request: Request): Promise<Response> {
  let env: unknown = {};
  try {
    const mod = await import("cloudflare:workers");
    env = mod.env;
  } catch {
    env = {};
  }
  const ctx = getRequestExecutionContext() ?? {
    waitUntil: () => {},
    passThroughOnException: () => {},
  };
  return mcpHandler(request, env, ctx as ExecutionContext);
}
