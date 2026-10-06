const cache = new Map<string, number[]>();
const pending = new Map<string, Promise<number[]>>();

const BAR_COUNT = 72;

function downsample(channel: Float32Array, barCount: number): number[] {
  const block = Math.max(1, Math.floor(channel.length / barCount));
  const peaks: number[] = [];
  for (let i = 0; i < barCount; i++) {
    const start = i * block;
    const end = Math.min(channel.length, start + block);
    let max = 0;
    for (let j = start; j < end; j++) {
      const v = Math.abs(channel[j]);
      if (v > max) max = v;
    }
    peaks.push(max);
  }
  const top = Math.max(...peaks, 0.001);
  return peaks.map((p) => p / top);
}

export async function loadWaveformPeaks(src: string): Promise<number[]> {
  const hit = cache.get(src);
  if (hit) return hit;
  const inflight = pending.get(src);
  if (inflight) return inflight;

  const job = (async () => {
    try {
      const res = await fetch(src);
      if (!res.ok) throw new Error("fetch failed");
      const buf = await res.arrayBuffer();
      const ctx = new AudioContext();
      const decoded = await ctx.decodeAudioData(buf.slice(0));
      await ctx.close();
      const channel = decoded.getChannelData(0);
      const peaks = downsample(channel, BAR_COUNT);
      cache.set(src, peaks);
      return peaks;
    } catch {
      const fallback = Array.from({ length: BAR_COUNT }, (_, i) =>
        0.15 + 0.55 * Math.abs(Math.sin(i * 0.35)),
      );
      cache.set(src, fallback);
      return fallback;
    } finally {
      pending.delete(src);
    }
  })();

  pending.set(src, job);
  return job;
}

export const WAVEFORM_BAR_COUNT = BAR_COUNT;
