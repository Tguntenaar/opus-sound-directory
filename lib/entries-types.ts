export type SoundEntry = {
  id: string;
  slug: string;
  title: string;
  category: string;
  tags: string[];
  /** Style facets for browse/filter display (e.g. upbeat, sad, bright). */
  mood: string[];
  /** Coarse tempo bucket. */
  tempo?: "slow" | "medium" | "fast";
  prompt: string;
  /** Generation source shown in UI (`local-synth` or Anthropic model id). */
  modelId: string;
  /** Opus model id intended for `--agent` runs when `modelId` is local-synth. */
  targetModelId?: string;
  generatedAt: string;
  seed: number;
  timing: {
    bpm: number;
    fps: number;
    durationSec: number;
    samples: number;
    sampleRate: number;
  };
  cues: { frame: number; label: string }[];
  master: { targetLufs: number; truePeakDbTp: number };
  metrics: {
    lufs: number | null;
    truePeak: number | null;
    /** Max momentary (400 ms) loudness from ffmpeg ebur128 when measured. */
    lufsMomentaryMax?: number | null;
    /** Max short-term (3 s) loudness from ffmpeg ebur128 when measured. */
    lufsShortTermMax?: number | null;
    durationSec: number | null;
    passedChecks: boolean;
  };
  assets: {
    wav: string;
    mp3: string;
    spectrogram: string;
    code: string;
  };
  notes: string;
  /** KV-backed community publish */
  isCommunity?: boolean;
  submissionId?: string;
  author?: { name?: string; url?: string };
  hasRenderedAudio?: boolean;
  codeApiPath?: string;
};
