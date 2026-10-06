#!/usr/bin/env node
/**
 * Submit sitemap URLs to IndexNow (Bing, Yandex, etc.).
 * Usage: node scripts/indexnow.mjs
 * Env: SITE_URL (default https://opussounds.directory), INDEXNOW_KEY (optional override)
 */
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const siteUrl = (process.env.SITE_URL || "https://opussounds.directory").replace(/\/$/, "");
const key =
  process.env.INDEXNOW_KEY?.trim() || "opus-sounds-directory-indexnow-key-2026";
const keyLocation = `${siteUrl}/${key}.txt`;

async function fetchSitemapUrls() {
  const res = await fetch(`${siteUrl}/sitemap.xml`);
  if (!res.ok) throw new Error(`sitemap fetch ${res.status}`);
  const xml = await res.text();
  const urls = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
  return urls;
}

async function main() {
  const urlList = await fetchSitemapUrls();
  if (urlList.length === 0) {
    console.error("No URLs in sitemap");
    process.exit(1);
  }
  const host = new URL(siteUrl).host;
  const body = JSON.stringify({ host, key, keyLocation, urlList });
  const res = await fetch("https://api.indexnow.org/indexnow", {
    method: "POST",
    headers: { "Content-Type": "application/json; charset=utf-8" },
    body,
  });
  const text = await res.text();
  console.log(`IndexNow ${res.status}: ${text || "(empty)"}`);
  console.log(`Submitted ${urlList.length} URL(s) from ${siteUrl}/sitemap.xml`);
  if (!res.ok) process.exit(1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
