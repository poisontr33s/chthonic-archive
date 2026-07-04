#!/usr/bin/env bun

// @SID: CI_CHECK_THEME_ICON_VALIDATE_V1

/**
 * Validates the chthonic-archive file icon theme and sync integrity.
 *
 * Checks:
 *   1. Every iconPath referenced in chthonic-file-icon-theme.json exists on disk.
 *   2. Every icon definition referenced in fileExtensions/fileNames/folderNames is declared.
 *   3. No declared icon definition is unreferenced (dead definitions).
 *   4. Sync integrity: chthonic-themes/themes/ matches chthonic-archive/themes/ (sha256 per file).
 *
 * Exit 0 = all pass. Exit 1 = failures found.
 * --report  emit structured JSON to stdout.
 */

import { createHash } from "crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "fs";
import { dirname, join, resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const REPORT = process.argv.includes("--report");

const ARCHIVE_THEMES = join(REPO_ROOT, "extensions/chthonic-archive/themes");
const DERIVED_THEMES = join(REPO_ROOT, "extensions/chthonic-themes/themes");
const ICON_THEME_FILE = join(ARCHIVE_THEMES, "chthonic-file-icon-theme.json");

// ─── helpers ──────────────────────────────────────────────────────────────────

function sha256File(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function allFilesIn(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const entries = readdirSync(dir, { withFileTypes: true });
  const results: string[] = [];
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) results.push(...allFilesIn(full));
    else results.push(full);
  }
  return results;
}

function relTo(base: string, full: string): string {
  return full.slice(base.length + 1).replace(/\\/g, "/");
}

// ─── 1+2+3: icon definition + reference validation ───────────────────────────

type Failure = { check: string; detail: string };
const failures: Failure[] = [];
const warnings: string[] = [];

let theme: any;
try {
  theme = JSON.parse(readFileSync(ICON_THEME_FILE, "utf8"));
} catch (e) {
  failures.push({ check: "parse", detail: `Failed to parse ${ICON_THEME_FILE}: ${e}` });
  finish();
}

const defs: Record<string, string> = {}; // id → iconPath (for file icons)
const referencedIds = new Set<string>();
const declaredIds = new Set<string>();

for (const [id, def] of Object.entries<any>(theme.iconDefinitions ?? {})) {
  declaredIds.add(id);
  if (def.iconPath) {
    const abs = resolve(dirname(ICON_THEME_FILE), def.iconPath);
    defs[id] = abs;
    if (!existsSync(abs)) {
      failures.push({ check: "missing-svg", detail: `${id} → ${def.iconPath} does not exist` });
    }
  }
}

// Collect all referenced IDs from the mapping sections
const mappingSections = [
  theme.file, theme.folder, theme.folderExpanded,
  ...Object.values<string>(theme.languageIds ?? {}),
  ...Object.values<string>(theme.fileExtensions ?? {}),
  ...Object.values<string>(theme.fileNames ?? {}),
  ...Object.values<string>(theme.folderNames ?? {}),
  ...Object.values<string>(theme.folderNamesExpanded ?? {}),
];
for (const id of mappingSections) {
  if (typeof id === "string") referencedIds.add(id);
}

// Undeclared references
for (const id of referencedIds) {
  if (!declaredIds.has(id)) {
    failures.push({ check: "undeclared-ref", detail: `Reference to undeclared icon id: "${id}"` });
  }
}

// Dead declarations (warn, not fail — might be intentional)
for (const id of declaredIds) {
  if (!referencedIds.has(id)) {
    warnings.push(`Dead icon definition (never referenced): "${id}"`);
  }
}

// Paired open/closed folder check
for (const [name, id] of Object.entries<string>(theme.folderNames ?? {})) {
  const openId = theme.folderNamesExpanded?.[name];
  if (!openId) {
    warnings.push(`folderNames["${name}"] = "${id}" has no folderNamesExpanded counterpart`);
  }
}

// ─── 4: product icon theme validation ────────────────────────────────────────

const PRODUCT_THEME_FILE = join(ARCHIVE_THEMES, "chthonic-product-icon-theme.json");
const FONT_MAP_FILE = join(ARCHIVE_THEMES, "fonts/chthonic-product-icons.json");

