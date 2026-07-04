import type { DialectProfile } from "./types";
import type { ImageWitnessConfig, KatexConfig } from "./types";
import type { ProviderConfig } from "./providers/types";

export const defaultProfile: DialectProfile = {
  name: "katex-gfm",
  inlineMathDelimiters: ["dollar", "paren", "github-backtick"],
  displayMathDelimiters: ["double-dollar", "bracket", "math-fence"],
  allowSingleDollarInline: true,
  allowEscapedParenMath: true,
  allowEscapedBracketMath: true,
  allowGithubBacktickMath: false,
  preserveFrontmatter: true,
  enableTables: true,
  protectRawHtml: true,
  protectCodeFences: true,
  escapePipesInsideTableMath: true,
  normalizeUnicodeInMath: true,
  allowHtmlEntityDecodeInMath: true,
};

export const defaultKatexConfig: KatexConfig = {
  enabled: true,
  strict: "warn",
  trust: false,
  maxExpand: 1000,
  macros: {},
  allowUnsupportedCommands: false,
  failOnUnsupportedCommands: false,
  failOnUnsafeCommands: true,
};

export const defaultImageWitnessConfig: ImageWitnessConfig = {
  enabled: true,
  policy: "sidecar-only",
  writeSidecars: true,
  equationFilenameHints: ["equation", "formula", "latex", "math", "expr", "expression", "derivation", "proof"],
  equationAltTextHints: ["equation", "formula", "latex", "math", "derivation", "proof"],
};

export const defaultProviderConfig: ProviderConfig = {
  enabled: false,
  defaultFormulaOcr: "none",
  defaultDocumentOcr: "none",
  defaultEmbedding: "none",
  defaultReranker: "none",
  allowNetwork: false,
  allowModelDownloads: false,
  pythonSidecar: { enabled: false, command: "uv", args: ["run", "python", "scripts/hf-mdseal-provider.py"] },
  transformersJs: { enabled: false, device: "webgpu", dtype: "q4" },
};
