import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import {
  getAllEntriesMerged,
  getEntryBySlugMerged,
  isEntryHidden,
} from "@/lib/entries";
import { isCommunityEntry } from "@/lib/community-types";
import { canonicalForPath } from "@/lib/site-metadata";
import { SITE_NAME } from "@/lib/site-url";
import { CATEGORIES } from "@/lib/categories";
import {
  entryMetaDescription,
  entryPageTitle,
  entryAudioUrls,
  relatedEntries,
  spectrogramAlt,
} from "@/lib/entry-seo";
import { AudioPlayer } from "@/components/audio-player";
import { CopyButton } from "@/components/copy-button";
import { MetricsPanel } from "@/components/metrics-panel";
import { CodeViewer } from "@/components/code-viewer";
import { DownloadLinks } from "@/components/download-links";
import { UsageBadges } from "@/components/usage-badges";
import { MoodChips } from "@/components/mood-chips";
import { ModelBadge } from "@/components/model-badge";
import { SpectrogramImage } from "@/components/spectrogram-image";
import { EntryShareActions } from "@/components/entry-share-actions";
import { entryAudioObjectJsonLd, breadcrumbListJsonLd } from "@/lib/structured-data";
import { JsonLd } from "@/components/json-ld";
import { RelatedEntries } from "@/components/related-entries";
import { RelatedGuideLink } from "@/components/related-guide-link";
import { DEFAULT_OG_IMAGE } from "@/lib/site-url";
import { entryWavDownloadPath } from "@/lib/wav-url";

type Props = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  const entries = await getAllEntriesMerged();
  return entries.map((e) => ({ slug: e.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const entry = await getEntryBySlugMerged(slug, true);
  if (!entry) {
    return { title: "Not found" };
  }
  if (isEntryHidden(entry)) {
    redirect(`/c/${entry.category}`);
  }
  const description = entryMetaDescription(entry);
  const title = entryPageTitle(entry);
  const image = entry.assets.spectrogram || DEFAULT_OG_IMAGE;
  const { mp3, canonical } = entryAudioUrls(entry);
  return {
    title,
    description,
    alternates: { canonical: canonicalForPath(`/e/${entry.slug}`) },
    openGraph: {
      type: "music.song",
      title: entry.title,
      description,
      url: `/e/${entry.slug}`,
      images: [{ url: image, alt: spectrogramAlt(entry) }],
      ...(entry.assets.mp3 ? { audio: [{ url: mp3, type: "audio/mpeg" }] } : {}),
    },
    twitter: {
      card: entry.assets.mp3 ? "player" : "summary_large_image",
      title: `${entry.title} · ${SITE_NAME}`,
      description,
      images: [image],
      ...(entry.assets.mp3
        ? {
            players: [
              {
                playerUrl: canonical,
                streamUrl: mp3,
                width: 480,
                height: 200,
              },
            ],
          }
        : {}),
    },
  };
}

export default async function EntryPage({ params }: Props) {
  const { slug } = await params;
  const entry = await getEntryBySlugMerged(slug, true);
  if (!entry) notFound();
  if (isEntryHidden(entry)) {
    redirect(`/c/${entry.category}`);
  }

  const community = isCommunityEntry(entry) ? entry : null;
  const hasAudio = community ? community.hasRenderedAudio && Boolean(entry.assets.mp3) : true;
  const all = await getAllEntriesMerged();
  const catLabel = CATEGORIES[entry.category]?.label ?? entry.category;
  const related = relatedEntries(entry, all);
  const breadcrumbs = breadcrumbListJsonLd([
    { name: "Browse", path: "/" },
    { name: catLabel, path: `/c/${entry.category}` },
    { name: entry.title, path: `/e/${entry.slug}` },
  ]);

  return (
    <article className="page-enter flex min-w-0 flex-col gap-8">
      <JsonLd data={[entryAudioObjectJsonLd(entry), breadcrumbs]} />
      <div className="flex flex-col gap-2">
        <Link
          href={`/c/${entry.category}`}
          className="inline-flex w-fit items-center gap-1.5 text-sm text-violet-400 transition-colors hover:text-violet-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500/60"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          {catLabel}
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold text-zinc-50">{entry.title}</h1>
            <p className="mt-1 text-sm text-zinc-400">{catLabel} · {entry.generatedAt}</p>
          </div>
          <EntryShareActions slug={entry.slug} title={entry.title} entry={entry} />
        </div>
        <RelatedGuideLink entryId={entry.id} category={entry.category} />
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <div className="max-w-md">
            <ModelBadge entry={entry} prominent />
          </div>
        </div>
        {community?.author?.name && (
          <p className="text-sm text-zinc-500">
            Credit:{" "}
            {community.author.url ? (
              <a
                href={community.author.url}
                className="text-violet-400 hover:text-violet-300"
                rel="noopener noreferrer"
                target="_blank"
              >
                {community.author.name}
              </a>
            ) : (
              community.author.name
            )}
          </p>
        )}
        <div className="mt-3">
          <MoodChips entry={entry} />
        </div>
        <UsageBadges entryId={entry.id} className="mt-3" />
      </div>

      {hasAudio ? (
        <>
          <AudioPlayer
            audioId={entry.id}
            src={entry.assets.mp3}
            title={entry.title}
            entry={entry}
          />
          <DownloadLinks
            entryId={entry.id}
            wav={
              community || !entry.assets.wav
                ? entry.assets.wav
                : entryWavDownloadPath(entry.id)
            }
            mp3={entry.assets.mp3}
            title={entry.title}
            entry={entry}
          />
        </>
      ) : (
        <p className="rounded-xl border border-zinc-800 bg-zinc-900/40 px-4 py-3 text-sm text-zinc-400">
          Prompt + code (not yet rendered) — run the synthesis script locally or wait for a maintainer
          render. Use the code section below.
        </p>
      )}

      <section className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-medium text-zinc-100">Prompt</h2>
          <CopyButton text={entry.prompt} entryId={entry.id} iconOnly entry={entry} source="detail" />
        </div>
        <pre
          className="max-w-full min-w-0 overflow-x-auto whitespace-pre-wrap rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-sm leading-relaxed text-zinc-300 transition-colors hover:border-zinc-700/90"
          tabIndex={0}
        >
          {entry.prompt}
        </pre>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium text-zinc-100">Metrics</h2>
        <MetricsPanel entry={entry} />
      </section>

      {entry.assets.spectrogram ? (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-medium text-zinc-100">Spectrogram</h2>
          <SpectrogramImage
            src={entry.assets.spectrogram}
            alt={spectrogramAlt(entry)}
            width={1200}
            height={400}
          />
        </section>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium text-zinc-100">Generated code</h2>
        <CodeViewer assetPath={entry.assets.code} entryId={entry.id} entry={entry} />
      </section>

      <section className="flex flex-col gap-2 text-sm text-zinc-400">
        <h2 className="text-lg font-medium text-zinc-100">Timing & cues</h2>
        <p>
          {entry.timing.bpm != null ? `${entry.timing.bpm} BPM · ` : ""}
          {entry.timing.fps} fps · seed {entry.seed}
        </p>
        <ul className="list-inside list-disc text-zinc-400">
          {entry.cues.map((c) => (
            <li key={c.frame}>
              Frame {c.frame}: {c.label}
            </li>
          ))}
        </ul>
        {entry.notes && <p className="text-zinc-400">{entry.notes}</p>}
      </section>

      <RelatedEntries entries={related} category={entry.category} />
    </article>
  );
}
