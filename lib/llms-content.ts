import { getAllBlogPosts } from "@/lib/blog";
import { getAllEntriesMerged } from "@/lib/entries";
import { modelAttribution } from "@/lib/model-display";
import { entryShareDescription } from "@/lib/site-metadata";
import { getSiteUrl, SITE_NAME, DEFAULT_SITE_DESCRIPTION } from "@/lib/site-url";
import { CC0_LICENSE_URL, LICENSE_MIT_URL, LICENSE_SOUNDS_URL } from "@/lib/licenses";

function modelLine(entry: { modelId: string; targetModelId?: string }): string {
  const attr = modelAttribution(entry.modelId, entry.targetModelId);
  if (attr.isLocalSynth) {
    return "modelId: local-synth";
  }
  if (entry.modelId === "claude-opus-5-5") {
    return "modelId: claude-opus-5-5 (Python synthesis from Claude Opus 5.5, measured and mastered)";
  }
  return `modelId: ${entry.modelId}`;
}

export async function buildLlmsTxt(): Promise<string> {
  const base = getSiteUrl();
  const entries = await getAllEntriesMerged();
  const posts = getAllBlogPosts();

  const lines: string[] = [
    `# ${SITE_NAME}`,
    "",
    `> ${DEFAULT_SITE_DESCRIPTION}`,
    "",
    `Licensing: site and runner code — MIT (${LICENSE_MIT_URL}). Directory audio, spectrograms, and entry prompts — CC0 1.0 (${CC0_LICENSE_URL}; ${LICENSE_SOUNDS_URL}). Community submissions use the same split.`,
    "",
    "## Sounds",
    "",
  ];

  for (const e of entries) {
    const oneLine = entryShareDescription(e).split("\n")[0];
    lines.push(
      `- [${e.title}](${base}/e/${e.slug}): ${oneLine}. ${modelLine(e)}.`,
    );
    lines.push(`  Prompt: ${e.prompt.replace(/\s+/g, " ").slice(0, 280)}${e.prompt.length > 280 ? "…" : ""}`);
  }

  if (posts.length) {
    lines.push("", "## Blog", "");
    for (const p of posts) {
      lines.push(`- [${p.title}](${base}/blog/${p.slug}): ${p.description}`);
    }
  }

  lines.push(
    "",
    "## Optional",
    "",
    `- [About](${base}/about)`,
    `- [Submit](${base}/submit)`,
    `- [MCP server](${base}/mcp) — remote tools at \`${base}/mcp\` (streamable HTTP)`,
    `- [Sitemap](${base}/sitemap.xml)`,
    `- [RSS](${base}/blog/rss.xml)`,
    `- [Full LLM index](${base}/llms-full.txt)`,
  );

  return `${lines.join("\n")}\n`;
}

export async function buildLlmsFullTxt(): Promise<string> {
  const base = getSiteUrl();
  const entries = await getAllEntriesMerged();
  const posts = getAllBlogPosts();

  const lines: string[] = [
    `# ${SITE_NAME} — full index`,
    "",
    `> ${DEFAULT_SITE_DESCRIPTION}`,
    "",
    `Licensing: code MIT (${LICENSE_MIT_URL}); sounds and entry prompts CC0 1.0 (${CC0_LICENSE_URL}). Details: ${LICENSE_SOUNDS_URL}.`,
    "",
    "## Sounds (full)",
    "",
  ];

  for (const e of entries) {
    lines.push(`### ${e.title}`);
    lines.push(`URL: ${base}/e/${e.slug}`);
    lines.push(modelLine(e));
    lines.push(`Description: ${entryShareDescription(e)}`);
    lines.push("Prompt:");
    lines.push(e.prompt);
    lines.push("");
  }

  if (posts.length) {
    lines.push("## Blog posts", "");
    for (const p of posts) {
      lines.push(`### ${p.title}`);
      lines.push(`URL: ${base}/blog/${p.slug}`);
      lines.push(`Date: ${p.date}`);
      lines.push(p.description);
      if (p.keywords.length) lines.push(`Keywords: ${p.keywords.join(", ")}`);
      lines.push("");
    }
  }

  return `${lines.join("\n")}\n`;
}
