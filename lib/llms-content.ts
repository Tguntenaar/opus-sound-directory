import { getAllBlogPosts } from "@/lib/blog";
import { getAllEntries } from "@/lib/entries";
import { modelAttribution } from "@/lib/model-display";
import { entryShareDescription } from "@/lib/site-metadata";
import { getSiteUrl, SITE_NAME, DEFAULT_SITE_DESCRIPTION } from "@/lib/site-url";

function modelLine(entry: { modelId: string; targetModelId?: string }): string {
  const attr = modelAttribution(entry.modelId, entry.targetModelId);
  if (attr.isLocalSynth) {
    return `modelId: local-synth (local numpy runner — not Opus-generated)${
      entry.targetModelId ? `; agent target: ${entry.targetModelId}` : ""
    }`;
  }
  return `modelId: ${entry.modelId}`;
}

export function buildLlmsTxt(): string {
  const base = getSiteUrl();
  const entries = getAllEntries();
  const posts = getAllBlogPosts();

  const lines: string[] = [
    `# ${SITE_NAME}`,
    "",
    `> ${DEFAULT_SITE_DESCRIPTION}`,
    "",
    "Synthesised audio for AI video workflows: each listing includes the Claude Opus-style prompt, Python synth code, spectrogram, and loudness metrics. Sounds are generated via Anthropic models when `modelId` says so, or via the local numpy verification runner when `modelId` is `local-synth`.",
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
    `- [Sitemap](${base}/sitemap.xml)`,
    `- [RSS](${base}/blog/rss.xml)`,
    `- [Full LLM index](${base}/llms-full.txt)`,
  );

  return `${lines.join("\n")}\n`;
}

export function buildLlmsFullTxt(): string {
  const base = getSiteUrl();
  const entries = getAllEntries();
  const posts = getAllBlogPosts();

  const lines: string[] = [
    `# ${SITE_NAME} — full index`,
    "",
    `> ${DEFAULT_SITE_DESCRIPTION}`,
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
