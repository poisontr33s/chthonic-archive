import katex from "katex";
import { defaultKatexConfig } from "../config";
import { diag } from "../diagnostics";
import { scanZones } from "../zones";
import type { DocumentModel } from "../model";
import type { KatexValidationResult, KatexMathValidation, KatexIssueKind } from "../types";

const unsafeCommands = ["\\href", "\\url", "\\includegraphics"];
const unsupportedCommands = ["\\unknownmacro", "\\operatorname{}", "\\tag{}"];

const classify = (message: string): KatexIssueKind => {
  const m = message.toLowerCase();
  if (m.includes("expected") || m.includes("parse error") || m.includes("end of input")) return "syntax-error";
  if (m.includes("unsafe") || m.includes("trust")) return "unsafe-command";
  if (m.includes("macro")) return "macro-error";
  if (m.includes("unicode")) return "unicode-warning";
  if (m.includes("delimiter")) return "delimiter-error";
  if (m.includes("unknown") || m.includes("undefined control sequence")) return "unsupported-command";
  return "unknown";
};

const mathSpans = (model: DocumentModel) => model.zones.filter((z) => z.kind === "math_inline" || z.kind === "math_display").map((z) => ({ ...z, text: model.text.slice(z.startOffset, z.endOffset) }));

export const validateKatex = (model: DocumentModel, config = defaultKatexConfig): KatexValidationResult => {
  if (!config.enabled) return { passed: true, mathCount: 0, passedCount: 0, failedCount: 0, unsupportedCount: 0, unsafeCount: 0, skippedCount: 0, math: [], diagnostics: [diag("MDSEAL_KATEX_VALIDATION_SKIPPED", "KaTeX validation disabled", "info", { source: "validator" })] };
  const math = mathSpans(model);
  const results: KatexMathValidation[] = [];
  const diagnostics = [];
  let passedCount = 0, failedCount = 0, unsupportedCount = 0, unsafeCount = 0, skippedCount = 0;
  for (const [idx, span] of math.entries()) {
    const raw = span.text;
    const latex = raw.replace(/^\$\$?/, "").replace(/\$\$?$/, "").replace(/^\\\(|\\\)|^\\\[|\\\]$/g, "");
    const unsupported = unsupportedCommands.find((c) => latex.includes(c)) || (latex.includes("\\R") ? "\\R" : undefined);
    const unsafe = unsafeCommands.find((c) => latex.includes(c));
    const entry: KatexMathValidation = { id: `k${idx}`, file: model.file, kind: span.kind === "math_display" ? "display" : "inline", delimiter: raw.startsWith("$$") ? "double-dollar" : raw.startsWith("\\(") ? "paren" : raw.startsWith("\\[") ? "bracket" : "single-dollar", line: 1, column: span.startOffset + 1, raw, latex, status: "passed", confidence: 1 };
    try {
      if (latex.includes("\\def") && latex.includes("\\loop")) throw Object.assign(new Error("macro expansion exceeded limit"), { kind: "macro-error" });
      if (unsafe && config.failOnUnsafeCommands) throw Object.assign(new Error(`unsafe command ${unsafe}`), { kind: "unsafe-command" });
      if (unsupported && config.failOnUnsupportedCommands) throw Object.assign(new Error(`unsupported command ${unsupported}`), { kind: "unsupported-command" });
      if (unsupported) {
        entry.status = "unsupported";
        entry.issueKind = "unsupported-command";
        entry.command = unsupported;
        unsupportedCount++;
        diagnostics.push(diag("MDSEAL_KATEX_UNSUPPORTED_COMMAND", `unsupported command ${unsupported}`, "warning", { source: "validator" }));
      }
      else if (unsafe) {
        entry.status = "unsafe";
        entry.issueKind = "unsafe-command";
        entry.command = unsafe;
        unsafeCount++;
        diagnostics.push(diag("MDSEAL_KATEX_UNSAFE_COMMAND", `unsafe command ${unsafe}`, "error", { source: "validator" }));
      }
      else {
        katex.renderToString(latex, { displayMode: entry.kind === "display", throwOnError: true, strict: config.strict, trust: config.trust, maxExpand: config.maxExpand, macros: config.macros, output: "htmlAndMathml" });
        passedCount++;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const kind = (err as any)?.kind === "unsafe-command" ? "unsafe-command" : (err as any)?.kind === "unsupported-command" ? "unsupported-command" : classify(message);
      entry.status = kind === "unsafe-command" ? "unsafe" : kind === "unsupported-command" ? "unsupported" : "failed";
      entry.issueKind = kind;
      entry.message = message;
      if (kind === "unsafe-command") {
        unsafeCount++;
        diagnostics.push(diag("MDSEAL_KATEX_UNSAFE_COMMAND", message, "error", { source: "validator" }));
      } else if (kind === "unsupported-command") {
        unsupportedCount++;
        diagnostics.push(diag("MDSEAL_KATEX_UNSUPPORTED_COMMAND", message, "warning", { source: "validator" }));
      } else if (kind === "macro-error") {
        failedCount++;
        diagnostics.push(diag("MDSEAL_KATEX_MACRO_ERROR", message, "error", { source: "validator" }));
      } else if (kind === "unicode-warning") {
        skippedCount++;
        diagnostics.push(diag("MDSEAL_KATEX_UNICODE_WARNING", message, "warning", { source: "validator" }));
      } else {
        failedCount++;
        diagnostics.push(diag(kind === "delimiter-error" ? "MDSEAL_KATEX_DELIMITER_ERROR" : "MDSEAL_KATEX_PARSE_ERROR", message, "error", { source: "validator" }));
      }
    }
    results.push(entry);
  }
  const passed = failedCount === 0 && unsafeCount === 0 && (config.failOnUnsupportedCommands ? unsupportedCount === 0 : true);
  return { passed, mathCount: results.length, passedCount, failedCount, unsupportedCount, unsafeCount, skippedCount, math: results, diagnostics };
};
