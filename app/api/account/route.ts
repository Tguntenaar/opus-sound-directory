import { authUnavailable, getAccountEnv, sessionContributor } from "@/lib/auth";
import { enabledProviders } from "@/lib/auth-config";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    const env = await getAccountEnv();
    const user = await sessionContributor(request);
    return Response.json({ user, providers: enabledProviders(env) }, { headers: { "Cache-Control": "no-store" } });
  } catch { return authUnavailable(); }
}
