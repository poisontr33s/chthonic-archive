#!/usr/bin/env bun
// @SID: SCRIPT_VERIFY_SONIC_LAKE_V1
// Verifier for the sonic history-lake + persistent calibration (SONIC_HISTORY / sonic_baseline.json).
// Induced-transition proof on an ISOLATED temp workspace — never touches the repo's live manifest.
// Deterministic checks PASS/FAIL regardless of whether audio is playing; audio-dependent facts
// (rotation, accrual amount) are reported, and rotation is asserted only when enough signal was
// produced to exercise it (else SKIPPED, named honestly).

import { spawn } from "child_process";
import { existsSync, mkdirSync, readFileSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

const EXE = join(
  process.cwd(),
  "extensions/chthonic-archive/native/target/release/sonic-daemon.exe",
);
const WS = join(tmpdir(), "sonic-lake-verify");
const MAN = join(WS, "manifest");
const HIST = join(MAN, "sonic_window_history.ndjson");
const HIST1 = join(MAN, "sonic_window_history.ndjson.1");
const BASE = join(MAN, "sonic_baseline.json");

let passes = 0;
let fails = 0;
function check(cond: boolean, label: string): void {
  if (cond) {
    passes++;
    console.log(`PASS  ${label}`);
  } else {
    fails++;
    console.log(`FAIL  ${label}`);
  }
}
function info(label: string): void {
  console.log(`  ..  ${label}`);
}
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
function isAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

interface Daemon {
  pid: number;
  stderr: () => string;
  stop: () => void;
}

function startDaemon(extraEnv: Record<string, string>): Daemon {
  let err = "";
  const child = spawn(EXE, [WS], {
    env: {
      ...process.env,
      SONIC_CAPTURE: "on",
      SONIC_HISTORY: "on",
      SONIC_REAP_ON_STDIN: "1",
      ...extraEnv,
    },
    stdio: ["pipe", "ignore", "pipe"],
    windowsHide: true,
  });
  child.stderr?.on("data", (d) => {
    err += String(d);
  });
  return {
    pid: child.pid ?? -1,
    stderr: () => err,
    stop: () => {
      try {
        child.stdin?.end();
      } catch {
        // best-effort
      }
    },
  };
}

function lineCount(path: string): number {
  if (!existsSync(path)) return 0;
  return readFileSync(path, "utf8").split("\n").filter((l) => l.trim().length).length;
}

async function main(): Promise<void> {
  if (!existsSync(EXE)) {
    console.log(`FAIL  daemon exe missing — build first: ${EXE}`);
    process.exit(1);
  }
  try {
    rmSync(WS, { recursive: true, force: true });
  } catch {
    // fresh slate
  }
  mkdirSync(MAN, { recursive: true });

  // ── Phase 1: the history lake ──────────────────────────────────────────
  // Tiny byte cap so a handful of non-silent lines force a rollover.
  const d1 = startDaemon({ SONIC_HISTORY_MAX_BYTES: "400" });
  check(d1.pid > 0 && isAlive(d1.pid), `daemon started — pid ${d1.pid}`);
  await sleep(8000);
  d1.stop();
  await sleep(1300);
  check(!isAlive(d1.pid), "daemon exited cleanly on stdin close");

  check(existsSync(HIST), "history lake file created");
  const lines = existsSync(HIST)
    ? readFileSync(HIST, "utf8").split("\n").filter((l) => l.trim().length)
    : [];
  let allValid = lines.length > 0;
  let nonSilent = 0;
  let silent = 0;
  for (const l of lines) {
    try {
      const o = JSON.parse(l) as { ts?: number; si?: boolean };
      if (typeof o.ts !== "number") allValid = false;
      if (o.si) silent++;
      else nonSilent++;
    } catch {
      allValid = false;
    }
  }
  check(allValid, `every line is valid JSON with a ts field (${lines.length} lines in current file)`);
  info(`current-file lines=${lines.length} non-silent=${nonSilent} silent-markers=${silent}`);

  // Rotation: PASS if rolled; FAIL if enough signal to exceed the cap but no roll; else SKIP.
  if (existsSync(HIST1)) {
    check(true, `history lake rotated at byte cap (.ndjson.1 present, ${lineCount(HIST1)} prior lines)`);
  } else if (nonSilent >= 6) {
    check(false, `history should have rotated (${nonSilent} non-silent lines exceed the 400B cap) but no .ndjson.1`);
  } else {
    info(`rotation not exercised — only ${nonSilent} non-silent lines (needs audio playing); SKIPPED`);
  }

  // ── Phase 2: calibration persists across a restart ─────────────────────
  check(existsSync(BASE), "baseline file written on clean shutdown");
  const readN = (): number => {
    try {
      return (JSON.parse(readFileSync(BASE, "utf8")) as { energy?: { n?: number } }).energy?.n ?? -1;
    } catch {
      return -1;
    }
  };
  const n1 = readN();
  info(`baseline energy.n after run 1 = ${n1}`);

  const d2 = startDaemon({});
  await sleep(2500);
  const resumed = /resumed baseline/.test(d2.stderr());
  check(resumed, 'restart loaded the persisted baseline ("resumed baseline" logged)');
  d2.stop();
  await sleep(1300);
  const n2 = readN();
  info(`baseline energy.n after run 2 = ${n2}`);
  check(n1 >= 0 && n2 >= n1, `baseline carried across restart, never reset (${n1} -> ${n2})`);

  for (const d of [d1, d2]) {
    if (isAlive(d.pid)) {
      try {
        process.kill(d.pid);
      } catch {
        // already gone
      }
    }
  }
  try {
    rmSync(WS, { recursive: true, force: true });
  } catch {
    // best-effort
  }

  console.log("");
  console.log(fails === 0 ? `PASS — all ${passes} checks` : `FAIL — ${fails} failed, ${passes} passed`);
  process.exit(fails === 0 ? 0 : 1);
}

void main();
