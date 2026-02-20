import { spawn } from "node:child_process";
import { watch } from "node:fs";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

type CliOptions = {
  once: boolean;
  specPath?: string;
};

type CommandResult = {
  ok: boolean;
  command: string;
  exitCode: number | null;
  stdout: string;
  stderr: string;
};

type HandoffSignal = {
  status: "Ready for Implementation" | "Failed";
  detectedAt: string;
  reason: string;
  spec: {
    name: string;
    path: string;
    intent?: string;
    objective?: string;
  };
  context: {
    outputPath: string;
    refreshOk: boolean;
    command: string;
    exitCode: number | null;
    stdoutTail: string;
    stderrTail: string;
  };
};

const srcDir = path.dirname(fileURLToPath(import.meta.url));
const extensionDir = path.resolve(srcDir, "..");
const repoRoot = path.resolve(extensionDir, "..", "..");
const specsDir = path.join(repoRoot, ".chthonic", "specs");
const cacheDir = path.join(repoRoot, ".chthonic", "cache", "neural-bus");
const contextOutPath = path.join(cacheDir, "latest_context.md");
const localSignalPath = path.join(extensionDir, "handoff_signal.json");
const cacheSignalPath = path.join(cacheDir, "handoff_signal.json");
const compressorBin = path.join(
  repoRoot,
  "extensions",
  "context-compressor",
  "target",
  "debug",
  process.platform === "win32" ? "context-compressor.exe" : "context-compressor"
);
const compressorManifest = path.join(
  repoRoot,
  "extensions",
  "context-compressor",
  "Cargo.toml"
);
const targetSourceDir = path.join(repoRoot, "src");

const debounceMap = new Map<string, ReturnType<typeof setTimeout>>();

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));
  await fs.mkdir(cacheDir, { recursive: true });
  await fs.mkdir(specsDir, { recursive: true });

  if (options.once) {
    const candidate =
      options.specPath !== undefined
        ? resolveSpecPath(options.specPath)
        : await findLatestSpecFile();
    if (!candidate) {
      console.log("[BUS] No spec files found to process.");
      return;
    }
    await processSpec(candidate, "once");
    return;
  }

  console.log(`[BUS] Spec Enforcer ONLINE`);
  console.log(`[BUS] Watching: ${specsDir}`);
  console.log(`[BUS] Context target: ${targetSourceDir}`);

  watch(specsDir, { persistent: true }, (_eventType, filename) => {
    if (!filename) {
      return;
    }
    const name = filename.toString();
    if (!name.endsWith(".md")) {
      return;
    }
    const specPath = path.join(specsDir, name);

    const pending = debounceMap.get(specPath);
    if (pending) {
      clearTimeout(pending);
    }
    const timer = setTimeout(() => {
      void processSpec(specPath, "watch");
      debounceMap.delete(specPath);
    }, 400);
    debounceMap.set(specPath, timer);
  });
}

function parseArgs(args: string[]): CliOptions {
  const options: CliOptions = { once: false };
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--once") {
      options.once = true;
      continue;
    }
    if (arg === "--spec") {
      const value = args[i + 1];
      if (!value) {
        throw new Error("missing value for --spec");
      }
      options.specPath = value;
      i += 1;
      continue;
    }
    if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    }
    throw new Error(`unknown arg '${arg}'`);
  }
  return options;
}

function printHelp(): void {
  console.log(`spec-enforcer
Usage:
  bun run src/index.ts
  bun run src/index.ts --once
  bun run src/index.ts --once --spec <spec-path>
`);
}

function resolveSpecPath(input: string): string {
  if (path.isAbsolute(input)) {
    return input;
  }
  return path.resolve(repoRoot, input);
}

async function findLatestSpecFile(): Promise<string | undefined> {
  const files = await fs.readdir(specsDir, { withFileTypes: true });
  const specs = files.filter((entry) => entry.isFile() && entry.name.endsWith(".md"));
  if (specs.length === 0) {
    return undefined;
  }

  const withTimes = await Promise.all(
    specs.map(async (entry) => {
      const fullPath = path.join(specsDir, entry.name);
      const stat = await fs.stat(fullPath);
      return { fullPath, mtimeMs: stat.mtimeMs };
    })
  );
  withTimes.sort((a, b) => b.mtimeMs - a.mtimeMs);
  return withTimes[0]?.fullPath;
}

