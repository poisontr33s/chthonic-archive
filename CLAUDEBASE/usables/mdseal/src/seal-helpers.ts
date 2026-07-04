import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import type { DocumentModel } from "./model";
import { imageReferences } from "./images";
import type { MdsealManifest, MdsealMathSeal, MdsealZoneSeal, MdsealFenceSeal, MdsealTableSeal, MdsealImageSeal, MdsealHiddenSymbolSeal, SealContextMatch } from "./types";

export const hash = (text: string | Uint8Array) => createHash("sha256").update(text).digest("hex");
export const lineOf = (text: string, offset: number) => text.slice(0, offset).split("\n").length;
export const colOf = (text: string, offset: number) => offset - text.lastIndexOf("\n", offset - 1);
export const lineCount = (text: string) => text.split("\n").length;
export const lineEndingKind = (text: string): MdsealManifest["lineEndings"] => text.includes("\r\n") ? "crlf" : text.includes("\n") ? "lf" : "unknown";
export const preview = (text: string, start: number, end: number) => text.slice(Math.max(0, start - 16), Math.min(text.length, end + 16));
export const relFile = (root: string, file: string) => file.startsWith(root) ? file.slice(root.length + 1).replaceAll("\\", "/") : file.replaceAll("\\", "/");

export const buildManifest = (root: string, model: DocumentModel, hashMode: "full" | "hash-only"): MdsealManifest => {
  const zones: MdsealZoneSeal[] = model.zones.map((z, idx) => ({ id: `z${idx}`, kind: z.kind, startOffset: z.startOffset, endOffset: z.endOffset, startLine: lineOf(model.text, z.startOffset), endLine: lineOf(model.text, z.endOffset), sha256: hash(z.text), preview: preview(model.text, z.startOffset, z.endOffset) }));
  const math = model.zones.filter((z) => z.kind === "math_inline" || z.kind === "math_display").map((z, idx) => {
    const left = model.text.slice(Math.max(0, z.startOffset - 24), z.startOffset);
    const right = model.text.slice(z.endOffset, Math.min(model.text.length, z.endOffset + 24));
    const raw = z.text;
    return { id: `m${idx}`, zoneId: zones.find((zz) => zz.startOffset === z.startOffset && zz.endOffset === z.endOffset)?.id ?? `z${idx}`, kind: z.kind === "math_display" ? "display" : "inline", delimiter: raw.startsWith("$$") ? "double-dollar" : raw.startsWith("\\(") ? "paren" : raw.startsWith("\\[") ? "bracket" : raw.startsWith("`") ? "github-backtick" : raw.startsWith("```") ? "math-fence" : "single-dollar", startOffset: z.startOffset, endOffset: z.endOffset, startLine: lineOf(model.text, z.startOffset), endLine: lineOf(model.text, z.endOffset), sha256: hash(raw), contentSha256: hash(raw.replace(/^\$+\s?|\s?\$+$/g, "").replace(/^\\\(|\\\)|^\\\[|\\\]$/g, "")), raw: hashMode === "full" ? raw : undefined, normalizedLatex: raw.replace(/^\$+\s?|\s?\$+$/g, "").replace(/^\\\(|\\\)|^\\\[|\\\]$/g, ""), leftContextSha256: hash(left), rightContextSha256: hash(right), leftContextPreview: left.slice(-16), rightContextPreview: right.slice(0, 16) } satisfies MdsealMathSeal;
  });
  const fences: MdsealFenceSeal[] = model.zones.filter((z) => z.kind === "code_fence").map((z, idx) => ({ id: `f${idx}`, language: z.text.split("\n")[0].replace(/^```/, "") || null, delimiter: z.text.split("\n")[0], startOffset: z.startOffset, endOffset: z.endOffset, startLine: lineOf(model.text, z.startOffset), endLine: lineOf(model.text, z.endOffset), sha256: hash(z.text), contentSha256: hash(z.text) }));
  const tables: MdsealTableSeal[] = model.zones.filter((z) => z.kind === "markdown_table").map((z, idx) => {
    const rows = z.text.split("\n").filter(Boolean);
    const cols = rows[0]?.split("|").length ?? 0;
    return { id: `t${idx}`, startLine: lineOf(model.text, z.startOffset), endLine: lineOf(model.text, z.endOffset), columnCount: cols, rowCount: rows.length, shapeSha256: hash(`${rows.length}:${cols}`), headerSha256: hash(rows[0] ?? "") };
  });
  const images: MdsealImageSeal[] = imageReferences(model).map((img, idx) => {
    const resolvedPath = /^(https?:|data:)/i.test(img.markdownPath) ? null : resolve(dirname(model.file), img.markdownPath);
    const exists = resolvedPath ? existsSync(resolvedPath) : false;
    const bytes = exists && resolvedPath ? readFileSync(resolvedPath) : null;
    return { id: `i${idx}`, markdownPath: img.markdownPath, resolvedPath: exists && resolvedPath ? resolvedPath.replace(root, "").replaceAll("\\", "/") : null, exists, altText: img.altText, title: img.title, sha256: bytes ? hash(bytes) : null, sizeBytes: bytes ? bytes.length : null, likelyEquation: /equation|formula|latex|math|expr|derivation|proof/i.test(img.markdownPath) || /equation|formula|latex|math|derivation|proof/i.test(img.altText) || /equation|formula|latex|math|derivation|proof/i.test(img.title ?? ""), ocrSidecar: null };
  });
  const hiddenSymbols: MdsealHiddenSymbolSeal[] = [];
  for (let i = 0; i < model.text.length; i++) {
    const ch = model.text[i];
    if (/[\u200b\u200c\u200d\u2060\ufeff\u202e\u00a0\u202f\u00ad\uFFFD]/.test(ch)) hiddenSymbols.push({ codepoint: `U+${ch.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0")}`, name: ch, offset: i, line: lineOf(model.text, i), column: colOf(model.text, i), zoneKind: model.zones.find((z) => z.startOffset <= i && i < z.endOffset)?.kind ?? "plain_text" });
  }
  const headings = model.text.split("\n").map((line, idx) => ({ line: idx + 1, match: line.match(/^(#{1,6})\s+(.*)$/) })).filter((x): x is { line: number; match: RegExpMatchArray } => !!x.match).map((x) => ({ level: x.match[1].length, text: x.match[2], line: x.line, sha256: hash(x.match[2]) }));
  return { schema: "mdseal.v1", toolVersion: "0.1.0", createdAt: new Date().toISOString(), file: relFile(root, model.file), sha256: hash(model.raw), encoding: "utf8", lineEndings: lineEndingKind(model.text), profile: model.dialect.name, hashMode, document: { byteLength: model.raw.length, lineCount: lineCount(model.text), headingIndex: headings }, zones, math, fences, tables, images, hiddenSymbols };
};

export const findSealPath = (root: string, file: string) => resolve(root, ".mdseal", `${relFile(root, file)}.mdseal.json`);

export const matchSealContext = (manifest: MdsealManifest, model: DocumentModel, target: MdsealMathSeal): SealContextMatch => {
  const zone = model.zones.find((z) => z.startOffset <= target.startOffset && target.startOffset <= z.endOffset);
  if (!zone) return { matched: false, confidence: 0, reason: "no matching zone" };
  const sourceZone = manifest.zones.find((z) => z.id === target.zoneId);
  const current = model.text.slice(zone.startOffset, zone.endOffset);
  const currentHash = hash(current);
  if (sourceZone && sourceZone.sha256 === currentHash) return { matched: true, confidence: 1, reason: "exact zone hash match", matchedStartOffset: zone.startOffset, matchedEndOffset: zone.endOffset };
  if (sourceZone && sourceZone.kind === zone.kind) return { matched: true, confidence: 0.9, reason: "zone kind and proximity match", matchedStartOffset: zone.startOffset, matchedEndOffset: zone.endOffset };
  return { matched: false, confidence: 0.2, reason: "context hash mismatch" };
};
