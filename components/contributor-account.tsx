"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { authClient } from "@/lib/auth-client";

type User = { id: string; name: string; email: string; emailVerified: boolean };
type Submission = { id: string; title: string; status: string; createdAt: string; reviewUrl?: string; reviewerNote?: string };
type Key = { id: string; name: string | null; start: string | null; expiresAt: Date | string | null };

export function ContributorAccount({ submission = false }: { submission?: boolean }) {
  const [user, setUser] = useState<User | null>(null);
  const [providers, setProviders] = useState<("github" | "google")[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [entries, setEntries] = useState<Submission[]>([]);
  const [keys, setKeys] = useState<Key[]>([]);
  const [newKey, setNewKey] = useState("");
  const [keyName, setKeyName] = useState("");

  async function refreshPrivateData() {
    const response = await fetch("/api/account/submissions", { cache: "no-store" });
    if (!response.ok) throw new Error("Could not load your submissions.");
    setEntries(((await response.json()) as { submissions: Submission[] }).submissions);
    const result = await authClient.apiKey.list();
    if (result.error) throw new Error("Could not load agent tokens.");
    setKeys(result.data?.apiKeys ?? []);
  }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const response = await fetch("/api/account", { cache: "no-store" });
        if (!response.ok) throw new Error("Sign-in is temporarily unavailable. Please try again later.");
        const data = await response.json() as { user: User | null; providers: ("github" | "google")[] };
        if (!active) return;
        setUser(data.user); setProviders(data.providers);
        if (data.user && !submission) await refreshPrivateData();
      } catch (e) { if (active) setError(e instanceof Error ? e.message : "Could not load your account."); }
      finally { if (active) setLoading(false); }
    })();
    return () => { active = false; };
  }, [submission]);

  async function run(action: () => Promise<void>) {
    setBusy(true); setError("");
    try { await action(); } catch (e) { setError(e instanceof Error ? e.message : "Please try again."); }
    finally { setBusy(false); }
  }
  const button = "rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-100 hover:border-violet-400 disabled:opacity-50";
  return <section className="mt-6 space-y-6">
    {loading && <p role="status" className="text-sm text-zinc-400">Loading your account…</p>}
    {error && <p role="alert" className="text-sm text-amber-300">{error}</p>}
    {!loading && !user && <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6">
      <h2 className="font-medium text-zinc-100">Sign in to contribute</h2>
      <p className="mt-2 text-sm text-zinc-400">Your sign-in email stays private. You choose how to be credited on published sounds.</p>
      <div className="mt-5 flex flex-wrap gap-3">{providers.map(provider => <button key={provider} className={button} disabled={busy} onClick={() => void run(async () => {
        const result = await authClient.signIn.social({ provider, callbackURL: submission ? "/submit" : "/account" });
        if (result.error) throw new Error("Could not start sign-in. Please try again.");
      })}>Continue with {provider === "github" ? "GitHub" : "Google"}</button>)}</div>
    </div>}
    {user && <>
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-zinc-800 p-5">
        <div><p className="font-medium text-zinc-100">{user.name}</p><p className="mt-1 text-sm text-zinc-400">{user.email} · private</p></div>
        <button className={button} disabled={busy} onClick={() => void run(async () => {
          const result = await authClient.signOut();
          if (result.error) throw new Error("Could not sign out.");
          window.location.reload();
        })}>Sign out</button>
      </div>
      {!user.emailVerified && <p className="text-sm text-amber-300">Verify your email with your sign-in provider before submitting sounds.</p>}
      {!submission && <>
        <div className="flex flex-wrap gap-3">{providers.map(provider => <button key={provider} className={button} disabled={busy} onClick={() => void run(async () => {
          const result = await authClient.linkSocial({ provider, callbackURL: "/account" });
          if (result.error) throw new Error("This provider may already be linked. Use your original sign-in if it belongs to another account.");
        })}>Link {provider === "github" ? "GitHub" : "Google"}</button>)}</div>
        <div className="flex items-center justify-between"><h2 className="text-xl font-medium text-zinc-100">Your recent submissions</h2><Link href="/submit" className="text-sm text-violet-300">Submit a sound →</Link></div>
        {entries.length === 0 ? <p className="text-sm text-zinc-500">Your submissions will appear here once you contribute a sound.</p> : <ul className="space-y-3">{entries.map(entry => <li key={entry.id} className="rounded-xl border border-zinc-800 p-4">
          <p className="font-medium text-zinc-100">{entry.reviewUrl ? <Link href={entry.reviewUrl}>{entry.title}</Link> : entry.title}</p>
          <p className="mt-1 text-sm text-violet-300">{entry.status.replaceAll("_", " ")} · {new Date(entry.createdAt).toLocaleDateString()}</p>
          {entry.reviewerNote && <p className="mt-2 text-sm text-zinc-400">{entry.reviewerNote}</p>}
        </li>)}</ul>}
        <section className="space-y-4 rounded-xl border border-zinc-800 p-5">
          <h2 className="text-xl font-medium text-zinc-100">Connect an agent</h2>
          <p className="text-sm leading-relaxed text-zinc-400">A token lets an agent submit sounds and check your submissions through MCP. It cannot manage your account. Tokens expire after 90 days; revoke one whenever you stop using it.</p>
          <form className="flex flex-wrap gap-3" onSubmit={event => { event.preventDefault(); void run(async () => {
            const result = await authClient.apiKey.create({ name: keyName.trim(), expiresIn: 60 * 60 * 24 * 90 });
            if (result.error || !result.data) throw new Error("Could not create a token.");
            setNewKey(result.data.key); setKeyName(""); await refreshPrivateData();
          }); }}>
            <input required maxLength={80} aria-label="Agent token name" placeholder="e.g. My sound agent" value={keyName} onChange={event => setKeyName(event.target.value)} className="min-w-0 flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" />
            <button className={button} disabled={busy || !user.emailVerified}>Create token</button>
          </form>
          {newKey && <div className="space-y-3 rounded-lg bg-violet-500/10 p-4"><p className="text-sm text-violet-200">Copy this token now. It is only shown once. Keep it out of prompts, logs, and source control.</p><code className="block break-all text-sm text-zinc-100">{newKey}</code><button className={button} onClick={() => void run(async () => navigator.clipboard.writeText(newKey))}>Copy token</button><button className={`${button} ml-2`} onClick={() => setNewKey("")}>Hide token</button></div>}
          <p className="text-sm text-zinc-400">Use <code>https://opussounds.directory/mcp</code> with the HTTP header <code>Authorization: Bearer YOUR_TOKEN</code>. Search and downloads work without a token.</p>
          <ul className="space-y-3">{keys.map(key => <li key={key.id} className="flex items-center justify-between gap-4 text-sm"><div className="min-w-0 break-words text-zinc-300">{key.name || "Agent token"}<span className="block text-xs text-zinc-500">Expires {key.expiresAt ? new Date(key.expiresAt).toLocaleDateString() : "never"}</span></div><button className={button} disabled={busy} onClick={() => void run(async () => {
            const result = await authClient.apiKey.delete({ keyId: key.id });
            if (result.error) throw new Error("Could not revoke token.");
            setNewKey(""); await refreshPrivateData();
          })}>Revoke</button></li>)}</ul>
        </section>
      </>}
    </>}
    <p className="text-xs text-zinc-500">Read how account information is used in our <Link href="/privacy" className="underline">privacy notice</Link>.</p>
  </section>;
}
