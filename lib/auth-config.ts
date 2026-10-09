import { betterAuth, type BetterAuthOptions } from "better-auth";
import { apiKey } from "@better-auth/api-key";

export type AuthSettings = {
  BETTER_AUTH_SECRET?: string;
  BETTER_AUTH_URL?: string;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
};

export function enabledProviders(settings: AuthSettings): ("github" | "google")[] {
  return [
    ...(settings.GITHUB_CLIENT_ID && settings.GITHUB_CLIENT_SECRET ? ["github" as const] : []),
    ...(settings.GOOGLE_CLIENT_ID && settings.GOOGLE_CLIENT_SECRET ? ["google" as const] : []),
  ];
}

export function createAuth(database: BetterAuthOptions["database"], settings: AuthSettings) {
  if (!database || !settings.BETTER_AUTH_SECRET || settings.BETTER_AUTH_SECRET.length < 32) {
    throw new Error("Account service is not configured");
  }
  const baseURL = settings.BETTER_AUTH_URL || "https://opussounds.directory";
  return betterAuth({
    appName: "Opus Sounds Directory",
    database,
    secret: settings.BETTER_AUTH_SECRET,
    baseURL,
    trustedOrigins: [new URL(baseURL).origin],
    emailAndPassword: { enabled: false },
    socialProviders: {
      ...(settings.GITHUB_CLIENT_ID && settings.GITHUB_CLIENT_SECRET ? {
        github: { clientId: settings.GITHUB_CLIENT_ID, clientSecret: settings.GITHUB_CLIENT_SECRET },
      } : {}),
      ...(settings.GOOGLE_CLIENT_ID && settings.GOOGLE_CLIENT_SECRET ? {
        google: { clientId: settings.GOOGLE_CLIENT_ID, clientSecret: settings.GOOGLE_CLIENT_SECRET },
      } : {}),
    },
    account: {
      encryptOAuthTokens: true,
      accountLinking: { enabled: true, disableImplicitLinking: true },
    },
    session: { expiresIn: 60 * 60 * 24 * 7, cookieCache: { enabled: false } },
    rateLimit: { enabled: true, storage: "database", window: 60, max: 60 },
    advanced: { ipAddress: { ipAddressHeaders: ["cf-connecting-ip"] } },
    plugins: [apiKey({
      defaultPrefix: "opus_",
      enableSessionForAPIKeys: false,
      keyExpiration: { defaultExpiresIn: 60 * 60 * 24 * 90, maxExpiresIn: 365 },
      rateLimit: { enabled: true, timeWindow: 60 * 1000, maxRequests: 60 },
      permissions: { defaultPermissions: { submissions: ["create", "read-own"] } },
    })],
  });
}
