import type { AiReviewResult, ScreeningFlags } from "./submit-types.ts";

export function parseReviewJson(text: string, model: string): AiReviewResult | null {
  try {
    const trimmed = text.trim().replace(/^```(?:json)?\s*/, "").replace(/\s*```$/, "");
    const obj = JSON.parse(trimmed);
    if (!obj || !["safe", "suspicious", "malicious"].includes(obj.verdict) ||
      !Number.isInteger(obj.quality) || obj.quality < 1 || obj.quality > 5 ||
      typeof obj.categoryFit !== "boolean" ||
      !Array.isArray(obj.reasons) || !obj.reasons.every((v: unknown) => typeof v === "string") ||
      !Array.isArray(obj.rightsConcerns) || !obj.rightsConcerns.every((v: unknown) => typeof v === "string")) return null;
    return { verdict: obj.verdict, quality: obj.quality, categoryFit: obj.categoryFit,
      reasons: obj.reasons, rightsConcerns: obj.rightsConcerns, complete: true, model, reviewedAt: new Date().toISOString() };
  } catch { return null; }
}

export function reviewAllowsPublication(review: AiReviewResult, flags: ScreeningFlags): boolean {
  return review.complete === true && review.verdict === "safe" && review.quality >= 3 &&
    review.categoryFit === true && review.rightsConcerns.length === 0 && !flags.spam &&
    !flags.bannedPatterns?.length && !flags.suspiciousClaims?.length;
}
