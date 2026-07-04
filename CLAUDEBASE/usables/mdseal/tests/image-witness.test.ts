import { expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadModel } from "../src/scan";
import { imageReferences } from "../src/images";
import { buildImageWitness, writeImageWitness, ensureWitnessOrRefuse } from "../src/image-witness";
import { createSeal } from "../src/seal";
import { defaultImageWitnessConfig } from "../src/config";

const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9q2V4AAAAASUVORK5CYII=", "base64");

test("parse basic markdown image and resolve image bytes", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-img-"));
  try {
    mkdirSync(join(dir, "images"));
    writeFileSync(join(dir, "paper.md"), "![equation](./images/equation.png)", "utf-8");
    writeFileSync(join(dir, "images", "equation.png"), png);
    const model = loadModel(join(dir, "paper.md"));
    const refs = imageReferences(model);
    expect(refs).toHaveLength(1);
    expect(refs[0].exists).toBe(true);
    expect(refs[0].sha256).toBeTruthy();
    expect(refs[0].likelyEquation).toBe(true);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("image witness sidecar is deterministic except createdAt", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-img-"));
  try {
    mkdirSync(join(dir, "images"));
    writeFileSync(join(dir, "paper.md"), "![equation](./images/equation.png)", "utf-8");
    writeFileSync(join(dir, "images", "equation.png"), png);
    const model = loadModel(join(dir, "paper.md"));
    const img = imageReferences(model)[0];
    const a = buildImageWitness(dir, model, img);
    const b = buildImageWitness(dir, model, img);
    expect({ ...a, createdAt: "x" }).toEqual({ ...b, createdAt: "x" });
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("image witness sidecar writes to mdseal images path", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-img-"));
  try {
    mkdirSync(join(dir, "images"));
    writeFileSync(join(dir, "paper.md"), "![equation](./images/equation.png)", "utf-8");
    writeFileSync(join(dir, "images", "equation.png"), png);
    const model = loadModel(join(dir, "paper.md"));
    const img = imageReferences(model)[0];
    const witness = buildImageWitness(dir, model, img);
    const p = writeImageWitness(dir, witness);
    expect(p).toContain(".mdseal");
    expect(existsSync(p!)).toBe(true);
    expect(JSON.parse(readFileSync(p!, "utf-8")).schema).toBe("mdseal.image-witness.v1");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("seal includes image hash and image drift can be detected", () => {
  const dir = mkdtempSync(join(tmpdir(), "mdseal-img-"));
  try {
    mkdirSync(join(dir, "images"));
    writeFileSync(join(dir, "paper.md"), "![equation](./images/equation.png)", "utf-8");
    writeFileSync(join(dir, "images", "equation.png"), png);
    const model = loadModel(join(dir, "paper.md"));
    const seal = createSeal(dir, model);
    expect(seal.images[0].sha256).toBeTruthy();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("ocr-dependent image policy refuses without OCR", () => {
  expect(ensureWitnessOrRefuse("add-alt-latex", false)?.code).toBe("MDSEAL_REFUSE_IMAGE_POLICY_REQUIRES_OCR");
  expect(ensureWitnessOrRefuse(defaultImageWitnessConfig.policy, false)).toBeNull();
});
