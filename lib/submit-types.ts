export type SubmissionSource = "web" | "mcp";

export type SubmissionStatus =
  | "scanning"
  | "live"
  | "pending_review"
  | "rejected";

export type ScreeningFlags = {
  spam?: boolean;
  bannedPatterns?: string[];
  suspiciousClaims?: string[];
  notes?: string[];
};

export type AiReviewResult = {
  verdict: "safe" | "suspicious" | "malicious";
  quality: number;
  reasons: string[];
  categoryFit: boolean;
  model: string;
  reviewedAt: string;
};

export type SubmitEntryInput = {
  title: string;
  prompt: string;
  email: string;
  category: string;
  mood: string[];
  codeSnippet?: string;
  codeUrl?: string;
  /** MCP: full generate.py body */
  code?: string;
  durationSec?: number;
  tempo?: "slow" | "medium" | "fast";
  audioUrl?: string;
  author_name?: string;
  author_url?: string;
  notes?: string;
};

export type SubmitEntry = SubmitEntryInput & {
  id: string;
  createdAt: string;
  source: SubmissionSource;
  status: SubmissionStatus;
  screening?: ScreeningFlags;
  aiReview?: AiReviewResult;
  reviewerNote?: string;
  /** Published community slug when status is live */
  communitySlug?: string;
  /** Resolved generate.py stored for review (web MCP) */
  storedCode?: string;
};
