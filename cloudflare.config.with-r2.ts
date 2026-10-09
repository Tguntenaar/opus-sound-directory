import { bindings, defineConfig, defineWorker } from "cf/config";

/** Deploy config with R2 full-quality WAV downloads. Use after bucket `opus-sounds-audio` exists. */
export default defineConfig({
  worker: defineWorker({
    name: "opus-sound-directory",
    domains: ["opussounds.directory"],
    workersDev: true,
    previewUrls: true,
    entrypoint: "vinext/server/fetch-handler",
    compatibilityDate: "2026-10-05",
    compatibilityFlags: ["nodejs_compat"],
    assets: { notFoundHandling: "none" },
    env: {
      ASSETS: bindings.assets(),
      ACCOUNTS_DB: bindings.d1({ name: "opus-sounds-accounts", id: "ec780306-8301-4ab1-b1bf-ffe299c7c506" }),
      IMAGES: bindings.images(),
      STATS_KV: bindings.kv({ id: "9ecc01912bb64cf9bed736db1e7525ef" }),
      SPONSOR_KV: bindings.kv({ id: "d24afdeb65a04134bd9ab17db3aef4a3" }),
      SPONSOR_SEND_EMAIL: bindings.sendEmail(),
      AI: bindings.ai(),
      AUDIO_R2: bindings.r2({ name: "opus-sounds-audio" }),
    },
  }),
});
