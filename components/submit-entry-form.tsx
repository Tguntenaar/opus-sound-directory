"use client";

import { useEffect, useRef, useState } from "react";
import { CATEGORY_ORDER, CATEGORIES } from "@/lib/categories";
import { MOOD_FACETS, type MoodSlug } from "@/lib/mood";
import { Button } from "@/components/ui/button";
import { SUBMIT_LICENSE_NOTE } from "@/lib/licenses";
import { captureEvent } from "@/lib/analytics-client";

import { ContributorAccount } from "@/components/contributor-account";

const MOOD_OPTIONS = Object.entries(MOOD_FACETS) as [MoodSlug, string][];

type FormState = {
  title: string;
  prompt: string;
  author_name: string;
  category: string;
  mood: MoodSlug[];
  codeSnippet: string;
  codeUrl: string;
  companyWebsite: string;
};

const initial: FormState = {
  title: "",
  prompt: "",
  author_name: "",
  category: CATEGORY_ORDER[0],
  mood: [],
  codeSnippet: "",
  codeUrl: "",
  companyWebsite: "",
};

export function SubmitEntryForm() {
  const started = useRef(false);
  const [access, setAccess] = useState<"loading" | "allowed" | "signin">("loading");
  useEffect(() => {
    let active = true;
    fetch("/api/account", { cache: "no-store" }).then(async response => {
      const data = await response.json() as { user?: { emailVerified: boolean } };
      if (active) {
        const nextAccess = response.ok && data.user?.emailVerified ? "allowed" : "signin";
        setAccess(nextAccess);
        captureEvent("submit_form_access", { source: "web", access: nextAccess });
      }
    }).catch(() => {
      if (active) {
        setAccess("signin");
        captureEvent("submit_form_access", { source: "web", access: "error" });
      }
    });
    return () => { active = false; };
  }, []);
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
        if (data.status === "live") {
          captureEvent("submit_status_live", { submission_id: id, source: "web" });
        }
        if (data.status === "live" || data.status === "rejected" || data.status === "pending_review") {
          break;
        }
      } catch {
        /* retry */
      }
    }
  }

  function trackStart() {
    if (started.current) return;
    started.current = true;
    captureEvent("submit_form_start", { source: "web" });
  }

  function toggleMood(slug: MoodSlug) {
    trackStart();
    setForm((f) => ({
      ...f,
      mood: f.mood.includes(slug) ? f.mood.filter((m) => m !== slug) : [...f.mood, slug],
    }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    captureEvent("submit_form_attempt", { source: "web", category: form.category });

    if (!form.title.trim()) {
      captureEvent("submit_form_validation_error", { source: "web", field: "title" });
      setError("Title is required");
      return;
    }
    if (form.prompt.trim().length < 40) {
      captureEvent("submit_form_validation_error", { source: "web", field: "prompt" });
      setError("Prompt must be at least 40 characters");
      return;
    }
    if (form.mood.length === 0) {
      captureEvent("submit_form_validation_error", { source: "web", field: "mood" });
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
          author_name: form.author_name.trim() || undefined,
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
        captureEvent("submit_form_error", { source: "web", reason: "server_rejected", http_status: res.status });
        setError(data.error ?? "Submission failed");
        return;
      }
      const sid = data.submissionId ?? data.id ?? null;
      setSubmissionId(sid);
      setSubmissionStatus(data.status ?? "scanning");
      captureEvent("submit_form_submit", {
        submission_id: sid ?? undefined,
        source: "web",
        category: form.category,
        mood_count: form.mood.length,
      });
      setSuccess(true);
      setForm(initial);
      if (sid) {
        void pollStatus(sid);
      }
    } catch {
      captureEvent("submit_form_error", { source: "web", reason: "network_or_response" });
      setError("Network error — try again");
    } finally {
      setSubmitting(false);
    }
  }

  if (access === "loading") return <p role="status" className="text-sm text-zinc-400">Checking sign-in…</p>;
  if (access !== "allowed") return <ContributorAccount submission />;

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
          Track progress in <a href="/account" className="text-violet-300 hover:underline">your account</a>.
        </p>
        <button
          type="button"
          className="mt-4 text-xs text-zinc-500 underline-offset-2 hover:text-zinc-300 hover:underline"
          onClick={() => {
            started.current = false;
            captureEvent("submit_another_click", { source: "web" });
            setSuccess(false);
          }}
        >
          Submit another
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={(e) => void onSubmit(e)} onChange={trackStart} onInvalidCapture={(e) => {
      const field = (e.target as HTMLInputElement).name;
      captureEvent("submit_form_validation_error", { source: "web", field });
    }} className="flex flex-col gap-4">
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
          rows={4}
          value={form.prompt}
          onChange={(e) => setForm((f) => ({ ...f, prompt: e.target.value }))}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-violet-500"
          placeholder="Duration, sample count, BPM, cue frames, master targets…"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-400">Public credit (optional)</span>
        <input
          name="author_name"
          maxLength={120}
          placeholder="Name or handle shown on your sound"
          value={form.author_name}
          onChange={(e) => setForm((f) => ({ ...f, author_name: e.target.value }))}
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
        {submitting ? "Sending…" : "Submit sound"}
      </Button>
    </form>
  );
}
