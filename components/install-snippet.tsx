"use client";

import { useState } from "react";

/** Installation snippets do not increment sound-copy statistics. */
export function InstallSnippet({ text, label }: { text: string; label: string }) {
  const [status, setStatus] = useState("");
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setStatus("Copied");
    } catch {
      setStatus("Select and copy the text below.");
    }
  }
  return (
    <div className="min-w-0 rounded-lg border border-zinc-800 bg-zinc-950">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 px-4 py-2">
        <span className="text-xs text-zinc-400">{label}</span>
        <button type="button" onClick={copy} aria-label={`Copy ${label}`} className="rounded px-2 py-1 text-xs text-violet-300 hover:bg-violet-500/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400">Copy</button>
      </div>
      <pre className="overflow-x-auto p-4 text-xs leading-6 text-zinc-200"><code>{text}</code></pre>
      <p role="status" className="px-4 pb-2 text-xs text-zinc-400">{status}</p>
    </div>
  );
}
