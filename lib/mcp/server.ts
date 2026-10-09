import { mcpContributor } from "@/lib/auth";
import { ownsSubmission } from "@/lib/submission-access";
import { SubmissionRateLimitError } from "@/lib/submit-kv";
import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";
import { getHousePromptTemplate } from "@/lib/mcp/prompt-template";
import { getSoundDetail, resolveSoundEntry } from "@/lib/mcp/entry-detail";
import { listCategoryCounts, searchSounds } from "@/lib/mcp/search";
import { validateMcpSubmit } from "@/lib/mcp/submit-validate";
import {
  getSubmitEntry,
  saveSubmitEntry,
} from "@/lib/submit-kv";
import { runSubmissionPipeline, submissionReviewUrl } from "@/lib/submit-pipeline";
import { scheduleBackground } from "@/lib/schedule-background";
import { getAllEntries } from "@/lib/entries";
import { MCP_SUBMIT_LICENSE_NOTE } from "@/lib/licenses";
import { instrumentMcpTool } from "@/lib/mcp/tool-telemetry";

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

export function createOpusMcpServer(request: Request) {
  const server = new McpServer({
    name: "opus-sounds",
    version: "2.0.0",
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
    async (args) =>
      instrumentMcpTool(request, "search_sounds", async () => {
        const hits = await searchSounds(args);
        const summary = hits.length
          ? `Found ${hits.length} sound(s). Top: ${hits[0]?.title ?? "—"}.`
          : "No sounds matched.";
        return toolText(summary, { results: hits });
      }),
  );

  server.registerTool(
    "get_sound",
    {
      description:
        "Fetch one directory entry by id or slug — prompt, timing, cues, metrics, asset URLs, and generate.py.",
      inputSchema: { id: z.string() },
    },
    async ({ id }) =>
      instrumentMcpTool(request, "get_sound", async () => {
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
      }),
  );

  server.registerTool(
    "list_categories",
    {
      description: "List sound categories with per-category mood counts.",
      inputSchema: {},
    },
    async () =>
      instrumentMcpTool(request, "list_categories", async () => {
        const categories = await listCategoryCounts();
        return toolText(`${categories.length} categories.`, { categories });
      }),
  );

  server.registerTool(
    "get_prompt_template",
    {
      description:
        "House prompt template for writing a new numpy/scipy synth sound (48 kHz, −14 LUFS, cue frames, seed).",
      inputSchema: { category: z.string().optional() },
    },
    async ({ category }) =>
      instrumentMcpTool(request, "get_prompt_template", async () => {
        const tpl = getHousePromptTemplate(category);
        return toolText("House synth prompt template.", tpl);
      }),
  );

  server.registerTool(
    "submit_sound",
    {
      description:
        `Submit a community sound for automated screening + AI review. Requires an account token. Flagged or incomplete reviews stay unpublished. Returns submissionId and status. ${MCP_SUBMIT_LICENSE_NOTE}`,
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
    async (args) =>
      instrumentMcpTool(request, "submit_sound", async () => {
        let owner;
        try { owner = await mcpContributor(request, "create"); }
        catch { return { ...toolText("Account service unavailable.", { error: "temporarily_unavailable" }), isError: true }; }
        if (!owner) return { ...toolText("Create an agent token in your account and send it as a Bearer authorization header.", { error: "authentication_required", accountUrl: "https://opussounds.directory/account" }), isError: true };
        if (!owner.emailVerified) return { ...toolText("Verify your sign-in email before submitting.", { error: "email_not_verified" }), isError: true };
        const validated = validateMcpSubmit({ ...args, email: owner.email });
        if (!validated.ok) {
          return toolText("Validation failed.", { error: validated.error });
        }
        let entry;
        try { entry = await saveSubmitEntry(validated.data, "mcp", owner); }
        catch (error) {
          return { ...toolText(error instanceof SubmissionRateLimitError ? "Try again in an hour." : "Submission service unavailable.", { error: error instanceof SubmissionRateLimitError ? "rate_limited" : "temporarily_unavailable" }), isError: true };
        }
        scheduleBackground(runSubmissionPipeline(entry.id));
        const payload = {
          submissionId: entry.id,
          status: entry.status,
          reviewUrl: submissionReviewUrl(entry),
        };
        return toolText("Submission queued for automated review.", payload);
      }),
  );

  server.registerTool(
    "get_submission_status",
    {
      description: "Check your own submission using an account token: scanning | live | pending_review | rejected.",
      inputSchema: { submissionId: z.string() },
    },
    async ({ submissionId }) =>
      instrumentMcpTool(request, "get_submission_status", async () => {
        let owner;
        try { owner = await mcpContributor(request, "read-own"); }
        catch { return { ...toolText("Account service unavailable.", { error: "temporarily_unavailable" }), isError: true }; }
        if (!owner) return { ...toolText("An account token is required.", { error: "authentication_required" }), isError: true };
        const entry = await getSubmitEntry(submissionId);
        if (!entry || !ownsSubmission(entry.ownerId, owner.id)) return toolText("Not found.", { error: "not_found" });
        const payload = {
          submissionId: entry.id,
          status: entry.status,
          reviewUrl: submissionReviewUrl(entry),
          reviewerNote: entry.reviewerNote,
          communitySlug: entry.communitySlug,
        };
        return toolText(`Status: ${entry.status}`, payload);
      }),
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
