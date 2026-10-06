import type { SoundEntry } from "@/lib/entries";
import { entryMetricsPassed, isShortUiEntry } from "@/lib/entry-metrics";

function fmt(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined) return "—";
  return `${value}${suffix}`;
}

export function MetricsPanel({ entry }: { entry: SoundEntry }) {
  const { metrics, timing, master } = entry;
  const passed = entryMetricsPassed(entry);
  const shortUi = isShortUiEntry(entry);

  const lengthRow = {
    label: "Length",
    value:
      metrics.durationSec != null
        ? `${metrics.durationSec}s · ${timing.samples.toLocaleString()} samples @ ${timing.sampleRate} Hz`
        : `${timing.durationSec}s (target)`,
  };

  const targetRow = {
    label: "Target master",
    value: `${master.targetLufs} LUFS · peak ≤ ${master.truePeakDbTp} dBTP`,
  };

  const checksRow = passed ? [{ label: "Checks", value: "Passed" }] : [];

  const rows = shortUi
    ? [
        {
          label: "Integrated LUFS (approx.)",
          value: fmt(metrics.lufs, " LUFS"),
        },
        { label: "True peak", value: fmt(metrics.truePeak, " dBTP") },
        {
          label: "Momentary max",
          value: fmt(metrics.lufsMomentaryMax, " LUFS"),
        },
        {
          label: "Short-term max",
          value: fmt(metrics.lufsShortTermMax, " LUFS"),
        },
        lengthRow,
        targetRow,
        ...checksRow,
      ]
    : [
        { label: "Integrated LUFS", value: fmt(metrics.lufs, " LUFS") },
        { label: "True peak", value: fmt(metrics.truePeak, " dBTP") },
        lengthRow,
        targetRow,
        ...checksRow,
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
