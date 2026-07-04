import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import type { DocumentModel } from "./model";
import type { MdsealImageWitness, MdsealImageReference, ImageWitnessPolicy, Diagnostic } from "./types";
import { defaultImageWitnessConfig } from "./config";
import { hash, relFile } from "./seal-helpers";
import { refuse } from "./refusals";
import { diag } from "./diagnostics";

export const witnessPathFor = (root: string, imageSha256: string) => resolve(root, ".mdseal", "images", `${imageSha256}.image-witness.json`);

export const buildImageWitness = (root: string, model: DocumentModel, image: MdsealImageReference, policy: ImageWitnessPolicy = defaultImageWitnessConfig.policy): MdsealImageWitness => ({
  schema: "mdseal.image-witness.v1",
  toolVersion: "0.1.0",
  createdAt: new Date().toISOString(),
  sourceMarkdownFile: relFile(root, model.file),
  markdownPath: image.markdownPath,
  resolvedPath: image.resolvedPath,
  exists: image.exists,
  sha256: image.sha256,
  sizeBytes: image.sizeBytes,
  extension: image.extension,
  altText: image.altText,
  title: image.title,
  likelyEquation: image.likelyEquation,
  likelyEquationReason: image.likelyEquationReason,
  policy,
  ocr: { status: "not-run", provider: "none", result: null },
});

export const writeImageWitness = (root: string, witness: MdsealImageWitness) => {
  const p = witness.sha256 ? witnessPathFor(root, witness.sha256) : null;
  if (!p) return null;
  mkdirSync(dirname(p), { recursive: true });
  writeFileSync(p, `${JSON.stringify(witness, null, 2)}\n`, "utf-8");
  return p;
};

export const readImageWitness = (root: string, sha256: string) => {
  const p = witnessPathFor(root, sha256);
  if (!existsSync(p)) return null;
  return JSON.parse(readFileSync(p, "utf-8")) as MdsealImageWitness;
};

export const imageWitnessDiagnostics = (root: string, model: DocumentModel): Diagnostic[] => {
  const diags: Diagnostic[] = [];
  for (const img of model.images as MdsealImageReference[]) {
    if (!img.exists) continue;
    diags.push(diag("MDSEAL_IMAGE_WITNESS_SKIPPED", `image witness available for ${img.markdownPath}`, "info", { startOffset: img.startOffset, endOffset: img.endOffset, line: img.line, column: img.column, source: "validator" }));
  }
  return diags;
};

export const ensureWitnessOrRefuse = (policy: ImageWitnessPolicy, hasOcr: boolean) => {
  if (policy === "sidecar-only" || policy === "report-only") return null;
  if (!hasOcr) return refuse("MDSEAL_REFUSE_IMAGE_POLICY_REQUIRES_OCR", "image policy requires OCR", "cli");
  return null;
};
