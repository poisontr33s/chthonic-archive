import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";

test("image references are found", () => {
  const file = fileURLToPath(new URL("./fixtures/broken/image.md", import.meta.url));
  expect(loadModel(file).images.length).toBe(1);
});
