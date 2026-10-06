import { NextResponse } from "next/server";
import { scheduleBackground } from "@/lib/schedule-background";
import { listSponsorLeads, saveSponsorLead } from "@/lib/sponsor-kv";
import { notifySponsorLead } from "@/lib/sponsor-notify";
import { isHoneypotDiscard, validateSponsorPayload } from "@/lib/sponsor-validate";

async function getAdminTokenFromEnv(): Promise<string | undefined> {
  try {
    const { env } = await import("cloudflare:workers");
    const token = (env as { SPONSOR_ADMIN_TOKEN?: string }).SPONSOR_ADMIN_TOKEN;
    if (token) return token;
  } catch {
    // not in workerd
  }
  return process.env.SPONSOR_ADMIN_TOKEN;
}

function readRequestToken(request: Request): string | null {
  const auth = request.headers.get("authorization");
  if (auth?.toLowerCase().startsWith("bearer ")) {
    return auth.slice(7).trim();
  }
  return request.headers.get("x-sponsor-admin-token")?.trim() ?? null;
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON" }, { status: 400 });
  }

  const result = validateSponsorPayload(body);
  if (!result.ok) {
    return NextResponse.json({ ok: false, error: result.error }, { status: 400 });
  }

  if (isHoneypotDiscard(result.data)) {
    return NextResponse.json({ ok: true });
  }

  const lead = await saveSponsorLead(result.data);
  scheduleBackground(notifySponsorLead(lead));
  const { captureServerEvent } = await import("@/lib/posthog-server");
  scheduleBackground(
    captureServerEvent({
      distinctId: `sponsor:${lead.id}`,
      event: "sponsor_form_submit",
      properties: {
        package_count: lead.packages.length,
        budget_range: lead.budgetRange,
        ...(lead.ref ? { ref: lead.ref } : {}),
      },
    }),
  );
  return NextResponse.json({ ok: true, id: lead.id });
}

export async function GET(request: Request) {
  const configured = await getAdminTokenFromEnv();
  if (!configured) {
    return NextResponse.json({ enabled: false, leads: [] });
  }

  const provided = readRequestToken(request);
  if (!provided || provided !== configured) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const leads = await listSponsorLeads(100);
  return NextResponse.json({ enabled: true, leads });
}
