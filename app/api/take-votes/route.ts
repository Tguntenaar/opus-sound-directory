import { NextResponse } from "next/server";
import {
  castTakeVote,
  getAllTakeVotes,
  getTakeVotesForEntry,
} from "@/lib/take-votes-kv";
import { isHero8VotingEntry } from "@/lib/hero8-takes";
import { hashDistinctSuffix } from "@/lib/posthog-server";

const VOTER_COOKIE = "osd_take_voter";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

function clientFingerprint(request: Request): string {
  const ip =
    request.headers.get("cf-connecting-ip") ??
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "unknown";
  return ip.slice(0, 120);
}

function voterIdFromRequest(request: Request): string {
  const cookie = request.headers.get("cookie") ?? "";
  const match = cookie.match(new RegExp(`${VOTER_COOKIE}=([^;]+)`));
  return match?.[1]?.trim() || "";
}

function withVoterCookie(response: NextResponse, voterId: string): NextResponse {
  response.headers.append(
    "Set-Cookie",
    `${VOTER_COOKIE}=${voterId}; Path=/; Max-Age=${COOKIE_MAX_AGE}; HttpOnly; SameSite=Lax; Secure`,
  );
  return response;
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const entryId = url.searchParams.get("entryId");
  if (entryId) {
    if (!isHero8VotingEntry(entryId)) {
      return NextResponse.json({ error: "Unknown entry" }, { status: 404 });
    }
    const votes = await getTakeVotesForEntry(entryId);
    return NextResponse.json({ entryId, votes });
  }
  const votes = await getAllTakeVotes();
  return NextResponse.json({ votes });
}

export async function POST(request: Request) {
  let body: { entryId?: string; takeId?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const { entryId, takeId } = body;
  if (!entryId || !takeId) {
    return NextResponse.json({ error: "Missing entryId or takeId" }, { status: 400 });
  }

  let voterId = voterIdFromRequest(request);
  if (!voterId) {
    voterId = crypto.randomUUID();
  }

  const fingerprint = await hashDistinctSuffix(clientFingerprint(request));
  const result = await castTakeVote(entryId, takeId, voterId, fingerprint);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: result.status });
  }

  const res = NextResponse.json({
    entryId,
    takeId,
    votes: result.votes,
    alreadyVoted: result.alreadyVoted ?? false,
  });
  return withVoterCookie(res, voterId);
}
