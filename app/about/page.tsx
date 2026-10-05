import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="prose prose-invert max-w-2xl prose-headings:text-zinc-100 prose-p:text-zinc-400">
      <h1 className="text-3xl font-semibold">About this directory</h1>
      <p>
        Opus Sound Directory catalogues <strong className="text-zinc-200">Claude Opus–generated</strong>{" "}
        audio built for video: ad beds, transitions, UI ticks, logo stings, and ambient layers. Each
        listing is stored as JSON in git with assets under <code className="text-zinc-300">public/assets/</code>.
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
        <Link href="/submit" className="text-violet-400 hover:text-violet-300">
          Submit form
        </Link>{" "}
        is a stub — v1 source of truth is JSON in the repo.
      </p>
    </div>
  );
}
