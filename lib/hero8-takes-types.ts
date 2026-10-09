export type Hero8CodexTakeRow = {
  entryId: string;
  takeId: string;
  codexTake: number;
  lufs: number;
  truePeakDbTp: number;
  durationSec: number;
  mp3: string;
};

export type EntryTakeId = "opus" | `codex-${1 | 2 | 3}`;

export type EntryTakeDef = {
  id: EntryTakeId;
  label: string;
  modelId: string;
  mp3: string;
  wav?: string;
  lufs?: number;
  truePeakDbTp?: number;
};
