import type { DialectProfile, Diagnostic, ZoneKind, HtmlImageReference } from "./types";

export type ZoneSpan = { kind: ZoneKind; startOffset: number; endOffset: number; text: string };
export type ImageRef =
  | { kind: "markdown_image"; alt: string; path: string; title: string | null; startOffset: number; endOffset: number }
  | HtmlImageReference;

export type DocumentModel = {
  file: string;
  raw: Uint8Array;
  text: string;
  encoding: string;
  eol: "\n" | "\r\n";
  zones: ZoneSpan[];
  images: ImageRef[];
  diagnostics: Diagnostic[];
  dialect: DialectProfile;
};

export type SealManifest = {
  sourcePath: string;
  sourceSha256: string;
  lineEnding: string;
  encoding: string;
  zoneTable: ZoneSpan[];
  mathSpanTable: Array<{ startOffset: number; endOffset: number; raw: string; delimiter: string; hash: string }>;
  codeFenceSpans: Array<{ startOffset: number; endOffset: number; hash: string }>;
  frontmatterHash?: string;
  tableShapeHashes: Array<{ hash: string; rows: number; cols: number }>;
  imageReferences: Array<{ path: string; alt: string; sha256?: string }>;
  hiddenSymbols: Array<{ symbol: string; offset: number; zone?: ZoneKind }>;
  dialectProfile: string;
  toolVersion: string;
  createdAt: string;
  hashOnly?: boolean;
};
