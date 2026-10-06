#!/usr/bin/env node
/** Quick SEO sanity checks against local preview or SITE_URL. */
const base = (process.env.SITE_URL || "http://127.0.0.1:43124").replace(/\/$/, "");

const paths = [
  "/",
  "/about",
  "/c/risers",
  "/c/ui-sounds",
  "/e/ui-success-chime",
  "/e/drop-whoosh-stinger",
  "/blog/how-to-write-a-sound-effect-prompt",
];

function extractJsonLd(html) {
  const blocks = [];
  const re = /<script type="application\/ld\+json">([^<]+)<\/script>/g;
  let m;
  while ((m = re.exec(html))) {
    blocks.push(JSON.parse(m[1]));
  }
  return blocks;
}

async function check(path) {
  const url = `${base}${path}`;
  const res = await fetch(url);
  const html = await res.text();
  const title = html.match(/<title[^>]*>([^<]*)<\/title>/i)?.[1] ?? "";
  const desc = html.match(/<meta name="description" content="([^"]*)"/i)?.[1] ?? "";
  const h1s = [...html.matchAll(/<h1[^>]*>/gi)].length;
  const ld = extractJsonLd(html);
  const issues = [];
  if (!res.ok) issues.push(`HTTP ${res.status}`);
  if (!title) issues.push("missing title");
  if (!desc) issues.push("missing description");
  if (h1s !== 1) issues.push(`h1 count ${h1s}`);
  for (const block of ld) {
    try {
      JSON.stringify(block);
    } catch {
      issues.push("invalid JSON-LD");
    }
  }
  return { path, title, issues, ldCount: ld.length };
}

async function main() {
  const results = await Promise.all(paths.map(check));
  const titles = new Map();
  let failed = false;
  for (const r of results) {
    if (r.issues.length) {
      failed = true;
      console.log(`FAIL ${r.path}: ${r.issues.join(", ")}`);
    } else {
      console.log(`OK   ${r.path} (${r.ldCount} JSON-LD)`);
    }
    if (titles.has(r.title)) {
      console.log(`WARN duplicate title: ${r.title}`);
    }
    titles.set(r.title, r.path);
  }
  process.exit(failed ? 1 : 0);
}

main();
