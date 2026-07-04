import type { DocumentModel } from "./model";
import type { Diagnostic, Patch, RepairRule, ZoneKind } from "./types";
import { diag } from "./diagnostics";
import { refuse } from "./refusals";

type Match = { start: number; end: number; before: string; after: string; zone?: ZoneKind };

const replacementPatch = (file: string, code: string, description: string, match: Match, confidence = 0.95, protectedZoneTouches: Patch["protectedZoneTouches"] = []): Patch => ({
  file,
  code,
  description,
  confidence,
  replacements: [{ startOffset: match.start, endOffset: match.end, before: match.before, after: match.after }],
  protectedZoneTouches,
});

const inZone = (model: DocumentModel, start: number, kinds: ZoneKind[]) => model.zones.some((z) => z.startOffset <= start && start < z.endOffset && kinds.includes(z.kind));
const zoneAt = (model: DocumentModel, start: number) => model.zones.find((z) => z.startOffset <= start && start < z.endOffset)?.kind;

const makeRule = (rule: RepairRule) => rule;
const patchText = (text: string, patch: Patch) => {
  const r = patch.replacements[0];
  return text.slice(0, r.startOffset) + r.after + text.slice(r.endOffset);
};

const safe = (model: DocumentModel, start: number) => !inZone(model, start, ["code_fence", "inline_code", "frontmatter", "link_destination", "image_destination", "html_block", "html_inline"]);
const mathSafe = (model: DocumentModel, start: number) => inZone(model, start, ["math_inline", "math_display"]) || model.text.slice(Math.max(0, start - 2), start + 2).includes("$$") || model.text.slice(Math.max(0, start - 1), start + 1).includes("$");

const collect = (text: string, re: RegExp) => {
  const out: Match[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) out.push({ start: m.index, end: m.index + m[0].length, before: m[0], after: m[0] });
  return out;
};

const singleLineMathFixes = (model: DocumentModel) => {
  const fixes: Match[] = [];
  for (const m of collect(model.text, /\[([^\]\n]+)\]/g)) if (safe(model, m.start)) fixes.push({ ...m, after: `\\[${m.before.slice(1, -1)}\\]` });
  for (const m of collect(model.text, /\(([^\)\n]+)\)/g)) if (safe(model, m.start) && /[=^+\-*/\\]/.test(m.before)) fixes.push({ ...m, after: `\\(${m.before.slice(1, -1)}\\)` });
  return fixes;
};

const inlineDollarFixes = (model: DocumentModel) => {
  const fixes: Match[] = [];
  const text = model.text;
  const dollarPositions = [...text.matchAll(/\$/g)].map((m) => m.index ?? 0);
  if (dollarPositions.length % 2 === 1) {
    const start = dollarPositions[dollarPositions.length - 1];
    if (safe(model, start)) fixes.push({ start, end: start, before: "", after: "$" });
  }
  return fixes;
};

