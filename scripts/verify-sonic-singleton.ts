#!/usr/bin/env bun
// @SID: SCRIPT_VERIFY_SONIC_SINGLETON_V1
/**
 * verify-sonic-singleton.ts — proves the shared-singleton daemon by inducing the real
 * transitions (per "validate a state-changer by inducing the transition, not a no-op"):
 *
 *   1. one reader spawns exactly one daemon, which claims the lock + writes a window
 *   2. a SECOND daemon started while the first is alive stands down (peer-detect) — no 2nd daemon
 *   3. daemonAlive() (the predicate the MCP attaches on) reads true while the lock beat is fresh
 *   4. the daemon SURVIVES while readers keep touching — it is detached (we only touch a file)
 *   5. once readers go stale (all sessions closed), the daemon SELF-EXITS and releases the lock
 *
 * Isolated under a temp workspace so it never touches the user's live window/lock. Uses short
 * idle/grace via env so the run takes seconds, not the 45s production idle window.
 *
 * Run:  bun run scripts/verify-sonic-singleton.ts
 * Exit: 0 = all assertions PASS, 1 = any FAIL.
 */
import { spawn as nodeSpawn } from "child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

const REPO = process.cwd();
const EXE = join(REPO, "extensions/chthonic-archive/native/target/release/sonic-daemon.exe");
const WS = join(tmpdir(), "sonic-singleton-verify");
const MANIFEST = join(WS, "manifest");
const LOCK = join(MANIFEST, "sonic_daemon.lock");
const READERS = join(MANIFEST, "sonic_daemon.readers");
const WINDOW = join(MANIFEST, "sonic_window.json");

const IDLE_MS = 3000;
const GRACE_MS = 1000;

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function isAlive(pid: number | undefined): boolean {
  if (!pid) return false;
  try {
    process.kill(pid, 0); // signal 0 = existence check
    return true;
  } catch {
    return false;
  }
}

function spawnDaemon(): number | undefined {
  const child = nodeSpawn(EXE, [WS], {
    env: {
      ...process.env,
      SONIC_SINGLETON: "1",
      SONIC_CAPTURE: "on",
      SONIC_SINGLETON_IDLE_MS: String(IDLE_MS),
      SONIC_SINGLETON_GRACE_MS: String(GRACE_MS),
    },
    detached: true,
    stdio: ["ignore", "ignore", "inherit"], // surface daemon stderr so the proof is visible
    windowsHide: true,
  });
  child.unref();
  return child.pid;
}

function touch(): void {
  try {
    mkdirSync(MANIFEST, { recursive: true });
    writeFileSync(READERS, String(Date.now()));
  } catch {
    // best-effort
  }
}

function readLock(): { pid?: number; beat_ms?: number } | null {
  try {
    return JSON.parse(readFileSync(LOCK, "utf8")) as { pid?: number; beat_ms?: number };
  } catch {
    return null;
  }
}

const results: Array<{ name: string; pass: boolean }> = [];
function check(name: string, pass: boolean, detail = ""): void {
  results.push({ name, pass });
  console.log(`${pass ? "PASS" : "FAIL"}  ${name}${detail ? ` — ${detail}` : ""}`);
}

async function main(): Promise<void> {
  if (!existsSync(EXE)) {
    console.error(
      `[verify] daemon exe missing: ${EXE}\n  build: cargo build --manifest-path extensions/chthonic-archive/native/Cargo.toml -p sonic-daemon --release`,
    );
    process.exit(1);
  }

  // Clean slate.
  try {
    rmSync(WS, { recursive: true, force: true });
  } catch {
    // ignore
  }
  mkdirSync(MANIFEST, { recursive: true });

  // A live reader heartbeat for the first phases.
  touch();
  const beat = setInterval(touch, 500);

  // ── 1. first daemon claims the lock + produces a window ──
  const pidA = spawnDaemon();
  await sleep(2500); // startup + claim + first snapshot (or first blocked-retry — both beat the lock)
  check("daemonA process alive", isAlive(pidA), `pid ${pidA}`);
  check("lock claimed by daemonA", readLock()?.pid === pidA, `lock.pid=${readLock()?.pid} expected ${pidA}`);
  check("window file written", existsSync(WINDOW));

  // ── 2. second daemon stands down (peer-detect) — no second daemon ──
  const pidB = spawnDaemon();
  await sleep(2000); // B reads the fresh lock, prints "already serving", exits
  check("daemonB stood down (no 2nd daemon)", !isAlive(pidB), `pid ${pidB}`);
  check("lock still owned by daemonA", readLock()?.pid === pidA, `lock.pid=${readLock()?.pid}`);

  // ── 3. attach predicate (what the MCP uses to decide not to spawn) ──
  const l = readLock();
  const fresh = typeof l?.beat_ms === "number" && Date.now() - l.beat_ms < 4000;
  check("daemonAlive() true while serving (MCP attaches)", fresh);

  // ── 4. survives while readers stay fresh (detached: we only touch a file) ──
  await sleep(2000);
  check("daemonA survives with live readers", isAlive(pidA), `pid ${pidA}`);

  // ── 5. self-exits + releases lock once all readers go stale ──
  clearInterval(beat); // every session "closes" — stop touching
  await sleep(IDLE_MS + GRACE_MS + 2500); // idle window + beat slack
  check("daemonA self-exited after readers idle", !isAlive(pidA), `pid ${pidA}`);
  check("lock released on self-exit", !existsSync(LOCK), `lock present=${existsSync(LOCK)}`);

  // Cleanup.
  for (const pid of [pidA, pidB]) {
    if (isAlive(pid)) {
      try {
        process.kill(pid!);
      } catch {
        // ignore
      }
    }
  }
  try {
    rmSync(WS, { recursive: true, force: true });
  } catch {
    // ignore
  }

  const failed = results.filter((r) => !r.pass).length;
  console.log(
    `\n${failed ? `FAIL — ${failed}/${results.length} checks failed` : `PASS — all ${results.length} checks`}`,
  );
  process.exit(failed ? 1 : 0);
}

void main().catch((e) => {
  console.error(`[verify] crashed: ${e}`);
  process.exit(1);
});
