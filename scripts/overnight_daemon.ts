#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: overnight_daemon.ts                           ║
// ║ MCP client integration - Observatory communication layer                   ║
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: ORANGE                                                 ║
// ║ Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ║ Purpose: Overnight daemon - deterministic repo-local batch runner          ║
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):                                      ║
// ║ Dependents (Rely on me):                                                ║
// ║   └─◄ scripts\sentry_init.ts                                            ║
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Overnight Daemon (Bun-centric, repo-local)
 *
 * Purpose:
 * - Provide a deterministic, repeatable “overnight loop” runner that does NOT require network access.
 * - Generate a prioritized queue of tiny, self-contained improvements based on repo-local signals.
 * - Optionally invoke the existing siphon tooling to fork an alternate working set into dumpster-dive.
 *
 * Non-goals:
 * - No auto-commits.
 * - No environment/profile mutation.
 * - No background auto-activation outside explicit invocation.
 */

import { join, resolve, dirname } from "path";
import { mkdir } from "fs/promises";
// import { initSentry } from "./sentry_init";

type TodoHit = {
  file: string;
  line: number;
  kind: "TODO" | "FIXME" | "HACK";
  text: string;
};

type CandidateFile = {
  relPath: string;
  size: number;
  mtimeMs: number;
  score: number;
  reasons: string[];
  todoHits: number;
};

// NEW: Enhanced classification types
type LanguageInfo = {
  extension: string;
  language: string;
  frameworks: string[];
};

type ComplexityMetrics = {
  cyclomatic: number;
  nestingDepth: number;
  functionCount: number;
  avgFunctionLength: number;
};

type FileClassification = {
  path: string;
  language: string;
  size: number;
  complexity: ComplexityMetrics;
  imports: string[];
  exports: string[];
  todoCount: number;
  docstringCount: number;
  commentDensity: number;
  patterns: string[];
  antiPatterns: string[];
  securityFlags: string[];
};

type FolderClassification = {
  path: string;
  primaryLanguage: string;
  purpose: string;
  fileCount: number;
  totalSize: number;
  averageComplexity: number;
  documentationCoverage: number;
  files: FileClassification[];
};

type Report = {
  generatedAt: string;
  repoRoot: string;
  config: {
    topN: number;
    maxTodoHits: number;
    enableSiphon: boolean;
    enableClassification?: boolean;
    durationMinutes?: number;
    intervalMinutes?: number;
    cycleIndex?: number;
    verify?: string[];
  };
  summary: {
    filesScanned: number;
    todoHits: number;
    topCandidates: number;
    verification?: {
      attempted: string[];
      ok: boolean;
      results: Array<{
        name: string;
        cmd: string;
        args: string[];
        exitCode: number;
        stdoutFile: string;
        stderrFile: string;
      }>;
    };
    siphon?: {
      dest: string;
      manifest?: string;
      attempted: boolean;
      ok: boolean;
      error?: string;
    };
  };
  topCandidates: CandidateFile[];
  todoHits: TodoHit[];
  languageMetrics?: {
    byLanguage: Record<string, number>;
    totalFiles: number;
  };
  complexityMetrics?: {
    averageComplexity: number;
    maxComplexity: number;
    maxComplexityFile: string;
    highComplexityFiles: Array<{ path: string; complexity: number }>;
  };
  narrativeDrift?: {
    score: number;
    vocabularyCoverage: number;
    usedTermsCount: number;
    totalLexiconTerms: number;
    topTerms: Array<[string, number]>;
    collisions: any[];
  };
  qualiaResonance?: {
    score: number;
    detected_terms: Array<{
      term: string;
      canonical: string;
      frequency: number;
      files: string[];
    }>;
  };
  classification?: {
    enabled: boolean;
    filesClassified: number;
    foldersAnalyzed: number;
  };
};

const TODO_SCAN_EXTENSIONS = new Set([
  ".rs", ".ts", ".tsx", ".js", ".jsx", ".py", ".ps1", ".psm1", ".psd1",
  ".go", ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".sh", ".bash", ".zsh",
  ".md", ".txt", ".rst", ".sql", ".toml", ".yaml", ".yml", ".html", ".css", ".scss", ".vue", ".svelte",
]);

const TODO_DOC_EXTENSIONS = new Set([".md", ".txt", ".rst"]);

function fileExtension(relPath: string): string {
  const p = relPath.replaceAll("\\", "/").toLowerCase();
  const idx = p.lastIndexOf(".");
  if (idx < 0) return "";
  return p.slice(idx);
}

function shouldScanTodoForPath(relPath: string): boolean {
  return TODO_SCAN_EXTENSIONS.has(fileExtension(relPath));
}

