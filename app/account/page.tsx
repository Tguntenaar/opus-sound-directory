import type { Metadata } from "next";
import { ContributorAccount } from "@/components/contributor-account";
export const metadata: Metadata = { title: "Your account", robots: { index: false, follow: false } };
export default function AccountPage() {
  return <div className="mx-auto max-w-2xl"><h1 className="text-3xl font-semibold text-zinc-50">Your account</h1>
    <ContributorAccount />
  </div>;
}
