#!/usr/bin/env node
/**
 * Upload masters/<entryId>/out.wav to R2 (remote).
 * Requires CLOUDFLARE_API_TOKEN (or wrangler login) and bucket opus-sounds-audio.
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const mastersDir = path.join(root, "masters");
const bucket = "opus-sounds-audio";

if (!fs.existsSync(mastersDir)) {
  console.error("Missing masters/ — run the audio pipeline to populate masters/<id>/out.wav");
  process.exit(1);
}

const ids = fs
  .readdirSync(mastersDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name)
  .sort();

if (!ids.length) {
  console.error("No masters/<id>/ directories found.");
  process.exit(1);
}

for (const id of ids) {
  const file = path.join(mastersDir, id, "out.wav");
  if (!fs.existsSync(file)) {
    console.warn(`skip ${id}: missing ${file}`);
    continue;
  }
  const objectKey = `${id}/out.wav`;
  console.log(`put ${bucket}/${objectKey}`);
  execFileSync(
    "npx",
    [
      "wrangler",
      "r2",
      "object",
      "put",
      `${bucket}/${objectKey}`,
      "--file",
      file,
      "--content-type",
      "audio/wav",
      "--remote",
    ],
    { cwd: root, stdio: "inherit" },
  );
}

console.log(`Uploaded ${ids.length} WAV(s) to R2 bucket ${bucket}.`);
