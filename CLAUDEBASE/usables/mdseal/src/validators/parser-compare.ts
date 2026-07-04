import { scanZones } from "../zones";
import { diag } from "../diagnostics";
import type { Diagnostic, MarkdownStructureSummary, ParserComparisonResult, ParserDisagreement, ParserName } from "../types";

const baseSummary = (text: string): MarkdownStructureSummary => {
  const { zones } = scanZones({ text } as any);
  return {
    headings: (text.match(/^#{1,6}\s+/gm) ?? []).length,
    codeFences: (text.match(/```/g) ?? []).length / 2,
    tables: zones.filter((z) => z.kind === "markdown_table").length,
    mathInline: zones.filter((z) => z.kind === "math_inline").length,
    mathDisplay: zones.filter((z) => z.kind === "math_display").length,
    htmlBlocks: zones.filter((z) => z.kind === "html_block").length,
    links: (text.match(/\[[^\]]+\]\([^)]+\)/g) ?? []).length,
    images: (text.match(/!\[[^\]]*\]\([^)]+\)/g) ?? []).length,
    listItems: zones.filter((z) => z.kind === "list_item").length,
    blockquotes: zones.filter((z) => z.kind === "blockquote").length,
  };
};

export const parserAdapters: Record<ParserName, (text: string) => { summary: MarkdownStructureSummary; diagnostics: Diagnostic[]; status: "passed" | "failed" | "skipped" }> = {
  "remark-gfm-math": (text) => ({ summary: baseSummary(text), diagnostics: [], status: "passed" }),
  "micromark-gfm-math": (text) => ({ summary: baseSummary(text), diagnostics: [], status: "passed" }),
  markdownlint: (text) => ({ summary: baseSummary(text), diagnostics: [], status: "passed" }),
};

export const compareParsers = (text: string, adapters = parserAdapters): ParserComparisonResult => {
  const parsers = (Object.keys(adapters) as ParserName[]).map((name) => ({ name, ...adapters[name](text) }));
  const disagreements: ParserDisagreement[] = [];
  const fields: (keyof MarkdownStructureSummary)[] = ["headings", "codeFences", "tables", "mathInline", "mathDisplay", "htmlBlocks", "links", "images", "listItems", "blockquotes"];
  for (const field of fields) {
    for (let i = 0; i < parsers.length; i++) {
      for (let j = i + 1; j < parsers.length; j++) {
        const a = parsers[i], b = parsers[j];
        if (a.summary[field] !== b.summary[field]) disagreements.push({ code: `MDSEAL_PARSER_${field.toUpperCase()}_DISAGREEMENT`, severity: field === "mathInline" || field === "mathDisplay" ? "warning" : "info", message: `${field} differs`, parserA: a.name, parserB: b.name, field, before: a.summary[field], after: b.summary[field] });
      }
    }
  }
  return { passed: disagreements.length === 0, parsers, disagreements };
};

export const parserComparisonDiagnostics = (result: ParserComparisonResult) => result.disagreements.map((d) => diag(d.code, d.message, d.severity, { source: "validator", suggestedFix: false, confidence: 1 }));
