#!/usr/bin/env node
/**
 * Full-site crawl audit for Opus Sounds Directory.
 * Usage: node scripts/crawl-audit.mjs [baseUrl]
 *        SITE_URL=https://opussounds.directory node scripts/crawl-audit.mjs
 *
 * Exit 0 if no blocking findings; 1 if any error-severity finding.
 */
const base = (process.argv[2] || process.env.SITE_URL || "https://opussounds.directory").replace(
  /\/$/,
  "",
);
const CANONICAL_HOST = "https://opussounds.directory";

const EXTRA_PATHS = [
  "/submit",
  "/llms.txt",
  "/llms-full.txt",
  "/blog/rss.xml",
  "/robots.txt",
];

const VISIBLE_PLACEHOLDER_RE =
  /\b(lorem ipsum|TODO|FIXME|\[object Object\]|placeholder text)\b/i;
const EMPTY_HEADING_RE = /<h[1-6][^>]*>\s*<\/h[1-6]>/gi;

function htmlForVisibleTextCheck(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<!--[\s\S]*?-->/g, "");
}

function stripTags(html) {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");
}

/** Decode common HTML entities so length checks match visible snippet text. */
function decodeHtmlEntities(str) {
  return str
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCharCode(parseInt(h, 16)));
}

const TITLE_MIN = 30;
const TITLE_MAX = 65;
const DESC_MIN = 70;
const DESC_MAX = 160;

/** @typedef {{ severity: 'error'|'warn'|'info', url: string, check: string, detail: string }} Finding */

/** @type {Finding[]} */
const findings = [];

function add(severity, url, check, detail) {
  findings.push({ severity, url, check, detail });
}

async function fetchText(url, opts = {}) {
  const res = await fetch(url, {
    redirect: "follow",
    headers: { "User-Agent": "opus-crawl-audit/1.0 (+https://opussounds.directory)" },
    ...opts,
  });
  const text = await res.text().catch(() => "");
  return { res, text };
}

async function headOrGet(url) {
  try {
    let res = await fetch(url, {
      method: "HEAD",
      redirect: "follow",
      headers: { "User-Agent": "opus-crawl-audit/1.0" },
    });
    if (res.status === 405 || res.status === 501) {
      res = await fetch(url, {
        method: "GET",
        redirect: "follow",
        headers: { "User-Agent": "opus-crawl-audit/1.0" },
      });
    }
    return res;
  } catch (e) {
    return { ok: false, status: 0, headers: new Headers(), error: String(e) };
  }
}

function parseSitemapLocs(xml) {
  return [...xml.matchAll(/<loc>\s*([^<\s]+)\s*<\/loc>/gi)].map((m) => m[1].trim());
}

function extractMeta(html, nameOrProp, isProperty = false) {
  const attr = isProperty ? "property" : "name";
  const re = new RegExp(
    `<meta[^>]+${attr}=["']${nameOrProp}["'][^>]+content=["']([^"']*)["']|<meta[^>]+content=["']([^"']*)["'][^>]+${attr}=["']${nameOrProp}["']`,
    "i",
  );
  const m = html.match(re);
  return m ? (m[1] ?? m[2] ?? "") : "";
}

function extractLinkRel(html, rel) {
  const re = new RegExp(
    `<link[^>]+rel=["']${rel}["'][^>]+href=["']([^"']+)["']|<link[^>]+href=["']([^"']+)["'][^>]+rel=["']${rel}["']`,
    "gi",
  );
  const out = [];
  let m;
  while ((m = re.exec(html))) {
    out.push(m[1] ?? m[2]);
  }
  return out;
}

function extractJsonLd(html) {
  const blocks = [];
  const re = /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html))) {
    blocks.push(m[1].trim());
  }
  return blocks;
}

function resolveUrl(href, pageUrl) {
  try {
    return new URL(href, pageUrl).href;
  } catch {
    return null;
  }
}

function isInternal(url) {
  try {
    const u = new URL(url);
    return u.hostname === "opussounds.directory" || u.hostname === "www.opussounds.directory";
  } catch {
    return false;
  }
}

function collectAssetUrls(html, pageUrl) {
  const urls = new Set();
  const patterns = [
    /<(?:img|script|source|audio|video|embed)[^>]+src=["']([^"']+)["']/gi,
    /<link[^>]+href=["']([^"']+)["']/gi,
    /url\(["']?([^"')]+)["']?\)/gi,
  ];
  for (const re of patterns) {
    let m;
    while ((m = re.exec(html))) {
      const r = resolveUrl(m[1], pageUrl);
      if (r) urls.add(r);
    }
  }
  for (const href of extractLinkRel(html, "canonical")) {
    const r = resolveUrl(href, pageUrl);
    if (r) urls.add(r);
  }
  const og = extractMeta(html, "og:image", true) || extractMeta(html, "twitter:image", true);
  if (og) {
    const r = resolveUrl(og, pageUrl);
    if (r) urls.add(r);
  }
  return urls;
}

