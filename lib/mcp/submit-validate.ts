import { CATEGORY_ORDER } from "@/lib/categories";
import { MOOD_FACETS } from "@/lib/mood";
import { isAllowedAudioUrl } from "@/lib/audio-url-policy";
import type { SubmitEntryInput } from "@/lib/submit-types";

const CATEGORY_IDS = new Set<string>(CATEGORY_ORDER);
const MOOD_IDS = new Set(Object.keys(MOOD_FACETS));
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function trimStr(value: unknown, max: number): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

export function validateMcpSubmit(body: Record<string, unknown>): {
  ok: true;
  data: SubmitEntryInput;
} | { ok: false; error: string } {
  const title = trimStr(body.title, 160);
  const prompt = trimStr(body.prompt, 8000);
  const category = trimStr(body.category, 40);
  const code = trimStr(body.code, 100_000);
  const email = body.email ? trimStr(body.email, 200).toLowerCase() : "mcp@anonymous.local";

  if (!title) return { ok: false, error: "title is required" };
  if (!prompt || prompt.length < 40) {
    return { ok: false, error: "prompt must be at least 40 characters" };
  }
  if (!CATEGORY_IDS.has(category)) return { ok: false, error: "invalid category" };
  if (!code || code.length < 20) return { ok: false, error: "code (generate.py) is required" };
  if (email !== "mcp@anonymous.local" && !EMAIL_RE.test(email)) {
    return { ok: false, error: "invalid email" };
  }

  let mood: string[] = [];
  if (Array.isArray(body.mood)) {
    mood = body.mood.filter((m): m is string => typeof m === "string" && MOOD_IDS.has(m));
  }
  if (mood.length === 0) return { ok: false, error: "mood must include at least one valid facet" };

  const durationSec = Number(body.durationSec);
  if (!Number.isFinite(durationSec) || durationSec <= 0 || durationSec > 600) {
    return { ok: false, error: "durationSec must be between 0 and 600" };
  }

  let tempo: SubmitEntryInput["tempo"];
  if (body.tempo === "slow" || body.tempo === "medium" || body.tempo === "fast") {
    tempo = body.tempo;
  }

  let audioUrl: string | undefined;
  if (body.audioUrl) {
    const raw = trimStr(body.audioUrl, 500);
    if (!isAllowedAudioUrl(raw)) {
      return { ok: false, error: "audioUrl must be https .mp3 or .wav from allowlisted host" };
    }
    audioUrl = raw;
  }

  let author_url: string | undefined;
  if (body.author_url) {
    try {
      const url = new URL(trimStr(body.author_url, 500));
      if (url.protocol !== "https:" && url.protocol !== "http:") throw new Error("Unsupported link protocol");
      author_url = url.toString();
    } catch {
      return { ok: false, error: "author_url must be a valid URL" };
    }
  }

  return {
    ok: true,
    data: {
      title,
      prompt,
      email,
      category,
      mood,
      code,
      durationSec,
      tempo,
      audioUrl,
      author_name: body.author_name ? trimStr(body.author_name, 120) : undefined,
      author_url,
      notes: body.notes ? trimStr(body.notes, 2000) : undefined,
    },
  };
}
