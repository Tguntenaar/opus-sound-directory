import { Bot, Cpu } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { modelAttribution } from "@/lib/model-display";

export function ModelBadge({
  entry,
  prominent = false,
  chip = false,
}: {
  entry: Pick<SoundEntry, "modelId" | "targetModelId">;
  prominent?: boolean;
  chip?: boolean;
}) {
  const { primary, secondary, isLocalSynth } = modelAttribution(
    entry.modelId,
    entry.targetModelId,
  );

  if (chip) {
    const label = isLocalSynth ? "Local synth" : primary.replace(/^Made with /, "");
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium tracking-wide ${
          isLocalSynth
            ? "bg-zinc-800 text-zinc-400"
            : "bg-violet-500/10 text-violet-200/90"
        }`}
        title={secondary ?? primary}
      >
        {isLocalSynth ? (
          <Cpu className="h-3 w-3 shrink-0 opacity-80" aria-hidden />
        ) : (
          <Bot className="h-3 w-3 shrink-0 opacity-80" aria-hidden />
        )}
        <span className="sr-only">Model: </span>
        {label}
      </span>
    );
  }

  if (prominent) {
    return (
      <div
        className={`rounded-lg border px-3 py-2 ${
          isLocalSynth
            ? "border-amber-500/30 bg-amber-500/10"
            : "border-violet-500/30 bg-violet-500/10"
        }`}
      >
        <p className="flex items-center gap-2 text-sm font-medium text-zinc-100">
          {isLocalSynth ? (
            <Cpu className="h-4 w-4 text-amber-200/80" aria-hidden />
          ) : (
            <Bot className="h-4 w-4 text-violet-200/80" aria-hidden />
          )}
          {primary}
        </p>
        {secondary && <p className="mt-0.5 text-xs text-zinc-500">{secondary}</p>}
      </div>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-zinc-500">
      <Bot className="h-3 w-3 opacity-70" aria-hidden />
      <span className="font-medium text-zinc-400">{primary}</span>
      {secondary ? <span className="text-zinc-600"> · {secondary}</span> : null}
    </span>
  );
}
