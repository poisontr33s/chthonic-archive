import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";
import { applyRepairs } from "../src/repairs";

test("repairs unicode minus", () => {
  const file = fileURLToPath(new URL("./fixtures/broken/unicode-minus.md", import.meta.url));
  const model = loadModel(file);
  const repaired = applyRepairs(model);
  expect(repaired.text.includes("-")).toBe(true);
});
