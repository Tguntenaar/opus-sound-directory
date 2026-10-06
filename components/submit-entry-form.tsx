"use client";

import { useState } from "react";
import { CATEGORY_ORDER, CATEGORIES } from "@/lib/categories";
import { MOOD_FACETS, type MoodSlug } from "@/lib/mood";
import { Button } from "@/components/ui/button";
import { SUBMIT_LICENSE_NOTE } from "@/lib/licenses";

const MOOD_OPTIONS = Object.entries(MOOD_FACETS) as [MoodSlug, string][];

type FormState = {
  title: string;
  prompt: string;
  email: string;
  category: string;
  mood: MoodSlug[];
  codeSnippet: string;
  codeUrl: string;
  companyWebsite: string;
};

const initial: FormState = {
  title: "",
  prompt: "",
  email: "",
  category: CATEGORY_ORDER[0],
  mood: [],
  codeSnippet: "",
  codeUrl: "",
  companyWebsite: "",
};

export function SubmitEntryForm() {
  const [form, setForm] = useState<FormState>(initial);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [submissionId, setSubmissionId] = useState<string | null>(null);
  const [submissionStatus, setSubmissionStatus] = useState<string | null>(null);

  async function pollStatus(id: string) {
    for (let i = 0; i < 24; i++) {
      await new Promise((r) => setTimeout(r, 2500));
      try {
        const res = await fetch(`/api/submit/status?id=${encodeURIComponent(id)}`);
        if (!res.ok) continue;
        const data = (await res.json()) as { status?: string; reviewUrl?: string };
        if (data.status) setSubmissionStatus(data.status);
        if (data.status === "live" || data.status === "rejected" || data.status === "pending_review") {
          break;
        }
      } catch {
        /* retry */
      }
    }
  }

  function toggleMood(slug: MoodSlug) {
    setForm((f) => ({
      ...f,
      mood: f.mood.includes(slug) ? f.mood.filter((m) => m !== slug) : [...f.mood, slug],
    }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!form.title.trim()) {
      setError("Title is required");
      return;
    }
    if (form.prompt.trim().length < 40) {
      setError("Prompt must be at least 40 characters");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      setError("Enter a valid contact email");
      return;
    }
    if (form.mood.length === 0) {
      setError("Select at least one mood");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: form.title.trim(),
          prompt: form.prompt.trim(),
          email: form.email.trim(),
          category: form.category,
          mood: form.mood,
          codeSnippet: form.codeSnippet.trim() || undefined,
          codeUrl: form.codeUrl.trim() || undefined,
          companyWebsite: form.companyWebsite,
        }),
      });
      const data = (await res.json()) as {
        ok?: boolean;
        error?: string;
        submissionId?: string;
        id?: string;
        status?: string;
      };
      if (!res.ok || !data.ok) {
        setError(data.error ?? "Submission failed");
        return;
      }
      const sid = data.submissionId ?? data.id ?? null;
      setSubmissionId(sid);
      setSubmissionStatus(data.status ?? "scanning");
      setSuccess(true);
      setForm(initial);
      if (sid) {
        void pollStatus(sid);
      }
    } catch {
      setError("Network error — try again");
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div
        className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-6 text-sm text-zinc-200"
        role="status"
      >
        <p className="font-medium text-violet-100">Thanks — we got your submission.</p>
        {submissionId && (
          <p className="mt-2 text-zinc-400">
            Status: <span className="font-mono text-zinc-200">{submissionStatus ?? "scanning"}</span>
            {submissionId ? ` · id ${submissionId}` : null}
          </p>
        )}
        <p className="mt-2 text-zinc-400">
          Safe submissions auto-publish as community entries after automated screening and AI review.
          Prefer git? Open a pull request on{" "}
          <a
            href="https://github.com/Tguntenaar/opus-sound-directory"
            className="text-violet-300 underline-offset-2 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            github.com/Tguntenaar/opus-sound-directory
          </a>{" "}
          with your entry JSON and assets.
        </p>
        <button
          type="button"
          className="mt-4 text-xs text-zinc-500 underline-offset-2 hover:text-zinc-300 hover:underline"
          onClick={() => setSuccess(false)}
        >
          Submit another
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={(e) => void onSubmit(e)} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-400">Title</span>
        <input
          required
          name="title"
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-violet-500"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-400">Category</span>
        <select
          name="category"
          value={form.category}
          onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100"
        >
          {CATEGORY_ORDER.map((id) => (
            <option key={id} value={id}>
              {CATEGORIES[id].label}
            </option>
          ))}
        </select>
      </label>

      <fieldset className="flex flex-col gap-2 text-sm">
        <legend className="text-zinc-400">Mood</legend>
        <div className="flex flex-wrap gap-2">
          {MOOD_OPTIONS.map(([slug, label]) => {
            const on = form.mood.includes(slug);
            return (
              <button
                key={slug}
                type="button"
                onClick={() => toggleMood(slug)}
                className={
                  on
                    ? "rounded-md border border-violet-500/50 bg-violet-500/15 px-2.5 py-1 text-xs text-violet-100"
                    : "rounded-md border border-zinc-700 px-2.5 py-1 text-xs text-zinc-400 hover:border-zinc-600"
                }
                aria-pressed={on}
              >
                {label}
              </button>
            );
          })}
        </div>
      </fieldset>

      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-400">Prompt</span>
        <textarea
          required
          name="prompt"
          rows={8}
          value={form.prompt}
          onChange={(e) => setForm((f) => ({ ...f, prompt: e.target.value }))}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-violet-500"
          placeholder="Duration, sample count, BPM, cue frames, master targets…"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-400">Contact email</span>
        <input
          required
          type="email"
          name="email"
          autoComplete="email"
          value={form.email}
          onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-violet-500"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-400">generate.py (optional)</span>
        <textarea
          name="codeSnippet"
          rows={5}
          value={form.codeSnippet}
          onChange={(e) => setForm((f) => ({ ...f, codeSnippet: e.target.value }))}
          className="font-mono rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 outline-none focus:border-violet-500"
          placeholder="# paste synthesis code or leave blank"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-400">Code link (optional)</span>
        <input
          name="codeUrl"
          type="url"
          value={form.codeUrl}
          onChange={(e) => setForm((f) => ({ ...f, codeUrl: e.target.value }))}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-violet-500"
          placeholder="https://gist.github.com/…"
        />
      </label>

      <input
        type="text"
        name="companyWebsite"
        value={form.companyWebsite}
        onChange={(e) => setForm((f) => ({ ...f, companyWebsite: e.target.value }))}
        className="hidden"
        tabIndex={-1}
        autoComplete="off"
        aria-hidden
      />

      {error && (
        <p className="text-sm text-amber-400/90" role="alert">
          {error}
        </p>
      )}

      <p className="text-xs leading-relaxed text-zinc-600">{SUBMIT_LICENSE_NOTE}</p>

      <Button type="submit" disabled={submitting}>
        {submitting ? "Sending…" : "Submit entry"}
      </Button>
    </form>
  );
}