function isCommentCarrier(line: string): boolean {
  return /(^\s*(#|\/\/|\/\*|\*|--|;|<!--)\s*)|(?:\/\/|#|\/\*|--|;)/.test(line);
}

function nowStamp(): string {
  // Deterministic format; content varies by time but no randomness.
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function parseArgs(argv: string[]) {
  const args = new Map<string, string | boolean>();
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) {
      args.set(key, next);
      i++;
    } else {
      args.set(key, true);
    }
  }
  return args;
}

async function findRepoRoot(startDir: string): Promise<string> {
  let cur = resolve(startDir);
  for (;;) {
    const gitDir = join(cur, ".git");
    try {
      const st = await Bun.file(gitDir).exists();
      if (st) return cur;
    } catch {
      // ignore
    }

    const parent = dirname(cur);
    if (parent === cur) break;
    cur = parent;
  }
  // Fallback: assume script lives in repo/scripts.
  return resolve(startDir, "..");
}

function shouldExclude(relPath: string): boolean {
  const p = relPath.replaceAll("\\", "/");
  const hard = [
    ".git/",
    "target/",
    "build/",
    "dist/",
    "bin/",
    "obj/",
    "node_modules/",
    "dumpster-dive/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "coverage/",
    "codex/codex-session-logs/",
    "logs/sessions/",
    "meta-ide/LocalAI-3.11.0/",
    "meta-ide/copilot-cli-0.0.406/",
    "meta-ide/copilot-sdk/sdk/",
    "meta-ide/copilot-sdk/prebuilds/",
    "meta-ide/copilot-sdk/definitions/",
    "meta-ide/copilot-sdk/schemas/",
  ];
  for (const h of hard) {
    if (p.startsWith(h) || p.includes(`/${h}`)) return true;
  }
  // Keep the scan sane.
  if (
    p.endsWith(".spv") ||
    p.endsWith(".exe") ||
    p.endsWith(".dll") ||
    p.endsWith(".so") ||
    p.endsWith(".dylib") ||
    p.endsWith(".msi") ||
    p.endsWith(".zip") ||
    p.endsWith(".tar.gz") ||
    p.endsWith(".sqlite") ||
    p.endsWith(".db") ||
    p.endsWith(".png") ||
    p.endsWith(".jpg") ||
    p.endsWith(".jpeg") ||
    p.endsWith(".gif") ||
    p.endsWith(".webp") ||
    p.endsWith(".ico") ||
    p.endsWith(".woff") ||
    p.endsWith(".woff2") ||
    p.endsWith(".ttf") ||
    p.endsWith(".otf") ||
    p.endsWith(".pdf") ||
    p.endsWith(".map") ||
    p.endsWith(".min.js") ||
    p.endsWith(".min.css")
  ) return true;
  return false;
}

function calculateDebtScore(fc: FileClassification): { score: number; reasons: string[] } {
  let score = 0;
  const reasons: string[] = [];

  // Complexity weight: base level
  const comp = fc.complexity.cyclomatic;
  if (comp > 200) {
    score += 500;
    reasons.push("🚨 Critical Complexity: Giant file detected");
  } else if (comp > 100) {
    score += 250;
    reasons.push("⚠️ High Complexity: Needs decomposition");
  } else if (comp > 50) {
    score += 100;
    reasons.push("Moderate Complexity");
  }

  // Comment Density Inverse: Lower density = Higher Debt
  // Ideal density is ~0.2 (20%). If density is 0.05, multiplier is high.
  const density = fc.commentDensity;
  const docInverse = Math.max(0, 5 - (density * 10)); // 0.2 density -> 3 points, 0.0 density -> 5 points

  if (comp > 20) {
    const documentationDebt = Math.round(comp * docInverse);
    if (documentationDebt > 0) {
      score += documentationDebt;
      reasons.push(`Documentation Debt: ${documentationDebt} (rel to complexity: ${comp}, density: ${density.toFixed(2)})`);
    }
  }

  // Anti-patterns
  if (fc.antiPatterns.includes("long-function")) {
    score += 50;
    reasons.push("Anti-pattern: Long function detected");
  }
  if (fc.antiPatterns.includes("deeply-nested")) {
    score += 75;
    reasons.push("Anti-pattern: Deeply nested logic");
  }

  // Language specific governance
  if (fc.language === "rust" && fc.patterns.includes("unwrap")) {
    score += 30;
    reasons.push("Governance: Fragile error handling (unwrap)");
  }

  if ((fc.language === "typescript" || fc.language === "javascript") && fc.patterns.includes("any")) {
    score += 40;
    reasons.push("Governance: Type safety debt (any usage)");
  }

  return { score, reasons };
}

function baseScoreFor(relPath: string, fc?: FileClassification): { score: number; reasons: string[] } {
  const p = relPath.replaceAll("\\", "/");
  let score = 0;
  const reasons: string[] = [];

  const bump = (n: number, r: string) => {
    score += n;
    reasons.push(r);
  };

  // If we have classification data, use the Debt Score as the baseline
  if (fc) {
    const debt = calculateDebtScore(fc);
    score += debt.score;
    reasons.push(...debt.reasons);
  }

  if (p.startsWith(".github/instructions/")) bump(50, "governance: path-specific instructions");
  if (p === ".github/copilot-instructions.md") bump(45, "governance: SSOT monolith");
  if (p.startsWith(".github/tools/")) bump(35, "governance tooling");
  if (p.startsWith("scripts/")) bump(30, "repo tooling");
  if (p.startsWith("src/")) bump(25, "product code");
  if (p.startsWith(".vscode/")) bump(20, "editor/tooling config");

  if (p.endsWith(".rs")) bump(20, "rust code");
  if (p.endsWith(".ps1") || p.endsWith(".psm1") || p.endsWith(".psd1")) bump(18, "powershell tooling");
  if (p.endsWith(".toml")) bump(10, "project config (toml)");
  if (p.endsWith(".json")) bump(6, "data/config (json)");
  if (p.endsWith(".md")) bump(4, "documentation");

  // Penalize likely bulk / high-churn areas.
  if (p.includes("/from-github/") || p.includes("/forge/") || p.includes("/intake/")) {
    score -= 25;
    reasons.push("bulk area (de-prioritized)");
  }

  return { score, reasons };
}

function scanTodoLines(relPath: string, text: string): TodoHit[] {
  const hits: TodoHit[] = [];
  if (!shouldScanTodoForPath(relPath)) return hits;

  const ext = fileExtension(relPath);
  const docLike = TODO_DOC_EXTENSIONS.has(ext);
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!docLike && !isCommentCarrier(line)) continue;

    const m = /\b(TODO|FIXME|HACK)\b\s*:?\s*(.*)$/i.exec(line);
    if (!m) continue;
    const rawKind = m[1].toUpperCase();
    const kind = (rawKind === "TODO" || rawKind === "FIXME" || rawKind === "HACK") ? rawKind : "TODO";
    hits.push({
      file: "",
      line: i + 1,
      kind,
      text: (m[2] ?? "").trim().slice(0, 240),
    });
  }
  return hits;
}

