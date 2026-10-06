import { serveEntryWav } from "@/lib/audio-wav-response";

type RouteParams = { params: Promise<{ id: string }> };

export async function GET(request: Request, { params }: RouteParams) {
  const { id } = await params;
  let env: { AUDIO_R2?: unknown; ASSETS?: { fetch: (r: Request) => Promise<Response> } } =
    {};
  try {
    const mod = await import("cloudflare:workers");
    env = mod.env as typeof env;
  } catch {
    // local Node preview without worker bindings
  }
  return serveEntryWav(request, id, env);
}
