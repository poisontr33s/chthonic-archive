import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";
import { createSeal } from "../src/seal";

const file = fileURLToPath(new URL("../examples/sealed-research.md", import.meta.url));

test("seal manifest contains rich math and structural entries", () => {
  const model = loadModel(file);
  const seal = createSeal(".", model);
  expect(seal.schema).toBe("mdseal.v1");
  expect(seal.math.length).toBeGreaterThan(0);
  expect(seal.fences.length).toBeGreaterThanOrEqual(0);
  expect(seal.tables.length).toBeGreaterThanOrEqual(0);
  expect(seal.images.length).toBeGreaterThanOrEqual(0);
  expect(seal.hiddenSymbols.length).toBeGreaterThanOrEqual(0);
});

test("hash-only seals omit raw math", () => {
  const model = loadModel(file);
  const seal = createSeal(".", model, true);
  expect(seal.math.some((m) => m.raw !== undefined)).toBe(false);
});

test("full seals include raw math when available", () => {
  const model = loadModel(file);
  const seal = createSeal(".", model, false);
  expect(seal.math.some((m) => m.raw !== undefined)).toBe(true);
});

test("seal manifest is deterministic except createdAt", () => {
  const model = loadModel(file);
  const a = createSeal(".", model, false);
  const b = createSeal(".", model, false);
  const strip = (x: typeof a) => ({ ...x, createdAt: "x" });
  expect(strip(a)).toEqual(strip(b));
});
