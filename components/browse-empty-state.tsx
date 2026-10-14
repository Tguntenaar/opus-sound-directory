"use client";

import { BookmarkX, SearchX } from "lucide-react";

type Props = {
  bookmarksOnly: boolean;
  hasQuery: boolean;
  hasFacetFilters: boolean;
  onClearSearch: () => void;
  onClearFacets: () => void;
  onShowAll: () => void;
};

export function BrowseEmptyState({
  bookmarksOnly,
  hasQuery,
  hasFacetFilters,
  onClearSearch,
  onClearFacets,
  onShowAll,
}: Props) {
  const Icon = bookmarksOnly ? BookmarkX : SearchX;
  let title = "No sounds match";
  let hint = "Try another search or clear filters.";
  let action: { label: string; onClick: () => void } | null = null;

  if (bookmarksOnly) {
    title = "No bookmarked sounds";
    hint = "Save sounds from a card or entry page.";
    action = { label: "Show all sounds", onClick: onShowAll };
  } else if (hasQuery && hasFacetFilters) {
    action = {
      label: "Reset search and filters",
      onClick: () => {
        onClearSearch();
        onClearFacets();
      },
    };
  } else if (hasQuery) {
    title = "No results";
    hint = "Try a shorter or different term.";
    action = { label: "Clear search", onClick: onClearSearch };
  } else if (hasFacetFilters) {
    action = { label: "Clear filters", onClick: onClearFacets };
  }

  return (
    <div
      role="status"
      className="animate-fade-in flex flex-col items-center gap-4 py-16 text-center"
    >
      <div
        className="flex h-12 w-12 items-center justify-center rounded-full border border-zinc-800/90 bg-zinc-900/40 text-zinc-500"
        aria-hidden
      >
        <Icon className="h-5 w-5" strokeWidth={1.75} />
      </div>
      <div className="max-w-xs space-y-1">
        <p className="text-sm font-medium text-zinc-400">{title}</p>
        <p className="text-xs leading-relaxed text-zinc-600">{hint}</p>
      </div>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="rounded-lg border border-zinc-800 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:border-zinc-600 hover:bg-zinc-900/60 hover:text-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
