import type { ReactNode } from "react";
import { AuthProvidersProvider } from "@/components/auth-providers";
import { getEnabledAuthProviders } from "@/lib/auth";

export default async function SubmitLayout({ children }: { children: ReactNode }) {
  const providers = await getEnabledAuthProviders();
  return <AuthProvidersProvider providers={providers}>{children}</AuthProvidersProvider>;
}
