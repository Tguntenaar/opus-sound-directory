import { NextResponse } from "next/server";
import {
  getAllStats,
  incrementStat,
  isValidEntryId,
  isValidEvent,
} from "@/lib/stats-kv";

export async function GET() {
  const stats = await getAllStats();
  return NextResponse.json({ stats });
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!body || typeof body !== "object") {
    return NextResponse.json({ error: "Invalid id or event" }, { status: 400 });
  }
  const { id, event } = body as { id?: unknown; event?: unknown };
  if (typeof id !== "string" || typeof event !== "string" || !isValidEvent(event) || !(await isValidEntryId(id))) {
    return NextResponse.json({ error: "Invalid id or event" }, { status: 400 });
  }

  try {
    const stats = await incrementStat(id, event);
    return NextResponse.json({ id, stats });
  } catch {
    return NextResponse.json({ error: "Statistics unavailable" }, { status: 503 });
  }
}
