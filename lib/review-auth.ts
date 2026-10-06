export async function getReviewAdminToken(): Promise<string | undefined> {
  try {
    const { env } = await import("cloudflare:workers");
    const token = (env as { REVIEW_ADMIN_TOKEN?: string }).REVIEW_ADMIN_TOKEN;
    if (token) return token;
  } catch {
    // not in workerd
  }
  return process.env.REVIEW_ADMIN_TOKEN;
}

export function readReviewTokenFromRequest(request: Request): string | null {
  const auth = request.headers.get("authorization");
  if (auth?.toLowerCase().startsWith("bearer ")) {
    return auth.slice(7).trim();
  }
  const url = new URL(request.url);
  const q = url.searchParams.get("token");
  if (q) return q.trim();
  const headerToken = request.headers.get("x-review-admin-token")?.trim();
  if (headerToken) return headerToken;
  return readReviewTokenFromCookieHeader(request.headers.get("cookie"));
}

export function readReviewTokenFromCookieHeader(
  cookieHeader: string | null | undefined,
): string | null {
  if (!cookieHeader) return null;
  const match = /(?:^|;\s*)review_admin_token=([^;]*)/.exec(cookieHeader);
  if (!match) return null;
  try {
    return decodeURIComponent(match[1].trim());
  } catch {
    return match[1].trim();
  }
}

export async function isReviewAuthorized(request: Request): Promise<boolean> {
  const configured = await getReviewAdminToken();
  if (!configured) return false;
  const provided = readReviewTokenFromRequest(request);
  return Boolean(provided && provided === configured);
}
