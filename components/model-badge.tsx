import type { SoundEntry } from "@/lib/entries";
import { modelAttribution } from "@/lib/model-display";

export function ModelBadge({
  entry,
  prominent = false,
  chip = false,
}: {
  entry: Pick<SoundEntry, "modelId" | "targetModelId">;
  prominent?: boolean;
  /** Small pill for browse cards — primary label only. */
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
        className={`inline-block rounded-md px-1.5 py-0.5 text-[10px] font-medium tracking-wide ${
          isLocalSynth
            ? "bg-zinc-800 text-zinc-400"
            : "bg-violet-500/10 text-violet-200/90"
        }`}
        title={secondary ?? undefined}
      >
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
