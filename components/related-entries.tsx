import Link from "next/link";
import type { SoundEntry } from "@/lib/entries";
import { CATEGORIES } from "@/lib/categories";

export function RelatedEntries({
  entries,
  category,
}: {
  entries: SoundEntry[];
  category: string;
}) {
  if (entries.length === 0) return null;
  const catLabel = CATEGORIES[category]?.label ?? category;
  return (
    <section className="border-t border-zinc-800/80 pt-8">
      <h2 className="text-sm font-medium text-zinc-300">More like this</h2>
      <p className="mt-1 text-xs text-zinc-600">More free {catLabel.toLowerCase()} on the directory.</p>
      <ul className="mt-4 flex flex-col gap-2">
        {entries.map((e) => (
          <li key={e.id}>
            <Link
              href={`/e/${e.slug}`}
              className="text-sm text-violet-400/90 transition-colors hover:text-violet-300"
            >
              {e.title}
              <span className="text-zinc-600"> · {e.timing.durationSec}s</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
