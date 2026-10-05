import type { SoundEntry } from "@/lib/entries";
import { modelAttribution } from "@/lib/model-display";

export function ModelBadge({
  entry,
  prominent = false,
}: {
  entry: Pick<SoundEntry, "modelId" | "targetModelId">;
  prominent?: boolean;
}) {
  const { primary, secondary, isLocalSynth } = modelAttribution(
    entry.modelId,
    entry.targetModelId,
  );

  if (prominent) {
    return (
      <div
        className={`rounded-lg border px-3 py-2 ${
          isLocalSynth
            ? "border-amber-500/30 bg-amber-500/10"
            : "border-violet-500/30 bg-violet-500/10"
        }`}
      >
        <p className="text-sm font-medium text-zinc-100">{primary}</p>
        {secondary && <p className="mt-0.5 text-xs text-zinc-500">{secondary}</p>}
      </div>
    );
  }

  return (
    <span className="text-xs text-zinc-500">
      <span className="font-medium text-zinc-400">{primary}</span>
      {secondary ? <span className="text-zinc-600"> · {secondary}</span> : null}
    </span>
  );
}
