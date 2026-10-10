"use client";

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { X } from "lucide-react";
import { authClient } from "@/lib/auth-client";
import { toggleBookmark, useBookmarks } from "@/lib/use-bookmarks";
import { GithubIcon, GoogleIcon } from "@/components/social-icons";
import type { AuthProvider } from "@/lib/auth-config";

type Provider = AuthProvider;
const PENDING = "opus-sounds:pending-bookmark";

function normalizeProviders(list: Provider[]): Provider[] {
  return list.filter(provider => provider === "google" || provider === "github");
}

const BookmarkLogin = createContext<(id: string, save: () => void) => void>(() => {});
export const useBookmarkLogin = () => useContext(BookmarkLogin);

export function BookmarkLoginProvider({ children }: { children: ReactNode }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const busyRef = useRef(false);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providersKnown, setProvidersKnown] = useState(false);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const bookmarks = useBookmarks();

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/account", { cache: "no-store" }).then(async response => {
      if (!response.ok) return;
      const account = await response.json() as { providers?: Provider[] };
      if (cancelled || !account.providers) return;
      setProviders(normalizeProviders(account.providers));
    }).catch(() => {}).finally(() => {
      if (!cancelled) setProvidersKnown(true);
    });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let pending: { id: string; at: number };
    try {
      pending = JSON.parse(sessionStorage.getItem(PENDING) ?? "null");
      if (!pending || typeof pending.id !== "string" || typeof pending.at !== "number" || Date.now() - pending.at > 3600000) return;
    } catch { return; }
    let cancelled = false;
    void fetch("/api/account", { cache: "no-store" }).then(async response => {
      if (!response.ok) return;
      const account = await response.json() as { user: unknown };
      if (cancelled || !account.user) return;
      sessionStorage.removeItem(PENDING);
      if (!bookmarks.has(pending.id)) toggleBookmark(pending.id);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [bookmarks]);

  async function request(id: string, save: () => void) {
    if (busyRef.current) return;
    busyRef.current = true;
    setError("");
    setPendingId(id);
    try {
      const response = await fetch("/api/account", { cache: "no-store" });
      if (!response.ok) throw new Error("Sign-in is temporarily unavailable. Please try again.");
      const account = await response.json() as { user: unknown; providers: Provider[] };
      if (account.user) { save(); return; }
      setProviders(normalizeProviders(account.providers));
      setProvidersKnown(true);
      dialog.current?.showModal();
    } catch (cause) {
      setProviders([]);
      setProvidersKnown(true);
      setError(cause instanceof Error ? cause.message : "Could not check your account.");
      dialog.current?.showModal();
    } finally { busyRef.current = false; }
  }

  async function signIn(provider: Provider) {
    setBusy(true); setError("");
    try {
      if (pendingId) sessionStorage.setItem(PENDING, JSON.stringify({ id: pendingId, at: Date.now() }));
      const callbackURL = window.location.pathname + window.location.search;
      const result = await authClient.signIn.social({ provider, callbackURL, errorCallbackURL: callbackURL, disableRedirect: true });
      if (result.error || !result.data?.url) throw new Error("Could not start sign-in. Please try again.");
      window.location.assign(result.data.url);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not start sign-in.");
      setBusy(false);
    }
  }

  const showUnavailable = providersKnown && !providers.length && !error;

  return <BookmarkLogin.Provider value={(id, save) => void request(id, save)}>
    {children}
    <dialog ref={dialog} aria-labelledby="bookmark-login-title"
      className="ph-no-capture fixed inset-0 m-auto w-[calc(100%-2rem)] max-w-sm rounded-2xl border border-zinc-800 bg-zinc-950 p-6 text-zinc-100 backdrop:bg-black/70"
      onClick={event => { if (event.target === event.currentTarget) dialog.current?.close(); }}>
      <div onClick={event => event.stopPropagation()}>
        <button type="button" aria-label="Close sign-in" onClick={() => dialog.current?.close()} className="absolute right-3 top-3 rounded-lg p-2 text-zinc-400 hover:text-white"><X className="h-4 w-4" /></button>
        <h2 id="bookmark-login-title" className="pr-8 text-lg font-medium">Sign in to bookmark</h2>
        <p className="mt-2 text-sm text-zinc-400">Keep your favorite sounds close.</p>
        <div className="mt-5 space-y-3">
          {providers.map(provider => <button key={provider} type="button" disabled={busy} onClick={() => void signIn(provider)}
            className="flex min-h-11 w-full items-center justify-center gap-3 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm hover:border-violet-400 disabled:opacity-50">
            {provider === "google" ? <GoogleIcon className="h-5 w-5" /> : <GithubIcon className="h-5 w-5" />}
            Continue with {provider === "google" ? "Google" : "GitHub"}
          </button>)}
          {showUnavailable && <p className="text-sm text-zinc-400">Sign-in is currently unavailable.</p>}
          {error && <p role="alert" className="text-sm text-amber-300">{error}</p>}
        </div>
      </div>
    </dialog>
  </BookmarkLogin.Provider>;
}
