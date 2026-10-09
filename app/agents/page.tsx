import type { Metadata } from "next";
import Link from "next/link";
import { BrandMark } from "@/components/brand-mark";
import { InstallSnippet } from "@/components/install-snippet";
import { canonicalForPath } from "@/lib/site-metadata";

export const metadata: Metadata = {
  title: "Use with your agent",
  description: "Install the Opus Sounds skill and connect your agent to sound effects, music beds and loops. Find audio for apps, games and videos.",
  alternates: { canonical: canonicalForPath("/agents") },
};

const install = "npx skills add Tguntenaar/opus-sound-directory --skill opus-sounds";
const endpoint = "https://opussounds.directory/mcp";
const cursorConfig = JSON.stringify({ mcpServers: { "opus-sounds": { url: endpoint } } }, null, 2);
const examples = [
  "Find a gentle notification sound under one second.",
  "Compare three sound effects for a game reward, with preview links.",
  "Find an ambient loop for my video and show me its duration and license.",
];

export default function AgentsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-10 py-4 sm:py-8">
      <header className="space-y-5">
        <BrandMark size={44} />
        <p className="text-xs font-medium uppercase tracking-widest text-violet-400">Opus Sounds for agents</p>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-50 sm:text-4xl">Bring sound into your agent’s workflow.</h1>
        <p className="max-w-2xl text-base leading-7 text-zinc-400">Find sound effects, preview options and add them to your app, game or video. Install the skill for guidance, then connect MCP for access to the live directory.</p>
        <div className="flex flex-wrap gap-3 text-xs text-zinc-300"><span className="rounded-full border border-zinc-800 px-3 py-1">Sounds: CC0</span><span className="rounded-full border border-zinc-800 px-3 py-1">Skill: MIT</span><span className="rounded-full border border-zinc-800 px-3 py-1">Public read access</span></div>
      </header>

      <section className="min-w-0 space-y-4 rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 sm:p-7">
        <h2 className="text-xl font-medium text-zinc-100">1. Install the skill</h2>
        <p className="text-sm leading-6 text-zinc-400">Run this in your project with Node.js and npm installed. The installer lets you choose a supported agent. The skill teaches it how to find suitable sounds, check their details and integrate the chosen assets.</p>
        <InstallSnippet text={install} label="Skill install command" />
        <p className="text-sm text-zinc-400">Review the <a className="text-violet-300 underline underline-offset-4" href="https://github.com/Tguntenaar/opus-sound-directory/tree/main/skills/opus-sounds">skill source</a> or see the <a className="text-violet-300 underline underline-offset-4" href="https://github.com/vercel-labs/skills#supported-agents">supported agents</a>. Reload your agent if the skill does not appear.</p>
      </section>

      <section className="min-w-0 space-y-5 rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 sm:p-7">
        <h2 className="text-xl font-medium text-zinc-100">2. Connect the live directory</h2>
        <p className="text-sm leading-6 text-zinc-400">Installing the skill does not automatically connect MCP. Add the server using your agent’s setup below. No API key is needed for public read tools.</p>
        <details className="rounded-lg border border-zinc-800 p-4" open>
          <summary className="cursor-pointer text-sm font-medium text-zinc-200">Claude Code</summary>
          <div className="mt-4 space-y-3"><InstallSnippet text={`claude mcp add --transport http opus-sounds ${endpoint}`} label="Claude Code MCP command" /><p className="text-xs leading-5 text-zinc-400">Run in your project, then check the connection with <code>claude mcp list</code>. <a className="text-violet-300 underline" href="https://code.claude.com/docs/en/mcp">Official setup guide</a>.</p></div>
        </details>
        <details className="rounded-lg border border-zinc-800 p-4">
          <summary className="cursor-pointer text-sm font-medium text-zinc-200">Cursor</summary>
          <div className="mt-4 space-y-3"><p className="text-xs leading-5 text-zinc-400">Merge this entry into <code>.cursor/mcp.json</code> in your project. Keep your existing servers. Then enable or reload it in MCP settings.</p><InstallSnippet text={cursorConfig} label="Cursor MCP configuration" /><a className="text-xs text-violet-300 underline" href="https://cursor.com/docs/mcp">Official setup guide</a></div>
        </details>
        <details className="rounded-lg border border-zinc-800 p-4">
          <summary className="cursor-pointer text-sm font-medium text-zinc-200">Other MCP clients</summary>
          <div className="mt-4 space-y-3"><p className="text-sm leading-6 text-zinc-400">Add a remote server with Streamable HTTP transport using the URL below. Configuration varies by client; skill support and MCP support are separate capabilities.</p><InstallSnippet text={endpoint} label="MCP server URL" /></div>
        </details>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium text-zinc-100">3. Find your first sound</h2>
        <p className="text-sm leading-6 text-zinc-400">Check that your agent can see <code>search_sounds</code> and <code>get_sound</code>, then try one of these requests.</p>
        {examples.map((text, i) => <InstallSnippet key={text} text={text} label={`Example request ${i + 1}`} />)}
        <p className="text-sm leading-6 text-zinc-400">You can also <Link href="/" className="text-violet-300 underline underline-offset-4">browse the directory</Link> without an agent. If MCP is unavailable, the skill can use public entry pages to find sounds.</p>
      </section>

      <section className="space-y-3 border-t border-zinc-800 pt-6 text-sm leading-6 text-zinc-400">
        <h2 className="font-medium text-zinc-200">Made for finding and using sounds</h2>
        <p>This skill covers discovery, downloads and integration. Sound submission is a separate workflow and is not included in this setup’s verified capabilities.</p>
        <p>Sound assets are CC0, including commercial use without required credit. Synthesis code and the skill are MIT-licensed. <a href="https://github.com/Tguntenaar/opus-sound-directory/blob/main/ASSETS-LICENSE.md" className="text-violet-300 underline underline-offset-4">Read the license details</a>.</p>
      </section>
    </div>
  );
}
