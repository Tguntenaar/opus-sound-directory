import { createAuth, enabledProviders, type AuthProvider, type AuthSettings } from "./auth-config";

export async function getAccountEnv() {
  const { env } = await import("cloudflare:workers");
  return env as typeof env & AuthSettings;
}

export async function getAuth() {
  const env = await getAccountEnv();
  return createAuth(env.ACCOUNTS_DB, env);
}

export type Contributor = { id: string; email: string; emailVerified: boolean; name: string };

export async function getEnabledAuthProviders(): Promise<AuthProvider[]> {
  try {
    return enabledProviders(await getAccountEnv());
  } catch {
    return [];
  }
}

export async function sessionContributor(request: Request): Promise<Contributor | null> {
  return sessionContributorFromHeaders(request.headers);
}

export async function sessionContributorFromHeaders(headerList: Headers): Promise<Contributor | null> {
  const auth = await getAuth();
  const session = await auth.api.getSession({ headers: headerList });
  return session?.user ?? null;
}

/** MCP keys deliberately cannot create browser sessions or administer other keys. */
export async function mcpContributor(request: Request, permission: "create" | "read-own"): Promise<Contributor | null> {
  const header = request.headers.get("authorization") || "";
  const match = /^Bearer (opus_[A-Za-z0-9_-]+)$/i.exec(header);
  if (!match) return null;
  const auth = await getAuth();
  const result = await auth.api.verifyApiKey({ body: {
    key: match[1], permissions: { submissions: [permission] },
  } });
  if (!result.valid || !result.key) return null;
  const context = await auth.$context;
  return await context.internalAdapter.findUserById(result.key.referenceId);
}

export function sameOriginMutation(request: Request): boolean {
  const origin = request.headers.get("origin");
  return !!origin && origin === new URL(request.url).origin;
}

export function authUnavailable() {
  return Response.json({ error: "Sign-in is temporarily unavailable. Please try again later." }, {
    status: 503, headers: { "Cache-Control": "no-store" },
  });
}
