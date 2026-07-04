import type { DocumentModel, ZoneSpan, ImageRef } from "./model";
import type { ZoneKind } from "./types";

const push = (zones: ZoneSpan[], kind: ZoneKind, startOffset: number, endOffset: number, text: string) => zones.push({ kind, startOffset, endOffset, text });

export const scanZones = (model: Pick<DocumentModel, "text">): { zones: ZoneSpan[]; images: ImageRef[] } => {
  const text = model.text;
  const zones: ZoneSpan[] = [];
  const images: ImageRef[] = [];
  let i = 0;
  const lines = text.split(/\n/);
  let offset = 0;
  let inFence = false;
  let fenceStart = 0;
  let frontmatterDone = false;
  if (text.startsWith("---\n")) {
    const end = text.indexOf("\n---\n", 4);
    if (end >= 0) {
      push(zones, "frontmatter", 0, end + 5, text.slice(0, end + 5));
      offset = end + 5;
      frontmatterDone = true;
    }
  }
  for (const line of lines) {
    const lineStart = offset;
    const lineEnd = offset + line.length;
    if (!frontmatterDone && line.startsWith("```")) {
      inFence = !inFence;
      if (inFence) fenceStart = lineStart;
      else push(zones, "code_fence", fenceStart, lineEnd, text.slice(fenceStart, lineEnd));
      offset += line.length + 1;
      continue;
    }
    if (inFence) {
      offset += line.length + 1;
      continue;
    }
    let m: RegExpExecArray | null;
    const img = /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g;
    while ((m = img.exec(line))) {
      const start = lineStart + m.index;
      const end = start + m[0].length;
      images.push({ alt: m[1], path: m[2], title: m[3] ?? null, startOffset: start, endOffset: end });
      push(zones, "image_alt_text", start, start + m[0].indexOf("]("), m[1]);
      push(zones, "image_destination", start + m[0].indexOf("(") + 1, end - 1, m[2]);
    }
    const inline = /`[^`]*`/g;
    while ((m = inline.exec(line))) push(zones, "inline_code", lineStart + m.index, lineStart + m.index + m[0].length, m[0]);
    const math = /\$\$[^]*?\$\$|\$[^$\n]+?\$/g;
    while ((m = math.exec(line))) push(zones, m[0].startsWith("$$") ? "math_display" : "math_inline", lineStart + m.index, lineStart + m.index + m[0].length, m[0]);
    const loneDollar = line.indexOf("$");
    if (loneDollar >= 0 && !line.match(/\$[^$\n]+?\$/)) push(zones, "unknown", lineStart + loneDollar, lineStart + line.length, line.slice(loneDollar));
    if (/^\s*>\s?/.test(line)) push(zones, "blockquote", lineStart, lineEnd, line);
    if (/^\s*[-*+]\s+/.test(line) || /^\s*\d+\.\s+/.test(line)) push(zones, "list_item", lineStart, lineEnd, line);
    if (line.includes("|") && /\|/.test(line) && !line.startsWith("http")) push(zones, "markdown_table", lineStart, lineEnd, line);
    if (/<[a-zA-Z]/.test(line)) push(zones, line.includes("</") ? "html_block" : "html_inline", lineStart, lineEnd, line);
    i++;
    offset += line.length + 1;
  }
  return { zones, images };
};