function collectInternalLinks(html, pageUrl) {
  const links = new Set();
  const re = /<a[^>]+href=["']([^"']+)["']/gi;
  let m;
  while ((m = re.exec(html))) {
    const href = m[1];
    if (href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) continue;
    const r = resolveUrl(href, pageUrl);
    if (r && isInternal(r)) links.add(r);
  }
  return links;
}

const checkedAssets = new Map();

async function checkAsset(url) {
  if (checkedAssets.has(url)) return checkedAssets.get(url);
  const res = await headOrGet(url);
  const ct = res.headers?.get?.("content-type") ?? "";
  const ok = res.ok || res.status === 206;
  const result = { ok, status: res.status, contentType: ct };
  checkedAssets.set(url, result);
  return result;
}

function isHtmlPage(url) {
  const p = new URL(url).pathname;
  if (p.endsWith(".xml") || p.endsWith(".txt") || p === "/robots.txt") return false;
  if (p.endsWith(".rss.xml")) return false;
  return true;
}

async function auditPage(url) {
  const { res, text } = await fetchText(url);
  if (!res.ok) {
    add("error", url, "http-status", `HTTP ${res.status}`);
    return { title: "", description: "", html: text };
  }

  const isHtml = (res.headers.get("content-type") || "").includes("html") || isHtmlPage(url);
  if (!isHtml) {
    return { title: "", description: "", html: text };
  }

  const title = decodeHtmlEntities(
    (text.match(/<title[^>]*>([^<]*)<\/title>/i)?.[1] ?? "").trim(),
  );
  const description = decodeHtmlEntities(extractMeta(text, "description"));
  const canonicals = extractLinkRel(text, "canonical");
  const h1Count = [...text.matchAll(/<h1[^>]*>/gi)].length;

  if (!title) add("error", url, "title", "missing <title>");
  else {
    if (title.length < TITLE_MIN)
      add("warn", url, "title-length", `${title.length} chars (min ~${TITLE_MIN}): "${title}"`);
    if (title.length > TITLE_MAX)
      add("warn", url, "title-length", `${title.length} chars (max ~${TITLE_MAX}): "${title}"`);
  }

  if (!description) add("warn", url, "meta-description", "missing meta description");
  else {
    if (description.length < DESC_MIN)
      add("warn", url, "meta-description-length", `${description.length} chars (min ~${DESC_MIN})`);
    if (description.length > DESC_MAX)
      add("warn", url, "meta-description-length", `${description.length} chars (max ~${DESC_MAX})`);
  }

  if (canonicals.length === 0) add("warn", url, "canonical", "missing canonical link");
  else {
    for (const c of canonicals) {
      if (!c.startsWith(CANONICAL_HOST))
        add("error", url, "canonical-host", `canonical ${c} is not on ${CANONICAL_HOST}`);
      const norm = c.replace(/\/$/, "");
      const pageNorm = url.replace(/\/$/, "");
      if (norm !== pageNorm && !pageNorm.endsWith("/") && c !== url)
        add("warn", url, "canonical-match", `canonical ${c} vs page ${url}`);
    }
  }

  const ogImage = extractMeta(text, "og:image", true);
  const twImage = extractMeta(text, "twitter:image", true) || extractMeta(text, "twitter:image");
  for (const [label, imgUrl] of [
    ["og:image", ogImage],
    ["twitter:image", twImage],
  ]) {
    if (!imgUrl) {
      add("warn", url, label, "missing");
      continue;
    }
    const resolved = resolveUrl(imgUrl, url);
    const check = await checkAsset(resolved);
    if (!check.ok)
      add("error", url, label, `${resolved} → HTTP ${check.status}`);
    else if (!check.contentType.startsWith("image/"))
      add("warn", url, label, `${resolved} content-type: ${check.contentType}`);
  }

  for (const block of extractJsonLd(text)) {
    try {
      JSON.parse(block);
    } catch (e) {
      add("error", url, "json-ld", `parse error: ${e.message}`);
    }
  }

  const visibleText = stripTags(htmlForVisibleTextCheck(text));
  if (VISIBLE_PLACEHOLDER_RE.test(visibleText))
    add("error", url, "placeholder-text", "matched placeholder/TODO/lorem in visible page text");
  if (/\bundefined\b/.test(visibleText) || /\bNaN\b/.test(visibleText))
    add("error", url, "placeholder-text", "rendered undefined or NaN in visible page text");

  const emptyHeadings = text.match(EMPTY_HEADING_RE);
  if (emptyHeadings?.length)
    add("error", url, "empty-heading", `${emptyHeadings.length} empty heading tag(s)`);

  if (h1Count === 0 && isHtmlPage(url)) add("warn", url, "h1", "no h1");
  if (h1Count > 1) add("warn", url, "h1", `multiple h1 (${h1Count})`);

  const assets = collectAssetUrls(text, url);
  for (const assetUrl of assets) {
    if (!isInternal(assetUrl) && !assetUrl.startsWith(CANONICAL_HOST)) continue;
    const path = new URL(assetUrl).pathname;
    const interesting =
      /\.(mp3|wav|png|webp|jpg|jpeg|gif|svg|ico|woff2?|ttf|css)(\?|$)/i.test(path) ||
      path.startsWith("/assets/") ||
      path.includes("/audio/");
    if (!interesting) continue;
    const check = await checkAsset(assetUrl);
    if (!check.ok) add("error", url, "asset-404", `${assetUrl} → HTTP ${check.status}`);
  }

  const links = collectInternalLinks(text, url);
  for (const link of links) {
    const check = await headOrGet(link);
    if (!check.ok && check.status !== 0)
      add("error", url, "internal-link", `${link} → HTTP ${check.status}`);
  }

  return { title, description, html: text };
}

