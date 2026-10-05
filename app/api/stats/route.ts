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
  let body: { id?: string; event?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const { id, event } = body;
  if (!id || !event || !isValidEntryId(id) || !isValidEvent(event)) {
    return NextResponse.json({ error: "Invalid id or event" }, { status: 400 });
  }

  const stats = await incrementStat(id, event);
  return NextResponse.json({ id, stats });
}
