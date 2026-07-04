import { expect, test } from "bun:test";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

test("fixtures exist", () => {
  expect(existsSync(fileURLToPath(new URL("./fixtures/sealed", import.meta.url)))).toBe(true);
});
