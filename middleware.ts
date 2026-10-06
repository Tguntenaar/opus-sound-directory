import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const CANONICAL_HOST = "opussounds.directory";

export function middleware(request: NextRequest) {
  const hostHeader = request.headers.get("host") ?? "";
  const host = hostHeader.split(":")[0]?.toLowerCase() ?? "";

  if (host === `www.${CANONICAL_HOST}`) {
    const url = request.nextUrl.clone();
    url.protocol = "https:";
    url.host = CANONICAL_HOST;
    return NextResponse.redirect(url, 301);
  }

  const isLocal = host === "localhost" || host === "127.0.0.1";
  if (!isLocal && host !== CANONICAL_HOST) {
    const response = NextResponse.next();
    response.headers.set("X-Robots-Tag", "noindex, nofollow");
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
