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
      /** Sponsor interest leads (`sponsor:lead:{uuid}`, index `sponsor:index`). */
      SPONSOR_KV: bindings.kv(),
      /**
       * Optional Email Sending binding — enable domain in dashboard, set SPONSOR_MAIL_FROM
       * (verified sender). Notifies thomas@guntenaar.org unless SPONSOR_MAIL_TO is set.
       */
      SPONSOR_SEND_EMAIL: bindings.sendEmail(),
      /** Workers AI — automated submission review (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`). */
      AI: bindings.ai(),
      /** Full-quality 48 kHz WAV masters — enable after R2 bucket exists (see `cloudflare.config.with-r2.ts`). */
      // AUDIO_R2: bindings.r2({ name: "opus-sounds-audio" }),
    },
  }),
});
