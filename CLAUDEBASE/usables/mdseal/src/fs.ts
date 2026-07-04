import { decodeUtf8, encodeUtf8, sha256 } from "./bytes";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

export const readDocument = (file: string) => {
  const raw = readFileSync(file);
  const text = decodeUtf8(raw);
  const eol = text.includes("\r\n") ? "\r\n" : "\n";
  return { raw, text, eol, encoding: "utf-8", sha256: sha256(raw) };
};
export const writeText = (file: string, text: string) => {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, text, "utf-8");
};
export const ensureDir = (file: string) => mkdirSync(file, { recursive: true });
export const exists = existsSync;
export const abs = resolve;
export const joinPath = join;
