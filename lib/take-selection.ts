import type { EntryTakeDef, EntryTakeId } from "@/lib/hero8-takes-types";

export type TakeVoteMap = Record<string, number>;

/** Highest vote wins; ties keep the Opus catalog default (`opus`). */
export function pickDefaultTakeId(
  takes: EntryTakeDef[],
  votes: TakeVoteMap,
): EntryTakeId {
  if (takes.length === 0) return "opus";
  const opus = takes.find((t) => t.id === "opus");
  const fallback = (opus?.id ?? takes[0].id) as EntryTakeId;

  let maxVotes = 0;
  const leaders: EntryTakeId[] = [];
  for (const take of takes) {
    const count = votes[take.id] ?? 0;
    if (count > maxVotes) {
      maxVotes = count;
      leaders.length = 0;
      leaders.push(take.id);
    } else if (count === maxVotes && count > 0) {
      leaders.push(take.id);
    }
  }

  if (maxVotes <= 0) return fallback;
  if (leaders.length > 1) return fallback;
  return leaders[0];
}

export function pickDefaultTake(
  takes: EntryTakeDef[],
  votes: TakeVoteMap,
): EntryTakeDef {
  const id = pickDefaultTakeId(takes, votes);
  return takes.find((t) => t.id === id) ?? takes[0];
}
