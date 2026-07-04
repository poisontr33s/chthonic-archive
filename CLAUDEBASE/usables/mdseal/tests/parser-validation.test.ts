import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";
import { validateCandidate } from "../src/validation";
import { compareParsers } from "../src/validators/parser-compare";

test("validation includes parser comparison result", () => {
  const file = fileURLToPath(new URL("./fixtures/cases/table-pipe-inside-math/broken.md", import.meta.url));
  const model = loadModel(file);
  const validation = validateCandidate(model, model.text);
  expect(validation.parserComparison).toBeDefined();
  expect(validation.parserComparison?.parsers.length).toBe(3);
});

test("parser comparison gate can refuse regressions", () => {
  const regression = compareParsers("x", {
    "remark-gfm-math": () => ({ summary: { headings: 1, codeFences: 1, tables: 1, mathInline: 1, mathDisplay: 0, htmlBlocks: 0, links: 0, images: 0, listItems: 0, blockquotes: 0 }, diagnostics: [], status: "passed" as const }),
    "micromark-gfm-math": () => ({ summary: { headings: 1, codeFences: 0, tables: 0, mathInline: 0, mathDisplay: 0, htmlBlocks: 0, links: 0, images: 0, listItems: 0, blockquotes: 0 }, diagnostics: [], status: "passed" as const }),
    markdownlint: () => ({ summary: { headings: 1, codeFences: 0, tables: 1, mathInline: 1, mathDisplay: 0, htmlBlocks: 0, links: 0, images: 0, listItems: 0, blockquotes: 0 }, diagnostics: [], status: "passed" as const }),
  } as any);
  expect(regression.disagreements.length).toBeGreaterThan(0);
});

