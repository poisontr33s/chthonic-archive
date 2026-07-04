export type ZoneKind =
  | "frontmatter"
  | "code_fence"
  | "inline_code"
  | "html_block"
  | "html_inline"
  | "link_destination"
  | "image_destination"
  | "image_alt_text"
  | "math_inline"
  | "math_display"
  | "markdown_table"
  | "blockquote"
  | "list_item"
  | "plain_text"
  | "unknown";

export type DialectProfile = {
  name: string;
  inlineMathDelimiters: Array<"dollar" | "paren" | "github-backtick">;
  displayMathDelimiters: Array<"double-dollar" | "bracket" | "math-fence">;
  allowSingleDollarInline: boolean;
  allowEscapedParenMath: boolean;
  allowEscapedBracketMath: boolean;
  allowGithubBacktickMath: boolean;
  preserveFrontmatter: boolean;
  enableTables: boolean;
  protectRawHtml: boolean;
  protectCodeFences: boolean;
  escapePipesInsideTableMath: boolean;
  normalizeUnicodeInMath: boolean;
  allowHtmlEntityDecodeInMath: boolean;
};

export type Diagnostic = {
  code: string;
  message: string;
  severity: "info" | "warning" | "error";
  file?: string;
  startOffset?: number;
  endOffset?: number;
  line?: number;
  column?: number;
  zone?: ZoneKind;
  detail?: string;
  suggestedFix?: boolean;
  confidence?: number;
  source?: "deterministic-rule" | "validator" | "seal" | "provider" | "cli";
};

export type Patch = {
  file: string;
  code: string;
  description: string;
  confidence: number;
  replacements: Array<{ startOffset: number; endOffset: number; before: string; after: string }>;
  protectedZoneTouches: Array<{ zone: ZoneKind; reason: string }>;
};

export type MdsealZoneSeal = {
  id: string;
  kind: ZoneKind;
  startOffset: number;
  endOffset: number;
  startLine: number;
  endLine: number;
  sha256: string;
  preview: string;
};

export type MdsealMathSeal = {
  id: string;
  zoneId: string;
  kind: "inline" | "display";
  delimiter: "single-dollar" | "double-dollar" | "paren" | "bracket" | "github-backtick" | "math-fence" | "unknown";
  startOffset: number;
  endOffset: number;
  startLine: number;
  endLine: number;
  sha256: string;
  contentSha256: string;
  raw?: string;
  normalizedLatex: string;
  leftContextSha256: string;
  rightContextSha256: string;
  leftContextPreview: string;
  rightContextPreview: string;
};

export type MdsealFenceSeal = {
  id: string;
  language: string | null;
  delimiter: string;
  startOffset: number;
  endOffset: number;
  startLine: number;
  endLine: number;
  sha256: string;
  contentSha256: string;
};

export type MdsealTableSeal = {
  id: string;
  startLine: number;
  endLine: number;
  columnCount: number;
  rowCount: number;
  shapeSha256: string;
  headerSha256: string;
};

export type MdsealImageSeal = {
  id: string;
  markdownPath: string;
  resolvedPath: string | null;
  exists: boolean;
  altText: string;
  title: string | null;
  sha256: string | null;
  sizeBytes: number | null;
  likelyEquation: boolean;
  ocrSidecar: string | null;
};

export type MdsealImageReference = {
  id: string;
  file: string;
  markdownPath: string;
  resolvedPath: string | null;
  exists: boolean;
  altText: string;
  title: string | null;
  line: number;
  column: number;
  startOffset: number;
  endOffset: number;
  sha256: string | null;
  sizeBytes: number | null;
  extension: string | null;
  likelyEquation: boolean;
  likelyEquationReason: string | null;
};

export type HtmlImageSrcsetCandidate = {
  url: string;
  descriptor: string | null;
  isRemote: boolean;
  isDataUri: boolean;
  isRelative: boolean;
  isAbsolute: boolean;
};

export type HtmlImageSourceCandidate = {
  tagName: "source";
  src: string | null;
  srcset: HtmlImageSrcsetCandidate[];
  type: string | null;
  media: string | null;
  rawAttributes: Record<string, string>;
};

export type HtmlImageReference = {
  kind: "html_image";
  tagName: "img" | "source" | "picture";
  src: string | null;
  alt?: string;
  title?: string;
  width?: string;
  height?: string;
  srcset?: HtmlImageSrcsetCandidate[];
  sourceTagCandidates?: HtmlImageSourceCandidate[];
  isRemote: boolean;
  isDataUri: boolean;
  isRelative: boolean;
  isAbsolute: boolean;
  line?: number;
  column?: number;
  startOffset?: number;
  endOffset?: number;
  rawAttributes: Record<string, string>;
  container?: "picture" | "html_block" | "html_inline";
};

export type ImageWitnessPolicy = "sidecar-only" | "report-only" | "add-alt-latex" | "add-adjacent-caption" | "add-html-comment";

export type ImageWitnessConfig = {
  enabled: boolean;
  policy: ImageWitnessPolicy;
  writeSidecars: boolean;
  equationFilenameHints: string[];
  equationAltTextHints: string[];
};