// NEW: Language detection
function detectLanguage(filePath: string, content: string): LanguageInfo {
  const ext = filePath.slice(filePath.lastIndexOf("."));
  const languageMap: Record<string, string> = {
    ".rs": "rust",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".py": "python",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".psd1": "powershell",
    ".md": "markdown",
    ".json": "json",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".glsl": "glsl",
    ".vert": "glsl",
    ".frag": "glsl",
  };

  const language = languageMap[ext] || "unknown";
  const frameworks: string[] = [];

  // Framework detection via imports
  if (language === "rust") {
    const useMatches = content.matchAll(/use\s+(\w+)::/g);
    for (const m of useMatches) {
      const crate = m[1];
      if (["tokio", "serde", "vulkan", "ash", "winit"].includes(crate)) {
        frameworks.push(crate);
      }
    }
  } else if (language === "typescript" || language === "javascript") {
    const importMatches = content.matchAll(/import\s+.*?from\s+['"]([^'"]+)['"]/g);
    for (const m of importMatches) {
      const pkg = m[1];
      if (pkg.startsWith("react")) frameworks.push("react");
      if (pkg.startsWith("next")) frameworks.push("next.js");
      if (pkg.startsWith("bun")) frameworks.push("bun");
    }
  } else if (language === "python") {
    const importMatches = content.matchAll(/(?:from|import)\s+(\w+)/g);
    for (const m of importMatches) {
      const mod = m[1];
      if (["sqlite3", "dataclasses", "pathlib", "typing"].includes(mod)) {
        frameworks.push(mod);
      }
    }
  }

  return { extension: ext, language, frameworks: [...new Set(frameworks)] };
}

