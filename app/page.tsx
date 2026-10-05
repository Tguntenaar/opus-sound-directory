import { getAllEntries } from "@/lib/entries";
import { CATEGORY_ORDER, CATEGORIES } from "@/lib/categories";
import { EntryCard } from "@/components/entry-card";

export default function HomePage() {
  const entries = getAllEntries();

  return (
    <div className="flex flex-col gap-10">
      <section className="max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">
          Opus-generated sound, on the record
        </h1>
        <p className="mt-3 text-zinc-400 leading-relaxed">
          Each entry ships the prompt, Python synthesis code, waveform, spectrogram, and loudness
          metrics. Audio here is{" "}
          <strong className="font-medium text-zinc-200">synthesised</strong> — precise and
          royalty-free for video — but not a stand-in for real instruments, vocals, or a final mix.
          Your ear still wins.
        </p>
      </section>

      {CATEGORY_ORDER.map((catId) => {
        const group = entries.filter((e) => e.category === catId);
        if (group.length === 0) return null;
        const meta = CATEGORIES[catId];
        return (
          <section key={catId} id={catId} className="scroll-mt-8">
            <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
              <h2 className="text-xl font-medium text-zinc-100">{meta.label}</h2>
              <p className="text-sm text-zinc-500">{meta.description}</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {group.map((entry) => (
                <EntryCard key={entry.id} entry={entry} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
