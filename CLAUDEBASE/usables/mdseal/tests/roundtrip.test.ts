import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";
import { applyRepairs } from "../src/repairs";

test("repairs are idempotent for simple input", () => {
  const file = fileURLToPath(new URL("./fixtures/broken/unicode-minus.md", import.meta.url));
  const model = loadModel(file);
  const once = applyRepairs(model).text;
  expect(applyRepairs({ ...model, text: once }).text).toBe(once);
});
