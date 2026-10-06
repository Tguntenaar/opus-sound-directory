import type { SoundEntry } from "@/lib/entries-types";

export const COMMUNITY_MODEL_ID = "community";

export type CommunitySoundEntry = SoundEntry & {
  isCommunity: true;
  submissionId: string;
  author?: { name?: string; url?: string };
  /** True when vetted https mp3/wav is embedded */
  hasRenderedAudio: boolean;
  /** Code is served from /api/community/[slug]/code */
  codeApiPath: string;
};

export function isCommunityEntry(
  entry: SoundEntry,
): entry is CommunitySoundEntry {
  return Boolean((entry as CommunitySoundEntry).isCommunity);
}
