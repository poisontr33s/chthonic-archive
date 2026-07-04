import { dirname, extname, resolve } from "node:path";
import { existsSync, readFileSync } from "node:fs";
import type { DocumentModel, ImageRef } from "./model";
import type { Diagnostic, HtmlImageReference, HtmlImageSourceCandidate, HtmlImageSrcsetCandidate, MdsealImageReference } from "./types";
import { diag } from "./diagnostics";
import { hash, lineOf, colOf } from "./seal-helpers";
import { defaultImageWitnessConfig } from "./config";

const imageHint = (value: string | null | undefined, hints: string[]) => !!value && hints.some((hint) => value.toLowerCase().includes(hint.toLowerCase()));
const htmlAttr = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))/g;
const commonExt = new Set([".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp", ".tif", ".tiff"]);

const classifyPath = (value: string | null) => {
  const src = value ?? "";
  return {
    isRemote: /^https?:\/\//i.test(src),
    isDataUri: /^data:/i.test(src),
    isRelative: !!src && !/^([a-zA-Z]:[\\/]|\/|https?:\/\/|data:)/i.test(src),
    isAbsolute: /^([a-zA-Z]:[\\/]|\/)/i.test(src),
  };
};

export const resolveImagePath = (file: string, markdownPath: string) => resolve(dirname(file), decodeURIComponent(markdownPath));

export const likelyEquation = (ref: Pick<MdsealImageReference, "markdownPath" | "altText" | "title">, config = defaultImageWitnessConfig): { likelyEquation: boolean; likelyEquationReason: string | null } => {
  if (imageHint(ref.markdownPath, config.equationFilenameHints)) return { likelyEquation: true, likelyEquationReason: "filename hint" };
  if (imageHint(ref.altText, config.equationAltTextHints)) return { likelyEquation: true, likelyEquationReason: "alt-text hint" };
  if (imageHint(ref.title, config.equationAltTextHints)) return { likelyEquation: true, likelyEquationReason: "title hint" };
  return { likelyEquation: false, likelyEquationReason: null };
};

const parseSrcset = (srcset: string | null | undefined): HtmlImageSrcsetCandidate[] => {
  if (!srcset) return [];
  return srcset.split(",").map((part) => part.trim()).filter(Boolean).map((part) => {
    const [url, ...rest] = part.split(/\s+/);
    const cls = classifyPath(url);
    return { url, descriptor: rest.join(" ") || null, ...cls };
  });
};

const parseAttributes = (text: string) => {
  const attrs: Record<string, string> = {};
  let m: RegExpExecArray | null;
  while ((m = htmlAttr.exec(text))) attrs[m[1].toLowerCase()] = m[2] ?? m[3] ?? m[4] ?? "";
  return attrs;
};

const parseHtmlImages = (model: DocumentModel): HtmlImageReference[] => {
  const refs: HtmlImageReference[] = [];
  const re = /<(picture\b[^>]*>[\s\S]*?<\/picture>|img\b[^>]*>|source\b[^>]*>)/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(model.text))) {
    const raw = m[0];
    const attrs = parseAttributes(raw);
    const tag = raw.startsWith("<picture") ? "picture" : raw.startsWith("<source") ? "source" : "img";
    const src = attrs.src ?? null;
    const srcset = parseSrcset(attrs.srcset);
    const cls = classifyPath(src);
    const startOffset = m.index;
    refs.push({
      kind: "html_image",
      tagName: tag as HtmlImageReference["tagName"],
      src,
      alt: attrs.alt,
      title: attrs.title,
      width: attrs.width,
      height: attrs.height,
      srcset,
      sourceTagCandidates: tag === "picture" ? (Array.from(raw.matchAll(/<source\b[^>]*>/gi)).map((sm) => {
        const sourceAttrs = parseAttributes(sm[0]);
        return { tagName: "source", src: sourceAttrs.src ?? null, srcset: parseSrcset(sourceAttrs.srcset), type: sourceAttrs.type ?? null, media: sourceAttrs.media ?? null, rawAttributes: sourceAttrs };
      })) : undefined,
      isRemote: cls.isRemote,
      isDataUri: cls.isDataUri,
      isRelative: cls.isRelative,
      isAbsolute: cls.isAbsolute,
      line: lineOf(model.text, startOffset),
      column: colOf(model.text, startOffset),
      startOffset,
      endOffset: startOffset + raw.length,
      rawAttributes: attrs,
      container: tag === "picture" ? "picture" : "html_inline",
    });
  }
  return refs;
};

