import type { Metadata } from "next";
import Link from "next/link";
import { canonicalForPath } from "@/lib/site-metadata";
import { DEFAULT_OG_IMAGE, SITE_NAME } from "@/lib/site-url";

const title = "About";

export const metadata: Metadata = {
  title,
  alternates: { canonical: canonicalForPath("/about") },
  openGraph: {
    title: `${title} · ${SITE_NAME}`,
    url: "/about",
    images: [{ url: DEFAULT_OG_IMAGE, width: 1200, height: 630 }],
  },
};

export default function AboutPage() {
  return (
    <div className="prose prose-invert max-w-2xl prose-headings:text-zinc-100 prose-p:text-zinc-400">
      <h1 className="text-3xl font-semibold">About this directory</h1>
      <p>
        Opus Sound Directory catalogues synthesised audio built for video: ad beds, transitions, UI
        ticks, logo stings, and ambient layers — with the{" "}
        <strong className="text-zinc-200">Claude Opus prompts and Python code</strong> behind each
        entry. Listings live as JSON in git with assets under{" "}
        <code className="text-zinc-300">public/assets/</code>.
      </p>
      <p>
        Each entry ships the prompt, Python synthesis code, waveform, spectrogram, and loudness
        metrics. Audio here is <strong className="text-zinc-200">synthesised</strong> — precise and
        royalty-free for video — but not a stand-in for real instruments, vocals, or a final mix. Your
        ear still wins.
      </p>
      <h2 className="text-xl font-medium text-zinc-100">What you are hearing</h2>
      <p>
        Everything is <strong className="text-zinc-200">synthesised in Python</strong> (numpy/scipy)
        from written prompts — no sample packs, no artist references. That means timing and loudness
        can be nailed to frames, and the results are royalty-free for rough cuts and prototypes.
      </p>
      <p>
        It also means timbres are artificial: not realistic drums, vocals, or boutique mix glue. Prompts
        and metrics help you reproduce and iterate; a human still has to judge taste and final level in
        context.
      </p>
      <h2 className="text-xl font-medium text-zinc-100">How entries are made</h2>
      <ol className="list-decimal pl-5 text-zinc-400">
        <li>Write a numeric prompt (duration, sample count, BPM, cue frames, master targets).</li>
        <li>Run the Python runner (mock or future Claude agent mode).</li>
        <li>Verify length, LUFS/peak, spectrogram; commit JSON + assets.</li>
      </ol>
      <p>
        Use the{" "}
        <Link href="/submit" className="text-violet-400 hover:text-violet-300">submit form</Link> or
        open a PR on{" "}
        <a
          href="https://github.com/Tguntenaar/opus-sound-directory"
          className="text-violet-400 hover:text-violet-300"
          target="_blank"
          rel="noopener noreferrer"
        >
          GitHub
        </a>{" "}
        to add entries.
      </p>
    </div>
  );
}
