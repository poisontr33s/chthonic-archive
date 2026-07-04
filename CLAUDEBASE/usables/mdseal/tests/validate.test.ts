import { expect, test } from "bun:test";
import { fileURLToPath } from "node:url";
import { loadModel } from "../src/scan";
import { markdownDiagnostics } from "../src/validators/markdown";

test("markdown validation returns diagnostics", () => {
  const file = fileURLToPath(new URL("./fixtures/broken/fence.md", import.meta.url));
  const model = loadModel(file);
  expect(markdownDiagnostics(model).length).toBeGreaterThan(0);
});
