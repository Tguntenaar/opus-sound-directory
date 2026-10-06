import { BUDGET_RANGES, SPONSOR_PACKAGES, type SponsorPackageId } from "@/lib/sponsor-packages";
import type { SponsorLeadInput } from "@/lib/sponsor-types";

const PACKAGE_IDS = new Set(SPONSOR_PACKAGES.map((p) => p.id));
const BUDGET_VALUES = new Set(BUDGET_RANGES.map((b) => b.value));

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type SponsorFormPayload = {
  companyName: string;
  contactName: string;
  email: string;
  website: string;
  packages: SponsorPackageId[];
  budgetRange: string;
  message: string;
  logoUrl?: string;
  /** Honeypot — must be empty */
  companyFax?: string;
  ref?: string;
};

export function validateSponsorPayload(body: unknown): {
  ok: true;
  data: SponsorLeadInput;
} | { ok: false; error: string } {
  if (!body || typeof body !== "object") {
    return { ok: false, error: "Invalid body" };
  }
  const b = body as Record<string, unknown>;

  if (typeof b.companyFax === "string" && b.companyFax.trim() !== "") {
    return { ok: true, data: honeypotDiscard() };
  }

  const companyName = trimStr(b.companyName, 120);
  const contactName = trimStr(b.contactName, 120);
  const email = trimStr(b.email, 200).toLowerCase();
  const website = trimStr(b.website, 500);
  const message = trimStr(b.message, 4000);
  const logoUrl = b.logoUrl ? trimStr(b.logoUrl, 500) : undefined;
  const ref = b.ref ? trimStr(b.ref, 120) : undefined;
  const budgetRange = trimStr(b.budgetRange, 40);

  if (!companyName) return { ok: false, error: "Company name is required" };
  if (!contactName) return { ok: false, error: "Contact name is required" };
  if (!email || !EMAIL_RE.test(email)) return { ok: false, error: "Valid work email is required" };
  if (!website) return { ok: false, error: "Website is required" };
  try {
    const u = new URL(website.startsWith("http") ? website : `https://${website}`);
    if (!u.hostname.includes(".")) return { ok: false, error: "Valid website URL is required" };
  } catch {
    return { ok: false, error: "Valid website URL is required" };
  }
  if (!BUDGET_VALUES.has(budgetRange as (typeof BUDGET_RANGES)[number]["value"])) {
    return { ok: false, error: "Select a budget range" };
  }
  if (!message || message.length < 20) {
    return { ok: false, error: "Message must be at least 20 characters" };
  }

  let packages: SponsorPackageId[] = [];
  if (Array.isArray(b.packages)) {
    packages = b.packages.filter(
      (p): p is SponsorPackageId => typeof p === "string" && PACKAGE_IDS.has(p as SponsorPackageId),
    );
  }
  if (packages.length === 0) {
    return { ok: false, error: "Select at least one package" };
  }

  if (logoUrl) {
    try {
      new URL(logoUrl);
    } catch {
      return { ok: false, error: "Logo URL must be a valid URL" };
    }
  }

  const normalizedWebsite = website.startsWith("http") ? website : `https://${website}`;

  return {
    ok: true,
    data: {
      companyName,
      contactName,
      email,
      website: normalizedWebsite,
      packages,
      budgetRange,
      message,
      logoUrl: logoUrl || undefined,
      ref: ref || undefined,
    },
  };
}

/** Bots get success without storing — caller should return { ok: true } only */
function honeypotDiscard(): SponsorLeadInput {
  return {
    companyName: "",
    contactName: "",
    email: "bot@invalid.local",
    website: "https://invalid.local",
    packages: ["custom"],
    budgetRange: "exploring",
    message: "",
  };
}

export function isHoneypotDiscard(data: SponsorLeadInput): boolean {
  return data.email === "bot@invalid.local";
}

function trimStr(value: unknown, max: number): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}
