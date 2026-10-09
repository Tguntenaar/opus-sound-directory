import { CATEGORY_ORDER } from "@/lib/categories";
import { MOOD_FACETS } from "@/lib/mood";
import type { SubmitEntryInput } from "@/lib/submit-types";

const CATEGORY_IDS = new Set<string>(CATEGORY_ORDER);
const MOOD_IDS = new Set(Object.keys(MOOD_FACETS));
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type SubmitFormPayload = SubmitEntryInput & {
  /** Honeypot — must be empty */
  companyWebsite?: string;
};

export function validateSubmitPayload(body: unknown): {
  ok: true;
  data: SubmitEntryInput;
} | { ok: false; error: string } {
  if (!body || typeof body !== "object") {
    return { ok: false, error: "Invalid body" };
  }
  const b = body as Record<string, unknown>;

  if (typeof b.companyWebsite === "string" && b.companyWebsite.trim() !== "") {
    return { ok: true, data: honeypotDiscard() };
  }

  const title = trimStr(b.title, 160);
  const prompt = trimStr(b.prompt, 8000);
  const email = trimStr(b.email, 200).toLowerCase();
  const category = trimStr(b.category, 40);
  const codeSnippet = b.codeSnippet ? trimStr(b.codeSnippet, 50000) : undefined;
  const codeUrl = b.codeUrl ? trimStr(b.codeUrl, 500) : undefined;

  if (!title) return { ok: false, error: "Title is required" };
  if (!prompt || prompt.length < 40) {
    return { ok: false, error: "Prompt must be at least 40 characters" };
  }
  if (!email || !EMAIL_RE.test(email)) return { ok: false, error: "Valid email is required" };
  if (!CATEGORY_IDS.has(category)) return { ok: false, error: "Select a category" };

  let mood: string[] = [];
  if (Array.isArray(b.mood)) {
    mood = b.mood.filter((m): m is string => typeof m === "string" && MOOD_IDS.has(m));
  }
  if (mood.length === 0) return { ok: false, error: "Select at least one mood" };

  if (codeUrl) {
    try {
      new URL(codeUrl.startsWith("http") ? codeUrl : `https://${codeUrl}`);
    } catch {
      return { ok: false, error: "Code link must be a valid URL" };
    }
  }

  const normalizedCodeUrl = codeUrl
    ? codeUrl.startsWith("http")
      ? codeUrl
      : `https://${codeUrl}`
    : undefined;

  return {
    ok: true,
    data: {
      author_name: trimStr(b.author_name, 120) || undefined,
      title,
      prompt,
      email,
      category,
      mood,
      codeSnippet: codeSnippet || undefined,
      codeUrl: normalizedCodeUrl,
    },
  };
}

function honeypotDiscard(): SubmitEntryInput {
  return {
    title: "",
    prompt: "",
    email: "bot@invalid.local",
    category: "ambient",
    mood: ["calm"],
  };
}

export function isSubmitHoneypotDiscard(data: SubmitEntryInput): boolean {
  return data.email === "bot@invalid.local";
}

function trimStr(value: unknown, max: number): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}
