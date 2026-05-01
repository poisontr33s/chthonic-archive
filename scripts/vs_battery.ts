#!/usr/bin/env bun
// @SID: VS_BATTERY_PROBE_V1
// scripts/vs_battery.ts
// Parse .vs/visualStudioInstaller/**/.vsconfig files → emit manifest/vs_battery.json
// Subcommands: audit | diff <a> <b> | install <name> | components <name>
//
// Usage:
//   bun run scripts/vs_battery.ts audit
//   bun run scripts/vs_battery.ts diff "VS_2022_BT" "VS_2026_BT"
//   bun run scripts/vs_battery.ts components "VS_2026_Community"
//   bun run scripts/vs_battery.ts install "VS_2026_Community" [--dry-run]

import { readdirSync, readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";

const REPO_ROOT = join(import.meta.dir, "..");
const VS_INSTALLER_DIR = join(REPO_ROOT, ".vs", "visualStudioInstaller");
const MANIFEST_OUT = join(REPO_ROOT, "manifest", "vs_battery.json");

// Component groups we care about for the chthonic stack
const NOTABLE_PATTERNS: Record<string, RegExp> = {
  vulkan_hlsl:    /VC\.Tools|VC\.Core|HLSL|CMake\.Project|Llvm\.Clang/,
  game_engines:   /Component\.(Cocos|Unity|Unreal)/,
  cuda_compute:   /CUDA|DirectML|NVIDIA/,
  cross_platform: /LinuxBuildTools|Android|MDD\.Linux|WslDebugging/,
  dotnet:         /NetCore\.Component|NetCore\.Runtime|Net\.Component\.\d/,
  python:         /PythonTools/,
  wdk:            /DriverKit/,
  vcpkg:          /Vcpkg/,
};

interface VsConfig {
  version: string;
  components: string[];
  extensions: string[];
}

interface BatteryEntry {
  name: string;             // Normalized short name
  path: string;             // vsconfig file path (relative to repo root)
  total_components: number;
  notable: Record<string, string[]>;
  workloads: string[];
}

interface BatteryManifest {
  generated_at: string;
  configs: BatteryEntry[];
  cross_diff: {
    unique_to: Record<string, string[]>;
    shared: string[];
  };
}

function normalizeName(folderName: string): string {
  return folderName
    .replace(/Visual_Studio_/g, "VS_")
    .replace(/SQL_Server_/g, "SSMS_")
    .replace(/_Insiders/g, "")
    .replace(/Management_Studio/g, "SSMS")
    .replace(/_Build_Tools/g, "_BT")
    .replace(/_/g, "_");
}

function parseConfig(filePath: string): VsConfig {
  const raw = readFileSync(filePath, "utf8");
  return JSON.parse(raw) as VsConfig;
}

function extractNotable(components: string[]): Record<string, string[]> {
  const result: Record<string, string[]> = {};
  for (const [category, pattern] of Object.entries(NOTABLE_PATTERNS)) {
    const matches = components.filter(c => pattern.test(c));
    if (matches.length > 0) result[category] = matches;
  }
  return result;
}

function extractWorkloads(components: string[]): string[] {
  return components.filter(c => c.startsWith("Microsoft.VisualStudio.Workload."));
}

function buildBattery(folderName: string): BatteryEntry | null {
  const configPath = join(VS_INSTALLER_DIR, folderName, ".vsconfig");
  if (!existsSync(configPath)) return null;

  const cfg = parseConfig(configPath);
  const relPath = `.vs/visualStudioInstaller/${folderName}/.vsconfig`;
  return {
    name: normalizeName(folderName),
    path: relPath,
    total_components: cfg.components.length,
    notable: extractNotable(cfg.components),
    workloads: extractWorkloads(cfg.components),
  };
}

function runAudit(): BatteryManifest {
  const folders = readdirSync(VS_INSTALLER_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  const configs: BatteryEntry[] = [];
  const allComponentSets: Record<string, Set<string>> = {};

  for (const folder of folders) {
    const entry = buildBattery(folder);
    if (!entry) continue;
    configs.push(entry);

    // Build per-config component set for diff
    const configPath = join(VS_INSTALLER_DIR, folder, ".vsconfig");
    const cfg = parseConfig(configPath);
    allComponentSets[entry.name] = new Set(cfg.components);
  }

  // Cross diff: unique_to[A] = components in A but not in any other
  const unique_to: Record<string, string[]> = {};
  const names = Object.keys(allComponentSets);
  for (const name of names) {
    const others = names.filter(n => n !== name);
    const uniq = [...allComponentSets[name]].filter(
      c => others.every(o => !allComponentSets[o].has(c))
    );
    if (uniq.length > 0) unique_to[name] = uniq.sort();
  }

  // Shared = in all configs
  const allSets = Object.values(allComponentSets);
  const shared = allSets.length > 0
    ? [...allSets[0]].filter(c => allSets.every(s => s.has(c))).sort()
    : [];

  const manifest: BatteryManifest = {
    generated_at: new Date().toISOString(),
    configs,
    cross_diff: { unique_to, shared },
  };

  writeFileSync(MANIFEST_OUT, JSON.stringify(manifest, null, 2), "utf8");
  return manifest;
}

function printAudit(manifest: BatteryManifest): void {
  console.log("\n⚡ VS Battery Audit\n");
  for (const c of manifest.configs) {
    console.log(`  ┌─ ${c.name} (${c.total_components} components)`);
    console.log(`  │  path: ${c.path}`);
    if (Object.keys(c.notable).length > 0) {
      console.log(`  │  notable:`);
      for (const [cat, items] of Object.entries(c.notable)) {
        console.log(`  │    ${cat}: ${items.length} components`);
      }
    }
    if (c.workloads.length > 0) {
      console.log(`  │  workloads: ${c.workloads.map(w => w.replace("Microsoft.VisualStudio.Workload.", "")).join(", ")}`);
    }
    console.log(`  └─`);
  }
  console.log(`\n  manifest → ${MANIFEST_OUT}`);
}

function runDiff(nameA: string, nameB: string): void {
  const manifest = runAudit();
  const a = manifest.configs.find(c => c.name === nameA);
  const b = manifest.configs.find(c => c.name === nameB);
  if (!a || !b) {
    const names = manifest.configs.map(c => c.name).join(", ");
    console.error(`Error: config not found. Available: ${names}`);
    process.exit(1);
  }

  // Re-read full component lists
  const folderA = readdirSync(VS_INSTALLER_DIR).find(f => normalizeName(f) === nameA)!;
  const folderB = readdirSync(VS_INSTALLER_DIR).find(f => normalizeName(f) === nameB)!;
  const cfgA = parseConfig(join(VS_INSTALLER_DIR, folderA, ".vsconfig"));
  const cfgB = parseConfig(join(VS_INSTALLER_DIR, folderB, ".vsconfig"));
  const setA = new Set(cfgA.components);
  const setB = new Set(cfgB.components);

  const onlyA = cfgA.components.filter(c => !setB.has(c));
  const onlyB = cfgB.components.filter(c => !setA.has(c));
  const both = cfgA.components.filter(c => setB.has(c));

  console.log(`\n  diff: ${nameA} vs ${nameB}`);
  console.log(`  shared: ${both.length}  only-${nameA}: ${onlyA.length}  only-${nameB}: ${onlyB.length}`);
  if (onlyA.length > 0) {
    console.log(`\n  ─ only in ${nameA} ─`);
    onlyA.slice(0, 30).forEach(c => console.log(`    ${c}`));
    if (onlyA.length > 30) console.log(`    ... (${onlyA.length - 30} more)`);
  }
  if (onlyB.length > 0) {
    console.log(`\n  ─ only in ${nameB} ─`);
    onlyB.slice(0, 30).forEach(c => console.log(`    ${c}`));
    if (onlyB.length > 30) console.log(`    ... (${onlyB.length - 30} more)`);
  }
}

function runComponents(name: string): void {
  const folder = readdirSync(VS_INSTALLER_DIR).find(f => normalizeName(f) === name);
  if (!folder) {
    const names = readdirSync(VS_INSTALLER_DIR).map(normalizeName).join(", ");
    console.error(`Error: config not found. Available: ${names}`);
    process.exit(1);
  }
  const cfg = parseConfig(join(VS_INSTALLER_DIR, folder, ".vsconfig"));
  console.log(`\n  Components in ${name} (${cfg.components.length} total):\n`);
  cfg.components.forEach(c => console.log(`    ${c}`));
}

// VS Installer CLI: finds vs_installer.exe or winget-based approach
async function runInstall(name: string, dryRun: boolean): Promise<void> {
  const folder = readdirSync(VS_INSTALLER_DIR).find(f => normalizeName(f) === name);
  if (!folder) {
    console.error(`Config "${name}" not found.`);
    process.exit(1);
  }
  const vsConfigPath = join(VS_INSTALLER_DIR, folder, ".vsconfig").replace(/\\/g, "\\\\");

  // Locate VS installer
  const installerCandidates = [
    "C:\\Program Files (x86)\\Microsoft Visual Studio\\Installer\\vs_installer.exe",
    "C:\\Program Files\\Microsoft Visual Studio\\Installer\\vs_installer.exe",
  ];
  const installer = installerCandidates.find(p => existsSync(p));

  if (!installer) {
    console.log(`\n  VS Installer not found at standard locations.`);
    console.log(`  Manual install command:`);
    console.log(`    winget install Microsoft.VisualStudio.2022.BuildTools --override "--config ${vsConfigPath}"`);
    return;
  }

  const cmd = `"${installer}" modify --config "${vsConfigPath}" --passive`;
  console.log(`\n  Battery: ${name}`);
  console.log(`  Config:  ${vsConfigPath}`);
  console.log(`  Command: ${cmd}`);

  if (dryRun) {
    console.log(`\n  [dry-run] — not executed`);
  } else {
    console.log(`\n  Launching VS Installer...`);
    const { spawnSync } = require("child_process");
    const result = spawnSync(installer, ["modify", "--config", vsConfigPath, "--passive"], {
      stdio: "inherit",
      shell: false,
    });
    if (result.status !== 0) {
      console.error(`  Installer exited with code ${result.status}`);
      process.exit(result.status ?? 1);
    }
  }
}

// --- Main ---
const [, , subcmd, ...args] = process.argv;

switch (subcmd) {
  case "audit":
  case undefined: {
    const manifest = runAudit();
    printAudit(manifest);
    break;
  }
  case "diff": {
    if (args.length < 2) { console.error("Usage: vs_battery.ts diff <A> <B>"); process.exit(1); }
    runDiff(args[0], args[1]);
    break;
  }
  case "components": {
    if (!args[0]) { console.error("Usage: vs_battery.ts components <name>"); process.exit(1); }
    runComponents(args[0]);
    break;
  }
  case "install": {
    if (!args[0]) { console.error("Usage: vs_battery.ts install <name> [--dry-run]"); process.exit(1); }
    const dryRun = args.includes("--dry-run");
    runInstall(args[0], dryRun);
    break;
  }
  default:
    console.error(`Unknown subcommand: ${subcmd}`);
    console.error("Subcommands: audit | diff <A> <B> | components <name> | install <name> [--dry-run]");
    process.exit(1);
}
