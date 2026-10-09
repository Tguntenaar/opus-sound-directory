import type { Metadata } from "next";
import { ContributorAccount } from "@/components/contributor-account";
export const metadata: Metadata = { title: "Your account", robots: { index: false, follow: false } };
export default function AccountPage() {
  return <div className="mx-auto max-w-2xl"><h1 className="text-3xl font-semibold text-zinc-50">Your sounds, your contribution.</h1>
    <p className="mt-3 text-sm leading-relaxed text-zinc-400">Sign in to contribute sounds, follow their review, and connect your agents. Browsing and downloading sounds are open to everyone.</p>
    <ContributorAccount />
  </div>;
}
