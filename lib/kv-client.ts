export type KvLike = {
  get(key: string): Promise<string | null>;
  put(key: string, value: string): Promise<void>;
  list?: (options?: { prefix?: string; limit?: number }) => Promise<{
    keys: { name: string }[];
  }>;
};

const devStores = new Map<string, Map<string, string>>();

function devKv(storeId: string): KvLike {
  if (!devStores.has(storeId)) devStores.set(storeId, new Map());
  const mem = devStores.get(storeId)!;
  return {
    async get(key) {
      return mem.get(key) ?? null;
    },
    async put(key, value) {
      mem.set(key, value);
    },
    async list({ prefix = "" } = {}) {
      const keys = [...mem.keys()]
        .filter((k) => k.startsWith(prefix))
        .map((name) => ({ name }));
      return { keys };
    },
  };
}

export async function getKvBinding(binding: "STATS_KV" | "SPONSOR_KV"): Promise<KvLike> {
  try {
    const { env } = await import("cloudflare:workers");
    const kv = (env as Record<string, KvLike | undefined>)[binding];
    if (kv) return kv;
  } catch {
    // outside workerd
  }
  return devKv(binding);
}
