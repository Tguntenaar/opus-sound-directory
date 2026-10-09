"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ArrowUpRight, Search, X } from "lucide-react";
import type { SearchResults } from "@/lib/search-records";
import { CATEGORIES } from "@/lib/categories";
import { SearchPreview } from "@/components/search-preview";

export function GlobalSearch() {
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [active, setActive] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [shortcut, setShortcut] = useState("⌘K");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setShortcut(/Mac|iPhone|iPad/.test(navigator.platform) ? "⌘K" : "Ctrl K");
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k" && !event.altKey && !event.repeat) {
        event.preventDefault();
        setOpen((value) => !value);
      }
    }
    window.addEventListener("keydown", onKey);
    setReady(true);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => { setOpen(false); }, [pathname]);

  useEffect(() => {
    if (!open) {
      dialog.current?.close();
      return;
    }
    dialog.current?.showModal();
    input.current?.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = overflow; };
  }, [open]);

  useEffect(() => {
    setResults(null);
    setError("");
    setActive(0);
    const value = query.trim();
    if (!open || value.length < 2) {
      setLoading(false);
      return;
    }
    setLoading(true);
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(value)}`, { signal: controller.signal });
        if (!response.ok) throw new Error("Search failed");
        const data: SearchResults = await response.json();
        if (!controller.signal.aborted) setResults(data);
      } catch {
        if (!controller.signal.aborted) setError("Search is unavailable. Try again.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [open, query, attempt]);

  useEffect(() => {
    document.getElementById(`sound-search-result-${active}`)?.scrollIntoView({ block: "nearest" });
  }, [active]);

  function select(slug: string) {
    setOpen(false);
    router.push(`/e/${encodeURIComponent(slug)}`);
  }

  return <>
    <button type="button" disabled={!ready} onClick={() => setOpen(true)} aria-label="Search all sounds" aria-haspopup="dialog" aria-keyshortcuts="Meta+K Control+K"
      className="inline-flex h-9 items-center gap-2 rounded-lg px-2 text-zinc-400 transition-colors hover:bg-zinc-900 hover:text-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400">
      <Search className="h-4 w-4" aria-hidden />
      <kbd className="hidden rounded border border-zinc-800 px-1.5 py-0.5 text-[10px] sm:inline">{shortcut}</kbd>
    </button>
    <dialog ref={dialog} aria-labelledby="sound-search-title" onCancel={(event) => { event.preventDefault(); setOpen(false); }}
      onClick={(event) => { if (event.target === dialog.current) setOpen(false); }}
      onKeyDown={(event) => {
        // Keep page-level playback and grid shortcuts out of the dialog.
        event.stopPropagation();
        if (event.key === "Tab") {
          const controls = dialog.current?.querySelectorAll<HTMLElement>('input:not(:disabled), button:not(:disabled), a[href]');
          const first = controls?.[0];
          const last = controls?.[controls.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
          event.preventDefault();
          setOpen(false);
        }
      }}
      className="fixed inset-x-0 top-[12vh] m-0 mx-auto w-[calc(100%-2rem)] max-w-xl overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 p-0 text-zinc-100 shadow-2xl backdrop:bg-black/70 backdrop:backdrop-blur-sm">
      <div>
        <h2 id="sound-search-title" className="sr-only">Search all sounds</h2>
        <div className="flex items-center gap-3 border-b border-zinc-800 px-4">
          <Search className="h-5 w-5 shrink-0 text-zinc-500" aria-hidden />
          <input ref={input} role="combobox" aria-label="Search all sounds" aria-autocomplete="list" aria-haspopup="grid" aria-expanded={Boolean(results?.hits.length)}
            aria-controls="sound-search-results" aria-activedescendant={results?.hits[active] ? `sound-search-result-${active}` : undefined}
            value={query} maxLength={200} placeholder="Search sounds…" autoComplete="off" spellCheck={false}
            onChange={(event) => { setQuery(event.target.value); setResults(null); }}
            onKeyDown={(event) => {
              if (event.nativeEvent.isComposing) return;
              const hits = results?.hits ?? [];
              if ((event.key === "ArrowDown" || event.key === "ArrowUp") && hits.length) {
                event.preventDefault();
                setActive((value) => (value + (event.key === "ArrowDown" ? 1 : -1) + hits.length) % hits.length);
              }
              if (event.key === "Enter" && hits[active]) { event.preventDefault(); select(hits[active].slug); }
            }}
            className="min-w-0 flex-1 bg-transparent py-5 text-base outline-none placeholder:text-zinc-500" />
          <button type="button" aria-label="Close search" onClick={() => setOpen(false)} className="rounded-lg p-2 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-100 focus-visible:outline-violet-400"><X className="h-4 w-4" aria-hidden /></button>
        </div>
        <div className="max-h-[55dvh] overflow-y-auto p-2">
          <p role="status" className={results?.hits.length ? "sr-only" : "px-3 py-8 text-center text-sm text-zinc-500"}>
            {loading ? "Searching…" : error || (query.trim().length < 2 ? "Type at least two characters to find a sound." : results ? results.nbHits ? `${results.nbHits} sounds found.` : "No sounds found. Try another word." : "")}
          </p>
          {error && <button type="button" onClick={() => setAttempt((value) => value + 1)} className="mx-auto mb-4 block rounded-lg border border-zinc-700 px-3 py-2 text-sm">Try again</button>}
          <ul id="sound-search-results" role="grid" aria-label="Sounds" aria-busy={loading}>
            {results?.hits.map((hit, index) => <li key={hit.objectID} id={`sound-search-result-${index}`} role="row" aria-selected={index === active}
              onPointerMove={() => setActive(index)} onFocus={() => setActive(index)}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 ${index === active ? "bg-zinc-800/80" : "hover:bg-zinc-900"}`}>
              <div role="gridcell">{open && hit.previewUrl ? <SearchPreview hit={hit} /> : <span className="inline-block w-10 text-center text-xs text-zinc-600" title="No audio preview">—</span>}</div>
              <div role="gridcell" className="min-w-0 flex-1">
                <button type="button" onClick={() => select(hit.slug)} aria-label={`Open ${hit.title}`} className="flex w-full items-center gap-3 rounded py-2 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400">
                  <span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{hit.title}</span><span className="mt-1 block truncate text-xs text-zinc-500">{CATEGORIES[hit.category]?.label ?? hit.category} · {Number(hit.durationSec.toFixed(1))}s</span></span>
                  <ArrowUpRight className="h-4 w-4 shrink-0 text-zinc-500" aria-hidden />
                </button>
              </div>
            </li>)}
          </ul>
        </div>
        <div className="flex justify-between border-t border-zinc-800 px-4 py-3 text-[11px] text-zinc-500"><span>↑ ↓ Navigate · Enter Open · Esc Close</span>{results?.provider === "algolia" && <a href="https://www.algolia.com/" target="_blank" rel="noreferrer" className="hover:text-zinc-300">Search by Algolia</a>}</div>
      </div>
    </dialog>
  </>;
}
