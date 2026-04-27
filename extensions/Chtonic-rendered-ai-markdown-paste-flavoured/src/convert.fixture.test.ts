import { expect, test } from "bun:test";
import { htmlToMarkdown } from "./convert";

test("fixture HTML converts to expected Markdown", async () => {
  const html = await Bun.file("fixtures/rendered-sample.html").text();
  const expected = await Bun.file("fixtures/rendered-sample.md").text();

  expect(htmlToMarkdown(html)).toBe(expected);
});
