import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";
import { applyRepairs } from "../src/repairs";
import { validateCandidate } from "../src/validation";

const fixture = (name: string) => fileURLToPath(new URL(`./fixtures/cases/${name}/broken.md`, import.meta.url));

test("bracket delimiter repair is deterministic", () => {
  const model = loadModel(fixture("deescaped-display-brackets"));
  const repaired = applyRepairs(model);
  expect(repaired.text).toContain("\\[");
  expect(validateCandidate(model, repaired.text).passed).toBe(true);
  expect(applyRepairs({ ...model, text: repaired.text }).text).toBe(repaired.text);
});

test("backslash macro repair inside math only", () => {
  const model = loadModel(fixture("backslash-collapsed-inside-math"));
  const repaired = applyRepairs(model);
  expect(repaired.text).toContain("\\frac{a}{b}");
  expect(applyRepairs({ ...model, text: repaired.text }).text).toBe(repaired.text);
});

test("prose alpha is not guessed", () => {
  const prose = { ...loadModel(fixture("plain-text")), text: "The alpha version uses frac internally." };
  const repaired = applyRepairs(prose);
  expect(repaired.text).toBe(prose.text);
});

