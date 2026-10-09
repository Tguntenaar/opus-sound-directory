"use client";

import { useId, useState, type ReactNode } from "react";

/** Installation snippets do not increment sound-copy statistics. */
export function InstallSnippet({ text, label, tabs, panelId, labelledBy }: { text: string; label: string; tabs?: ReactNode; panelId?: string; labelledBy?: string }) {
  const [copyResult, setCopyResult] = useState({ text: "", status: "" });
  const status = copyResult.text === text ? copyResult.status : "";
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopyResult({ text, status: "Copied" });
    } catch {
      setCopyResult({ text, status: "Select and copy the text below." });
    }
  }
  return (
    <div className="min-w-0 rounded-lg border border-zinc-800 bg-zinc-950">
      {tabs}
      <div id={panelId} role={panelId ? "tabpanel" : undefined} aria-labelledby={labelledBy} tabIndex={panelId ? 0 : undefined}>
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 px-4 py-2">
          <span className="text-xs text-zinc-400">{label}</span>
          <button type="button" onClick={copy} aria-label={`Copy ${label}`} className="rounded px-2 py-1 text-xs text-violet-300 hover:bg-violet-500/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400">Copy</button>
        </div>
        <pre className="overflow-x-auto p-4 text-xs leading-6 text-zinc-200"><code>{text}</code></pre>
        <p role="status" className="px-4 pb-2 text-xs text-zinc-400">{status}</p>
      </div>
    </div>
  );
}

type HarnessSnippet = { name: string; text: string; label: string; description?: string };

export function HarnessSnippets({ snippets }: { snippets: HarnessSnippet[] }) {
  const [active, setActive] = useState(0);
  const id = useId();
  const snippet = snippets[active];
  if (!snippet) return null;

  return (
    <div>
      <InstallSnippet
        panelId={`${id}-panel`}
        labelledBy={`${id}-tab-${active}`}
        text={snippet.text}
        label={snippet.label}
        tabs={
          <div role="tablist" aria-label="Agent harness" className="flex overflow-x-auto border-b border-zinc-800 px-2">
            {snippets.map((item, index) => (
              <button
                key={item.name}
                id={`${id}-tab-${index}`}
                type="button"
                role="tab"
                aria-selected={active === index}
                aria-controls={`${id}-panel`}
                tabIndex={active === index ? 0 : -1}
                onClick={() => setActive(index)}
                onKeyDown={(event) => {
                  let next = index;
                  if (event.key === "ArrowRight") next = (index + 1) % snippets.length;
                  else if (event.key === "ArrowLeft") next = (index - 1 + snippets.length) % snippets.length;
                  else if (event.key === "Home") next = 0;
                  else if (event.key === "End") next = snippets.length - 1;
                  else return;
                  event.preventDefault();
                  setActive(next);
                  document.getElementById(`${id}-tab-${next}`)?.focus();
                }}
                className={`shrink-0 border-b-2 px-3 py-3 text-xs transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-4px] focus-visible:outline-violet-400 ${active === index ? "border-violet-400 text-violet-300" : "border-transparent text-zinc-400 hover:text-zinc-200"}`}
              >
                {item.name}
              </button>
            ))}
          </div>
        }
      />
      {snippet.description && <p className="mt-3 text-sm text-zinc-400">{snippet.description}</p>}
    </div>
  );
}