if (existsSync(PRODUCT_THEME_FILE) && existsSync(FONT_MAP_FILE)) {
  let productTheme: any;
  let fontMap: Record<string, string>;
  try {
    productTheme = JSON.parse(readFileSync(PRODUCT_THEME_FILE, "utf8"));
    fontMap = JSON.parse(readFileSync(FONT_MAP_FILE, "utf8"));
  } catch (e) {
    failures.push({ check: "product-parse", detail: `Failed to parse product icon theme or font map: ${e}` });
    fontMap = {};
    productTheme = {};
  }

  // Build set of valid codepoints from font map: "U+E001" → 0xE001
  const validCodepoints = new Set<number>();
  for (const cp of Object.values(fontMap)) {
    validCodepoints.add(parseInt(cp.replace("U+", ""), 16));
  }

  const usedCodepoints = new Set<number>();
  const unusedFontChars: string[] = [];

  for (const [iconId, def] of Object.entries<any>(productTheme.iconDefinitions ?? {})) {
    if (def.fontCharacter) {
      // fontCharacter is the actual Unicode char after JSON parse (e.g. \uE001)
      const charCode = def.fontCharacter.codePointAt(0)!;
      usedCodepoints.add(charCode);
      if (!validCodepoints.has(charCode)) {
        failures.push({
          check: "product-missing-glyph",
          detail: `Product icon "${iconId}" uses U+${charCode.toString(16).toUpperCase().padStart(4, '0')} not in font map`,
        });
      }
    }
  }

  // Warn on unused font characters
  for (const [name, cp] of Object.entries(fontMap)) {
    const charCode = parseInt(cp.replace("U+", ""), 16);
    if (!usedCodepoints.has(charCode)) {
      warnings.push(`Product font glyph "${name}" (${cp}) is in font map but not used by any icon definition`);
    }
  }

  // Detect extensions/folder collision (known design limitation — pending E02D glyph addition)
  const extensionsDef = productTheme.iconDefinitions?.extensions?.fontCharacter;
  const folderDef = productTheme.iconDefinitions?.folder?.fontCharacter;
  if (extensionsDef && folderDef && extensionsDef.codePointAt(0) === folderDef.codePointAt(0)) {
    warnings.push(
      `"extensions" and "folder" share fontCharacter U+${extensionsDef.codePointAt(0)!.toString(16).toUpperCase().padStart(4,'0')} — they render identically. ` +
      `Fix: run \`uv run scripts/build-product-icon-font.py --add-glyph\` to add E02D, then update theme to use E02D for folder/workspace entries.`
    );
  }
}

// ─── 5: sync integrity ────────────────────────────────────────────────────────

type SyncResult = { missing: string[]; stale: string[]; extra: string[] };
const sync: SyncResult = { missing: [], stale: [], extra: [] };

if (existsSync(DERIVED_THEMES)) {
  const sourceFiles = allFilesIn(ARCHIVE_THEMES).map(f => relTo(ARCHIVE_THEMES, f));
  const derivedFiles = new Set(allFilesIn(DERIVED_THEMES).map(f => relTo(DERIVED_THEMES, f)));

  for (const rel of sourceFiles) {
    if (!derivedFiles.has(rel)) {
      sync.missing.push(rel);
    } else {
      const srcHash = sha256File(join(ARCHIVE_THEMES, rel));
      const drvHash = sha256File(join(DERIVED_THEMES, rel));
      if (srcHash !== drvHash) sync.stale.push(rel);
    }
  }
  for (const rel of derivedFiles) {
    if (!sourceFiles.includes(rel)) sync.extra.push(rel);
  }

  if (sync.missing.length > 0) {
    failures.push({
      check: "sync-missing",
      detail: `${sync.missing.length} file(s) in chthonic-archive/themes not in chthonic-themes/themes: ${sync.missing.slice(0, 5).join(", ")}${sync.missing.length > 5 ? " ..." : ""}`,
    });
  }
  if (sync.stale.length > 0) {
    failures.push({
      check: "sync-stale",
      detail: `${sync.stale.length} file(s) differ between source and derived: ${sync.stale.slice(0, 5).join(", ")}${sync.stale.length > 5 ? " ..." : ""}. Run: bun run --cwd extensions/chthonic-themes sync-themes`,
    });
  }
} else {
  warnings.push("chthonic-themes/themes/ not found — sync check skipped (run sync-themes first)");
}

// ─── output ──────────────────────────────────────────────────────────────────

function finish() {
  const passed = failures.length === 0;

  if (REPORT) {
    console.log(JSON.stringify({ passed, failures, warnings, sync }, null, 2));
  } else {
    if (warnings.length > 0) {
      for (const w of warnings) console.warn(`[theme-icon-validate] WARN  ${w}`);
    }
    if (passed) {
      console.log(`[theme-icon-validate] ✓ all checks passed (${declaredIds.size} icons, ${referencedIds.size} references)`);
    } else {
      for (const f of failures) {
        console.error(`[theme-icon-validate] ✗ [${f.check}] ${f.detail}`);
      }
      console.error(`[theme-icon-validate] ✗ ${failures.length} check(s) failed`);
    }
  }
  process.exit(passed ? 0 : 1);
}

finish();
