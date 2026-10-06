import type { SponsorPackageId } from "@/lib/sponsor-packages";

export type SponsorLead = {
  id: string;
  createdAt: string;
  companyName: string;
  contactName: string;
  email: string;
  website: string;
  packages: SponsorPackageId[];
  budgetRange: string;
  message: string;
  logoUrl?: string;
  ref?: string;
};

export type SponsorLeadInput = Omit<SponsorLead, "id" | "createdAt">;
