const TRAILING_FAQ_HEADING =
  /^##\s+(FAQ|Frequently asked questions)\s*$/i;

/** Remove a trailing markdown FAQ section when frontmatter `faq` is rendered separately. */
export function stripTrailingFaqSectionFromBody(content: string): string {
  const trimmed = content.trimEnd();
  const lines = trimmed.split("\n");
  let lastH2Index = -1;
  for (let i = 0; i < lines.length; i++) {
    if (/^##\s+/.test(lines[i])) lastH2Index = i;
  }
  if (lastH2Index < 0) return trimmed;
  if (!TRAILING_FAQ_HEADING.test(lines[lastH2Index].trim())) return trimmed;
  return lines.slice(0, lastH2Index).join("\n").trimEnd();
}
