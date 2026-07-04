import { expect, test } from "bun:test";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadModel } from "../src/scan";
import { htmlImageReferences, imageReferences } from "../src/images";

test("simple img tag is discovered", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-htmlimg-"));
  try {
    const file = join(dir, "paper.md");
    writeFileSync(file, '<img src="a.png" alt="Diagram" title="Fig 1" width="640" height="480">', "utf-8");
    const model = loadModel(file);
    const refs = htmlImageReferences(model);
    expect(refs).toHaveLength(1);
    expect(refs[0].src).toBe("a.png");
    expect(refs[0].alt).toBe("Diagram");
    expect(refs[0].width).toBe("640");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("picture source and srcset candidates are discovered", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-htmlimg-"));
  try {
    const file = join(dir, "paper.md");
    writeFileSync(file, '<picture><source srcset="a.png 1x, b.png 2x" media="(min-width: 800px)"><img src="fallback.png" alt="Chart"></picture>', "utf-8");
    const model = loadModel(file);
    const refs = htmlImageReferences(model);
    expect(refs).toHaveLength(1);
    expect(refs[0].sourceTagCandidates?.length).toBe(1);
    expect(refs[0].sourceTagCandidates?.[0].srcset.length).toBe(2);
    expect(refs[0].src).toBe("fallback.png");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("remote and data uri image refs are classified without fetch", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-htmlimg-"));
  try {
    const file = join(dir, "paper.md");
    writeFileSync(file, '<img src="https://example.com/a.png"><img src="data:image/png;base64,AAAA">', "utf-8");
    const model = loadModel(file);
    const refs = htmlImageReferences(model);
    expect(refs[0].isRemote).toBe(true);
    expect(refs[1].isDataUri).toBe(true);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("mixed markdown and html image references coexist", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-htmlimg-"));
  try {
    const file = join(dir, "paper.md");
    writeFileSync(file, '![md](./m.png)\n<img src="./h.png" alt="html">', "utf-8");
    const model = loadModel(file);
    const refs = imageReferences(model);
    expect(refs.length).toBe(2);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("malformed html image does not crash", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-htmlimg-"));
  try {
    const file = join(dir, "paper.md");
    writeFileSync(file, '<img src="unterminated alt="oops">', "utf-8");
    const model = loadModel(file);
    expect(() => htmlImageReferences(model)).not.toThrow();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
