import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

type JsonValue = Record<string, unknown>;

const root = resolve(import.meta.dir, "..");
const coreDir = join(root, "core");
const debugCore = join(coreDir, "target", "debug", "deepseek-core.exe");
const releaseCore = join(coreDir, "target", "release", "deepseek-core.exe");
const corePath = Bun.file(debugCore).exists() ? debugCore : releaseCore;

if (!process.env.DEEPSEEK_API_KEY) {
  console.error("DEEPSEEK_API_KEY is not present; live DeepSeek probe was not run.");
  process.exit(2);
}

if (!Bun.file(corePath).exists()) {
  console.error(`deepseek-core.exe was not found at ${debugCore} or ${releaseCore}`);
  process.exit(2);
}

const tempRoot = mkdtempSync(join(tmpdir(), "chthonic-live-deepseek-"));
const probePath = join(tempRoot, "probe.txt");
const sessionPath = join(tempRoot, "session.json");
const probeUri = pathToFileURL(probePath).href;
writeFileSync(probePath, "hello world\n", "utf8");

const child = spawn(corePath, ["rpc"], {
  cwd: coreDir,
  env: {
    ...process.env,
    CHTHONIC_PROVIDER: "deepseek",
    DEEPSEEK_CODE_SESSION_PATH: sessionPath,
  },
  stdio: ["pipe", "pipe", "pipe"],
});

const lines: JsonValue[] = [];
let stdoutBuffer = "";
let stderrBuffer = "";

child.stdout.on("data", (chunk: Buffer) => {
  stdoutBuffer += chunk.toString("utf8");
  let newline = stdoutBuffer.indexOf("\n");
  while (newline >= 0) {
    const raw = stdoutBuffer.slice(0, newline).trim();
    stdoutBuffer = stdoutBuffer.slice(newline + 1);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as JsonValue;
        lines.push(parsed);
        summarize(parsed);
      } catch {
        console.log(`non-json stdout: ${raw}`);
      }
    }
    newline = stdoutBuffer.indexOf("\n");
  }
});

child.stderr.on("data", (chunk: Buffer) => {
  stderrBuffer += chunk.toString("utf8");
});

try {
  const prompt = [
    "You are a function that returns only one markdown fenced json block.",
    "Output exactly one JSON object following this schema and no commentary:",
    "```json",
    "{",
    '  "planId": "live-deepseek-probe-1",',
    '  "summary": "Insert a harmless live DeepSeek probe comment",',
    '  "edits": [',
    "    {",
    `      "uri": ${JSON.stringify(probeUri)},`,
    '      "range": { "start": { "line": 0, "character": 0 }, "end": { "line": 0, "character": 0 } },',
    '      "newText": "// live DeepSeek probe\\n"',
    "    }",
    "  ],",
    '  "requiredPermissions": ["writeFile"],',
    '  "createdAtMs": 1234567890',
    "}",
    "```",
    'The target file currently contains "hello world".',
    "Return only the fenced JSON block.",
  ].join("\n");

  send(child, {
    jsonrpc: "2.0",
    id: 1,
    method: "chat.stream",
    params: { text: prompt, workspace: "live-deepseek-edit-plan-probe" },
  });

  const planMessage = await waitFor(
    (message) => message.method === "edit/plan" || hasErrorForId(message, 1) || isCoreError(message),
    120_000,
  );

  if (hasErrorForId(planMessage, 1)) {
    throw new Error(`chat.stream failed: ${JSON.stringify(planMessage.error)}`);
  }
  if (isCoreError(planMessage)) {
    const params = planMessage.params as JsonValue | undefined;
    throw new Error(`chat.stream failed: ${String(params?.message ?? "core error")}`);
  }

  const plan = planMessage.params as JsonValue;
  const planId = String(plan.planId ?? "");
  if (!planId) {
    throw new Error(`edit/plan did not include planId: ${JSON.stringify(planMessage)}`);
  }

  send(child, {
    jsonrpc: "2.0",
    id: 2,
    method: "edit/confirm",
    params: { planId },
  });

  const diffMessage = await waitFor(
    (message) => message.method === "diff/apply" || hasErrorForId(message, 2),
    30_000,
  );
  if (hasErrorForId(diffMessage, 2)) {
    throw new Error(`edit/confirm failed: ${JSON.stringify(diffMessage.error)}`);
  }

  const confirmMessage = await waitFor((message) => message.id === 2, 30_000);
  if (hasErrorForId(confirmMessage, 2)) {
    throw new Error(`edit/confirm failed: ${JSON.stringify(confirmMessage.error)}`);
  }

  console.log("live DeepSeek edit-plan probe passed");
  console.log(`probeUri=${probeUri}`);
  console.log(`planId=${planId}`);
  console.log("standalone RPC verified edit/plan and diff/apply emission");
} finally {
  try {
    send(child, { jsonrpc: "2.0", id: 99, method: "core.shutdown", params: {} });
  } catch {
    // Process may already be gone.
  }
  setTimeout(() => child.kill(), 500).unref();
}

function send(process: ChildProcessWithoutNullStreams, payload: JsonValue) {
  process.stdin.write(`${JSON.stringify(payload)}\n`);
}

function summarize(message: JsonValue) {
  if (message.method === "chat.chunk") {
    return;
  }
  if (message.method === "core.log") {
    const params = message.params as JsonValue | undefined;
    console.log(`core.log ${params?.level ?? "info"}: ${params?.message ?? ""}`);
    return;
  }
  if (message.method === "edit/plan") {
    const params = message.params as JsonValue | undefined;
    const edits = Array.isArray(params?.edits) ? params.edits : [];
    const firstEdit = edits[0] as JsonValue | undefined;
    console.log(
      `edit/plan planId=${params?.planId ?? ""} edits=${edits.length} snippet=${Boolean(firstEdit?.snippetId)}`,
    );
    return;
  }
  if (message.method === "diff/apply") {
    const params = message.params as JsonValue | undefined;
    const edits = Array.isArray(params?.edits) ? params.edits : [];
    console.log(`diff/apply edits=${edits.length}`);
    return;
  }
  if (message.id !== undefined) {
    console.log(`response id=${message.id} ok=${!message.error}`);
  }
}

function hasErrorForId(message: JsonValue, id: number) {
  return message.id === id && Boolean(message.error);
}

function isCoreError(message: JsonValue) {
  const params = message.params as JsonValue | undefined;
  return message.method === "core.log" && params?.level === "error";
}

async function waitFor(predicate: (message: JsonValue) => boolean, timeoutMs: number) {
  const started = Date.now();
  let cursor = 0;
  while (Date.now() - started < timeoutMs) {
    while (cursor < lines.length) {
      const message = lines[cursor++];
      if (predicate(message)) {
        return message;
      }
    }
    if (child.exitCode !== null) {
      throw new Error(`deepseek-core exited with ${child.exitCode}: ${stderrBuffer.trim()}`);
    }
    await Bun.sleep(50);
  }
  throw new Error(`timed out waiting for RPC event; stderr=${stderrBuffer.trim()}`);
}
