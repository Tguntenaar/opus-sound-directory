import type { Metadata } from "next";
import { headers } from "vinext/shims/headers";
import { ContributorAccount } from "@/components/contributor-account";
import { getEnabledAuthProviders, sessionContributorFromHeaders } from "@/lib/auth";
import type { AuthProvider } from "@/lib/auth-config";

export const metadata: Metadata = { title: "Your account", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

export default async function AccountPage() {
  const headerList = await headers();
  let initialUser: { id: string; name: string; email: string; emailVerified: boolean } | null = null;
  let initialProviders: AuthProvider[] = [];
  try {
    [initialUser, initialProviders] = await Promise.all([
      sessionContributorFromHeaders(headerList),
      getEnabledAuthProviders(),
    ]);
  } catch {
    initialUser = null;
    initialProviders = [];
  }
  return <div className="mx-auto max-w-2xl"><h1 className="text-3xl font-semibold text-zinc-50">Your account</h1>
    <ContributorAccount initialUser={initialUser} initialProviders={initialProviders} />
  </div>;
}