export type MdsealImageWitness = {
  schema: "mdseal.image-witness.v1";
  toolVersion: string;
  createdAt: string;
  sourceMarkdownFile: string;
  markdownPath: string;
  resolvedPath: string | null;
  exists: boolean;
  sha256: string | null;
  sizeBytes: number | null;
  extension: string | null;
  altText: string;
  title: string | null;
  likelyEquation: boolean;
  likelyEquationReason: string | null;
  policy: ImageWitnessPolicy;
  ocr: {
    status: "not-run";
    provider: "none";
    result: null;
  };
};

export type ProviderConfig = {
  enabled: boolean;
  defaultFormulaOcr: string;
  defaultDocumentOcr: string;
  defaultEmbedding: string;
  defaultReranker: string;
  allowNetwork: boolean;
  allowModelDownloads: boolean;
  pythonSidecar: {
    enabled: boolean;
    command: string;
    args: string[];
    cwd?: string;
  };
  transformersJs: {
    enabled: boolean;
    device: "cpu" | "webgpu" | "wasm";
    dtype: "fp32" | "fp16" | "q8" | "q4";
  };
};

export type MdsealHiddenSymbolSeal = {
  codepoint: string;
  name: string;
  offset: number;
  line: number;
  column: number;
  zoneKind: ZoneKind;
};

export type MdsealManifest = {
  schema: "mdseal.v1";
  toolVersion: string;
  createdAt: string;
  file: string;
  sha256: string;
  encoding: "utf8";
  lineEndings: "lf" | "crlf" | "mixed" | "unknown";
  profile: string;
  hashMode: "full" | "hash-only";
  document: {
    byteLength: number;
    lineCount: number;
    headingIndex: Array<{ level: number; text: string; line: number; sha256: string }>;
  };
  zones: MdsealZoneSeal[];
  math: MdsealMathSeal[];
  fences: MdsealFenceSeal[];
  tables: MdsealTableSeal[];
  images: MdsealImageSeal[];
  hiddenSymbols: MdsealHiddenSymbolSeal[];
};

export type SealContextMatch = {
  matched: boolean;
  confidence: number;
  reason: string;
  matchedStartOffset?: number;
  matchedEndOffset?: number;
};

export type RepairRule = {
  code: string;
  description: string;
  appliesTo: ZoneKind[];
  detect(input: import("./model").DocumentModel): Diagnostic[];
  fix(input: import("./model").DocumentModel, diagnostic: Diagnostic): Patch | null;
};

export type ValidationGateResult = {
  passed: boolean;
  gates: Array<{ name: string; status: "passed" | "failed" | "skipped"; diagnostics: Diagnostic[] }>;
  parserComparison?: ParserComparisonResult;
  katex?: KatexValidationResult;
};

export type ParserName = "remark-gfm-math" | "micromark-gfm-math" | "markdownlint";

export type MarkdownStructureSummary = {
  headings: number;
  codeFences: number;
  tables: number;
  mathInline: number;
  mathDisplay: number;
  htmlBlocks: number;
  links: number;
  images: number;
  listItems: number;
  blockquotes: number;
};

export type ParserDisagreement = {
  code: string;
  severity: "error" | "warning" | "info";
  message: string;
  parserA: ParserName;
  parserB: ParserName;
  field: keyof MarkdownStructureSummary;
  before?: number;
  after?: number;
};

export type ParserComparisonResult = {
  passed: boolean;
  parsers: Array<{ name: ParserName; status: "passed" | "failed" | "skipped"; diagnostics: Diagnostic[]; summary: MarkdownStructureSummary }>;
  disagreements: ParserDisagreement[];
};

export type KatexValidationStatus = "passed" | "failed" | "unsupported" | "unsafe" | "skipped";
export type KatexIssueKind = "syntax-error" | "unsupported-command" | "unsafe-command" | "delimiter-error" | "macro-error" | "strictness-warning" | "unicode-warning" | "unknown";
export type KatexMathValidation = {
  id: string;
  file: string;
  kind: "inline" | "display";
  delimiter: string;
  line: number;
  column: number;
  raw: string;
  latex: string;
  status: KatexValidationStatus;
  issueKind?: KatexIssueKind;
  message?: string;
  command?: string;
  confidence: number;
};
export type KatexValidationResult = {
  passed: boolean;
  mathCount: number;
  passedCount: number;
  failedCount: number;
  unsupportedCount: number;
  unsafeCount: number;
  skippedCount: number;
  math: KatexMathValidation[];
  diagnostics: Diagnostic[];
};

export type MdsealJsonResult = {
  command: string;
  status: "passed" | "failed" | "warning";
  files: Array<{
    file: string;
    profile: string;
    seal: {
      status: "missing" | "present" | "stale" | "hash-only";
      path: string | null;
    };
    diagnostics: Diagnostic[];
    patches: Patch[];
    validation: ValidationGateResult;
    wrote: boolean;
    backupPath?: string;
    images?: {
      count: number;
      existing: number;
      missing: number;
      likelyEquation: number;
      witnessWritten: number;
      witnessSkipped: number;
      hashChanged: number;
      witnesses: Array<{
        markdownPath: string;
        witnessPath: string | null;
        status: "written" | "skipped" | "missing" | "stale" | "report-only";
        sha256: string | null;
        likelyEquation: boolean;
      }>;
    };
  }>;
  summary: {
    filesChecked: number;
    filesChanged: number;
    diagnostics: number;
    errors: number;
    warnings: number;
  };
};
