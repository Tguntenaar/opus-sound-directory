import { bindings, defineConfig, defineWorker } from "cf/config";

export default defineConfig({
  worker: defineWorker({
    name: "opus-sound-directory",
    entrypoint: "vinext/server/fetch-handler",
    compatibilityDate: "2026-10-05",
    compatibilityFlags: ["nodejs_compat"],
    assets: { notFoundHandling: "none" },
    env: {
      ASSETS: bindings.assets(),
      IMAGES: bindings.images(),
      /** Copy/download counters per entry (`stats:{id}:copy|download`). */
      STATS_KV: bindings.kv(),
    },
  }),
});
