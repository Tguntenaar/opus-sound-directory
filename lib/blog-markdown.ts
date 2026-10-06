import { marked } from "marked";
import { stripTrailingFaqSectionFromBody } from "@/lib/blog-strip-faq";
import { getEntryById, getEntryBySlug } from "@/lib/entries";

export type BlogTocItem = { id: string; text: string };

export type BlogBlock =
  | { type: "html"; html: string }
  | { type: "entry"; entryId: string };

const ENTRY_LINK_RE =
  /^\[([^\]]*)\]\((\/entries\/([^/)]+)|\/e\/([^/)]+))\)\s*$/;
const ENTRY_BARE_RE = /^(\/entries\/([^/\s]+)|\/e\/([^/\s]+))\s*$/;

function slugifyHeading(text: string): string {
  return text
    .toLowerCase()
    .replace(/<[^>]+>/g, "")
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

function resolveEntryId(pathSegment: string, altSlug?: string): string | undefined {
  const byId = getEntryById(pathSegment);
  if (byId) return byId.id;
  const slug = altSlug ?? pathSegment;
  const bySlug = getEntryBySlug(slug);
  return bySlug?.id;
}

function parseEntryLine(line: string): string | undefined {
  const md = line.trim();
  const linkMatch = ENTRY_LINK_RE.exec(md);
  if (linkMatch) {
    const idPart = linkMatch[3] ?? linkMatch[4];
    const alt = linkMatch[4];
    return resolveEntryId(idPart, alt);
  }
  const bare = ENTRY_BARE_RE.exec(md);
  if (bare) {
    const idPart = bare[2] ?? bare[3];
    const alt = bare[3];
    return resolveEntryId(idPart, alt);
  }
  return undefined;
}

function extractH2FromMarkdown(md: string): BlogTocItem[] {
  const items: BlogTocItem[] = [];
  for (const line of md.split("\n")) {
    const m = /^##\s+(.+)$/.exec(line.trim());
    if (!m) continue;
    const text = m[1].replace(/\s+#+\s*$/, "").trim();
    items.push({ id: slugifyHeading(text), text });
  }
  return items;
}

marked.use({
  renderer: {
    heading({ text, depth }) {
      const plain = String(text);
      const id = slugifyHeading(plain);
      const level = depth === 1 ? 2 : depth;
      if (level === 2 || level === 3) {
        return `<h${level} id="${id}"><a class="blog-heading-anchor" href="#${id}">${plain}</a></h${level}>\n`;
      }
      return `<h${level}>${plain}</h${level}>\n`;
    },
  },
});

marked.setOptions({ gfm: true, breaks: false });

export function renderBlogBody(body: string): {
  blocks: BlogBlock[];
  toc: BlogTocItem[];
  showToc: boolean;
} {
  body = stripTrailingFaqSectionFromBody(body);
  const toc = extractH2FromMarkdown(body);
  const showToc = toc.length >= 4;
  const chunks = body.split(/\n\n+/);
  const blocks: BlogBlock[] = [];

  for (const chunk of chunks) {
    const entryId = parseEntryLine(chunk);
    if (entryId) {
      blocks.push({ type: "entry", entryId });
      continue;
    }
    const html = marked.parse(chunk) as string;
    blocks.push({ type: "html", html });
  }

  return { blocks, toc, showToc };
}
