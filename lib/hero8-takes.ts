import { TARGET_OPUS_MODEL_ID, CODEX_MODEL_ID } from "@/lib/model-display";
import { HERO8_CODEX_TAKE_ROWS } from "@/lib/hero8-takes.generated";
import type { EntryTakeDef, EntryTakeId } from "@/lib/hero8-takes-types";
import { passesTakeQuality } from "@/lib/hero8-take-quality";
import type { SoundEntry } from "@/lib/entries-types";

/** Catalog entry ids that participate in hero8 take voting. */
export const HERO8_VOTING_ENTRY_IDS: readonly string[] = [
  "heavy-boom-meme",
  "whoosh-pass-by",
  "ui-cozy-sprite",
  "endless-riser-shepard",
  "dialup-modem-56k",
  "wah-wah-fail",
  "arcade-game-over",
  "trailer-braam-hit",
  "game-coin-pickup",
];

const CODEX_LABELS: Record<number, string> = {
  1: "A",
  2: "B",
  3: "C",
};

export function isHero8VotingEntry(entryId: string): boolean {
  return HERO8_VOTING_ENTRY_IDS.includes(entryId);
}

function codexTakesForEntry(entryId: string): EntryTakeDef[] {
  return HERO8_CODEX_TAKE_ROWS.filter((r) => r.entryId === entryId)
    .filter((r) => passesTakeQuality(r))
    .map((r) => ({
      id: r.takeId as EntryTakeId,
      label: CODEX_LABELS[r.codexTake] ?? String(r.codexTake),
      modelId: CODEX_MODEL_ID,
      mp3: r.mp3,
      wav: r.wav,
      lufs: r.lufs,
      truePeakDbTp: r.truePeakDbTp,
    }));
}

/** All takes available for voting on an entry (Opus catalog default + passing Codex takes). */
export function entryTakesFor(entry: Pick<SoundEntry, "id" | "modelId" | "assets">): EntryTakeDef[] {
  if (!isHero8VotingEntry(entry.id)) return [];
  const codex = codexTakesForEntry(entry.id);
  if (codex.length === 0) return [];

  const opus: EntryTakeDef = {
    id: "opus",
    label: "Opus",
    modelId: entry.modelId || TARGET_OPUS_MODEL_ID,
    mp3: entry.assets.mp3 ?? "",
    wav: entry.assets.wav,
    lufs: undefined,
    truePeakDbTp: undefined,
  };
  if (!opus.mp3) return codex;
  return [opus, ...codex];
}

export function isValidTakeForEntry(entryId: string, takeId: string): boolean {
  if (!isHero8VotingEntry(entryId)) return false;
  if (takeId === "opus") return true;
  return HERO8_CODEX_TAKE_ROWS.some(
    (r) => r.entryId === entryId && r.takeId === takeId && passesTakeQuality(r),
  );
}

export function takeById(
  entry: Pick<SoundEntry, "id" | "modelId" | "assets">,
  takeId: EntryTakeId,
): EntryTakeDef | undefined {
  return entryTakesFor(entry).find((t) => t.id === takeId);
}
