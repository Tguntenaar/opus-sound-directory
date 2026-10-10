"use client";

import { createContext, useContext, type ReactNode } from "react";
import type { AuthProvider } from "@/lib/auth-config";

const AuthProvidersContext = createContext<AuthProvider[]>([]);

export function AuthProvidersProvider({ providers, children }: { providers: AuthProvider[]; children: ReactNode }) {
  return <AuthProvidersContext.Provider value={providers}>{children}</AuthProvidersContext.Provider>;
}

export function useAuthProviders() {
  return useContext(AuthProvidersContext);
}
