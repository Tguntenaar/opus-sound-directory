/** Minimum count shown as a number on the public site (below → "New" badge). */
export const NEW_BADGE_THRESHOLD = 10;

export function isLowPublicStatCount(count: number): boolean {
  return count < NEW_BADGE_THRESHOLD;
}

export function shouldShowNewStatBadge(counts: readonly number[]): boolean {
  return counts.some(isLowPublicStatCount);
}

export function isPublicStatCountVisible(count: number): boolean {
  return !isLowPublicStatCount(count);
}