const backslashFixes = (model: DocumentModel) => {
  const fixes: Match[] = [];
  for (const m of collect(model.text, /(?<!\\)\b(frac|sqrt|alpha|beta|gamma)\s*(\{?)/g)) {
    if (!mathSafe(model, m.start)) continue;
    const cmd = m.before.match(/frac|sqrt|alpha|beta|gamma/)?.[0] ?? "";
    if (!cmd) continue;
    fixes.push({ ...m, after: `\\${m.before}` });
  }
  return fixes;
};

const entityFixes = (model: DocumentModel) => {
  const fixes: Match[] = [];
  for (const m of collect(model.text, /&amp;|&nbsp;/g)) if (mathSafe(model, m.start)) fixes.push({ ...m, after: m.before === "&amp;" ? "&" : " ", end: m.end });
  return fixes;
};

const unicodeFixes = (model: DocumentModel) => {
  const fixes: Match[] = [];
  for (const m of collect(model.text, /[\u00ad\u00a0\u200b\u200c\u200d\u2060\u202e\u202f\u2212“”]/g)) {
    if (!mathSafe(model, m.start)) continue;
    const map: Record<string, string> = { "\u2212": "-", "\u00ad": "", "\u00a0": " ", "\u202f": " ", "\u200b": "", "\u200c": "", "\u200d": "", "\u2060": "", "\u202e": "", "“": '"', "”": '"' };
    fixes.push({ ...m, after: map[m.before] ?? m.before });
  }
  return fixes;
};

const pipeFixes = (model: DocumentModel) => {
  const fixes: Match[] = [];
  for (const z of model.zones.filter((z) => z.kind === "markdown_table")) {
    const text = model.text.slice(z.startOffset, z.endOffset);
    const codeSpans = [...text.matchAll(/`[^`]*`/g)].map((m) => [m.index ?? 0, (m.index ?? 0) + m[0].length] as const);
    let inMath = false;
    for (let i = 0; i < text.length; i++) {
      if (text[i] === "$" && text[i + 1] !== "$") inMath = !inMath;
      if (text[i] === "|" && inMath && !codeSpans.some(([s, e]) => i >= s && i < e)) {
        fixes.push({ start: z.startOffset + i, end: z.startOffset + i + 1, before: "|", after: "\\|" });
      }
    }
  }
  return fixes;
};

const listBlockquoteFixes = (model: DocumentModel) => {
  const fixes: Match[] = [];
  for (const z of model.zones.filter((z) => z.kind === "list_item" || z.kind === "blockquote")) {
    const text = model.text.slice(z.startOffset, z.endOffset);
    if (/\$\$[\s\S]*?\$\$/.test(text) || /\[[\s\S]*\]/.test(text) || /\([\s\S]*\)/.test(text)) continue;
  }
  return fixes;
};

const fenceFixes = (model: DocumentModel) => {
  const fixes: Match[] = [];
  const fenceCount = (model.text.match(/```/g) ?? []).length;
  if (fenceCount % 2 === 1) fixes.push({ start: model.text.length, end: model.text.length, before: "", after: "\n```" });
  return fixes;
};

const imageFixes = (_model: DocumentModel) => [];

export const repairRules: RepairRule[] = [
  makeRule({
    code: "MDSEAL_MATH_BRACKET_DELIMITER_DEESCAPED",
    description: "restore escaped bracket math delimiters",
    appliesTo: ["plain_text", "math_inline", "math_display"],
    detect: (m) => singleLineMathFixes(m).filter((f) => f.before.startsWith("[")),
    fix: (m, d) => {
      const start = d.startOffset ?? 0;
      const raw = m.text.slice(start, start + 32);
      const body = raw.match(/^\[([^\]\n]+)\]/)?.[1];
      return body ? replacementPatch(m.file, d.code, d.message, { start, end: start + body.length + 2, before: `[${body}]`, after: `\\[${body}\\]` }, 0.98) : null;
    },
  }),
  makeRule({
    code: "MDSEAL_MATH_PAREN_DELIMITER_DEESCAPED",
    description: "restore escaped paren math delimiters",
    appliesTo: ["plain_text", "math_inline", "math_display"],
    detect: (m) => singleLineMathFixes(m).filter((f) => f.before.startsWith("(")),
    fix: (m, d) => {
      const start = d.startOffset ?? 0;
      const raw = m.text.slice(start, start + 48);
      const body = raw.match(/^\(([^\)\n]+)\)/)?.[1];
      return body ? replacementPatch(m.file, d.code, d.message, { start, end: start + body.length + 2, before: `(${body})`, after: `\\(${body}\\)` }, 0.98) : null;
    },
  }),
  makeRule({
    code: "MDSEAL_MATH_UNBALANCED_INLINE_DOLLAR",
    description: "close unbalanced inline dollar math",
    appliesTo: ["plain_text", "math_inline"],
    detect: (m) => inlineDollarFixes(m).map((f) => diag("MDSEAL_MATH_UNBALANCED_INLINE_DOLLAR", "unbalanced dollar math", "warning", { startOffset: f.start, confidence: 0.6, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => {
      if ((d.confidence ?? 0) < 0.75) return null;
      const start = d.startOffset ?? m.text.length;
      return replacementPatch(m.file, d.code, d.message, { start, end: start, before: "", after: "$" }, 0.6);
    },
  }),
  makeRule({
    code: "MDSEAL_TRAILING_ESCAPE_BEFORE_DELIMITER",
    description: "remove trailing escape before delimiter",
    appliesTo: ["plain_text", "math_inline", "math_display"],
    detect: (m) => collect(m.text, /\\\$/g).filter((f) => mathSafe(m, f.start)).map((f) => diag("MDSEAL_TRAILING_ESCAPE_BEFORE_DELIMITER", "trailing escape before delimiter", "warning", { startOffset: f.start, confidence: 0.9, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => {
      const start = d.startOffset ?? 0;
      return replacementPatch(m.file, d.code, d.message, { start, end: start + 1, before: "\\", after: "" }, 0.95);
    },
  }),
  makeRule({
    code: "MDSEAL_MATH_BACKSLASH_COLLAPSED",
    description: "restore missing math backslashes",
    appliesTo: ["math_inline", "math_display"],
    detect: (m) => backslashFixes(m).map((f) => diag("MDSEAL_MATH_BACKSLASH_COLLAPSED", "collapsed backslash in math", "warning", { startOffset: f.start, confidence: 0.9, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => {
      const start = d.startOffset ?? 0;
      const before = m.text.slice(start, start + 6).match(/frac|sqrt|alpha|beta|gamma/)?.[0] ?? "";
      return before ? replacementPatch(m.file, d.code, d.message, { start, end: start + before.length, before, after: `\\${before}` }, 0.9) : null;
    },
  }),
  makeRule({
    code: "MDSEAL_MATH_HTML_ENTITY_IN_FORMULA",
    description: "decode HTML entities in math",
    appliesTo: ["math_inline", "math_display"],
    detect: (m) => entityFixes(m).map((f) => diag("MDSEAL_MATH_HTML_ENTITY_IN_FORMULA", "HTML entity in formula", "warning", { startOffset: f.start, confidence: 0.95, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => {
      const start = d.startOffset ?? 0;
      const before = m.text.slice(start, start + 5);
      return replacementPatch(m.file, d.code, d.message, { start, end: start + before.length, before, after: before === "&amp;" ? "&" : " " }, 0.95);
    },
  }),
  makeRule({
    code: "MDSEAL_SOFT_HYPHEN_IN_MATH",
    description: "remove soft hyphen in math",
    appliesTo: ["math_inline", "math_display"],
    detect: (m) => collect(m.text, /\u00ad/g).filter((f) => mathSafe(m, f.start)).map((f) => diag("MDSEAL_SOFT_HYPHEN_IN_MATH", "soft hyphen in math", "info", { startOffset: f.start, confidence: 1, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => replacementPatch(m.file, d.code, d.message, { start: d.startOffset ?? 0, end: (d.startOffset ?? 0) + 1, before: "\u00ad", after: "" }, 1),
  }),
  makeRule({
    code: "MDSEAL_NBSP_IN_MATH",
    description: "normalize nbsp in math",
    appliesTo: ["math_inline", "math_display"],
    detect: (m) => collect(m.text, /\u00a0/g).filter((f) => mathSafe(m, f.start)).map((f) => diag("MDSEAL_NBSP_IN_MATH", "non-breaking space in math", "info", { startOffset: f.start, confidence: 1, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => replacementPatch(m.file, d.code, d.message, { start: d.startOffset ?? 0, end: (d.startOffset ?? 0) + 1, before: "\u00a0", after: " " }, 1),
  }),
  makeRule({
    code: "MDSEAL_UNICODE_MINUS_IN_MATH",
    description: "normalize unicode minus in math",
    appliesTo: ["math_inline", "math_display"],
    detect: (m) => collect(m.text, /\u2212/g).filter((f) => mathSafe(m, f.start)).map((f) => diag("MDSEAL_UNICODE_MINUS_IN_MATH", "unicode minus in math", "info", { startOffset: f.start, confidence: 1, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => replacementPatch(m.file, d.code, d.message, { start: d.startOffset ?? 0, end: (d.startOffset ?? 0) + 1, before: "−", after: "-" }, 1),
  }),
  makeRule({
    code: "MDSEAL_SMART_QUOTES_IN_MATH",
    description: "normalize smart quotes in math",
    appliesTo: ["math_inline", "math_display"],
    detect: (m) => collect(m.text, /[“”]/g).filter((f) => mathSafe(m, f.start)).map((f) => diag("MDSEAL_SMART_QUOTES_IN_MATH", "smart quote in math", "info", { startOffset: f.start, confidence: 1, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => replacementPatch(m.file, d.code, d.message, { start: d.startOffset ?? 0, end: (d.startOffset ?? 0) + 1, before: m.text[d.startOffset ?? 0] ?? "", after: '"' }, 1),
  }),
  makeRule({
    code: "MDSEAL_MATH_PIPE_IN_TABLE_CELL",
    description: "escape math pipes in table cells",
    appliesTo: ["markdown_table"],
    detect: (m) => pipeFixes(m).map((f) => diag("MDSEAL_MATH_PIPE_IN_TABLE_CELL", "pipe in math table cell", "warning", { startOffset: f.start, confidence: 0.9, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => replacementPatch(m.file, d.code, d.message, { start: d.startOffset ?? 0, end: (d.startOffset ?? 0) + 1, before: "|", after: "\\|" }, 0.9),
  }),
  makeRule({
    code: "MDSEAL_FENCE_UNCLOSED",
    description: "close unclosed fence",
    appliesTo: ["code_fence"],
    detect: (m) => fenceFixes(m).map((f) => diag("MDSEAL_FENCE_UNCLOSED", "code fence count is odd", "error", { confidence: 1, suggestedFix: true, source: "deterministic-rule" })),
    fix: (m, d) => replacementPatch(m.file, d.code, d.message, { start: m.text.length, end: m.text.length, before: "", after: "\n```" }, 0.95),
  }),
  makeRule({
    code: "MDSEAL_FENCE_COLLISION",
    description: "detect fence collision",
    appliesTo: ["code_fence"],
    detect: (m) => (m.text.includes("````") ? [diag("MDSEAL_FENCE_COLLISION", "fence collision", "warning", { confidence: 1, source: "deterministic-rule" })] : []),
    fix: (_m, _d) => null,
  }),
  makeRule({
    code: "MDSEAL_LIST_DISPLAY_MATH_INDENT",
    description: "preserve list display math indentation",
    appliesTo: ["list_item", "math_display"],
    detect: (_m) => [],
    fix: () => null,
  }),
  makeRule({
    code: "MDSEAL_MATH_BLANK_LINE_IN_DISPLAY_BLOCK",
    description: "compress blank lines in display math",
    appliesTo: ["math_display"],
    detect: (m) => (/\$\$[\s\S]*?\n\s*\n[\s\S]*?\$\$/m.test(m.text) ? [diag("MDSEAL_MATH_BLANK_LINE_IN_DISPLAY_BLOCK", "blank line in display math", "warning", { confidence: 0.9, source: "deterministic-rule" })] : []),
    fix: (_m, _d) => null,
  }),
  makeRule({
    code: "MDSEAL_IMAGE_EQUATION_WITHOUT_ALT_LATEX",
    description: "report likely equation images without alt latex",
    appliesTo: ["image_alt_text"],
    detect: (m) => m.images.filter((img) => !img.alt && /equation|formula|latex|math|expr|derivation|proof/i.test(img.path)).map((img) => diag("MDSEAL_IMAGE_EQUATION_WITHOUT_ALT_LATEX", "likely equation image lacks alt latex", "info", { startOffset: img.startOffset, endOffset: img.endOffset, source: "validator", suggestedFix: false, confidence: 0.8 })),
    fix: () => null,
  }),
  makeRule({
    code: "MDSEAL_IMAGE_HASH_CHANGED",
    description: "report stale image hashes",
    appliesTo: ["image_destination"],
    detect: (m) => m.images.filter((img) => /equation|formula|latex|math|expr|derivation|proof/i.test(img.path)).map((img) => diag("MDSEAL_IMAGE_HASH_CHANGED", "image hash changed or unknown", "info", { startOffset: img.startOffset, endOffset: img.endOffset, source: "validator", confidence: 0.7 })),
    fix: () => null,
  }),
];

export const applyRepairs = (model: DocumentModel) => {
  let text = model.text;
  const diagnostics: Diagnostic[] = [];
  const patches: Patch[] = [];
  for (const r of repairRules) {
    for (const d of r.detect({ ...model, text })) {
      diagnostics.push(d);
      const patch = r.fix({ ...model, text }, d);
      if (!patch) continue;
      const target = patch.replacements[0];
      if (!target) continue;
      if (!safe(model, target.startOffset) && !r.appliesTo.includes("code_fence")) {
        diagnostics.push(refuse("MDSEAL_REFUSE_PROTECTED_ZONE_TOUCH", "repair would touch a protected zone", "deterministic-rule", { startOffset: target.startOffset, confidence: 1 }));
        continue;
      }
      const next = patchText(text, patch);
      const post = { ...model, text: next };
      const validation = next === text ? { passed: true, gates: [] } : undefined;
      if (validation && next === text) continue;
      text = next;
      patches.push(patch);
    }
  }
  return { text, diagnostics, patches };
};