// NEW: Complexity analysis
function analyzeComplexity(content: string, language: string): ComplexityMetrics {
  const lines = content.split(/\r?\n/);
  let cyclomaticComplexity = 1; // Base complexity
  let maxNesting = 0;
  let currentNesting = 0;
  let functionCount = 0;
  let totalFunctionLines = 0;

  // Control flow keywords by language
  const controlFlowKeywords: Record<string, RegExp> = {
    rust: /\b(if|else if|match|while|for|loop)\b/,
    typescript: /\b(if|else if|switch|while|for|do)\b/,
    javascript: /\b(if|else if|switch|while|for|do)\b/,
    python: /\b(if|elif|while|for|match)\b/,
    powershell: /\b(if|elseif|switch|while|for|foreach)\b/i,
  };

  const funcKeywords: Record<string, RegExp> = {
    rust: /^\s*(?:pub\s+)?(?:async\s+)?fn\s+\w+/,
    typescript: /^\s*(?:export\s+)?(?:async\s+)?function\s+\w+|^\s*(?:const|let)\s+\w+\s*=\s*(?:async\s+)?\(/,
    javascript: /^\s*(?:export\s+)?(?:async\s+)?function\s+\w+|^\s*(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\(/,
    python: /^\s*(?:async\s+)?def\s+\w+/,
    powershell: /^\s*function\s+\w+|^\s*\$\w+\s*=\s*\{/i,
  };

  const controlFlowRegex = controlFlowKeywords[language];
  const funcRegex = funcKeywords[language];

  for (const line of lines) {
    // Count control flow for cyclomatic complexity
    if (controlFlowRegex && controlFlowRegex.test(line)) {
      cyclomaticComplexity++;
    }

    // Track nesting depth via indentation
    const indent = line.match(/^(\s*)/)?.[1].length ?? 0;
    const nestingLevel = Math.floor(indent / 2); // Assume 2-space indent
    currentNesting = nestingLevel;
    if (currentNesting > maxNesting) maxNesting = currentNesting;

    // Count functions
    if (funcRegex && funcRegex.test(line)) {
      functionCount++;
      totalFunctionLines += 1; // Simplified - count declaration line
    }
  }

  return {
    cyclomatic: cyclomaticComplexity,
    nestingDepth: maxNesting,
    functionCount,
    avgFunctionLength: functionCount > 0 ? Math.floor(lines.length / functionCount) : 0,
  };
}

// NEW: Extract imports/exports
function extractImportsExports(content: string, language: string): { imports: string[]; exports: string[] } {
  const imports: string[] = [];
  const exports: string[] = [];

  if (language === "rust") {
    // Rust use statements
    const useMatches = content.matchAll(/use\s+([\w:]+)/g);
    for (const m of useMatches) imports.push(m[1]);

    // Rust pub items (simplified)
    const pubMatches = content.matchAll(/pub\s+(?:fn|struct|enum|trait|mod)\s+(\w+)/g);
    for (const m of pubMatches) exports.push(m[1]);
  } else if (language === "typescript" || language === "javascript") {
    // TS/JS imports
    const importMatches = content.matchAll(/import\s+.*?from\s+['"]([^'"]+)['"]/g);
    for (const m of importMatches) imports.push(m[1]);

    // TS/JS exports
    const exportMatches = content.matchAll(/export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)/g);
    for (const m of exportMatches) exports.push(m[1]);
  } else if (language === "python") {
    // Python imports
    const importMatches = content.matchAll(/(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))/g);
    for (const m of importMatches) imports.push(m[1] || m[2]);

    // Python def (simplified - public functions not prefixed with _)
    const defMatches = content.matchAll(/^def\s+([a-zA-Z]\w+)/gm);
    for (const m of defMatches) {
      if (!m[1].startsWith("_")) exports.push(m[1]);
    }
  }

  return { imports: [...new Set(imports)], exports: [...new Set(exports)] };
}

// NEW: Pattern detection
function detectPatterns(content: string, language: string): { patterns: string[]; antiPatterns: string[]; securityFlags: string[] } {
  const patterns: string[] = [];
  const antiPatterns: string[] = [];
  const securityFlags: string[] = [];

  if (language === "rust") {
    if (/Result<.*,.*>/.test(content)) patterns.push("error-handling:Result");
    if (/async\s+fn/.test(content)) patterns.push("async-patterns");
    if (/\bpanic!\(/.test(content)) antiPatterns.push("panic-usage");
    if (/\.unwrap\(\)/.test(content)) antiPatterns.push("unwrap-usage");
    if (/unsafe\s*\{/.test(content)) securityFlags.push("unsafe-block");
  } else if (language === "typescript" || language === "javascript") {
    if (/async\s+function|async\s+\(/.test(content)) patterns.push("async-patterns");
    if (/:\s*any\b/.test(content)) antiPatterns.push("any-type-usage");
    if (/@ts-ignore/.test(content)) antiPatterns.push("ts-ignore");
    if (/dangerouslySetInnerHTML/.test(content)) securityFlags.push("dangerous-html");
    if (/eval\(/.test(content)) securityFlags.push("eval-usage");
  } else if (language === "python") {
    if (/async\s+def/.test(content)) patterns.push("async-patterns");
    if (/\beval\(/.test(content)) securityFlags.push("eval-usage");
    if (/\bexec\(/.test(content)) securityFlags.push("exec-usage");
  }

  // Cross-language secret detection
  if (/API_KEY|SECRET|PASSWORD|TOKEN/.test(content)) securityFlags.push("potential-secret");

  return { patterns: [...new Set(patterns)], antiPatterns: [...new Set(antiPatterns)], securityFlags: [...new Set(securityFlags)] };
}

// NEW: Documentation analysis
function analyzeDocumentation(content: string, language: string): { docstringCount: number; commentDensity: number } {
  const lines = content.split(/\r?\n/);
  let docstringCount = 0;
  let commentLineCount = 0;

  const docPatterns: Record<string, RegExp> = {
    rust: /^\s*\/\/\/|^\s*\/\*\*/,
    typescript: /^\s*\/\*\*|^\s*\/\/\//,
    javascript: /^\s*\/\*\*|^\s*\/\/\//,
    python: /^\s*"""|^\s*'''/,
    powershell: /^\s*<#|^\s*#/i,
  };

  const commentPatterns: Record<string, RegExp> = {
    rust: /^\s*\/\/|^\s*\/\*/,
    typescript: /^\s*\/\/|^\s*\/\*/,
    javascript: /^\s*\/\/|^\s*\/\*/,
    python: /^\s*#/,
    powershell: /^\s*#/i,
  };

  const docRegex = docPatterns[language];
  const commentRegex = commentPatterns[language];

  for (const line of lines) {
    if (docRegex && docRegex.test(line)) docstringCount++;
    if (commentRegex && commentRegex.test(line)) commentLineCount++;
  }

  return {
    docstringCount,
    commentDensity: lines.length > 0 ? commentLineCount / lines.length : 0,
  };
}

async function resolveExe(name: string, candidates: string[]): Promise<string> {
  for (const c of candidates) {
    if (!c) continue;
    try {
      if (await Bun.file(c).exists()) return c;
    } catch {
      // ignore
    }
  }
  return Bun.which(name) ?? name;
}

const RUBY_ROOT_CANDIDATES = [
  process.env.RUBY_ROOT,
  "C:\\Ruby40-x64",
  "D:\\Ruby40-x64",
  "C:\\Ruby35-x64",
  "D:\\Ruby35-x64",
  "C:\\Ruby34-x64",
  "D:\\Ruby34-x64",
  "C:\\Ruby33-x64",
  "D:\\Ruby33-x64",
  "C:\\Ruby32-x64",
  "D:\\Ruby32-x64",
  "C:\\Ruby31-x64",
  "D:\\Ruby31-x64",
].filter((value): value is string => Boolean(value));

function rubyToolchainCandidates(relativePath: string): string[] {
  return RUBY_ROOT_CANDIDATES.map((root) => join(root, relativePath));
}

const VERIFY_TOKENS = [
  "cargo-build",
  "cargo-test",
  "cargo-clippy",
  "uv-python",
  "polyglot-versions",
] as const;
type VerifyToken = typeof VERIFY_TOKENS[number];

function isVerifyToken(s: string): s is VerifyToken {
  return (VERIFY_TOKENS as readonly string[]).includes(s);
}

async function runAndLog(
  cwd: string,
  outDir: string,
  name: string,
  cmd: string,
  args: string[],
): Promise<{ exitCode: number; stdoutFile: string; stderrFile: string; cmd: string; args: string[] }> {
  const stdoutFile = join(outDir, `${name}.stdout.txt`);
  const stderrFile = join(outDir, `${name}.stderr.txt`);

  const proc = Bun.spawn([cmd, ...args], { cwd, stdout: "pipe", stderr: "pipe" });
  const [out, err] = await Promise.all([
    new Response(proc.stdout).text(),
    new Response(proc.stderr).text(),
  ]);
  const exitCode = await proc.exited;

  await Bun.write(stdoutFile, out);
  await Bun.write(stderrFile, err);

  return {
    exitCode,
    stdoutFile: stdoutFile.replaceAll("\\", "/"),
    stderrFile: stderrFile.replaceAll("\\", "/"),
    cmd,
    args,
  };
}

async function main() {
  try {
    const args = parseArgs(Bun.argv.slice(2));
  const topN = Number(args.get("top") ?? 20);
  const maxTodoHits = Number(args.get("maxTodo") ?? 80);
  const enableSiphon = Boolean(args.get("siphon"));
  const enableClassification = Boolean(args.get("classify")); // NEW
  const durationMinutes = Number(args.get("durationMinutes") ?? 0);
  const intervalMinutes = Number(args.get("intervalMinutes") ?? 15);
  const verifyRaw = args.get("verify");
  const verify = typeof verifyRaw === "string"
    ? verifyRaw
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0)
    : [];

  const unknownVerify = verify.filter((v) => !isVerifyToken(v));
  if (unknownVerify.length > 0) {
    console.error(`error: unknown --verify token(s): ${unknownVerify.join(", ")}`);
    console.error(`allowed: ${VERIFY_TOKENS.join(", ")}`);
    process.exit(2);
  }

  const scriptDir = dirname(Bun.fileURLToPath(import.meta.url));
  const repoRoot = await findRepoRoot(scriptDir);

  const outBase = join(repoRoot, "dumpster-dive", "intake", "overnight-daemon");
  const runStamp = nowStamp();
  const runDir = join(outBase, runStamp);
  await mkdir(runDir, { recursive: true });
  await Bun.write(join(runDir, ".keep"), "");

  async function runOnce(outDir: string, stamp: string, cycleIndex?: number) {
    const candidates: CandidateFile[] = [];
    const allTodoHits: TodoHit[] = [];
    const fileClassifications: FileClassification[] = []; // NEW
    const folderMap = new Map<string, FileClassification[]>(); // NEW

    // Enumerate files via filesystem walk.
    let filesScanned = 0;
    for await (const entry of new Bun.Glob("**/*").scan({ cwd: repoRoot, onlyFiles: true })) {
      const relPath = entry.replaceAll("\\", "/");
      if (shouldExclude(relPath)) continue;

      const full = join(repoRoot, relPath);

      let stat: { size: number; mtimeMs: number };
      try {
        const s = await Bun.file(full).stat();
        stat = { size: s.size, mtimeMs: s.mtimeMs };
      } catch {
        continue;
      }

      // Skip very large text files; keep deterministic and fast.
      if (stat.size > 2_000_000) continue;

      filesScanned++;

      let text = "";
      try {
        text = await Bun.file(full).text();
      } catch {
        // Skip files we can't read as text.
        continue;
      }

      const todoHits = scanTodoLines(relPath, text);
      for (const h of todoHits) h.file = relPath;
      allTodoHits.push(...todoHits);

      let classification: FileClassification | undefined;
      // NEW: Perform classification if enabled
      if (enableClassification) {
        const langInfo = detectLanguage(relPath, text);
        const complexity = analyzeComplexity(text, langInfo.language);
        const { imports, exports } = extractImportsExports(text, langInfo.language);
        const { patterns, antiPatterns, securityFlags } = detectPatterns(text, langInfo.language);
        const { docstringCount, commentDensity } = analyzeDocumentation(text, langInfo.language);

        classification = {
          path: relPath,
          language: langInfo.language,
          size: stat.size,
          complexity,
          imports,
          exports,
          todoCount: todoHits.length,
          docstringCount,
          commentDensity,
          patterns,
          antiPatterns,
          securityFlags,
        };

        fileClassifications.push(classification);

        // Group by folder
        const folder = relPath.includes("/") ? relPath.slice(0, relPath.lastIndexOf("/")) : "_root";
        if (!folderMap.has(folder)) folderMap.set(folder, []);
        folderMap.get(folder)!.push(classification);
      }

      // NOW calculate base score, passing classification if we have it
      const { score: base, reasons } = baseScoreFor(relPath, classification);

      // Small freshness bump (mtime), but capped to avoid time-dominance.
      const nowMs = Date.now();
      const ageMs = nowMs - stat.mtimeMs;
      const ageDays = ageMs / (1000 * 60 * 60 * 24);
      const freshness = Math.max(0, 10 - Math.floor(ageDays / 7));

      if (todoHits.length > 0) {
        reasons.push(`todos: ${todoHits.length}`);
      }

      candidates.push({
        relPath,
        size: stat.size,
        mtimeMs: stat.mtimeMs,
        score: base + freshness,
        reasons,
        todoHits: todoHits.length,
      });
    }

    // AGGREGATION: Build classification metrics if classification was enabled
    let languageMetrics: Report["languageMetrics"];
    let complexityMetrics: Report["complexityMetrics"];
    let classificationSummary: Report["classification"];

    if (enableClassification && fileClassifications.length > 0) {
      // Language metrics
      const langCounts = new Map<string, number>();
      let totalComplexity = 0;
      let maxComplexity = 0;
      let maxComplexityFile = "";

      for (const fc of fileClassifications) {
        langCounts.set(fc.language, (langCounts.get(fc.language) || 0) + 1);

        if (fc.complexity) {
          totalComplexity += fc.complexity.cyclomatic;
          if (fc.complexity.cyclomatic > maxComplexity) {
            maxComplexity = fc.complexity.cyclomatic;
            maxComplexityFile = fc.path;
          }
        }
      }

      languageMetrics = {
        byLanguage: Object.fromEntries(langCounts),
        totalFiles: fileClassifications.length,
      };

      complexityMetrics = {
        averageComplexity: fileClassifications.length > 0
          ? Math.round(totalComplexity / fileClassifications.length)
          : 0,
        maxComplexity,
        maxComplexityFile,
        highComplexityFiles: fileClassifications
          .filter(fc => fc.complexity && fc.complexity.cyclomatic > 20)
          .map(fc => ({ path: fc.path, complexity: fc.complexity!.cyclomatic }))
          .sort((a, b) => b.complexity - a.complexity)
          .slice(0, 10),
      };

      classificationSummary = {
        enabled: true,
        filesClassified: fileClassifications.length,
        foldersAnalyzed: folderMap.size,
      };
    }


    // Deterministic ranking.
    candidates.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.relPath.localeCompare(b.relPath);
    });

    const top = candidates.slice(0, Math.max(1, topN));

    // NEW: Run Narrative Scan via Python
    let narrativeDrift: Report["narrativeDrift"] | undefined;
    try {
      const pythonExe = await resolveExe("python", []);
      const proc = Bun.spawn([pythonExe, join(repoRoot, "scripts", "run_narrative_scan.py")], {
        cwd: repoRoot,
        stdout: "pipe",
        stderr: "ignore",
      });
      const output = await new Response(proc.stdout).text();
      const exitCode = await proc.exited;
      if (exitCode === 0) {
        const data = JSON.parse(output);
        narrativeDrift = {
          score: data.drift_score,
          vocabularyCoverage: data.vocabulary_coverage,
          usedTermsCount: data.used_terms_count,
          totalLexiconTerms: data.lexicon_size,
          topTerms: data.top_terms,
          collisions: data.collisions,
        };
      }
    } catch (e) {
      // ignore
    }

    // NEW: Run Qualia Check via Python
    let qualiaResonance: Report["qualiaResonance"] | undefined;
    try {
      const pythonExe = await resolveExe("python", []);
      const proc = Bun.spawn([pythonExe, join(repoRoot, "scripts", "run_qualia_check.py"), "mas_mcp"], {
        cwd: repoRoot,
        stdout: "pipe",
        stderr: "ignore",
      });
      const output = await new Response(proc.stdout).text();
      const exitCode = await proc.exited;
      if (exitCode === 0) {
        const data = JSON.parse(output);
        qualiaResonance = {
          score: data.qualia_score,
          detected_terms: data.detected_violations,
        };
      }
    } catch (e) {
      // ignore
    }

    const report: Report = {
      generatedAt: new Date().toISOString(),
      repoRoot,
      config: {
        topN,
        maxTodoHits,
        enableSiphon,
        enableClassification,
        durationMinutes: durationMinutes > 0 ? durationMinutes : undefined,
        intervalMinutes: durationMinutes > 0 ? intervalMinutes : undefined,
        cycleIndex,
        verify: verify.length > 0 ? verify : undefined,
      },
      summary: {
        filesScanned,
        todoHits: allTodoHits.length,
        topCandidates: top.length,
        siphon: enableSiphon
          ? { dest: "", attempted: true, ok: false }
          : undefined,
      },
      topCandidates: top,
      todoHits: allTodoHits,
      languageMetrics,
      complexityMetrics,
      narrativeDrift,
      qualiaResonance,
      classification: classificationSummary,
    };

    // Write JSON report.
    const jsonPath = join(outDir, "report.json");
    await Bun.write(jsonPath, JSON.stringify(report, null, 2));

    // Write folder-based classification JSON files if enabled
    if (enableClassification && folderMap.size > 0) {
      const classDir = join(outDir, "classifications");
      await mkdir(classDir, { recursive: true });

      for (const [folder, files] of folderMap.entries()) {
        // Calculate folder-level aggregations
        const langCounts = new Map<string, number>();
        let totalSize = 0;
        let totalComplexity = 0;
        let complexityCount = 0;
        let totalDocCoverage = 0;
        let docCount = 0;

        for (const fc of files) {
          langCounts.set(fc.language, (langCounts.get(fc.language) || 0) + 1);
          totalSize += fc.size;
          if (fc.complexity) {
            totalComplexity += fc.complexity.cyclomatic;
            complexityCount++;
          }
          if (fc.commentDensity !== undefined) {
            totalDocCoverage += fc.commentDensity;
            docCount++;
          }
        }

        // Determine primary language (most common)
        let primaryLanguage = "unknown";
        let maxCount = 0;
        for (const [lang, count] of langCounts.entries()) {
          if (count > maxCount) {
            maxCount = count;
            primaryLanguage = lang;
          }
        }

        // Infer purpose from folder name
        const folderName = folder === "_root" ? "root" : folder.split("/").pop() || folder;
        let purpose = "general";
        if (folderName.includes("test")) purpose = "testing";
        else if (folderName.includes("doc")) purpose = "documentation";
        else if (folderName.includes("script")) purpose = "automation";
        else if (folderName.includes("src") || folderName.includes("lib")) purpose = "core";
        else if (folderName.includes("asset") || folderName.includes("resource")) purpose = "resources";

        const folderClassification: FolderClassification = {
          path: folder,
          primaryLanguage,
          purpose,
          fileCount: files.length,
          totalSize,
          averageComplexity: complexityCount > 0 ? Math.round(totalComplexity / complexityCount) : 0,
          documentationCoverage: docCount > 0 ? Math.round((totalDocCoverage / docCount) * 100) / 100 : 0,
          files,
        };

        // Safe filename: replace / and \ with _
        const safeFilename = folder.replace(/[\/\\]/g, "_") + ".json";
        const folderJsonPath = join(classDir, safeFilename);
        await Bun.write(folderJsonPath, JSON.stringify(folderClassification, null, 2));
      }
    }

    // Write a compact Markdown report.
    const mdLines: string[] = [];
    mdLines.push(`# Overnight Daemon Report (${stamp})`);
    mdLines.push("");
    mdLines.push(`- Repo root: ${repoRoot.replaceAll("\\", "/")}`);
    mdLines.push(`- Files scanned: ${filesScanned}`);
    mdLines.push(`- TODO/FIXME/HACK hits (captured): ${allTodoHits.length}`);
    if (narrativeDrift) {
      mdLines.push(`- Cultural Drift Score: ${narrativeDrift.score}`);
      mdLines.push(`- Lexicon Coverage: ${Math.round(narrativeDrift.vocabularyCoverage * 100)}%`);
    }
    if (qualiaResonance) {
      mdLines.push(`- Qualia Resonance Score: ${qualiaResonance.score}`);
    }
    mdLines.push("");

    mdLines.push("## Top Candidates");
    mdLines.push("| Rank | File | Score | TODO hits | Reasons | ");
    mdLines.push("|---:|---|---:|---:|---| ");
    top.forEach((c, i) => {
      const reasons = c.reasons.slice(0, 4).join(", ");
      mdLines.push(`| ${i + 1} | ${c.relPath} | ${c.score} | ${c.todoHits} | ${reasons} |`);
    });

    mdLines.push("");
    mdLines.push("## TODO / FIXME / HACK (Sample)");
    mdLines.push("| File | Line | Kind | Text | ");
    mdLines.push("|---|---:|---|---| ");
    allTodoHits.slice(0, 40).forEach((h) => {
      const safe = h.text.replaceAll("|", "\\|");
      mdLines.push(`| ${h.file} | ${h.line} | ${h.kind} | ${safe} |`);
    });

    const mdPath = join(outDir, "report.md");
    await Bun.write(mdPath, mdLines.join("\n") + "\n");

    // Optional: run verification commands inside this single Bun process.
    if (verify.length > 0) {
      const home = process.env.USERPROFILE ?? "";
      const [cargo, rustc, uv, go, ruby, gcc, gpp, git] = await Promise.all([
        resolveExe("cargo", [join(home, ".cargo", "bin", "cargo.exe")]),
        resolveExe("rustc", [join(home, ".cargo", "bin", "rustc.exe")]),
        resolveExe("uv", [join(home, ".local", "bin", "uv.exe")]),
        resolveExe("go", ["C:\\Go\\bin\\go.exe", "C:\\Program Files\\Go\\bin\\go.exe"]),
        resolveExe("ruby", rubyToolchainCandidates(join("bin", "ruby.exe"))),
        resolveExe("gcc", rubyToolchainCandidates(join("msys64", "ucrt64", "bin", "gcc.exe"))),
        resolveExe("g++", rubyToolchainCandidates(join("msys64", "ucrt64", "bin", "g++.exe"))),
        resolveExe("git", ["C:\\Program Files\\Git\\cmd\\git.exe"]),
      ]);
      const bun = process.execPath;

      const results: Report["summary"]["verification"]["results"] = [];

      for (const v of verify as VerifyToken[]) {
        if (v === "cargo-build") {
          results.push({
            name: v,
            ...(await runAndLog(repoRoot, outDir, v, cargo, ["build"])),
          });
        } else if (v === "cargo-test") {
          results.push({
            name: v,
            ...(await runAndLog(repoRoot, outDir, v, cargo, ["test"])),
          });
        } else if (v === "cargo-clippy") {
          results.push({
            name: v,
            ...(await runAndLog(repoRoot, outDir, v, cargo, ["clippy", "--all-targets", "--all-features", "--", "-W", "clippy::pedantic"])),
          });
        } else if (v === "uv-python") {
          results.push({
            name: v,
            ...(await runAndLog(repoRoot, outDir, v, uv, ["python", "list", "--only-installed"])),
          });
        } else if (v === "polyglot-versions") {
          // Use built-in version flags. Keep it fast.
          results.push({ name: "bun", ...(await runAndLog(repoRoot, outDir, "bun", bun, ["--version"])) });
          results.push({ name: "uv", ...(await runAndLog(repoRoot, outDir, "uv", uv, ["--version"])) });
          results.push({ name: "cargo", ...(await runAndLog(repoRoot, outDir, "cargo", cargo, ["--version"])) });
          results.push({ name: "rustc", ...(await runAndLog(repoRoot, outDir, "rustc", rustc, ["--version"])) });
          results.push({ name: "go", ...(await runAndLog(repoRoot, outDir, "go", go, ["version"])) });
          results.push({ name: "ruby", ...(await runAndLog(repoRoot, outDir, "ruby", ruby, ["--version"])) });
          results.push({ name: "git", ...(await runAndLog(repoRoot, outDir, "git", git, ["--version"])) });
          results.push({ name: "gcc", ...(await runAndLog(repoRoot, outDir, "gcc", gcc, ["--version"])) });
          results.push({ name: "g++", ...(await runAndLog(repoRoot, outDir, "g++", gpp, ["--version"])) });
        }
      }

      const okAll = results.every((r) => r.exitCode === 0);
      report.summary.verification = { attempted: verify, ok: okAll, results };
      await Bun.write(jsonPath, JSON.stringify(report, null, 2));
    }

    // Optional: invoke PowerShell siphon tool to fork top candidates to dumpster-dive.
    if (enableSiphon) {
      const psExe = await resolveExe("pwsh", ["C:\\Program Files\\PowerShell\\7\\pwsh.exe", "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"]);
      const psScript = join(repoRoot, "scripts", "siphon_to_dumpster_dive.ps1");

      try {
        const relPaths = top.map((c) => c.relPath);
        const args = [
          "-NoProfile",
          "-ExecutionPolicy",
          "Bypass",
          "-File",
          psScript,
          "-DestRoot",
          join(repoRoot, "dumpster-dive", "intake", "overnight-siphon"),
          "-Paths",
          relPaths.join(","),
        ];

        const proc = Bun.spawn([psExe, ...args], {
          cwd: repoRoot,
          stdout: "pipe",
          stderr: "pipe",
        });

        const [out, err] = await Promise.all([
          new Response(proc.stdout).text(),
          new Response(proc.stderr).text(),
        ]);
        const exitCode = await proc.exited;

        await Bun.write(join(outDir, "siphon.stdout.txt"), out);
        await Bun.write(join(outDir, "siphon.stderr.txt"), err);

        report.summary.siphon = {
          dest: "dumpster-dive/intake/overnight-siphon",
          attempted: true,
          ok: exitCode === 0,
          error: exitCode === 0 ? undefined : `powershell exit ${exitCode}`,
        };

        await Bun.write(jsonPath, JSON.stringify(report, null, 2));
      } catch (e) {
        report.summary.siphon = {
          dest: "dumpster-dive/intake/overnight-siphon",
          attempted: true,
          ok: false,
          error: e instanceof Error ? e.message : String(e),
        };
        await Bun.write(jsonPath, JSON.stringify(report, null, 2));
      }
    }

    return { jsonPath, top: top[0]?.relPath ?? "(none)" };
  }

  const wantsLoop = Number.isFinite(durationMinutes) && durationMinutes > 0;
  const intervalMs = Math.max(0, intervalMinutes) * 60_000;
  const endAt = Date.now() + (wantsLoop ? durationMinutes * 60_000 : 0);

  const cycles: Array<{ cycleIndex: number; outDir: string; report: string; top: string }> = [];

  let cycleIndex = 1;
  while (true) {
    const cycleStamp = nowStamp();
    const outDir = wantsLoop
      ? join(runDir, `cycle_${String(cycleIndex).padStart(4, "0")}_${cycleStamp}`)
      : runDir;

    await mkdir(outDir, { recursive: true });

    const res = await runOnce(outDir, cycleStamp, wantsLoop ? cycleIndex : undefined);
    cycles.push({
      cycleIndex,
      outDir: outDir.replaceAll("\\", "/"),
      report: res.jsonPath.replaceAll("\\", "/"),
      top: res.top,
    });

    if (!wantsLoop) break;
    if (Date.now() >= endAt) break;

    cycleIndex++;
    if (intervalMs > 0) await Bun.sleep(intervalMs);
  }

  const runSummaryPath = join(runDir, "run.json");
  await Bun.write(
    runSummaryPath,
    JSON.stringify(
      {
        runStamp,
        repoRoot: repoRoot.replaceAll("\\", "/"),
        config: {
          topN,
          maxTodoHits,
          enableSiphon,
          durationMinutes: wantsLoop ? durationMinutes : undefined,
          intervalMinutes: wantsLoop ? intervalMinutes : undefined,
          verify: verify.length > 0 ? verify : undefined,
        },
        cycles,
      },
      null,
      2,
    ),
  );

  // Console output: minimal, deterministic.
  // (Keep this short so it’s usable in scheduled tasks.)
  if (wantsLoop) {
    console.log(`run: ${runSummaryPath.replaceAll("\\", "/")}`);
    const last = cycles[cycles.length - 1];
    if (last) {
      console.log(`report: ${last.report}`);
      console.log(`top: ${last.top}`);
    }
  } else {
      console.log(`report: ${cycles[0]?.report ?? runSummaryPath.replaceAll("\\", "/")}`);
      console.log(`top: ${cycles[0]?.top ?? "(none)"}`);
    }
  } catch (err: any) {
    console.error("FATAL ERROR:", err);
    throw err;
  }
}

await main().catch(err => {
  console.error("UNHANDLED REJECTION:", err);
  process.exit(1);
});