const parseMarkdownImages = (model: DocumentModel): ImageRef[] => {
  const refs: ImageRef[] = [];
  const re = /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(model.text))) refs.push({ kind: "markdown_image", alt: m[1], path: m[2], title: m[3] ?? null, startOffset: m.index, endOffset: m.index + m[0].length });
  return refs;
};

export const imageReferences = (model: DocumentModel): MdsealImageReference[] => {
  const refs: MdsealImageReference[] = [];
  for (const img of parseMarkdownImages(model)) {
    const resolvedPath = resolveImagePath(model.file, img.path);
    const exists = existsSync(resolvedPath);
    const bytes = exists ? readFileSync(resolvedPath) : null;
    const eq = likelyEquation({ markdownPath: img.path, altText: img.alt, title: img.title });
    refs.push({
      id: `img${refs.length}`,
      file: model.file,
      markdownPath: img.path,
      resolvedPath: exists ? resolvedPath : null,
      exists,
      altText: img.alt,
      title: img.title,
      line: lineOf(model.text, img.startOffset),
      column: colOf(model.text, img.startOffset),
      startOffset: img.startOffset,
      endOffset: img.endOffset,
      sha256: bytes ? hash(bytes) : null,
      sizeBytes: bytes ? bytes.length : null,
      extension: extname(img.path) || null,
      likelyEquation: eq.likelyEquation,
      likelyEquationReason: eq.likelyEquationReason,
    });
  }
  for (const img of parseHtmlImages(model)) {
    const src = img.src ?? "";
    const resolvedPath = src && img.isRelative ? resolveImagePath(model.file, src) : null;
    const exists = !!resolvedPath && existsSync(resolvedPath);
    const bytes = exists && resolvedPath ? readFileSync(resolvedPath) : null;
    const eq = likelyEquation({ markdownPath: src, altText: img.alt ?? "", title: img.title ?? null });
    refs.push({
      id: `img${refs.length}`,
      file: model.file,
      markdownPath: src,
      resolvedPath: resolvedPath && exists ? resolvedPath : null,
      exists,
      altText: img.alt ?? "",
      title: img.title ?? null,
      line: img.line ?? 0,
      column: img.column ?? 0,
      startOffset: img.startOffset ?? 0,
      endOffset: img.endOffset ?? 0,
      sha256: bytes ? hash(bytes) : null,
      sizeBytes: bytes ? bytes.length : null,
      extension: src ? extname(src) || null : null,
      likelyEquation: eq.likelyEquation,
      likelyEquationReason: eq.likelyEquationReason,
    });
  }
  return refs;
};

export const htmlImageReferences = (model: DocumentModel): HtmlImageReference[] => parseHtmlImages(model);

export const imageDiagnostics = (model: DocumentModel): Diagnostic[] => {
  const diags: Diagnostic[] = [];
  for (const img of imageReferences(model)) {
    diags.push(diag("MDSEAL_IMAGE_REFERENCE", `image reference ${img.markdownPath}`, "info", { startOffset: img.startOffset, endOffset: img.endOffset, line: img.line, column: img.column, source: "validator" }));
    if (!img.exists) diags.push(diag("MDSEAL_IMAGE_MISSING_FILE", `missing image file ${img.markdownPath}`, "warning", { startOffset: img.startOffset, endOffset: img.endOffset, line: img.line, column: img.column, suggestedFix: false, source: "validator" }));
    if (img.likelyEquation && !/\\/.test(img.altText)) diags.push(diag("MDSEAL_IMAGE_EQUATION_WITHOUT_ALT_LATEX", `likely equation image without LaTeX alt text ${img.markdownPath}`, "warning", { startOffset: img.startOffset, endOffset: img.endOffset, line: img.line, column: img.column, suggestedFix: false, source: "validator" }));
  }
  return diags;
};
