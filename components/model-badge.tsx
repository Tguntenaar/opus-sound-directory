import { Bot, Cpu, Users } from "lucide-react";
import type { SoundEntry } from "@/lib/entries";
import { modelBadgeDisplay } from "@/lib/model-badge-display";

export function ModelBadge({
  entry,
  prominent = false,
  chip = false,
}: {
  entry: Pick<SoundEntry, "modelId">;
  prominent?: boolean;
  chip?: boolean;
}) {
  const { label, tooltip, variant } = modelBadgeDisplay(entry);

  const Icon =
    variant === "local" ? Cpu : variant === "community" ? Users : Bot;

  if (chip) {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium tracking-wide ${
          variant === "community"
            ? "bg-emerald-500/10 text-emerald-200/90"
            : variant === "local"
              ? "bg-zinc-800 text-zinc-400"
              : "bg-violet-500/10 text-violet-200/90"
        }`}
        title={tooltip}
      >
        <Icon className="h-3 w-3 shrink-0 opacity-80" aria-hidden />
        <span className="sr-only">Model: </span>
        {label}
      </span>
    );
  }

  if (prominent) {
    return (
      <div
        className={`rounded-lg border px-3 py-2 ${
          variant === "local"
            ? "border-amber-500/30 bg-amber-500/10"
            : variant === "community"
              ? "border-emerald-500/30 bg-emerald-500/10"
              : "border-violet-500/30 bg-violet-500/10"
        }`}
        title={tooltip}
      >
        <p className="flex items-center gap-2 text-sm font-medium text-zinc-100">
          <Icon className="h-4 w-4 opacity-80" aria-hidden />
          {label}
        </p>
      </div>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-zinc-500" title={tooltip}>
      <Icon className="h-3 w-3 opacity-70" aria-hidden />
      <span className="font-medium text-zinc-400">{label}</span>
    </span>
  );
}
