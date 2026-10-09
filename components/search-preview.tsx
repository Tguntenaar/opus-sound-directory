"use client";

import { useEffect, useRef, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { PlayPauseIcon } from "@/components/play-pause-icon";
import { getPlayingId, notifyEnded, registerAudioElement, requestPause, requestPlay } from "@/lib/audio-controller";
import { useSoundPlaybackAnalytics } from "@/lib/use-sound-playback-analytics";
import type { SearchRecord } from "@/lib/search-records";

export function SearchPreview({ hit }: { hit: SearchRecord }) {
  const audio = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  // Search can show a sound that already has a player on the page.
  const audioId = `search-preview:${hit.slug}`;
  useSoundPlaybackAnalytics(hit, "search", audio, playing);

  useEffect(() => {
    const element = audio.current;
    if (!element) return;
    const unregister = registerAudioElement(audioId, element);
    return () => {
      if (getPlayingId() === audioId) requestPause(audioId);
      element.pause();
      unregister();
    };
  }, [audioId]);

  async function toggle() {
    if (getPlayingId() === audioId) {
      requestPause(audioId);
      setLoading(false);
      return;
    }
    if (failed) audio.current?.load();
    setFailed(false);
    setLoading(true);
    try {
      await requestPlay(audioId);
    } catch {
      if (!audio.current?.isConnected || getPlayingId() !== audioId) return;
      requestPause(audioId);
      setFailed(true);
      setLoading(false);
    }
  }

  return <div className="shrink-0">
    <audio ref={audio} src={hit.previewUrl ?? undefined} preload="none" data-search-preview={hit.slug}
      onPlaying={() => { setPlaying(true); setLoading(false); }}
      onPause={() => { setPlaying(false); setLoading(false); }}
      onEnded={() => { notifyEnded(audioId); setPlaying(false); }}
      onError={() => { if (getPlayingId() === audioId) requestPause(audioId); setFailed(true); setLoading(false); }} />
    <button type="button" onClick={() => void toggle()} aria-pressed={playing}
      aria-label={`${playing ? "Pause" : loading ? "Cancel preview for" : failed ? "Retry preview for" : "Preview"} ${hit.title}`}
      className={`inline-flex h-10 w-10 items-center justify-center rounded-lg border transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400 ${playing ? "border-violet-500/40 bg-violet-500/15 text-violet-300" : "border-zinc-700/60 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-100"}`}>
      {loading ? <LoaderCircle className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden /> : <PlayPauseIcon playing={playing} />}
    </button>
    {failed && <span role="status" className="sr-only">Preview unavailable for {hit.title}. Try again.</span>}
  </div>;
}
