import { getEntryById } from "@/lib/entries";

const WAV_CACHE = "public, max-age=31536000, immutable";

type R2Range = { offset: number; length?: number };

type R2ObjectBody = {
  body: ReadableStream | null;
  size: number;
  etag?: string;
};

type R2Bucket = {
  get(
    key: string,
    options?: { range?: R2Range | Headers },
  ): Promise<R2ObjectBody | null>;
  head?(key: string): Promise<{ size: number; etag?: string } | null>;
};

type AssetsFetcher = {
  fetch(request: Request): Promise<Response>;
};

function safeFilename(entryId: string): string {
  const entry = getEntryById(entryId);
  const base = entry?.title
    ? entry.title.replace(/\s+/g, "-").toLowerCase()
    : entryId;
  return `${base.replace(/[^a-z0-9._-]+/g, "-")}.wav`;
}

function parseRangeHeader(range: string | null, size: number): R2Range | null {
  if (!range || !range.startsWith("bytes=")) return null;
  const spec = range.slice("bytes=".length).split(",")[0]?.trim();
  if (!spec) return null;
  const [startStr, endStr] = spec.split("-");
  if (startStr === "" && endStr) {
    const suffix = parseInt(endStr, 10);
    if (!Number.isFinite(suffix) || suffix <= 0) return null;
    const offset = Math.max(0, size - suffix);
    return { offset, length: size - offset };
  }
  const start = parseInt(startStr, 10);
  if (!Number.isFinite(start) || start < 0) return null;
  const end = endStr ? parseInt(endStr, 10) : size - 1;
  if (!Number.isFinite(end) || end < start) return null;
  const length = Math.min(end - start + 1, size - start);
  return { offset: start, length };
}

function wavHeaders(
  entryId: string,
  size: number,
  etag?: string,
  extra?: Record<string, string>,
): Headers {
  const h = new Headers({
    "Content-Type": "audio/wav",
    "Content-Disposition": `attachment; filename="${safeFilename(entryId)}"`,
    "Accept-Ranges": "bytes",
    "Cache-Control": WAV_CACHE,
    ...extra,
  });
  if (etag) h.set("ETag", etag);
  if (!extra?.["Content-Range"]) h.set("Content-Length", String(size));
  return h;
}

function responseFromR2Body(
  entryId: string,
  object: R2ObjectBody,
  status: number,
  extraHeaders?: Record<string, string>,
): Response {
  if (!object.body) {
    return new Response("Empty object", { status: 502 });
  }
  return new Response(object.body, {
    status,
    headers: wavHeaders(entryId, object.size, object.etag, extraHeaders),
  });
}

export async function serveEntryWav(
  request: Request,
  entryId: string,
  env: { AUDIO_R2?: R2Bucket; ASSETS?: AssetsFetcher },
): Promise<Response> {
  if (!/^[a-z0-9][a-z0-9-]*$/.test(entryId)) {
    return new Response("Not found", { status: 404 });
  }

  const key = `${entryId}/out.wav`;
  const bucket = env.AUDIO_R2;

  if (bucket) {
    const rangeHeader = request.headers.get("Range");
    if (rangeHeader) {
      let totalSize: number | undefined;
      let etag: string | undefined;
      if (bucket.head) {
        const meta = await bucket.head(key);
        totalSize = meta?.size;
        etag = meta?.etag;
      }
      if (totalSize == null) {
        const probe = await bucket.get(key);
        if (!probe?.body) {
          totalSize = undefined;
        } else {
          totalSize = probe.size;
          etag = probe.etag;
          await probe.body.cancel();
        }
      }
      if (totalSize != null) {
        const parsed = parseRangeHeader(rangeHeader, totalSize);
        if (parsed) {
          const ranged = await bucket.get(key, { range: parsed });
          if (ranged?.body) {
            const length = parsed.length ?? totalSize - parsed.offset;
            const end = parsed.offset + length - 1;
            return responseFromR2Body(
              entryId,
              { body: ranged.body, size: length, etag: etag ?? ranged.etag },
              206,
              {
                "Content-Range": `bytes ${parsed.offset}-${end}/${totalSize}`,
                "Content-Length": String(length),
              },
            );
          }
        }
      }
    } else {
      const object = await bucket.get(key);
      if (object?.body) {
        return responseFromR2Body(entryId, object);
      }
    }
  }

  if (!env.ASSETS) {
    return new Response("Not found", { status: 404 });
  }

  const assetUrl = new URL(`/assets/${entryId}/out.wav`, request.url);
  const assetReq = new Request(assetUrl.toString(), {
    method: request.method,
    headers: request.headers,
  });
  const assetRes = await env.ASSETS.fetch(assetReq);
  if (!assetRes.ok) {
    return new Response("Not found", { status: 404 });
  }

  const headers = new Headers(assetRes.headers);
  headers.set("Content-Type", "audio/wav");
  headers.set("Content-Disposition", `attachment; filename="${safeFilename(entryId)}"`);
  headers.set("Cache-Control", WAV_CACHE);
  headers.set("Accept-Ranges", "bytes");
  return new Response(assetRes.body, { status: assetRes.status, headers });
}
