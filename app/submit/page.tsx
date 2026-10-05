"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";

export default function SubmitPage() {
  const [status, setStatus] = useState<"idle" | "done">("idle");

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("done");
  }

  return (
    <div className="mx-auto max-w-lg">
      <h1 className="text-3xl font-semibold text-zinc-50">Submit an entry</h1>
      <p className="mt-2 text-sm text-zinc-500">
        v1 stores entries as JSON in git. This form is a UI stub — submissions are not persisted yet.
      </p>

      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-zinc-400">Title</span>
          <input
            required
            name="title"
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-violet-500"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-zinc-400">Category</span>
          <select
            name="category"
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100"
          >
            <option value="chaos-calm">Chaos → calm</option>
            <option value="ad-beds">Ad bed</option>
            <option value="drops">Drop / transition</option>
            <option value="risers">Riser</option>
            <option value="ui-sounds">UI sound</option>
            <option value="logo-stings">Logo sting</option>
            <option value="ambient">Ambient</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-zinc-400">Prompt</span>
          <textarea
            required
            name="prompt"
            rows={8}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-100 outline-none focus:border-violet-500"
            placeholder="Include duration, sample count, BPM, cue frames, and master targets…"
          />
        </label>
        <Button type="submit">Submit (TODO)</Button>
        {status === "done" && (
          <p className="text-sm text-amber-400/90" role="status">
            Not wired yet — add a file under content/entries/ and run the runner locally.
          </p>
        )}
      </form>
    </div>
  );
}