async function processSpec(specPath: string, reason: string): Promise<void> {
  let raw: string;
  try {
    raw = await fs.readFile(specPath, "utf8");
  } catch (err) {
    return;
  }

  const specName = path.basename(specPath);
  const intent = extractSection(raw, "Intent") ?? extractInlineValue(raw, "Intent");
  const objective =
    extractSection(raw, "Objective") ?? extractInlineValue(raw, "Objective");

  console.log(`[BUS] Detected Spec: ${specName}. Preparing Context...`);

  const cmd = await runCompressor();
  const signal: HandoffSignal = {
    status: cmd.ok ? "Ready for Implementation" : "Failed",
    detectedAt: new Date().toISOString(),
    reason,
    spec: {
      name: specName,
      path: path.relative(repoRoot, specPath).replaceAll("\\", "/"),
      intent: intent || undefined,
      objective: objective || undefined,
    },
    context: {
      outputPath: path.relative(repoRoot, contextOutPath).replaceAll("\\", "/"),
      refreshOk: cmd.ok,
      command: cmd.command,
      exitCode: cmd.exitCode,
      stdoutTail: tail(cmd.stdout, 1200),
      stderrTail: tail(cmd.stderr, 1200),
    },
  };

  const payload = `${JSON.stringify(signal, null, 2)}\n`;
  await fs.writeFile(localSignalPath, payload, "utf8");
  await fs.writeFile(cacheSignalPath, payload, "utf8");

  console.log(
    `[BUS] Handoff Signal: ${signal.status} -> ${path.relative(repoRoot, localSignalPath)}`
  );
}

async function runCompressor(): Promise<CommandResult> {
  const useBinary = await exists(compressorBin);
  if (useBinary) {
    return runCommand(
      compressorBin,
      ["--in", targetSourceDir, "--format", "md", "--out", contextOutPath],
      repoRoot
    );
  }
  return runCommand(
    "cargo",
    [
      "run",
      "--manifest-path",
      compressorManifest,
      "--",
      "--in",
      targetSourceDir,
      "--format",
      "md",
      "--out",
      contextOutPath,
    ],
    repoRoot
  );
}

async function exists(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function runCommand(
  command: string,
  args: string[],
  cwd: string
): Promise<CommandResult> {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd,
      shell: false,
      windowsHide: true,
      env: process.env,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (data: Buffer) => {
      stdout += data.toString("utf8");
    });
    child.stderr.on("data", (data: Buffer) => {
      stderr += data.toString("utf8");
    });
    child.on("close", (code) => {
      const commandString = [command, ...args].join(" ");
      resolve({
        ok: code === 0,
        command: commandString,
        exitCode: code,
        stdout,
        stderr,
      });
    });
    child.on("error", (err) => {
      const commandString = [command, ...args].join(" ");
      resolve({
        ok: false,
        command: commandString,
        exitCode: 1,
        stdout,
        stderr: `${stderr}\n${String(err)}`,
      });
    });
  });
}

function extractSection(markdown: string, heading: string): string | undefined {
  const normalized = markdown.replaceAll("\r\n", "\n");
  const lines = normalized.split("\n");
  const marker = `## ${heading}`;
  let startIndex = -1;
  for (let i = 0; i < lines.length; i += 1) {
    if (lines[i]?.trim() === marker) {
      startIndex = i + 1;
      break;
    }
  }
  if (startIndex < 0) {
    return undefined;
  }
  const parts: string[] = [];
  for (let i = startIndex; i < lines.length; i += 1) {
    const line = lines[i]?.trim() ?? "";
    if (line.startsWith("## ")) {
      break;
    }
    if (line.length > 0) {
      parts.push(line.replace(/^[-*]\s+/, "").trim());
    }
  }
  const joined = parts.join(" ").trim();
  return joined.length > 0 ? joined : undefined;
}

function extractInlineValue(markdown: string, key: string): string | undefined {
  const regex = new RegExp(`\\*\\*${key}:\\*\\*\\s*(.+)`, "i");
  const match = markdown.match(regex);
  if (!match?.[1]) {
    return undefined;
  }
  return match[1].trim();
}

function tail(value: string, maxChars: number): string {
  if (value.length <= maxChars) {
    return value.trim();
  }
  return value.slice(value.length - maxChars).trim();
}

main().catch((err) => {
  console.error(`[BUS] Spec Enforcer failed: ${String(err)}`);
  process.exit(1);
});

