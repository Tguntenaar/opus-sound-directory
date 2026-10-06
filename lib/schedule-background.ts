import { getRequestExecutionContext } from "vinext/shims/request-context";

/** Keep background work alive on Cloudflare Workers; best-effort elsewhere. */
export function scheduleBackground(work: Promise<unknown>): void {
  const ctx = getRequestExecutionContext();
  if (ctx) {
    ctx.waitUntil(work);
    return;
  }
  void work;
}
