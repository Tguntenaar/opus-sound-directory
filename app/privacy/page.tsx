import type { Metadata } from "next";
export const metadata: Metadata = { title: "Contributor privacy" };
export default function PrivacyPage() {
  return <article className="mx-auto max-w-2xl space-y-5 text-sm leading-relaxed text-zinc-400">
    <h1 className="text-3xl font-semibold text-zinc-50">Contributor privacy</h1>
    <p>Browsing and downloading sounds does not require an account. To submit a sound, sign in with GitHub or Google. We use the provider account identifier, name, email address, and email verification status to create your account and associate submissions with you.</p>
    <h2 className="text-xl font-medium text-zinc-100">What becomes public</h2>
    <p>A published sound includes its title, prompt, synthesis code, audio, metadata, and any public credit you choose. Your sign-in email, private account identifier, login credentials, and unpublished submissions are not part of the public directory.</p>
    <h2 className="text-xl font-medium text-zinc-100">Account and review records</h2>
    <p>Account and submission records are stored using Cloudflare. Session cookies keep you signed in. We retain submission ownership and review records so contributors can follow progress and administrators can investigate reports. Administrators can see the submitter’s account identifier and contact email, code, prompt, and review results.</p>
    <p>Submissions may be processed by automated services for code and content review. Warning emails to the directory administrator can contain your submission details, contact email, and review findings. Automated checks help surface concerns; they do not establish that a submission is lawful.</p>
    <h2 className="text-xl font-medium text-zinc-100">Agent access</h2>
    <p>Agent tokens are stored as hashes and can be revoked from your account. They allow submission and access to your own submission status, but do not grant account management access. Session and abuse-prevention records can include IP addresses and browser information.</p>
    <h2 className="text-xl font-medium text-zinc-100">Requests and corrections</h2>
    <p>To ask about account data, deletion, or a submission, contact the maintainers through the repository’s contact options. Do not post private credentials or personal information in a public issue. Already published CC0 material may have been downloaded or reused by others.</p>
  </article>;
}