async function loadSitemapUrls() {
  const { res, text } = await fetchText(`${base}/sitemap.xml`);
  if (!res.ok) throw new Error(`sitemap.xml HTTP ${res.status}`);
  const locs = parseSitemapLocs(text);
  const extra = EXTRA_PATHS.map((p) => `${base}${p}`);
  const all = [...new Set([...locs, ...extra])];
  return all.sort();
}

async function runBrowserConsoleAudit() {
  let chromium;
  try {
    ({ chromium } = await import("@playwright/test"));
  } catch {
    console.warn("Skipping browser console audit (@playwright/test not installed).");
    return;
  }
  const paths = ["/", "/c/risers", "/e/ui-success-chime", "/blog/how-to-write-a-sound-effect-prompt"];
  const viewports = [
    { name: "desktop", width: 1280, height: 720 },
    { name: "mobile", width: 390, height: 844 },
  ];
  const browser = await chromium.launch({ headless: true });
  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();
    const errors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push({ path: page.url(), text: msg.text() });
    });
    page.on("pageerror", (err) => errors.push({ path: page.url(), text: err.message }));
    for (const path of paths) {
      const url = `${base}${path}`;
      errors.length = 0;
      await page.goto(url, { waitUntil: "networkidle", timeout: 60_000 });
      await page.waitForTimeout(500);
      if (errors.length) {
        for (const e of errors) {
          add("error", url, `console-${vp.name}`, e.text);
        }
      } else {
        add("info", url, `console-${vp.name}`, "no console errors");
      }
    }
    await context.close();
  }
  await browser.close();
}

async function main() {
  const withBrowser = process.argv.includes("--browser");
  console.log(`Crawl audit: ${base}\n`);
  const urls = await loadSitemapUrls();
  console.log(`URLs to check: ${urls.length}\n`);

  const titles = new Map();
  let done = 0;
  const concurrency = 6;

  async function worker(batch) {
    for (const url of batch) {
      const meta = await auditPage(url);
      if (meta.title) {
        if (titles.has(meta.title)) {
          add("error", url, "duplicate-title", `"${meta.title}" also on ${titles.get(meta.title)}`);
        } else {
          titles.set(meta.title, url);
        }
      }
      done++;
      if (done % 20 === 0) process.stderr.write(`  ${done}/${urls.length}\n`);
    }
  }

  const batches = [];
  for (let i = 0; i < urls.length; i += concurrency) {
    batches.push(urls.slice(i, i + concurrency));
  }
  for (const batch of batches) {
    await Promise.all(batch.map((u) => worker([u])));
  }

  const errors = findings.filter((f) => f.severity === "error");
  const warns = findings.filter((f) => f.severity === "warn");

  console.log("\n--- Summary ---");
  console.log(`Pages: ${urls.length}`);
  console.log(`Errors: ${errors.length}`);
  console.log(`Warnings: ${warns.length}`);

  if (findings.length) {
    console.log("\n--- Findings ---");
    for (const f of findings) {
      console.log(`[${f.severity}] ${f.check} @ ${f.url}\n    ${f.detail}`);
    }
  }

  if (withBrowser) {
    console.log("\n--- Browser console ---");
    await runBrowserConsoleAudit();
  }

  if (process.env.JSON_REPORT) {
    const finalErrors = findings.filter((f) => f.severity === "error");
    console.log(JSON.stringify({ base, urls: urls.length, findings }, null, 2));
    process.exit(finalErrors.length ? 1 : 0);
    return;
  }

  const finalErrors = findings.filter((f) => f.severity === "error");
  process.exit(finalErrors.length ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(2);
});
