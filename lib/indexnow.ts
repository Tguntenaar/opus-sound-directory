/** IndexNow API key (public verification file at /{key}.txt). Override via INDEXNOW_KEY env at build. */
export const INDEXNOW_KEY =
  process.env.INDEXNOW_KEY?.trim() || "opus-sounds-directory-indexnow-key-2026";

export const INDEXNOW_KEY_LOCATION = `https://opussounds.directory/${INDEXNOW_KEY}.txt`;
