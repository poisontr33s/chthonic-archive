#!/usr/bin/env bun

// @SID: BUILD_ICON_THEME_V1

// Generates extensions/chthonic-archive/themes/chthonic-file-icon-theme.json
// from the concise source manifest in themes/icons.source.ts
//
// Usage: bun run scripts/build-icon-theme.ts [--check]
//   --check  Diff only — exit 1 if generated output differs from on-disk file (CI gate)

import { writeFileSync, readFileSync, existsSync } from "fs";
import { resolve } from "path";
import { FILE_ICONS, FOLDER_ICONS } from "../extensions/chthonic-archive/themes/icons.source";

const OUT = resolve(import.meta.dir, "../extensions/chthonic-archive/themes/chthonic-file-icon-theme.json");
const CHECK = process.argv.includes("--check");

// ─── build iconDefinitions ────────────────────────────────────────────────────

const iconDefinitions: Record<string, object> = {};

for (const icon of FILE_ICONS) {
  iconDefinitions[`_${icon.id}`] = { iconPath: `./icons/${icon.svg}` };
}

// Default file + folder pairs
iconDefinitions["_file"]   = { iconPath: "./icons/file-default.svg" };
iconDefinitions["_folder"] = { iconPath: "./icons/folder-default.svg" };
iconDefinitions["_folderX"]= { iconPath: "./icons/folder-open.svg" };

for (const folder of FOLDER_ICONS) {
  iconDefinitions[`_${folder.id}`]  = { iconPath: `./icons/${folder.svg}` };
  iconDefinitions[`_${folder.id}X`] = { iconPath: `./icons/${folder.svgOpen}` };
}

// ─── build languageIds ────────────────────────────────────────────────────────

const languageIds: Record<string, string> = {};
for (const icon of FILE_ICONS) {
  for (const lang of icon.lang ?? []) {
    languageIds[lang] = `_${icon.id}`;
  }
}

// ─── build fileExtensions ─────────────────────────────────────────────────────

const fileExtensions: Record<string, string> = {};
for (const icon of FILE_ICONS) {
  for (const ext of icon.ext ?? []) {
    fileExtensions[ext] = `_${icon.id}`;
  }
}

// ─── build fileNames ─────────────────────────────────────────────────────────

const fileNames: Record<string, string> = {};
for (const icon of FILE_ICONS) {
  for (const name of icon.names ?? []) {
    fileNames[name] = `_${icon.id}`;
  }
}

// ─── build folderNames + folderNamesExpanded ──────────────────────────────────

const folderNames: Record<string, string> = {};
const folderNamesExpanded: Record<string, string> = {};
for (const folder of FOLDER_ICONS) {
  for (const name of folder.names) {
    folderNames[name]         = `_${folder.id}`;
    folderNamesExpanded[name] = `_${folder.id}X`;
  }
}

// ─── assemble theme ──────────────────────────────────────────────────────────

const theme = {
  iconDefinitions,
  file:           "_file",
  folder:         "_folder",
  folderExpanded: "_folderX",
  languageIds,
  fileExtensions,
  fileNames,
  folderNames,
  folderNamesExpanded,
};

const generated = JSON.stringify(theme, null, 2) + "\n";

if (CHECK) {
  if (!existsSync(OUT)) {
    console.error("[build-icon-theme] ✗ output file does not exist — run without --check first");
    process.exit(1);
  }
  const current = readFileSync(OUT, "utf8");
  if (current !== generated) {
    console.error("[build-icon-theme] ✗ chthonic-file-icon-theme.json is out of sync with icons.source.ts — run: bun run scripts/build-icon-theme.ts");
    process.exit(1);
  }
  console.log("[build-icon-theme] ✓ chthonic-file-icon-theme.json is in sync with icons.source.ts");
  process.exit(0);
}

writeFileSync(OUT, generated, "utf8");
console.log(`[build-icon-theme] ✓ wrote ${OUT}`);
