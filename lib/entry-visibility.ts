export function isEntryHidden(entry: { hidden?: boolean }): boolean {
  return Boolean(entry.hidden);
}
