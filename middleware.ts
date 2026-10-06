import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { proxyPosthogIngest } from "@/lib/posthog-proxy";
import {
  getReviewAdminToken,
  readReviewTokenFromCookieHeader,
  readReviewTokenFromRequest,
} from "@/lib/review-auth";

const CANONICAL_HOST = "opussounds.directory";

async function reviewTokenFromRequest(request: NextRequest): Promise<string | null> {
  const fromRequest = readReviewTokenFromRequest(request);
  if (fromRequest) return fromRequest;
  return readReviewTokenFromCookieHeader(request.headers.get("cookie"));
}

async function guardAdminReview(request: NextRequest): Promise<NextResponse | null> {
  if (request.nextUrl.pathname !== "/admin/review") return null;
  const configured = await getReviewAdminToken();
  if (!configured) {
    return new NextResponse("Unauthorized", { status: 401 });
  }
  const provided = await reviewTokenFromRequest(request);
  if (!provided || provided !== configured) {
    return new NextResponse("Unauthorized", { status: 401 });
  }
  const queryToken = request.nextUrl.searchParams.get("token")?.trim();
  if (queryToken === configured) {
    const response = NextResponse.next();
    response.cookies.set("review_admin_token", configured, {
      httpOnly: true,
      sameSite: "strict",
      path: "/",
      secure: request.nextUrl.protocol === "https:",
    });
    return response;
  }
  return null;
}

function isPosthogIngestPath(pathname: string): boolean {
  return (
    pathname.startsWith("/ingest") || pathname.startsWith("/api/ingest")
  );
}

export async function middleware(request: NextRequest) {
  if (isPosthogIngestPath(request.nextUrl.pathname)) {
    return proxyPosthogIngest(request);
  }

  const adminGuard = await guardAdminReview(request);
  if (adminGuard) return adminGuard;

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
