import { NextResponse } from "next/server";
import { getCommunityCode } from "@/lib/community-kv";

type Props = { params: Promise<{ slug: string }> };

export async function GET(_request: Request, { params }: Props) {
  const { slug } = await params;
  const code = await getCommunityCode(slug);
  if (!code) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  return new NextResponse(code, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=300",
    },
  });
}
