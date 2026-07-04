import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";

test("scan detects zones", () => {
  const file = fileURLToPath(new URL("./fixtures/broken/math.md", import.meta.url));
  const model = loadModel(file);
  expect(model.zones.length).toBeGreaterThan(0);
});
