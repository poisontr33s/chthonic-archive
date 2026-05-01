#!/usr/bin/env bun
// @SID: COCOS_PROBE_V1
/**
 * cocos_probe.ts — Cocos Dashboard + Creator discovery and headless CLI adapter
 *
 * Dashboard: C:\Program Files (x86)\CocosDashboard\CocosDashboard.exe (v2.2.1, Electron 31)
 * Creator: not yet installed — install via Dashboard, then re-run `bun run scripts/cocos_probe.ts probe`
 *
 * Subcommands:
 *   probe          — scan for installed Creator versions, emit manifest/cocos_probe.json
 *   info           — print discovered state (reads existing manifest if present)
 *   build <project> <platform> [options-json]  — headless build via Creator CLI
 *   open <project> — launch Creator GUI with a project
 *   dashboard      — print Dashboard launch command (with Vulkan GPU flags)
 */

import { existsSync, readFileSync, writeFileSync, readdirSync } from "fs";
import { join } from "path";
import { spawnSync, execSync } from "child_process";

// ─── Constants ────────────────────────────────────────────────────────────────

const DASHBOARD_EXE = "C:\\Program Files (x86)\\CocosDashboard\\CocosDashboard.exe";
const DASHBOARD_GPU_FLAGS = [
  "--ignore-gpu-blocklist",
  "--use-vulkan",
  "--enable-features=Vulkan",
  "--disable-gpu-compositing",
  "--enable-gpu-rasterization",
  "--enable-native-gpu-memory-buffers",
];

// Dashboard stores installed editors in its Electron user-data leveldb
// %APPDATA%\Cocos\ — LevelDB (CURRENT, MANIFEST-*, *.log)
// Can't easily parse LevelDB without native module; use path scan instead.

const CREATOR_SEARCH_ROOTS = [
  // Dashboard-managed (actual default on Windows)
  "C:\\ProgramData\\cocos\\editors\\Creator",
  join(process.env.PROGRAMDATA || "C:\\ProgramData", "cocos", "editors", "Creator"),
  // Legacy / custom paths
  "C:\\CocosCreator",
  join(process.env.USERPROFILE || "", "CocosCreator"),
  join(process.env.LOCALAPPDATA || "", "CocosCreator"),
  join(process.env.APPDATA || "", "CocosCreator"),
  "D:\\CocosCreator",
  "E:\\CocosCreator",
];

const MANIFEST_PATH = join(import.meta.dir, "../manifest/cocos_probe.json");

// ─── Types ────────────────────────────────────────────────────────────────────

interface CreatorInstall {
  version: string;
  exe: string;
  root: string;
}

interface CocosProbManifest {
  generated: string;
  dashboard: {
    exe: string;
    version: string;
    exists: boolean;
    gpu_flags: string[];
  };
  creators: CreatorInstall[];
  registry_entries: string[];
  status: "ready" | "creator_missing" | "dashboard_missing";
}

// ─── Discovery ────────────────────────────────────────────────────────────────

function findCreatorInstalls(): CreatorInstall[] {
  const found: CreatorInstall[] = [];

  // 1. Filesystem scan — Dashboard installs Creator under version subdirs
  const seenExes = new Set<string>();
  const uniqueRoots = [...new Set(CREATOR_SEARCH_ROOTS)];
  for (const root of uniqueRoots) {
    if (!existsSync(root)) continue;
    try {
      const entries = readdirSync(root, { withFileTypes: true });
      for (const e of entries) {
        if (!e.isDirectory()) continue;
        // Creator 3.x: Creator/<version>/CocosCreator.exe
        const creatorDir = join(root, e.name);
        const candidates = [
          join(creatorDir, "CocosCreator.exe"),
          join(creatorDir, "Creator", "CocosCreator.exe"),
          join(creatorDir, "editor", "CocosCreator.exe"),
        ];
        for (const exe of candidates) {
          if (existsSync(exe) && !seenExes.has(exe)) {
            seenExes.add(exe);
            found.push({ version: e.name, exe, root: creatorDir });
          }
        }
      }
    } catch {
      /* skip inaccessible */
    }
  }

  // 2. Windows Registry scan (HKCU and HKLM)
  const regPaths = [
    "HKCU\\SOFTWARE\\CocosCreator",
    "HKLM\\SOFTWARE\\CocosCreator",
    "HKCU\\SOFTWARE\\Wow6432Node\\CocosCreator",
    "HKLM\\SOFTWARE\\Wow6432Node\\CocosCreator",
  ];
  for (const rp of regPaths) {
    try {
      const out = execSync(`reg query "${rp}" /s 2>nul`, { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });
      const lines = out.split("\n").filter((l) => l.includes(".exe"));
      for (const line of lines) {
        const m = line.match(/([A-Z]:\\[^\r\n]+\.exe)/i);
        if (m && existsSync(m[1]) && !found.find((f) => f.exe === m[1])) {
          found.push({ version: "registry", exe: m[1], root: m[1].replace(/[^\\]+$/, "") });
        }
      }
    } catch {
      /* key not present */
    }
  }

  return found;
}

function readRegistryEntries(): string[] {
  const entries: string[] = [];
  try {
    const out = execSync(`reg query "HKCU\\SOFTWARE\\CocosCreator" /s 2>nul`, {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
    });
    entries.push(...out.split("\n").filter((l) => l.trim()));
  } catch {
    /* not present */
  }
  return entries;
}

