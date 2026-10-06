import { posthogIngestApiHost, serverPosthogKey } from "@/lib/posthog-config";

export type ServerCaptureEvent = {
  distinctId: string;
  event: string;
  properties?: Record<string, unknown>;
  timestamp?: string;
};

export async function captureServerEvent(payload: ServerCaptureEvent): Promise<void> {
  const apiKey = serverPosthogKey();
  if (!apiKey) return;

  const body = {
    api_key: apiKey,
    event: payload.event,
    distinct_id: payload.distinctId,
    properties: payload.properties ?? {},
    timestamp: payload.timestamp,
  };

  const url = `${posthogIngestApiHost()}/capture/`;
  try {
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    /* analytics must not break requests */
  }
}

export async function hashDistinctSuffix(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  const hex = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hex.slice(0, 16);
}

export async function mcpDistinctId(request: Request): Promise<string> {
  const clientName =
    request.headers.get("x-mcp-client")?.trim() ||
    request.headers.get("user-agent")?.trim().slice(0, 80);
  if (clientName && clientName !== "unknown") {
    return `mcp:${clientName.replace(/\s+/g, "_").slice(0, 64)}`;
  }
  const ip =
    request.headers.get("cf-connecting-ip") ??
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "unknown";
  const hashed = await hashDistinctSuffix(ip);
  return `mcp:${hashed}`;
}
