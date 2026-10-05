"use client";

import { useStats } from "@/components/stats-provider";

type Props = {
  entryId: string;
  wav: string;
  mp3: string;
  title: string;
};

export function DownloadLinks({ entryId, wav, mp3, title }: Props) {
  const { track } = useStats();

  function onDownload() {
    track(entryId, "download");
  }

  return (
    <div className="flex flex-wrap gap-2">
      <a
        href={wav}
        download={`${title.replace(/\s+/g, "-").toLowerCase()}.wav`}
        onClick={onDownload}
        className="rounded-lg border border-zinc-700 px-3 py-1.5 text-sm text-zinc-200 hover:border-violet-500 hover:text-violet-300"
      >
        Download WAV
      </a>
      <a
        href={mp3}
        download={`${title.replace(/\s+/g, "-").toLowerCase()}.mp3`}
        onClick={onDownload}
        className="rounded-lg border border-zinc-700 px-3 py-1.5 text-sm text-zinc-200 hover:border-violet-500 hover:text-violet-300"
      >
        Download MP3
      </a>
    </div>
  );
}
