import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";
import { getHousePromptTemplate } from "@/lib/mcp/prompt-template";
import { getSoundDetail, resolveSoundEntry } from "@/lib/mcp/entry-detail";
import { listCategoryCounts, searchSounds } from "@/lib/mcp/search";
import { validateMcpSubmit } from "@/lib/mcp/submit-validate";
import {
  checkSubmitRateLimit,
  getSubmitEntry,
  saveSubmitEntry,
  touchSubmitRateLimit,
} from "@/lib/submit-kv";
import { runSubmissionPipeline, submissionReviewUrl } from "@/lib/submit-pipeline";
import { scheduleBackground } from "@/lib/schedule-background";
import { getAllEntries } from "@/lib/entries";
import { MCP_SUBMIT_LICENSE_NOTE } from "@/lib/licenses";

function toolText(summary: string, data: unknown) {
  return {
    content: [
      {
        type: "text" as const,
        text: `${summary}\n\n${JSON.stringify(data)}`,
      },
    ],
  };
}

function clientIp(request: Request): string {
  return (
    request.headers.get("cf-connecting-ip") ??
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "unknown"
  ).slice(0, 120);
}

export function createOpusMcpServer(request: Request) {
  const server = new McpServer({
    name: "opus-sounds",
    version: "1.0.0",
  });

  server.registerTool(
    "search_sounds",
    {
      description:
        "Search the Opus Sounds Directory (static + community entries). Returns ranked hits with URLs and loudness.",
      inputSchema: {
        query: z.string().optional(),
        category: z.string().optional(),
        mood: z.string().optional(),
        tempo: z.enum(["slow", "medium", "fast"]).optional(),
        maxDurationSec: z.number().optional(),
        limit: z.number().int().min(1).max(50).optional(),
      },
    },
    async (args) => {
      const hits = await searchSounds(args);
      const summary = hits.length
        ? `Found ${hits.length} sound(s). Top: ${hits[0]?.title ?? "—"}.`
        : "No sounds matched.";
      return toolText(summary, { results: hits });
    },
  );

  server.registerTool(
    "get_sound",
    {
      description:
        "Fetch one directory entry by id or slug — prompt, timing, cues, metrics, asset URLs, and generate.py.",
      inputSchema: { id: z.string() },
    },
    async ({ id }) => {
      const detail = await getSoundDetail(id);
      if (!detail) {
        return toolText("Sound not found.", { error: "not_found", id });
      }
      const { entry, pageUrl, assets } = detail;
      const summary = `${entry.title} (${entry.category}) — ${pageUrl}`;
      return toolText(summary, {
        id: entry.id,
        slug: entry.slug,
        pageUrl,
        entry,
        assets,
      });
    },
  );

  server.registerTool(
    "list_categories",
    {
      description: "List sound categories with per-category mood counts.",
      inputSchema: {},
    },
    async () => {
      const categories = await listCategoryCounts();
      return toolText(`${categories.length} categories.`, { categories });
    },
  );

  server.registerTool(
    "get_prompt_template",
    {
      description:
        "House prompt template for writing a new numpy/scipy synth sound (48 kHz, −14 LUFS, cue frames, seed).",
      inputSchema: { category: z.string().optional() },
    },
    async ({ category }) => {
      const tpl = getHousePromptTemplate(category);
      return toolText("House synth prompt template.", tpl);
    },
  );

  server.registerTool(
    "submit_sound",
    {
      description:
        `Submit a community sound for automated screening + AI review. Auto-publishes when safe. Returns submissionId and status. ${MCP_SUBMIT_LICENSE_NOTE}`,
      inputSchema: {
        title: z.string(),
        prompt: z.string(),
        category: z.string(),
        mood: z.array(z.string()),
        tempo: z.enum(["slow", "medium", "fast"]).optional(),
        durationSec: z.number(),
        code: z.string(),
        audioUrl: z.string().optional(),
        author_name: z.string().optional(),
        author_url: z.string().optional(),
        email: z.string().optional(),
        notes: z.string().optional(),
      },
    },
    async (args) => {
      const validated = validateMcpSubmit(args as Record<string, unknown>);
      if (!validated.ok) {
        return toolText("Validation failed.", { error: validated.error });
      }
      const fingerprint = clientIp(request);
      if (!(await checkSubmitRateLimit(fingerprint))) {
        return toolText("Rate limited.", { error: "rate_limited" });
      }
      const entry = await saveSubmitEntry(validated.data, "mcp");
      await touchSubmitRateLimit(fingerprint);
      scheduleBackground(runSubmissionPipeline(entry.id));
      const payload = {
        submissionId: entry.id,
        status: entry.status,
        reviewUrl: submissionReviewUrl(entry),
      };
      return toolText("Submission queued for automated review.", payload);
    },
  );

  server.registerTool(
    "get_submission_status",
    {
      description: "Check a submission: scanning | live | pending_review | rejected.",
      inputSchema: { submissionId: z.string() },
    },
    async ({ submissionId }) => {
      const entry = await getSubmitEntry(submissionId);
      if (!entry) return toolText("Not found.", { error: "not_found" });
      const payload = {
        submissionId: entry.id,
        status: entry.status,
        reviewUrl: submissionReviewUrl(entry),
        reviewerNote: entry.reviewerNote,
        communitySlug: entry.communitySlug,
      };
      return toolText(`Status: ${entry.status}`, payload);
    },
  );

  for (const e of getAllEntries()) {
    server.registerResource(
      `sound-${e.id}`,
      `opus://sound/${e.id}`,
      {
        mimeType: "application/json",
        description: e.title,
      },
      async () => ({
        contents: [
          {
            uri: `opus://sound/${e.id}`,
            mimeType: "application/json",
            text: JSON.stringify(await getSoundDetail(e.id)),
          },
        ],
      }),
    );
  }

  return server;
}
