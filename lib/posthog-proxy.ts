import type { NextRequest } from "next/server";
import { posthogAssetsHost, posthogIngestApiHost } from "@/lib/posthog-config";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
]);

function upstreamForPath(pathname: string): { origin: string; upstreamPath: string } {
  const rest =
    pathname.replace(/^\/api\/ingest/, "").replace(/^\/ingest/, "") || "/";
  if (rest.startsWith("/static/")) {
    return { origin: posthogAssetsHost(), upstreamPath: rest };
  }
  return { origin: posthogIngestApiHost(), upstreamPath: rest };
}

/** First-party reverse proxy for PostHog (events + static assets). */
export async function proxyPosthogIngest(request: NextRequest): Promise<Response> {
  const { origin, upstreamPath } = upstreamForPath(request.nextUrl.pathname);
  const url = `${origin}${upstreamPath}${request.nextUrl.search}`;

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) headers.set(key, value);
  });

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "manual",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(url, init);
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}
