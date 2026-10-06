import type { SoundEntry } from "@/lib/entries";

function fmt(value: number | null, suffix = "") {
  if (value === null || value === undefined) return "—";
  return `${value}${suffix}`;
}

export function MetricsPanel({ entry }: { entry: SoundEntry }) {
  const { metrics, timing, master } = entry;
  const rows = [
    { label: "Integrated LUFS", value: fmt(metrics.lufs, " LUFS") },
    { label: "True peak", value: fmt(metrics.truePeak, " dBTP") },
    {
      label: "Length",
      value:
        metrics.durationSec != null
          ? `${metrics.durationSec}s · ${timing.samples.toLocaleString()} samples @ ${timing.sampleRate} Hz`
          : `${timing.durationSec}s (target)`,
    },
    { label: "Target master", value: `${master.targetLufs} LUFS · peak ≤ ${master.truePeakDbTp} dBTP` },
    {
      label: "Checks",
      value: metrics.passedChecks ? "Passed (runner)" : "Pending / partial",
    },
  ];

  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {rows.map((row) => (
        <div key={row.label} className="rounded-lg border border-zinc-800 bg-zinc-950/50 px-3 py-2">
          <dt className="text-xs text-zinc-500">{row.label}</dt>
          <dd className="mt-0.5 text-sm font-medium text-zinc-100">{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}