// ─── Subcommands ──────────────────────────────────────────────────────────────

function cmdProbe() {
  const dashExists = existsSync(DASHBOARD_EXE);
  const creators = findCreatorInstalls();
  const registry = readRegistryEntries();

  const manifest: CocosProbManifest = {
    generated: new Date().toISOString(),
    dashboard: {
      exe: DASHBOARD_EXE,
      version: "2.2.1",
      exists: dashExists,
      gpu_flags: DASHBOARD_GPU_FLAGS,
    },
    creators,
    registry_entries: registry,
    status: !dashExists ? "dashboard_missing" : creators.length === 0 ? "creator_missing" : "ready",
  };

  writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2));

  console.log("\n⚡ Cocos Probe\n");
  console.log(`  Dashboard: ${dashExists ? "✓" : "✗"} ${DASHBOARD_EXE}`);
  console.log(`  Dashboard version: 2.2.1 (Electron 31)`);
  console.log(`  Creator installs: ${creators.length}`);

  if (creators.length === 0) {
    console.log("\n  ⚠  Creator not installed.");
    console.log("     Launch the Dashboard and install Creator 3.8.x:");
    console.log(`     ${DASHBOARD_EXE}`);
    console.log(`     ${DASHBOARD_GPU_FLAGS.join(" ")}`);
    console.log("\n     Default install path (Dashboard-managed): C:\\ProgramData\\cocos\\editors\\Creator\\<version>\\");
    console.log("\n     After install, re-run: bun run scripts/cocos_probe.ts probe");
  } else {
    for (const c of creators) {
      console.log(`\n  Creator ${c.version}`);
      console.log(`    exe : ${c.exe}`);
      console.log(`    root: ${c.root}`);
    }
  }

  console.log(`\n  manifest → ${MANIFEST_PATH}\n`);
}

function cmdInfo() {
  if (!existsSync(MANIFEST_PATH)) {
    console.log("No manifest found. Run: bun run scripts/cocos_probe.ts probe");
    process.exit(1);
  }
  const m: CocosProbManifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf8"));
  console.log(JSON.stringify(m, null, 2));
}

function cmdBuild(args: string[]) {
  // build <project-path> <platform> [json-options]
  const projectPath = args[0];
  const platform = args[1];
  const extraJson = args[2];

  if (!projectPath || !platform) {
    console.error("Usage: cocos_probe.ts build <project-path> <platform> [options-json]");
    console.error("Platforms: web-mobile web-desktop windows mac-os android ios");
    console.error("Example: bun run scripts/cocos_probe.ts build ./game web-mobile");
    process.exit(1);
  }

  // Find Creator exe
  const creators = findCreatorInstalls();
  if (creators.length === 0) {
    console.error("ERROR: No Creator installation found. Run `bun run scripts/cocos_probe.ts probe` first.");
    process.exit(1);
  }

  // Use newest version (last in list) or first found
  const creator = creators[creators.length - 1];
  console.log(`Using Creator: ${creator.version} @ ${creator.exe}`);

  // Build options
  const buildOpts = extraJson
    ? JSON.parse(extraJson)
    : { platform, debug: false };

  const buildJson = JSON.stringify(buildOpts);

  console.log(`Building: ${projectPath}`);
  console.log(`Options: ${buildJson}`);

  // Creator 3.x headless CLI:
  // CocosCreator.exe --path <project> --build <json-or-platform>
  const result = spawnSync(creator.exe, ["--path", projectPath, "--build", buildJson], {
    stdio: "inherit",
    encoding: "utf8",
  });

  process.exit(result.status ?? 0);
}

function cmdOpen(args: string[]) {
  const projectPath = args[0];
  const creators = findCreatorInstalls();
  if (creators.length === 0) {
    console.error("ERROR: No Creator installation found.");
    process.exit(1);
  }
  const creator = creators[creators.length - 1];
  const result = spawnSync(creator.exe, projectPath ? ["--path", projectPath] : [], {
    detached: true,
    stdio: "ignore",
  });
  console.log(`Opened Creator ${creator.version}${projectPath ? ` with ${projectPath}` : ""}`);
  process.exit(result.status ?? 0);
}

function cmdDashboard() {
  console.log("\nCocos Dashboard launch command:\n");
  console.log(`"${DASHBOARD_EXE}"`);
  console.log(DASHBOARD_GPU_FLAGS.join(" "));
  console.log("\nFull command:");
  console.log(`"${DASHBOARD_EXE}" ${DASHBOARD_GPU_FLAGS.join(" ")}`);
  console.log("\nNote: --use-vulkan flags are for GPU compositing (Electron GUI).");
  console.log("      Headless Creator CLI does not need these flags.\n");
}

// ─── CLI dispatch ─────────────────────────────────────────────────────────────

const [, , subcmd, ...rest] = process.argv;

switch (subcmd) {
  case "probe":
  case undefined:
    cmdProbe();
    break;
  case "info":
    cmdInfo();
    break;
  case "build":
    cmdBuild(rest);
    break;
  case "open":
    cmdOpen(rest);
    break;
  case "dashboard":
    cmdDashboard();
    break;
  default:
    console.error(`Unknown subcommand: ${subcmd}`);
    console.error("Available: probe | info | build | open | dashboard");
    process.exit(1);
}
