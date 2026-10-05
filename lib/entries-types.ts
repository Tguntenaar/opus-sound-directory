export type SoundEntry = {
  id: string;
  slug: string;
  title: string;
  category: string;
  tags: string[];
  prompt: string;
  modelId: string;
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
};
