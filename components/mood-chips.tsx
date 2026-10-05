import type { SoundEntry } from "@/lib/entries";
import { formatMood, TEMPO_LABELS, type TempoSlug } from "@/lib/mood";

export function MoodChips({
  entry,
  compact = false,
}: {
  entry: Pick<SoundEntry, "mood" | "tempo">;
  compact?: boolean;
}) {
  const moods = entry.mood ?? [];
  if (moods.length === 0 && !entry.tempo) return null;

  const chip =
    compact
      ? "rounded-md bg-violet-500/10 px-1.5 py-0.5 text-[10px] font-medium text-violet-200/90"
      : "rounded-md border border-violet-500/25 bg-violet-500/10 px-2 py-0.5 text-xs font-medium text-violet-200";

  const tempoChip =
    compact
      ? "rounded-md bg-zinc-800/90 px-1.5 py-0.5 text-[10px] text-zinc-400"
      : "rounded-md border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-xs text-zinc-400";

  return (
    <div className="flex flex-wrap gap-1.5" aria-label="Mood and tempo">
      {entry.tempo && TEMPO_LABELS[entry.tempo as TempoSlug] && (
        <span className={tempoChip}>{TEMPO_LABELS[entry.tempo as TempoSlug]}</span>
      )}
      {moods.map((m) => (
        <span key={m} className={chip}>{formatMood(m)}</span>
      ))}
    </div>
  );
}
