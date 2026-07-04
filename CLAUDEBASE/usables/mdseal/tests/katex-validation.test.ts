import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";
import { validateKatex } from "../src/validators/katex";
import { defaultKatexConfig } from "../src/config";

const fixture = (name: string) => fileURLToPath(new URL(`./fixtures/cases/${name}/broken.md`, import.meta.url));

test("valid inline math passes", () => {
  const model = loadModel(fixture("katex-valid-inline"));
  const result = validateKatex(model);
  expect(result.passed).toBe(true);
  expect(result.passedCount).toBeGreaterThan(0);
});

test("valid display math passes", () => {
  const model = loadModel(fixture("katex-valid-display"));
  const result = validateKatex(model);
  expect(result.passed).toBe(true);
  expect(result.math.length).toBeGreaterThan(0);
});

test("invalid syntax fails", () => {
  const model = { ...loadModel(fixture("katex-invalid-syntax")), text: "$\\frac{a}{$" };
  const result = validateKatex(model);
  expect(result.passed).toBe(false);
  expect(result.failedCount).toBeGreaterThan(0);
});

test("unsupported command is reported", () => {
  const model = loadModel(fixture("katex-unsupported-command"));
  const result = validateKatex(model);
  expect(result.unsupportedCount).toBeGreaterThan(0);
});

test("unsafe command fails by default", () => {
  const model = loadModel(fixture("katex-unsafe-command"));
  const result = validateKatex(model);
  expect(result.passed).toBe(false);
  expect(result.unsafeCount).toBeGreaterThan(0);
});

test("custom macro passes when configured", () => {
  const model = loadModel(fixture("katex-custom-macro"));
  const result = validateKatex(model, { ...defaultKatexConfig, macros: { "\\R": "\\mathbb{R}" } });
  expect(result.passed).toBe(true);
});

test("custom macro fails without config", () => {
  const model = loadModel(fixture("katex-custom-macro"));
  const result = validateKatex(model, { ...defaultKatexConfig, failOnUnsupportedCommands: true });
  expect(result.passed).toBe(false);
});

test("maxExpand prevents runaway macro expansion", () => {
  const model = { ...loadModel(fixture("katex-custom-macro")), text: "$\\def\\loop{\\loop}\\loop$" };
  const result = validateKatex(model, { ...defaultKatexConfig, macros: { "\\loop": "\\loop" }, maxExpand: 2 });
  expect(result.passed).toBe(false);
});
