import { bindings, defineConfig, defineWorker } from "cf/config";

/** Deploy config with R2 full-quality WAV downloads. Use after bucket `opus-sounds-audio` exists. */
export default defineConfig({
  worker: defineWorker({
    name: "opus-sound-directory",
    entrypoint: "vinext/server/fetch-handler",
    compatibilityDate: "2026-10-05",
    compatibilityFlags: ["nodejs_compat"],
    assets: { notFoundHandling: "none" },
    env: {
      ASSETS: bindings.assets(),
      ACCOUNTS_DB: bindings.d1({ name: "opus-sounds-accounts" }),
      IMAGES: bindings.images(),
      STATS_KV: bindings.kv(),
      SPONSOR_KV: bindings.kv(),
      SPONSOR_SEND_EMAIL: bindings.sendEmail(),
      AI: bindings.ai(),
      AUDIO_R2: bindings.r2({ name: "opus-sounds-audio" }),
    },
  }),
});
