import { expect, test } from "bun:test";
import { compareParsers } from "../src/validators/parser-compare";

test("parser comparison produces stable summaries", () => {
  const result = compareParsers("# H\n\n$x$\n\n|a|b|\n|1|2|");
  expect(result.parsers.length).toBe(3);
  expect(result.disagreements.length).toBe(0);
  expect(result.passed).toBe(true);
});

test("parser comparison detects disagreements", () => {
  const adapters = {
    "remark-gfm-math": (_: string) => ({ summary: { headings: 1, codeFences: 0, tables: 1, mathInline: 1, mathDisplay: 0, htmlBlocks: 0, links: 0, images: 0, listItems: 0, blockquotes: 0 }, diagnostics: [], status: "passed" as const }),
    "micromark-gfm-math": (_: string) => ({ summary: { headings: 1, codeFences: 0, tables: 0, mathInline: 0, mathDisplay: 0, htmlBlocks: 0, links: 0, images: 0, listItems: 0, blockquotes: 0 }, diagnostics: [], status: "passed" as const }),
    markdownlint: (_: string) => ({ summary: { headings: 1, codeFences: 0, tables: 1, mathInline: 1, mathDisplay: 0, htmlBlocks: 0, links: 0, images: 0, listItems: 0, blockquotes: 0 }, diagnostics: [], status: "passed" as const }),
  };
  const result = compareParsers("x", adapters as any);
  expect(result.disagreements.length).toBeGreaterThan(0);
  expect(result.passed).toBe(false);
});

