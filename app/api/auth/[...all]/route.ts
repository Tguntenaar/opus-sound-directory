import { getAuth, authUnavailable } from "@/lib/auth";
export const dynamic = "force-dynamic";
async function handle(request: Request) {
  try {
    const auth = await getAuth();
    const response = await auth.handler(request);
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    return authUnavailable();
  }
}
export const GET = handle;
export const POST = handle;
