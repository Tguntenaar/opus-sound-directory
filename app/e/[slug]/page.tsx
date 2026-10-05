import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getAllEntries, getEntryBySlug } from "@/lib/entries";
import { entryShareDescription } from "@/lib/site-metadata";
import { SITE_NAME } from "@/lib/site-url";
import { CATEGORIES } from "@/lib/categories";
import { AudioPlayer } from "@/components/audio-player";
import { CopyButton } from "@/components/copy-button";
import { MetricsPanel } from "@/components/metrics-panel";
import { CodeViewer } from "@/components/code-viewer";
import { DownloadLinks } from "@/components/download-links";
import { UsageBadges } from "@/components/usage-badges";

type Props = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  return getAllEntries().map((e) => ({ slug: e.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const entry = getEntryBySlug(slug);
  if (!entry) {
    return { title: "Not found" };
  }
  const description = entryShareDescription(entry);
  const image = entry.assets.spectrogram;
  const title = entry.title;
  return {
    title,
    description,
    openGraph: {
      type: "article",
      title,
      description,
      url: `/e/${entry.slug}`,
      images: [
        {
          url: image,
          alt: `Spectrogram for ${entry.title}`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: `${title} · ${SITE_NAME}`,
      description,
      images: [image],
    },
  };
}

export default async function EntryPage({ params }: Props) {
  const { slug } = await params;
  const entry = getEntryBySlug(slug);
  if (!entry) notFound();

  const catLabel = CATEGORIES[entry.category]?.label ?? entry.category;

  return (
    <article className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <Link href="/" className="text-sm text-violet-400 hover:text-violet-300">
          ← Browse
        </Link>
        <h1 className="text-3xl font-semibold text-zinc-50">{entry.title}</h1>
        <p className="text-sm text-zinc-500">
          {catLabel} · {entry.modelId} · {entry.generatedAt}
        </p>
        <UsageBadges entryId={entry.id} className="mt-1" />
      </div>

      <AudioPlayer audioId={entry.id} src={entry.assets.wav} title={entry.title} />
      <DownloadLinks
        entryId={entry.id}
        wav={entry.assets.wav}
        mp3={entry.assets.mp3}
        title={entry.title}
      />

      <section className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-medium text-zinc-100">Prompt</h2>
          <CopyButton text={entry.prompt} entryId={entry.id} />
        </div>
        <pre
          className="whitespace-pre-wrap rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-sm leading-relaxed text-zinc-300"
          tabIndex={0}
        >
          {entry.prompt}
        </pre>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium text-zinc-100">Metrics</h2>
        <MetricsPanel entry={entry} />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium text-zinc-100">Spectrogram</h2>
        <img
          src={entry.assets.spectrogram}
          alt={`Spectrogram for ${entry.title}`}
          className="w-full rounded-xl border border-zinc-800 bg-zinc-950"
          loading="lazy"
        />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium text-zinc-100">Generated code</h2>
        <CodeViewer assetPath={entry.assets.code} />
      </section>

      <section className="flex flex-col gap-2 text-sm text-zinc-500">
        <h2 className="text-lg font-medium text-zinc-100">Timing & cues</h2>
        <p>
          {entry.timing.bpm} BPM · {entry.timing.fps} fps · seed {entry.seed}
        </p>
        <ul className="list-inside list-disc text-zinc-400">
          {entry.cues.map((c) => (
            <li key={c.frame}>
              Frame {c.frame}: {c.label}
            </li>
          ))}
        </ul>
        {entry.notes && <p className="text-zinc-600">{entry.notes}</p>}
      </section>
    </article>
  );
}
