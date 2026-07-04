import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import type { DocumentModel } from "./model";
import type { MdsealManifest } from "./types";
import { buildManifest, findSealPath } from "./seal-helpers";
import { sha256 } from "./bytes";

export const createSeal = (root: string, model: DocumentModel, hashOnly = false): MdsealManifest => buildManifest(root, model, hashOnly ? "hash-only" : "full");
export const sealPathFor = findSealPath;
export const writeSeal = (root: string, file: string, seal: MdsealManifest) => {
  const p = sealPathFor(root, file);
  mkdirSync(dirname(p), { recursive: true });
  writeFileSync(p, JSON.stringify(seal, null, 2).replace(/\r\n/g, "\n"), "utf-8");
  return p;
};
export const readSeal = (root: string, file: string) => JSON.parse(readFileSync(sealPathFor(root, file), "utf-8")) as MdsealManifest;
export const sealExists = (root: string, file: string) => existsSync(sealPathFor(root, file));
export const sealHash = (seal: MdsealManifest) => sha256(JSON.stringify(seal));
