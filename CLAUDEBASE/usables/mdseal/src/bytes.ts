import { createHash } from "node:crypto";
export const sha256 = (bytes: Uint8Array | string) => createHash("sha256").update(bytes).digest("hex");
export const decodeUtf8 = (bytes: Uint8Array) => new TextDecoder("utf-8", { fatal: false }).decode(bytes);
export const encodeUtf8 = (text: string) => new TextEncoder().encode(text);
