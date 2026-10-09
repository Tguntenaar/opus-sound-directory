import type { Metadata } from "next";
import Link from "next/link";
import { BrandMark } from "@/components/brand-mark";
import { HarnessSnippets, InstallSnippet } from "@/components/install-snippet";
import { canonicalForPath } from "@/lib/site-metadata";

export const metadata: Metadata = {
  title: "Use with your agent",
  description: "Install the Opus Sounds skill and connect your agent to sound effects, music beds and loops. Find audio for apps, games and videos.",
  alternates: { canonical: canonicalForPath("/agents") },
};

const install = "npx skills add Tguntenaar/opus-sound-directory --skill opus-sounds";
const endpoint = "https://opussounds.directory/mcp";
const cursorConfig = JSON.stringify({ mcpServers: { "opus-sounds": { url: endpoint } } }, null, 2);
export default function AgentsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-8 py-4 sm:py-8">
      <header className="space-y-3">
        <BrandMark size={36} />
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">Sounds for your agent</h1>
        <p className="text-sm text-zinc-400">Find, preview and download. No account needed.</p>
      </header>

      <section className="min-w-0 space-y-4 rounded-xl border border-zinc-800 p-5 sm:p-6">
        <h2 className="flex items-center gap-3 text-lg font-medium text-zinc-100"><span className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-500/10 text-xs text-violet-300">1</span>Install the skill</h2>
        <InstallSnippet text={install} label="Run in your project · requires Node.js" />
        <div className="flex flex-wrap gap-4 text-xs text-zinc-400">
          <a className="hover:text-violet-300" href="https://github.com/Tguntenaar/opus-sound-directory/tree/main/skills/opus-sounds">Skill source ↗</a>
          <a className="hover:text-violet-300" href="https://github.com/vercel-labs/skills#supported-agents">Supported agents ↗</a>
        </div>
      </section>

      <section className="min-w-0 space-y-4 rounded-xl border border-zinc-800 p-5 sm:p-6">
        <h2 className="flex items-center gap-3 text-lg font-medium text-zinc-100"><span className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-500/10 text-xs text-violet-300">2</span>Connect MCP</h2>
        <HarnessSnippets snippets={[
          { name: "Claude Code", text: `claude mcp add --transport http opus-sounds ${endpoint}`, label: "Run in your project" },
          { name: "Codex", text: `codex mcp add opus-sounds --url ${endpoint}`, label: "Run in your terminal · requires Codex CLI" },
          { name: "Cursor", text: cursorConfig, label: "Add to .cursor/mcp.json · keep existing servers" },
          { name: "Other agents", text: endpoint, label: "Remote server · Streamable HTTP", description: "Add this URL as a remote MCP server. No API key required for search or downloads." },
        ]} />
      </section>

      <section className="min-w-0 space-y-4 rounded-xl border border-zinc-800 p-5 sm:p-6">
        <h2 className="flex items-center gap-3 text-lg font-medium text-zinc-100"><span className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-500/10 text-xs text-violet-300">3</span>Ask for a sound</h2>
        <InstallSnippet text="Find a gentle notification sound under one second." label="Try this prompt" />
      </section>

      <footer className="flex flex-wrap gap-x-5 gap-y-3 text-xs text-zinc-500">
        <a href="https://github.com/Tguntenaar/opus-sound-directory/blob/main/ASSETS-LICENSE.md" className="hover:text-zinc-300">Sounds: CC0 · Skill: MIT ↗</a>
        <Link href="/account" className="hover:text-zinc-300">Submit via MCP →</Link>
        <Link href="/" className="hover:text-zinc-300">Browse sounds →</Link>
      </footer>
    </div>
  );
}
