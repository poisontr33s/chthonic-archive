import type { DocumentModel, SealManifest, ZoneSpan } from "./model";
import type { Diagnostic, ValidationGateResult } from "./types";
import { refuse } from "./refusals";
import { compareParsers, parserComparisonDiagnostics } from "./validators/parser-compare";
import { validateKatex } from "./validators/katex";

const zoneText = (text: string, z: ZoneSpan) => text.slice(z.startOffset, z.endOffset);
const count = (text: string, re: RegExp) => (text.match(re) ?? []).length;

export const validateCandidate = (before: DocumentModel, afterText: string): ValidationGateResult => {
  const gates: ValidationGateResult["gates"] = [];
  const parserComparison = compareParsers(afterText);
  const katexBefore = validateKatex(before);
  const katexAfter = validateKatex({ ...before, text: afterText });
  const codeBefore = count(before.text, /```/g);
  const codeAfter = count(afterText, /```/g);
  gates.push({ name: "markdown-parse", status: afterText.length > 0 ? "passed" : "failed", diagnostics: [] });
  gates.push({
    name: "math-balance",
    status: count(afterText, /\$/g) % 2 === 0 || count(before.text, /\$/g) % 2 === count(afterText, /\$/g) % 2 ? "passed" : "failed",
    diagnostics: count(afterText, /\$/g) % 2 === 0 ? [] : [refuse("MDSEAL_REFUSE_MATH_BALANCE_REGRESSION", "math delimiters did not balance", "validator")],
  });
  gates.push({
    name: "code-fence",
    status: codeAfter >= codeBefore ? "passed" : "failed",
    diagnostics: codeAfter >= codeBefore ? [] : [refuse("MDSEAL_REFUSE_CODE_FENCE_REGRESSION", "code fence count regressed", "validator")],
  });
  gates.push({
    name: "table-shape",
    status: afterText.includes("|") === before.text.includes("|") ? "passed" : "skipped",
    diagnostics: afterText.includes("|") === before.text.includes("|") ? [] : [refuse("MDSEAL_REFUSE_TABLE_SHAPE_REGRESSION", "table shape regressed", "validator")],
  });
  gates.push({
    name: "protected-zones",
    status: before.zones.every((z) => {
      if (["frontmatter", "code_fence", "inline_code", "html_block", "html_inline", "link_destination", "image_destination"].includes(z.kind)) return zoneText(before.text, z) === zoneText(afterText, z);
      return true;
    }) ? "passed" : "failed",
    diagnostics: before.zones.some((z) => ["frontmatter", "code_fence", "inline_code", "html_block", "html_inline", "link_destination", "image_destination"].includes(z.kind) && zoneText(before.text, z) !== zoneText(afterText, z))
      ? [refuse("MDSEAL_REFUSE_PROTECTED_ZONE_TOUCH", "protected zone changed", "validator")]
      : [],
  });
  gates.push({
    name: "parser-comparison",
    status: parserComparison.passed ? "passed" : "failed",
    diagnostics: parserComparison.passed ? [] : [refuse("MDSEAL_REFUSE_PARSER_COMPARISON_REGRESSION", "parser comparison regressed", "validator"), ...parserComparisonDiagnostics(parserComparison)],
  });
  gates.push({
    name: "katex",
    status: katexAfter.passed ? "passed" : "failed",
    diagnostics: katexAfter.passed ? [] : [refuse("MDSEAL_REFUSE_KATEX_REGRESSION", "KaTeX validation regressed", "validator"), ...katexAfter.diagnostics],
  });
  const passed = gates.every((g) => g.status !== "failed");
  return { passed, gates, parserComparison, katex: katexAfter };
};

export const sealContextMismatch = (): Diagnostic => refuse("MDSEAL_REFUSE_SEAL_CONTEXT_MISMATCH", "seal context does not match", "seal");
export const sealHashOnlyRefuse = (): Diagnostic => refuse("MDSEAL_REFUSE_SEAL_HASH_ONLY_RESTORE", "hash-only seal cannot restore raw math", "seal");
export const existingSealWithoutForce = (): Diagnostic => refuse("MDSEAL_REFUSE_EXISTING_SEAL_WITHOUT_FORCE", "existing seal present; pass --force to overwrite", "seal");
