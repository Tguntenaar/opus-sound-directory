/** Tracks focused sound card and last-played id for global Space shortcut. */

let focusedEntryId: string | null = null;
let lastPlayedEntryId: string | null = null;

export function setFocusedSoundCard(id: string | null) {
  focusedEntryId = id;
}

export function setLastPlayedEntryId(id: string | null) {
  lastPlayedEntryId = id;
}

export function getPlaybackShortcutTarget(): string | null {
  if (focusedEntryId) return focusedEntryId;
  return lastPlayedEntryId;
}
