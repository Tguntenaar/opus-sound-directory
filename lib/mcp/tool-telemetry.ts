import { scheduleBackground } from "@/lib/schedule-background";
import { captureServerEvent, mcpDistinctId } from "@/lib/posthog-server";

type ToolTextResult = {
  content: { type: string; text: string }[];
};

function toolCallFailed(result: ToolTextResult): boolean {
  const text = result.content[0]?.text ?? "";
  return (
    text.startsWith("Validation failed") ||
    text.startsWith("Rate limited") ||
    text.startsWith("Not found.") ||
    text.includes('"error"')
  );
}

export function instrumentMcpTool<T extends ToolTextResult>(
  request: Request,
  tool: string,
  run: () => Promise<T>,
): Promise<T> {
  const started = Date.now();
  return run()
    .then((result) => {
      const ok = !toolCallFailed(result);
      scheduleBackground(emitMcpToolCall(request, tool, ok, Date.now() - started));
      return result;
    })
    .catch((err) => {
      scheduleBackground(emitMcpToolCall(request, tool, false, Date.now() - started));
      throw err;
    });
}

async function emitMcpToolCall(
  request: Request,
  tool: string,
  ok: boolean,
  latency_ms: number,
): Promise<void> {
  const distinctId = await mcpDistinctId(request);
  await captureServerEvent({
    distinctId,
    event: "mcp_tool_call",
    properties: { tool, ok, latency_ms },
  });
}
