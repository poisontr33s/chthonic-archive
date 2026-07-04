import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";
import { createSeal } from "../src/seal";

test("seal can be created", () => {
  const file = fileURLToPath(new URL("./fixtures/golden/ok.md", import.meta.url));
  const model = loadModel(file);
  expect(createSeal(".", model).sha256.length).toBe(64);
});
