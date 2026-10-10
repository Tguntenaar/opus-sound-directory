"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { GithubIcon, GoogleIcon } from "@/components/social-icons";
import { authClient } from "@/lib/auth-client";
import { captureEvent, getPosthogWhenReady } from "@/lib/analytics-client";
import { useAuthProviders } from "@/components/auth-providers";
import { SIGN_IN_ATTEMPT_KEY } from "@/lib/auth-analytics";
import { shouldShowContributorSignIn } from "@/lib/contributor-sign-in";

type User = { id: string; name: string; email: string; emailVerified: boolean };
type Submission = { id: string; title: string; status: string; createdAt: string; reviewUrl?: string; reviewerNote?: string };
type Key = { id: string; name: string | null; start: string | null; expiresAt: Date | string | null };

export function ContributorAccount({
  submission = false,
  initialUser,
  initialProviders: initialProvidersProp,
}: {
  submission?: boolean;
  initialUser?: User | null;
  initialProviders?: ("github" | "google")[];
}) {
  const contextProviders = useAuthProviders();
  const sessionKnown = initialUser !== undefined;
  const seedProviders = initialProvidersProp ?? contextProviders;
  const [user, setUser] = useState<User | null>(initialUser ?? null);
  const [providers, setProviders] = useState(seedProviders);
  const [loading, setLoading] = useState(!sessionKnown);
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
  const showSignIn = shouldShowContributorSignIn(user, loading, providers, sessionKnown);
  return <section className="ph-no-capture mt-6 space-y-6">
    {loading && !showSignIn && <p role="status" className="text-sm text-zinc-400">Loading your account…</p>}
    {error && <p role="alert" className="text-sm text-amber-300">{error}</p>}
    {showSignIn && <div className="rounded-2xl border border-zinc-800 bg-gradient-to-br from-zinc-900 to-zinc-950 p-6 shadow-lg shadow-black/10 sm:p-8">
      <h2 className="text-lg font-semibold tracking-tight text-zinc-100">Sign in to contribute</h2>
      <p className="mt-2 text-sm text-zinc-400">Submit sounds and connect your agents.</p>
      <div className="mt-6 grid gap-3 sm:grid-cols-2">{providers.map(provider => <button key={provider} type="button" className={`inline-flex min-h-12 items-center justify-center gap-3 rounded-lg border px-5 py-3 text-sm font-medium shadow-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-violet-400 disabled:cursor-wait disabled:opacity-50 ${provider === "google" ? "border-zinc-300 bg-white text-zinc-800 hover:bg-zinc-100" : "border-zinc-600 bg-zinc-800 text-white hover:border-zinc-400 hover:bg-zinc-700"}`} disabled={busy} onClick={() => void run(async () => {
        const source = submission ? "submit" : "account";
        captureEvent("auth_sign_in_clicked", { provider, source });
        try {
          const result = await authClient.signIn.social({
            provider, callbackURL: `/${source}?sign_in=returned`,
            errorCallbackURL: `/${source}?sign_in=failed`, disableRedirect: true,
          });
          if (result.error || !result.data?.url) throw new Error("Could not start sign-in. Please try again.");
          try {
            sessionStorage.setItem(SIGN_IN_ATTEMPT_KEY, JSON.stringify({ provider, source, startedAt: Date.now() }));
          } catch { /* Storage restrictions must not prevent sign-in. */ }
          // Dispatch before leaving the site; analytics must never hold up sign-in.
          try {
            const ph = await Promise.race([
              getPosthogWhenReady(),
              new Promise<null>(resolve => setTimeout(() => resolve(null), 1000)),
            ]);
            ph?.capture("auth_sign_in_started", { provider, source }, {
              send_instantly: true, transport: "sendBeacon",
            });
          } catch { /* Continue to OAuth if analytics is blocked or unavailable. */ }
          window.location.assign(result.data.url);
        } catch {
          captureEvent("auth_sign_in_failed", { provider, source, stage: "start", failure_reason: "request_failed" });
          throw new Error("Could not start sign-in. Please try again.");
        }
      })}>{provider === "github" ? <GithubIcon className="h-5 w-5 shrink-0" /> : <GoogleIcon className="shrink-0" />}<span>Continue with {provider === "github" ? "GitHub" : "Google"}</span></button>)}</div>
    </div>}
    {user && <>
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-zinc-800 p-5">
        <div><p className="font-medium text-zinc-100">{user.name}</p><p className="mt-1 text-sm text-zinc-400">{user.email}</p></div>
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
        })}><span className="inline-flex items-center gap-2">{provider === "github" ? <GithubIcon /> : <GoogleIcon className="h-4 w-4" />}Link {provider === "github" ? "GitHub" : "Google"}</span></button>)}</div>
        <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-medium text-zinc-100">Submissions</h2><Link href="/submit" className="text-sm text-violet-300" onClick={() => captureEvent("add_sound_click", { placement: "account" })}>Submit a sound →</Link></div>
        {entries.length === 0 ? <p className="text-sm text-zinc-500">No submissions yet.</p> : <ul className="space-y-3">{entries.map(entry => <li key={entry.id} className="rounded-xl border border-zinc-800 p-4">
          <p className="font-medium text-zinc-100">{entry.reviewUrl ? <Link href={entry.reviewUrl}>{entry.title}</Link> : entry.title}</p>
          <p className="mt-1 text-sm text-violet-300">{entry.status.replaceAll("_", " ")} · {new Date(entry.createdAt).toLocaleDateString()}</p>
          {entry.reviewerNote && <p className="mt-2 text-sm text-zinc-400">{entry.reviewerNote}</p>}
        </li>)}</ul>}
        <section className="space-y-4 rounded-xl border border-zinc-800 p-5">
          <h2 className="text-xl font-medium text-zinc-100">Agent tokens</h2>
          <p className="text-sm leading-relaxed text-zinc-400">For MCP submissions. Expires in 90 days.</p>
          <form className="flex flex-wrap gap-3" onSubmit={event => { event.preventDefault(); void run(async () => {
            const result = await authClient.apiKey.create({ name: keyName.trim(), expiresIn: 60 * 60 * 24 * 90 });
            if (result.error || !result.data) throw new Error("Could not create a token.");
            setNewKey(result.data.key); setKeyName(""); await refreshPrivateData();
          }); }}>
            <input required maxLength={80} aria-label="Agent token name" placeholder="e.g. My sound agent" value={keyName} onChange={event => setKeyName(event.target.value)} className="min-w-0 flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" />
            <button className={button} disabled={busy || !user.emailVerified}>Create token</button>
          </form>
          {newKey && <div className="space-y-3 rounded-lg bg-violet-500/10 p-4"><p className="text-sm text-violet-200">Copy now — shown only once. Keep it private.</p><code className="block break-all text-sm text-zinc-100">{newKey}</code><button className={button} onClick={() => void run(async () => navigator.clipboard.writeText(newKey))}>Copy token</button><button className={`${button} ml-2`} onClick={() => setNewKey("")}>Hide token</button></div>}
          <details className="text-sm text-zinc-400">
            <summary className="w-fit cursor-pointer text-zinc-300 transition-colors hover:text-white focus-visible:outline-violet-400">Connection details</summary>
            <div className="mt-3 space-y-2 break-words rounded-lg bg-zinc-900 p-3">
              <p className="text-xs text-zinc-500">MCP endpoint</p><code className="block break-all">https://opussounds.directory/mcp</code>
              <p className="pt-2 text-xs text-zinc-500">HTTP header</p><code className="block break-all">Authorization: Bearer YOUR_TOKEN</code>
              <p className="pt-2 text-xs">Tokens can submit sounds and read your submission status. Revoke anytime.</p>
            </div>
          </details>
          <ul className="space-y-3">{keys.map(key => <li key={key.id} className="flex items-center justify-between gap-4 text-sm"><div className="min-w-0 break-words text-zinc-300">{key.name || "Agent token"}<span className="block text-xs text-zinc-500">Expires {key.expiresAt ? new Date(key.expiresAt).toLocaleDateString() : "never"}</span></div><button className={button} disabled={busy} onClick={() => void run(async () => {
            const result = await authClient.apiKey.delete({ keyId: key.id });
            if (result.error) throw new Error("Could not revoke token.");
            setNewKey(""); await refreshPrivateData();
          })}>Revoke</button></li>)}</ul>
        </section>
      </>}
    </>}
    <p className="text-xs text-zinc-500"><Link href="/privacy" className="transition-colors hover:text-zinc-300">Privacy</Link></p>
  </section>;
}
