import type { AuthProvider } from "./auth-config";

/** Whether to render the signed-out contributor sign-in card (including provider buttons). */
export function shouldShowContributorSignIn(
  user: unknown,
  loading: boolean,
  providers: readonly AuthProvider[],
  sessionKnown: boolean,
): boolean {
  if (user) return false;
  if (!loading) return true;
  if (sessionKnown) return true;
  return providers.length > 0;
}

/** Avoid showing a false empty sign-in state in the bookmark dialog before providers are loaded. */
export function shouldShowBookmarkSignInUnavailable(
  providersKnown: boolean,
  providers: readonly AuthProvider[],
  error: string,
): boolean {
  return providersKnown && providers.length === 0 && !error;
}
